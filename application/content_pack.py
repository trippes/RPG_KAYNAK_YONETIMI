"""Data-driven content loading for the playable starter slice."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType

from application import GameplayService
from application.content_loader import ContentPackageError, load_content_package
from character import Ability, Attribute, CharacterClass, CharacterFactory, Race
from core.domain.spatial import Position
from npc import Faction, NPC
from economy import Currency, Money, MarketProfile, MarketCatalogEntry
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward
from resources import Inventory, Quantity, ResourceType, ResourceUnit, WorldResourceNode
from world import build_world_map, build_local_map_definitions


CONTENT_SCHEMA_VERSION = 1
CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"
ACTIVE_PACKAGE_CONFIG = "active_package.json"


def _resolve_content_package_path(package_path: str | Path | None = None) -> Path:
    """Resolve an explicit package path or the package selected by content config."""
    roots = (CONTENT_ROOT, Path(sys.prefix) / "content")
    if package_path is not None:
        requested = Path(package_path).expanduser()
        candidates = (requested,) if requested.is_absolute() else tuple(root / requested for root in roots)
        for candidate in candidates:
            if (candidate / "manifest.json").is_file():
                return candidate.resolve()
        raise ContentDefinitionError(f"Content package was not found: {package_path}")

    for root in roots:
        config_path = root / ACTIVE_PACKAGE_CONFIG
        if not config_path.is_file():
            continue
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentDefinitionError("Active content package configuration could not be loaded.") from error
        if not isinstance(config, dict) or config.get("schema_version") != CONTENT_SCHEMA_VERSION:
            raise ContentDefinitionError("Active content package configuration has an unsupported schema.")
        relative = config.get("package_path")
        if not isinstance(relative, str) or not relative.strip():
            raise ContentDefinitionError("Active content package path must be a non-empty string.")
        selected = (root / relative).resolve()
        if not selected.is_relative_to(root.resolve()):
            raise ContentDefinitionError("Active content package path escapes the content directory.")
        if not (selected / "manifest.json").is_file():
            raise ContentDefinitionError(f"Active content package was not found: {relative}")
        return selected
    raise ContentDefinitionError("No active content package is configured.")




@dataclass(frozen=True)
class StarterContentIds:
    world_id: str | None = None
    hero_id: str | None = None
    village_id: str | None = None
    forest_id: str | None = None
    faction_id: str | None = None

from core.errors import RPGError

class ContentDefinitionError(ValueError, RPGError):
    """Raised when a content definition cannot safely enter the runtime."""


def _read_json_definition(source: Path, label: str) -> dict:
    try:
        definition = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentDefinitionError(f"{label} could not be loaded: {source}") from error
    if not isinstance(definition, dict):
        raise ContentDefinitionError(f"{label} must be a JSON object.")
    return definition


def _load_package_file(key: str, package_path: str | Path | None = None) -> dict:
    package_root = _resolve_content_package_path(package_path)
    try:
        package = load_content_package(package_root)
        return package.files[key]
    except (ContentPackageError, KeyError) as error:
        raise ContentDefinitionError(
            f"Content package file '{key}' could not be loaded."
        ) from error


def load_starter_content(path: str | Path | None = None, *, package_path: str | Path | None = None) -> dict:
    """Load and validate the starter world definition from the active content package."""
    definition = (
        _load_package_file("starter", package_path)
        if path is None
        else _read_json_definition(Path(path), "Content definition")
    )
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported content definition schema version.")
    required = {"ids", "world", "character", "locations", "faction", "dialogue"}
    missing = sorted(required - definition.keys())
    if missing:
        raise ContentDefinitionError(
            f"Content definition is missing sections: {', '.join(missing)}"
        )
    return definition


def load_opening_content(path: str | Path | None = None, *, package_path: str | Path | None = None) -> dict:
    """Load only the definition sections required before character creation."""
    return load_starter_content(path, package_path=package_path)


def load_npc_definitions(path: str | Path | None = None, *, package_path: str | Path | None = None) -> tuple[dict, ...]:
    """Load NPC records from the content package or an explicit JSON file."""
    definition = (
        _load_package_file("npcs", package_path)
        if path is None
        else _read_json_definition(Path(path), "NPC definition")
    )
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported NPC definition schema version.")
    records = definition.get("npcs")
    if not isinstance(records, list):
        raise ContentDefinitionError("NPC definitions must contain an 'npcs' list.")

    npc_ids: set[str] = set()
    allowed_phases = {"opening", "gameplay"}
    required_fields = {"id", "name", "role", "location_id", "position", "load_phase"}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContentDefinitionError(f"NPC record at index {index} must be an object.")
        missing = sorted(required_fields - record.keys())
        if missing:
            raise ContentDefinitionError(
                f"NPC record at index {index} is missing fields: {', '.join(missing)}"
            )
        npc_id = record["id"]
        if not isinstance(npc_id, str) or not npc_id.strip():
            raise ContentDefinitionError(f"NPC record at index {index} has an invalid id.")
        if npc_id in npc_ids:
            raise ContentDefinitionError(f"Duplicate NPC id: {npc_id}")
        npc_ids.add(npc_id)
        for field in ("name", "role", "location_id"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ContentDefinitionError(f"NPC '{npc_id}' has an invalid {field}.")
        if record["load_phase"] not in allowed_phases:
            raise ContentDefinitionError(
                f"NPC '{npc_id}' has an unsupported load phase."
            )
        if (
            not isinstance(record["position"], list)
            or len(record["position"]) != 2
            or any(type(value) is not int for value in record["position"])
        ):
            raise ContentDefinitionError(
                f"NPC '{npc_id}' position must contain two integer coordinates."
            )
        faction_ids = record.get("faction_ids", [])
        if (
            not isinstance(faction_ids, list)
            or any(not isinstance(value, str) or not value.strip() for value in faction_ids)
        ):
            raise ContentDefinitionError(f"NPC '{npc_id}' has invalid faction ids.")

    return tuple(records)

def _id_resolver(definition: dict, ids: StarterContentIds):
    configured = definition["ids"]
    valid_fields = {field.name for field in fields(StarterContentIds)}
    if set(configured) != valid_fields:
        raise ContentDefinitionError("Content ids must match StarterContentIds fields.")
    replacements = {key: getattr(ids, key) or configured[key] for key in valid_fields}
    return lambda key: replacements.get(key, key)


def load_character_definitions(path: str | Path | None = None, *, package_path: str | Path | None = None) -> dict:
    """Load and validate reusable race, class and ability definitions."""
    definition = _load_package_file("characters", package_path) if path is None else _read_json_definition(Path(path), "Character definition")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported character definition schema version.")
    for section in ("races", "classes"):
        records = definition.get(section)
        if not isinstance(records, list):
            raise ContentDefinitionError(f"Character definitions must contain a '{section}' list.")
        seen: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise ContentDefinitionError(f"{section} record at index {index} must be an object.")
            record_id, name = record.get("id"), record.get("name")
            if not isinstance(record_id, str) or not record_id.strip() or not isinstance(name, str) or not name.strip():
                raise ContentDefinitionError(f"{section} record at index {index} has invalid identity fields.")
            if record_id in seen:
                raise ContentDefinitionError(f"Duplicate {section[:-1]} id: {record_id}")
            seen.add(record_id)
            abilities = record.get("abilities", [])
            if not isinstance(abilities, list):
                raise ContentDefinitionError(f"{section[:-1]} '{record_id}' abilities must be a list.")
            for ability in abilities:
                if not isinstance(ability, dict) or not isinstance(ability.get("id"), str) or not ability["id"].strip() or not isinstance(ability.get("name"), str) or not ability["name"].strip():
                    raise ContentDefinitionError(f"{section[:-1]} '{record_id}' has an invalid ability.")
            if section == "races":
                modifiers = record.get("attribute_modifiers", {})
                if not isinstance(modifiers, dict):
                    raise ContentDefinitionError(f"Race '{record_id}' attribute_modifiers must be an object.")
                for attribute, amount in modifiers.items():
                    try:
                        Attribute(attribute)
                    except ValueError as error:
                        raise ContentDefinitionError(f"Race '{record_id}' has an unknown attribute: {attribute}") from error
                    if isinstance(amount, bool) or not isinstance(amount, int):
                        raise ContentDefinitionError(f"Race '{record_id}' has an invalid attribute modifier.")
            else:
                hit_points = record.get("hit_points", 10)
                ranks = record.get("skill_ranks", {})
                if isinstance(hit_points, bool) or not isinstance(hit_points, int) or hit_points <= 0:
                    raise ContentDefinitionError(f"Class '{record_id}' hit_points must be positive.")
                if not isinstance(ranks, dict) or any(not isinstance(key, str) or not key.strip() or isinstance(value, bool) or not isinstance(value, int) or value < 0 for key, value in ranks.items()):
                    raise ContentDefinitionError(f"Class '{record_id}' has invalid skill ranks.")
    return definition


def _build_character_factory(character_data: dict, character_definitions: dict) -> CharacterFactory:
    def abilities(records):
        return tuple(
            Ability(item["id"], item["name"], item.get("description", ""))
            for item in records
        )

    races = {
        record["id"]: Race(
            record["id"], record["name"],
            record.get("attribute_modifiers", {}),
            abilities(record.get("abilities", ())),
        )
        for record in character_definitions["races"]
    }
    classes = {
        record["id"]: CharacterClass(
            record["id"], record["name"],
            hit_points=record.get("hit_points", 10),
            skill_ranks=record.get("skill_ranks", {}),
            abilities=abilities(record.get("abilities", ())),
        )
        for record in character_definitions["classes"]
    }
    if character_data["race"]["id"] not in races or character_data["class"]["id"] not in classes:
        raise ContentDefinitionError("Starter character references an undefined race or class.")
    return CharacterFactory(races, classes)



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



def load_quest_definitions(path: str | Path | None = None, *, package_path: str | Path | None = None) -> tuple[dict, ...]:
    """Load and validate declarative quest and dialogue records."""
    definition = _load_package_file("quests", package_path) if path is None else _read_json_definition(Path(path), "Quest definition")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported quest definition schema version.")
    records = definition.get("quests")
    if not isinstance(records, list):
        raise ContentDefinitionError("Quest definitions must contain a 'quests' list.")
    quest_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContentDefinitionError(f"Quest record at index {index} must be an object.")
        quest_id, title, giver = record.get("id"), record.get("title"), record.get("giver_npc_id")
        if not all(isinstance(value, str) and value.strip() for value in (quest_id, title, giver)):
            raise ContentDefinitionError(f"Quest record at index {index} has invalid identity fields.")
        if quest_id in quest_ids:
            raise ContentDefinitionError(f"Duplicate quest id: {quest_id}")
        quest_ids.add(quest_id)
        if not isinstance(record.get("sequential_objectives", False), bool):
            raise ContentDefinitionError(f"Quest '{quest_id}' sequential_objectives must be boolean.")
        objectives = record.get("objectives")
        if not isinstance(objectives, list) or not objectives:
            raise ContentDefinitionError(f"Quest '{quest_id}' must define at least one objective.")
        objective_ids: set[str] = set()
        for objective in objectives:
            if not isinstance(objective, dict):
                raise ContentDefinitionError(f"Quest '{quest_id}' objective must be an object.")
            objective_id = objective.get("id")
            if not isinstance(objective_id, str) or not objective_id.strip() or objective_id in objective_ids:
                raise ContentDefinitionError(f"Quest '{quest_id}' has an invalid or duplicate objective id.")
            objective_ids.add(objective_id)
            if not isinstance(objective.get("description"), str) or not objective["description"].strip():
                raise ContentDefinitionError(f"Quest '{quest_id}' objective '{objective_id}' has no description.")
            try:
                ObjectiveType(objective.get("type"))
            except (TypeError, ValueError) as error:
                raise ContentDefinitionError(f"Quest '{quest_id}' objective '{objective_id}' has an invalid type.") from error
            required_count = objective.get("required", 1)
            if isinstance(required_count, bool) or not isinstance(required_count, int) or required_count < 1:
                raise ContentDefinitionError(f"Quest '{quest_id}' objective '{objective_id}' has invalid required count.")
            if not isinstance(objective.get("optional", False), bool):
                raise ContentDefinitionError(f"Quest '{quest_id}' objective '{objective_id}' optional must be boolean.")
        reward = record.get("reward", {})
        if not isinstance(reward, dict):
            raise ContentDefinitionError(f"Quest '{quest_id}' reward must be an object.")
        for key in ("experience", "currency"):
            amount = reward.get(key, 0)
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise ContentDefinitionError(f"Quest '{quest_id}' reward '{key}' must be a non-negative integer.")
        for key, id_key, amount_key in (("items", "id", "quantity"), ("reputation", "id", "amount")):
            entries = reward.get(key, [])
            if not isinstance(entries, list):
                raise ContentDefinitionError(f"Quest '{quest_id}' reward '{key}' must be a list.")
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get(id_key), str) or not entry[id_key].strip():
                    raise ContentDefinitionError(f"Quest '{quest_id}' has an invalid '{key}' reward entry.")
                amount = entry.get(amount_key)
                if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                    raise ContentDefinitionError(f"Quest '{quest_id}' has an invalid '{key}' reward amount.")
        dialogue = record.get("dialogue")
        if dialogue is not None and not isinstance(dialogue, dict):
            raise ContentDefinitionError(f"Quest '{quest_id}' dialogue must be an object.")
    return tuple(records)


def _register_quest_content(service, records) -> None:
    """Create generic quest aggregates and dialogue graphs from package data."""
    for record in records:
        objectives = tuple(
            Objective(
                item["id"], item["description"], ObjectiveType(item["type"]),
                target_id=item.get("target_id"), required=item.get("required", 1),
                optional=item.get("optional", False),
            )
            for item in record["objectives"]
        )
        reward_data = record.get("reward", {})
        reward = Reward(
            experience=reward_data.get("experience", 0),
            currency=reward_data.get("currency", 0),
            items=tuple((item["id"], item["quantity"]) for item in reward_data.get("items", ())),
            reputation=tuple((item["id"], item["amount"]) for item in reward_data.get("reputation", ())),
        )
        quest = Quest(
            record["id"], record["title"], objectives, reward,
            sequential_objectives=record.get("sequential_objectives", False),
            giver_npc_id=record["giver_npc_id"],
        )
        existing = service.application.holder.current.quest_log.get(quest.quest_id)
        if existing is None:
            service.register_quest_definition(quest)
        dialogue_data = record.get("dialogue")
        if dialogue_data is not None and service.application.holder.current.social.dialogues.get(dialogue_data.get("id")) is None:
            service.register_dialogue(_build_dialogue_from_definition(dialogue_data, record["giver_npc_id"]))



def _register_npcs_for_phase(service, npc_definitions, phase: str, resolve_id):
    """Register validated NPC records for the requested lifecycle phase."""
    bundle = service.application.holder.current
    for npc_data in npc_definitions:
        if npc_data["load_phase"] != phase:
            continue
        npc_id = npc_data["id"]
        if bundle.social.npcs.get(npc_id) is not None:
            continue
        service.register_npc(
            NPC(
                npc_id,
                npc_data["name"],
                npc_data["role"],
                tuple(resolve_id(value) for value in npc_data.get("faction_ids", ())),
                resolve_id(npc_data["location_id"]),
                position=Position(*npc_data["position"]),
            )
        )


def _validate_content_references(
    definition, map_definitions, npc_definitions, quest_definitions,
    resource_definitions, ids: StarterContentIds,
):
    """Validate cross-file references before any world content is registered."""
    resolved_ids = StarterContentIds(**{
        field.name: getattr(ids, field.name) or definition["ids"][field.name]
        for field in fields(StarterContentIds)
    })
    resolve_id = _id_resolver(definition, resolved_ids)
    maps = dict(map_definitions)
    for map_id, map_definition in maps.items():
        if map_definition.world_position is None:
            raise ContentDefinitionError(
                f"Map '{map_id}' is missing world_position in its map JSON file."
            )

    starting_maps = tuple(
        item for item in maps.values() if item.starting_position is not None
    )
    if len(starting_maps) != 1:
        raise ContentDefinitionError(
            "Content package must define exactly one map with starting_position."
        )

    npc_ids = {record["id"] for record in npc_definitions}
    for npc in npc_definitions:
        map_id = resolve_id(npc["location_id"])
        map_definition = maps.get(map_id)
        if map_definition is None:
            raise ContentDefinitionError(
                f"NPC '{npc['id']}' references missing map '{map_id}' "
                f"through location_id. Check npcs.json."
            )
        x, y = npc["position"]
        if not (0 <= x < map_definition.size.width and 0 <= y < map_definition.size.height):
            raise ContentDefinitionError(
                f"NPC '{npc['id']}' position ({x}, {y}) is outside map "
                f"'{map_id}' bounds ({map_definition.size.width}x{map_definition.size.height})."
            )

    resource_ids = {record["id"] for record in resource_definitions}
    for resource in resource_definitions:
        map_id = resolve_id(resource["location_id"])
        map_definition = maps.get(map_id)
        if map_definition is None:
            raise ContentDefinitionError(
                f"Resource node '{resource['id']}' references missing map "
                f"'{map_id}' through location_id."
            )
        landmark = next(
            (item for item in map_definition.landmarks
             if item.landmark_id == resource["landmark_id"]),
            None,
        )
        if landmark is None:
            raise ContentDefinitionError(
                f"Resource node '{resource['id']}' references missing landmark "
                f"'{resource['landmark_id']}' on map '{map_id}'."
            )
        if landmark.resource_node_id != resource["id"]:
            raise ContentDefinitionError(
                f"Map '{map_id}' landmark '{landmark.landmark_id}' must reference "
                f"resource node '{resource['id']}' through resource_node_id."
            )

    for quest in quest_definitions:
        if quest["giver_npc_id"] not in npc_ids:
            raise ContentDefinitionError(
                f"Quest '{quest['id']}' references missing giver NPC "
                f"'{quest['giver_npc_id']}'."
            )
        for objective in quest["objectives"]:
            target_id = objective.get("target_id")
            if objective["type"] == "collect" and target_id not in resource_ids:
                raise ContentDefinitionError(
                    f"Quest '{quest['id']}' objective '{objective['id']}' "
                    f"references missing resource node '{target_id}'."
                )
            if objective["type"] == "talk" and target_id not in npc_ids:
                raise ContentDefinitionError(
                    f"Quest '{quest['id']}' objective '{objective['id']}' "
                    f"references missing NPC '{target_id}'."
                )

    for market in definition.get("markets", ()):
        map_id = resolve_id(market["location_id"])
        if map_id not in maps:
            raise ContentDefinitionError(
                f"Market '{market['market_id']}' references missing map '{map_id}'."
            )
        if market["npc_id"] not in npc_ids:
            raise ContentDefinitionError(
                f"Market '{market['market_id']}' references missing NPC '{market['npc_id']}'."
            )
    for partner in definition.get("trade_partners", ()):
        if partner["npc_id"] not in npc_ids:
            raise ContentDefinitionError(
                f"Trade partner references missing NPC '{partner['npc_id']}'."
            )


def _register_opening_content(application, definition: dict, npc_definitions, character_definitions, map_definitions, ids: StarterContentIds):
    ids = StarterContentIds(**{
        field.name: getattr(ids, field.name) or definition["ids"][field.name]
        for field in fields(StarterContentIds)
    })
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
    factory = _build_character_factory(character_data, character_definitions)
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
    _register_npcs_for_phase(service, npc_definitions, "opening", resolve_id)
    opening_dialogue_data = definition["dialogue"]
    speaker_record = next(
        (
            record for record in npc_definitions
            if record.get("dialogue_id") == opening_dialogue_data.get("id")
        ),
        None,
    )
    if speaker_record is None:
        raise ContentDefinitionError(
            f"No NPC references opening dialogue '{opening_dialogue_data.get('id')}'."
        )
    dialogue = _build_dialogue_from_definition(
        opening_dialogue_data,
        speaker_record["id"],
    )
    service.register_dialogue(dialogue)
    world_map = build_world_map(dict(map_definitions), world.world_id)
    service.register_world_map(world_map)
    local_maps = build_local_map_definitions(dict(map_definitions), world.world_id)
    for local_map in local_maps:
        if not bundle.world_objects.has_local_map(local_map.world_id, local_map.location_id):
            bundle.world_objects.register_local_map(local_map)
    starting_maps = tuple(
        item for item in map_definitions.values()
        if item.starting_position is not None
    )
    if len(starting_maps) != 1:
        raise ContentDefinitionError(
            "Content package must define exactly one map with starting_position."
        )
    start_map = starting_maps[0]
    service.place_actor(resolve_id("hero_id"), start_map.map_id)
    service.set_actor_tile_position(
        resolve_id("hero_id"), start_map.starting_position[0], start_map.starting_position[1]
    )
    return service, ids


def populate_opening_content(
    application,
    ids: StarterContentIds = StarterContentIds(),
    definition_path=None,
    npc_definitions_path=None,
    character_definitions_path=None,
    content_package_path=None,
    gameplay_rules_path=None,
):
    """Build the opening session using data-defined NPC records."""
    definition = load_opening_content(definition_path, package_path=content_package_path)
    npc_definitions = load_npc_definitions(npc_definitions_path, package_path=content_package_path)
    character_definitions = load_character_definitions(character_definitions_path, package_path=content_package_path)
    gameplay_rules = load_gameplay_rules(gameplay_rules_path, package_path=content_package_path)
    resolved_package_path = _resolve_content_package_path(content_package_path)
    package = load_content_package(resolved_package_path)
    quest_definitions = load_quest_definitions(package_path=resolved_package_path)
    resource_definitions = load_resource_definitions(package_path=resolved_package_path)
    _validate_content_references(
        definition, package.map_definitions, npc_definitions,
        quest_definitions, resource_definitions, ids,
    )
    service, resolved_ids = _register_opening_content(
        application,
        definition,
        npc_definitions,
        character_definitions,
        package.map_definitions,
        ids,
    )
    service._content_package_path = resolved_package_path
    application._content_package_path = resolved_package_path
    player_rules = gameplay_rules["player"]
    service.configure_player_context(
        resolved_ids.hero_id,
        player_rules["inventory_id"],
        player_rules["account_id"],
    )
    service.configure_consumable_effects({
        item["resource_id"]: item["healing"]
        for item in gameplay_rules["consumables"]
    })
    service._gameplay_rules = gameplay_rules
    return service, resolved_ids


def populate_gameplay_resources(service, definition_path=None, resource_definitions_path=None, content_package_path=None, gameplay_rules_path=None):
    """Create gameplay inventory and resource nodes after character creation."""
    world = service.application.aktif_dunya()
    if world is None:
        raise RuntimeError("An active world is required for gameplay resources.")
    ids = getattr(service, "_starter_content_ids", StarterContentIds())
    active_package_path = content_package_path or getattr(service, "_content_package_path", None)
    gameplay_rules = (
        load_gameplay_rules(gameplay_rules_path, package_path=active_package_path)
        if gameplay_rules_path is not None or not hasattr(service, "_gameplay_rules")
        else service._gameplay_rules
    )
    player_rules = gameplay_rules["player"]
    service.configure_player_context(
        getattr(service, "player_actor_id", ids.hero_id),
        player_rules["inventory_id"],
        player_rules["account_id"],
    )
    service.configure_consumable_effects({
        item["resource_id"]: item["healing"]
        for item in gameplay_rules["consumables"]
    })
    definition = load_starter_content(definition_path, package_path=active_package_path)
    npc_definitions = load_npc_definitions(package_path=active_package_path)
    resolve_id = _id_resolver(definition, ids)
    _register_npcs_for_phase(service, npc_definitions, "gameplay", resolve_id)
    package = load_content_package(_resolve_content_package_path(active_package_path))
    _register_quest_content(service, load_quest_definitions(package_path=active_package_path))
    _register_opening_resources(
        service.application.holder.current,
        package.map_definitions,
        load_resource_definitions(resource_definitions_path, package_path=active_package_path),
        _id_resolver(definition, ids),
        world.world_id,
        player_rules["inventory_id"],
    )
    bundle = service.application.holder.current
    for market_data in definition.get("markets", ()):
        market_npc_id = market_data["npc_id"]
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
    starting_currency = gameplay_rules["economy"]["starting_currency"]
    starting_balance = gameplay_rules["economy"]["starting_balance"]
    if starting_balance and service.balance(player_rules["account_id"], starting_currency).amount == 0:
        service.credit(player_rules["account_id"], starting_currency, starting_balance)





def load_gameplay_rules(path: str | Path | None = None, *, package_path: str | Path | None = None) -> dict:
    """Load configurable player identity, starting economy and consumable effects."""
    definition = _load_package_file("gameplay_rules", package_path) if path is None else _read_json_definition(Path(path), "Gameplay rules")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported gameplay rules schema version.")
    player = definition.get("player")
    economy = definition.get("economy")
    consumables = definition.get("consumables")
    if not isinstance(player, dict) or any(not isinstance(player.get(key), str) or not player[key].strip() for key in ("inventory_id", "account_id")):
        raise ContentDefinitionError("Gameplay rules must define player inventory_id and account_id.")
    if not isinstance(economy, dict):
        raise ContentDefinitionError("Gameplay rules must define an economy object.")
    currency = economy.get("starting_currency")
    balance = economy.get("starting_balance")
    if not isinstance(currency, str) or not currency.strip() or isinstance(balance, bool) or not isinstance(balance, int) or balance < 0:
        raise ContentDefinitionError("Gameplay rules contain an invalid starting balance.")
    if not isinstance(consumables, list):
        raise ContentDefinitionError("Gameplay rules consumables must be a list.")
    seen: set[str] = set()
    for item in consumables:
        if not isinstance(item, dict) or not isinstance(item.get("resource_id"), str) or not item["resource_id"].strip():
            raise ContentDefinitionError("Gameplay rules contain an invalid consumable.")
        if item["resource_id"] in seen:
            raise ContentDefinitionError(f"Duplicate consumable definition: {item['resource_id']}")
        seen.add(item["resource_id"])
        healing = item.get("healing")
        if isinstance(healing, bool) or not isinstance(healing, int) or healing < 0:
            raise ContentDefinitionError(f"Consumable '{item['resource_id']}' has invalid healing.")
    return definition



def load_resource_definitions(path: str | Path | None = None, *, package_path: str | Path | None = None) -> tuple[dict, ...]:
    """Load and validate explicit world resource-node definitions."""
    definition = _load_package_file("resources", package_path) if path is None else _read_json_definition(Path(path), "Resource definition")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported resource definition schema version.")
    records = definition.get("nodes")
    if not isinstance(records, list):
        raise ContentDefinitionError("Resource definitions must contain a 'nodes' list.")
    seen: set[str] = set()
    required_text = ("id", "landmark_id", "location_id", "resource_type", "unit")
    numeric = ("initial_quantity", "capacity", "regeneration_rate", "gathering_duration_ticks")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContentDefinitionError(f"Resource node at index {index} must be an object.")
        for key in required_text:
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ContentDefinitionError(f"Resource node at index {index} has an invalid {key}.")
        if record["id"] in seen:
            raise ContentDefinitionError(f"Duplicate resource node id: {record['id']}")
        seen.add(record["id"])
        try:
            ResourceUnit(record["unit"])
            ResourceType(record["resource_type"])
        except (TypeError, ValueError) as error:
            raise ContentDefinitionError(f"Resource node '{record['id']}' has an invalid resource type or unit.") from error
        for key in numeric:
            value = record.get(key)
            minimum = 1 if key in ("capacity", "gathering_duration_ticks") else 0
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ContentDefinitionError(f"Resource node '{record['id']}' has an invalid {key}.")
        if record["initial_quantity"] > record["capacity"]:
            raise ContentDefinitionError(f"Resource node '{record['id']}' starts above its capacity.")
    return tuple(records)



def _register_opening_resources(bundle, map_definitions, resource_definitions, resolve_id, world_id, inventory_id):
    """Register resource nodes exclusively from validated content records."""
    inventories = dict(bundle.inventories)
    inventories.setdefault(inventory_id, Inventory())
    object.__setattr__(bundle, "inventories", MappingProxyType(inventories))

    landmarks = {
        (map_id, landmark.landmark_id): landmark
        for map_id, map_definition in map_definitions.items()
        for landmark in map_definition.landmarks
    }
    for record in resource_definitions:
        location_id = resolve_id(record["location_id"])
        landmark = landmarks.get((location_id, record["landmark_id"]))
        if landmark is None:
            raise ContentDefinitionError(
                f"Resource node '{record['id']}' references unknown landmark "
                f"'{record['landmark_id']}' on map '{location_id}'."
            )
        if landmark.resource_node_id != record["id"]:
            raise ContentDefinitionError(
                f"Map landmark '{record['landmark_id']}' must reference resource "
                f"node '{record['id']}' through resource_node_id."
            )
        if bundle.resource_nodes.get(record["id"]) is not None:
            continue
        unit = ResourceUnit(record["unit"])
        bundle.resource_nodes.add(
            WorldResourceNode(
                record["id"],
                world_id,
                ResourceType(record["resource_type"]),
                Quantity(record["initial_quantity"], unit),
                Quantity(record["capacity"], unit),
                Quantity(record["regeneration_rate"], unit),
                location_id=location_id,
                gathering_duration_ticks=record["gathering_duration_ticks"],
            )
        )


def build_starter_world_map(
    world_id: str,
    ids: StarterContentIds = StarterContentIds(),
    definition_path=None,
    package_path=None,
):
    """Build the world graph from the selected package's local map catalog."""
    if definition_path is not None:
        raise ContentDefinitionError(
            "World-map construction now requires map JSON files from the content package."
        )
    package = load_content_package(_resolve_content_package_path(package_path))
    return build_world_map(dict(package.map_definitions), world_id)


def build_starter_local_map_definitions(world_id: str, package_path=None):
    """Return the package-defined local dimensions for world-object placement."""
    package = load_content_package(_resolve_content_package_path(package_path))
    return build_local_map_definitions(dict(package.map_definitions), world_id)


__all__ = [
    "CONTENT_SCHEMA_VERSION",
    "ContentDefinitionError",
    "StarterContentIds",
    "load_starter_content",
    "load_opening_content",
    "load_npc_definitions",
    "load_character_definitions",
    "load_quest_definitions",
    "load_resource_definitions",
    "load_gameplay_rules",
    "populate_opening_content",
    "populate_gameplay_resources",
    "build_starter_world_map",
    "build_starter_local_map_definitions",
]