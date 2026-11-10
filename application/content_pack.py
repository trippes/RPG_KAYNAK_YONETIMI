"""Data-driven content loading for the playable starter slice."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType

from application import GameplayService
from character import Ability, CharacterClass, CharacterFactory, Race
from core.domain.spatial import Position
from npc import Faction, NPC
from quests import Dialogue, DialogueChoice, DialogueNode
from resources import Inventory, Quantity, ResourceType, ResourceUnit, WorldResourceNode
from world import Location, WorldMap


DEFAULT_CONTENT_PATH = Path(__file__).resolve().parent.parent / "data" / "starter_content.json"
CONTENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StarterContentIds:
    world_id: str = "demo_valley"
    hero_id: str = "hero"
    village_id: str = "village"
    forest_id: str = "forest"
    faction_id: str = "wardens"
    npc_id: str = "warden_lyra"


class ContentDefinitionError(ValueError):
    """Raised when a content definition cannot safely enter the runtime."""


def load_starter_content(path: str | Path | None = None) -> dict:
    """Load and validate a JSON content definition without mutating it."""
    if path is None:
        candidates = (
            DEFAULT_CONTENT_PATH,
            Path(sys.prefix) / "data" / "starter_content.json",
            Path(sys.prefix) / "starter_content.json",
        )
        source = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    else:
        source = Path(path)
    try:
        definition = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentDefinitionError(f"Content definition could not be loaded: {source}") from error
    if not isinstance(definition, dict):
        raise ContentDefinitionError("Content definition must be a JSON object.")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported content definition schema version.")
    required = {"ids", "world", "character", "locations", "faction", "npc", "dialogue"}
    missing = sorted(required - definition.keys())
    if missing:
        raise ContentDefinitionError(f"Content definition is missing sections: {', '.join(missing)}")
    return definition


def load_opening_content(path: str | Path | None = None) -> dict:
    """Load only the definition sections required before character creation."""
    if path is None:
        candidates = (
            DEFAULT_CONTENT_PATH,
            Path(sys.prefix) / "data" / "starter_content.json",
            Path(sys.prefix) / "starter_content.json",
        )
        source = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    else:
        source = Path(path)
    try:
        definition = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentDefinitionError(f"Opening content definition could not be loaded: {source}") from error
    if not isinstance(definition, dict):
        raise ContentDefinitionError("Opening content definition must be a JSON object.")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported content definition schema version.")
    required = {"ids", "world", "character", "locations", "faction", "npc", "dialogue"}
    missing = sorted(required - definition.keys())
    if missing:
        raise ContentDefinitionError(
            f"Opening content definition is missing sections: {', '.join(missing)}"
        )
    return definition


def _id_resolver(definition: dict, ids: StarterContentIds):
    configured = definition["ids"]
    valid_fields = {field.name for field in fields(StarterContentIds)}
    if set(configured) != valid_fields:
        raise ContentDefinitionError("Content ids must match StarterContentIds fields.")
    replacements = {key: getattr(ids, key) for key in valid_fields}
    return lambda key: replacements.get(key, key)


def _build_character_factory(character_data: dict) -> CharacterFactory:
    race_data = character_data["race"]
    class_data = character_data["class"]
    return CharacterFactory(
        {
            race_data["id"]: Race(
                race_data["id"], race_data["name"],
                abilities=(Ability(race_data["ability_id"], race_data["ability_name"]),),
            ),
            "elf": Race(
                "elf", "Orman Elfi",
                {"dexterity": 2, "wisdom": 1},
                (Ability("night_sight", "Gece Görüşü", "Karanlıkta daha iyi algı."),),
            ),
            "dwarf": Race(
                "dwarf", "Dağ Cücesi",
                {"constitution": 2, "strength": 1},
                (Ability("stone_endurance", "Taş Dayanıklılığı", "Yüksek fiziksel direnç."),),
            ),
        },
        {
            class_data["id"]: CharacterClass(
                class_data["id"], class_data["name"],
                hit_points=class_data["hit_points"],
                skill_ranks=class_data.get(
                    "skill_ranks", {"gathering": 1, "survival": 1}
                ),
            ),
            "warden": CharacterClass(
                "warden", "Vadi Muhafızı", hit_points=16,
                skill_ranks={"combat": 2, "survival": 1},
                abilities=(Ability("guard_stance", "Muhafız Duruşu", "Savunmada eğitimli."),),
            ),
            "arcanist": CharacterClass(
                "arcanist", "Arkanist", hit_points=9,
                skill_ranks={"lore": 2, "alchemy": 1},
                abilities=(Ability("spark", "Kıvılcım", "Temel büyü bilgisi."),),
            ),
        },
    )


def _register_opening_content(application, definition: dict, ids: StarterContentIds):
    resolve_id = _id_resolver(definition, ids)
    world_data = definition["world"]
    world = application.aktif_dunya() or application.dunya_olustur(
        world_data["name"],
        width=world_data["width"],
        height=world_data["height"],
        world_id=resolve_id("world_id"),
    )
    bundle = application.holder.current
    character_data = definition["character"]
    factory = _build_character_factory(character_data)
    if not bundle.characters:
        application.karakter_olustur(
            factory,
            resolve_id("hero_id"),
            character_data["name"],
            character_data["race"]["id"],
            character_data["class"]["id"],
            resolve_id("hero_id"),
        )
    service = GameplayService(application)
    service.register_character_factory(factory)
    service._starter_content_ids = ids
    faction_data = definition["faction"]
    service.register_faction(Faction(resolve_id("faction_id"), faction_data["name"]))
    npc_data = definition["npc"]
    service.register_npc(
        NPC(
            resolve_id("npc_id"),
            npc_data["name"],
            npc_data["role"],
            (resolve_id("faction_id"),),
            resolve_id(npc_data["location_id"]),
            position=Position(*(npc_data.get("position") or (16, 30))),
        )
    )
    dialogue_data = definition["dialogue"]
    nodes = tuple(
        DialogueNode(
            node_data["id"],
            resolve_id("npc_id"),
            node_data["text"],
            tuple(
        DialogueChoice(
            choice["id"],
            choice["text"],
            choice.get("next"),
            action=choice.get("action"),
)
                for choice in node_data.get("choices", ())
            ),
        )
        for node_data in dialogue_data["nodes"]
    )
    service.register_dialogue(
        Dialogue(dialogue_data["id"], nodes, dialogue_data["start_node"])
    )
    world_map = _build_world_map_from_definition(
        definition, world.world_id, ids
    )
    service.register_world_map(world_map)
    service.place_actor(resolve_id("hero_id"), resolve_id("village_id"))
    start_position = character_data.get("starting_position") or (16, 29)
    service.set_actor_tile_position(
        resolve_id("hero_id"), start_position[0], start_position[1]
    )
    return service, ids


def populate_opening_content(
    application, ids: StarterContentIds = StarterContentIds(), definition_path=None
):
    """Build only the opening session used before character creation."""
    return _register_opening_content(
        application,
        load_opening_content(definition_path),
        ids,
    )


def populate_gameplay_resources(service, definition_path=None):
    """Create gameplay inventory and resource nodes after character creation."""
    world = service.application.aktif_dunya()
    if world is None:
        raise RuntimeError("An active world is required for gameplay resources.")
    ids = getattr(service, "_starter_content_ids", StarterContentIds())
    definition = load_starter_content(definition_path)
    _register_opening_resources(
        service.application.holder.current,
        definition,
        _id_resolver(definition, ids),
        ids,
        world.world_id,
    )


def _register_opening_resources(bundle, definition, resolve_id, ids, world_id):
    """Register the starter inventory and every gatherable landmark as a resource node."""
    inventories = dict(bundle.inventories)
    inventories.setdefault("player", Inventory())
    object.__setattr__(bundle, "inventories", MappingProxyType(inventories))

    for location_data in definition["locations"]:
        location_id = resolve_id(location_data["id"])
        for landmark in location_data.get("landmarks", ()):
            activities = tuple(landmark.get("activities", ()))
            if "gather" not in activities:
                continue

            landmark_id = landmark["id"]
            landmark_name = landmark["name"].lower()
            normalized_id = landmark_id.lower()
            if "tree" in normalized_id or "ağaç" in landmark_name:
                node_id = (
                    "forest_wood"
                    if landmark_id == "forest_tree_01"
                    else f"{landmark_id}_wood"
                )
                resource_id = "wood"
            elif "mine" in normalized_id or "maden" in landmark_name:
                node_id = (
                    "north_iron_mine"
                    if location_id == ids.forest_id
                    else landmark_id
                )
                resource_id = "iron_ore"
            else:
                continue

            if bundle.resource_nodes.get(node_id) is not None:
                continue
            quantity = Quantity(20, ResourceUnit.ITEM)
            bundle.resource_nodes.add(
                WorldResourceNode(
                    node_id,
                    world_id,
                    ResourceType(resource_id),
                    quantity,
                    quantity,
                    Quantity(0, ResourceUnit.ITEM),
                    location_id=location_id,
                )
            )


def _build_world_map_from_definition(
    definition: dict, world_id: str, ids: StarterContentIds
):
    resolve_id = _id_resolver(definition, ids)
    world_map = WorldMap(world_id)
    for location in definition["locations"]:
        world_map.add_location(
            Location(
                resolve_id(location["id"]),
                location["name"],
                tuple(location["position"])
                if location.get("position") is not None
                else None,
                location.get("description", ""),
                location.get("type", "unknown"),
                tuple(location.get("activities", ())),
                tuple(
                    (
                        landmark["id"],
                        landmark["name"],
                        tuple(landmark.get("position", (180, 180))),
                        tuple(landmark.get("activities", ())),
                        landmark.get("description", ""),
                    )
                    for landmark in location.get("landmarks", ())
                ),
            )
        )
    for connection in definition.get("connections", ()):
        world_map.connect(resolve_id(connection[0]), resolve_id(connection[1]))
    return world_map


def build_starter_world_map(
    world_id: str,
    ids: StarterContentIds = StarterContentIds(),
    definition_path=None,
):
    """Rebuild the static starter map without resetting saved gameplay state."""
    definition = load_starter_content(definition_path)

    return _build_world_map_from_definition(definition, world_id, ids)


__all__ = [
    "CONTENT_SCHEMA_VERSION",
    "ContentDefinitionError",
    "StarterContentIds",
    "load_starter_content",
    "load_opening_content",
    "populate_opening_content",
    "populate_gameplay_resources",
    "build_starter_world_map",
]