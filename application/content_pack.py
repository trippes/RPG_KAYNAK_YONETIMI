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
from economy import Currency, Money, MarketProfile, MarketCatalogEntry
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

from core.errors import RPGError

class ContentDefinitionError(ValueError, RPGError):
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



def _build_dialogue_from_definition(dialogue_data: dict, speaker_id: str) -> Dialogue:
    """Validate untrusted JSON dialogue records before creating runtime objects."""
    if not isinstance(dialogue_data, dict):
        raise ContentDefinitionError("Dialogue definition must be an object.")

    dialogue_id = dialogue_data.get("id")
    start_node_id = dialogue_data.get("start_node")
    raw_nodes = dialogue_data.get("nodes")
    if not isinstance(dialogue_id, str) or not dialogue_id.strip():
        raise ContentDefinitionError("Dialogue id must be a non-empty string.")
    if not isinstance(start_node_id, str) or not start_node_id.strip():
        raise ContentDefinitionError("Dialogue start_node must be a non-empty string.")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ContentDefinitionError("Dialogue nodes must be a non-empty list.")

    node_ids: set[str] = set()
    pending_next_ids: set[str] = set()
    nodes: list[DialogueNode] = []

    for node_index, node_data in enumerate(raw_nodes):
        if not isinstance(node_data, dict):
            raise ContentDefinitionError(
                f"Dialogue node at index {node_index} must be an object."
            )
        node_id = node_data.get("id")
        text = node_data.get("text")
        raw_choices = node_data.get("choices", [])
        if not isinstance(node_id, str) or not node_id.strip():
            raise ContentDefinitionError(
                f"Dialogue node at index {node_index} has an invalid id."
            )
        if node_id in node_ids:
            raise ContentDefinitionError(f"Duplicate dialogue node id: {node_id}")
        if not isinstance(text, str) or not text.strip():
            raise ContentDefinitionError(f"Dialogue node {node_id} has no text.")
        if not isinstance(raw_choices, list):
            raise ContentDefinitionError(
                f"Dialogue choices for node {node_id} must be a list."
            )

        node_ids.add(node_id)
        choice_ids: set[str] = set()
        choices: list[DialogueChoice] = []
        for choice_index, choice_data in enumerate(raw_choices):
            if not isinstance(choice_data, dict):
                raise ContentDefinitionError(
                    f"Choice {choice_index} in node {node_id} must be an object."
                )
            choice_id = choice_data.get("id")
            choice_text = choice_data.get("text")
            next_node_id = choice_data.get("next")
            action = choice_data.get("action")
            if not isinstance(choice_id, str) or not choice_id.strip():
                raise ContentDefinitionError(
                    f"Choice {choice_index} in node {node_id} has an invalid id."
                )
            if choice_id in choice_ids:
                raise ContentDefinitionError(
                    f"Duplicate choice id {choice_id} in dialogue node {node_id}."
                )
            if not isinstance(choice_text, str) or not choice_text.strip():
                raise ContentDefinitionError(
                    f"Choice {choice_id} in node {node_id} has no text."
                )
            if next_node_id is not None and (
                not isinstance(next_node_id, str) or not next_node_id.strip()
            ):
                raise ContentDefinitionError(
                    f"Choice {choice_id} in node {node_id} has an invalid next node."
                )
            if action is not None and (
                not isinstance(action, str) or not action.strip()
            ):
                raise ContentDefinitionError(
                    f"Choice {choice_id} in node {node_id} has an invalid action."
                )
            choice_ids.add(choice_id)
            if next_node_id is not None:
                pending_next_ids.add(next_node_id)
            choices.append(
                DialogueChoice(
                    choice_id=choice_id,
                    text=choice_text,
                    next_node_id=next_node_id,
                    action=action,
                )
            )

        nodes.append(
            DialogueNode(
                node_id=node_id,
                speaker_id=speaker_id,
                text=text,
                choices=tuple(choices),
            )
        )

    missing_nodes = sorted(pending_next_ids - node_ids)
    if start_node_id not in node_ids:
        raise ContentDefinitionError(
            f"Dialogue start node does not exist: {start_node_id}"
        )
    if missing_nodes:
        raise ContentDefinitionError(
            "Dialogue choices reference missing nodes: " + ", ".join(missing_nodes)
        )

    return Dialogue(dialogue_id, tuple(nodes), start_node_id)


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
    dialogue = _build_dialogue_from_definition(
        definition["dialogue"],
        resolve_id("npc_id"),
    )
    service.register_dialogue(dialogue)
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
    resolve_id = _id_resolver(definition, ids)
    bundle = service.application.holder.current
    for market_data in definition.get("markets", ()):
        market_npc_id = market_data["npc_id"]
        if bundle.social.npcs.get(market_npc_id) is None:
            service.register_npc(NPC(
                market_npc_id, market_data["npc_name"],
                market_data.get("npc_role", "merchant"),
                tuple(market_data.get("faction_ids", ())),
                resolve_id(market_data["location_id"]),
                position=Position(*(market_data.get("position") or (20, 20))),
            ))
        dialogue_data = market_data["dialogue"]
        if bundle.social.dialogues.get(dialogue_data["id"]) is None:
            service.register_dialogue(_build_dialogue_from_definition(
                dialogue_data, market_npc_id,
            ))
        catalog = tuple(MarketCatalogEntry(
            ResourceType(entry["resource_type"]),
            Money(entry["base_price"], Currency(entry.get("currency", "gold"))),
            entry["min_quantity"], entry["max_quantity"],
        ) for entry in market_data["catalog"])
        service.register_market_profile(MarketProfile(
            market_data["market_id"], resolve_id(market_data["location_id"]),
            market_data["npc_id"], market_data["merchant_id"], market_data["inventory_id"],
            market_data["restock_interval"], catalog, market_data.get("visible_products", 4),
        ))
    for trade_data in definition.get("trade_partners", ()):
        trade_npc_id = trade_data["npc_id"]
        if bundle.social.npcs.get(trade_npc_id) is None:
            service.register_npc(NPC(
                trade_npc_id, trade_data["npc_name"],
                trade_data.get("npc_role", "civilian"),
                tuple(trade_data.get("faction_ids", ())),
                resolve_id(trade_data["location_id"]),
                position=Position(*(trade_data.get("position") or (20, 20))),
            ))
        dialogue_data = trade_data["dialogue"]
        if bundle.social.dialogues.get(dialogue_data["id"]) is None:
            service.register_dialogue(_build_dialogue_from_definition(
                dialogue_data, trade_npc_id,
            ))
        service.register_trade_partner(
            trade_npc_id, trade_data["merchant_id"], trade_data["inventory_id"],
            trade_data["accepted_resources"], trade_data["initial_gold"],
            trade_data.get("buyback_rate", 50), trade_data.get("unit_prices", {}),
        )
    if service.balance("hero", "gold").amount == 0:
        service.credit("hero", "gold", 100)



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
                    gathering_duration_ticks=landmark.get("gathering_duration_ticks", 150),
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