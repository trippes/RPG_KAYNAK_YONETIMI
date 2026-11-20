"""Versioned persistence adapters for social, companion and combat state."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from core.domain.spatial import ContinuousEntityPosition, LocalHexPosition, WorldPoint
from npc import (
    BehaviorController, BehaviorState, CompanionCommand, CompanionRegistry,
    Faction, NPC, NPCRegistry, Relationship, RelationshipGraph,
    ReputationLedger,
)
from quests import Dialogue, DialogueChoice, DialogueNode

from .combat_runtime import Combatant, CombatRuntime
from .social_runtime import SocialRuntime

SOCIAL_SCHEMA = "rpg-social"
SOCIAL_SCHEMA_VERSION = 2
COMBAT_SCHEMA = "rpg-combat"
COMBAT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SocialSnapshot:
    npcs: tuple[dict, ...] = ()
    relationships: tuple[dict, ...] = ()
    dialogues: tuple[dict, ...] = ()
    factions: tuple[dict, ...] = ()
    reputation: tuple[tuple[str, int], ...] = ()
    schema: str = SOCIAL_SCHEMA
    schema_version: int = SOCIAL_SCHEMA_VERSION
    companions: tuple[dict, ...] = ()

    @property
    def has_legacy_spatial_state(self) -> bool:
        return any(
            item.get("location_id") is not None or item.get("position") is not None
            for item in self.npcs
        )

    def to_dict(self):
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "npcs": list(self.npcs),
            "relationships": list(self.relationships),
            "dialogues": list(self.dialogues),
            "factions": list(self.factions),
            "reputation": [list(item) for item in self.reputation],
            "companions": list(self.companions),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]):
        if not isinstance(data, Mapping) or data.get("schema") != SOCIAL_SCHEMA:
            raise ValueError("Unsupported social snapshot schema.")
        version = data.get("schema_version")
        if version not in {1, SOCIAL_SCHEMA_VERSION}:
            raise ValueError("Unsupported social snapshot schema.")
        values = [
            data.get("npcs", []),
            data.get("relationships", []),
            data.get("dialogues", []),
            data.get("factions", []),
        ]
        if any(not isinstance(value, list) for value in values):
            raise ValueError("Social snapshot collections must be lists.")
        npcs = tuple(dict(item) for item in values[0])
        relationships = tuple(dict(item) for item in values[1])
        dialogues = tuple(dict(item) for item in values[2])
        factions = tuple(dict(item) for item in values[3])
        if len({item.get("npc_id") for item in npcs}) != len(npcs):
            raise ValueError("Duplicate NPC ID.")
        if len({item.get("dialogue_id") for item in dialogues}) != len(dialogues):
            raise ValueError("Duplicate dialogue ID.")
        valid_behavior_states = {state.value for state in BehaviorState}
        for npc in npcs:
            if npc.get("behavior_state", BehaviorState.IDLE.value) not in valid_behavior_states:
                raise ValueError("Unknown NPC behavior state.")
            raw_route = npc.get("patrol_route", [])
            if not isinstance(raw_route, list):
                raise ValueError("NPC patrol_route must be a list.")
            route = []
            for point in raw_route:
                if (
                    not isinstance(point, list) or len(point) != 2
                    or type(point[0]) is not int or type(point[1]) is not int
                ):
                    raise ValueError("NPC patrol waypoints must be integer [q, r] pairs.")
                route.append([point[0], point[1]])
            npc["patrol_route"] = route
            interval = npc.get("patrol_interval_seconds", 0.5)
            if (
                isinstance(interval, bool)
                or not isinstance(interval, (int, float))
                or not math.isfinite(interval)
                or interval <= 0
            ):
                raise ValueError("NPC patrol interval must be positive and finite.")
            npc["patrol_interval_seconds"] = float(interval)

        raw_reputation = data.get("reputation", [])
        if not isinstance(raw_reputation, list):
            raise ValueError("Social reputation must be a list.")
        reputation = tuple((str(item[0]), int(item[1])) for item in raw_reputation)

        companions = []
        raw_companions = data.get("companions", []) if version >= 2 else []
        if not isinstance(raw_companions, list):
            raise ValueError("Social companions must be a list.")
        npc_ids = {item["npc_id"] for item in npcs}
        seen_companions = set()
        for item in raw_companions:
            record = dict(item)
            npc_id = record.get("npc_id")
            if npc_id not in npc_ids:
                raise ValueError("Companion references an unknown NPC.")
            if npc_id in seen_companions:
                raise ValueError("Duplicate companion ID.")
            seen_companions.add(npc_id)
            command = CompanionCommand(record.get("command", "follow"))
            wait = record.get("wait_position")
            if command is CompanionCommand.WAIT:
                if not isinstance(wait, Mapping):
                    raise ValueError("WAIT companion requires a wait position.")
                if not isinstance(wait.get("map_id"), str):
                    raise ValueError("Companion wait position requires a map_id.")
                record["wait_position"] = {
                    "map_id": wait["map_id"],
                    "x": float(wait["x"]),
                    "y": float(wait["y"]),
                }
            elif wait is not None:
                raise ValueError("FOLLOW companion cannot have a wait position.")
            companions.append(record)

        return cls(
            npcs, relationships, dialogues, factions, reputation,
            schema=SOCIAL_SCHEMA,
            schema_version=SOCIAL_SCHEMA_VERSION,
            companions=tuple(companions),
        )

    @classmethod
    def from_runtime(cls, runtime: SocialRuntime):
        npcs = tuple({
            "npc_id": npc.npc_id,
            "name": npc.name,
            "role": npc.role,
            "faction_ids": list(npc.faction_ids),
            "active": npc.active,
            "behavior_state": npc.behavior_state.value,
            "patrol_route": [[point.q, point.r] for point in npc.patrol_route],
            "patrol_interval_seconds": npc.patrol_interval_seconds,
        } for npc in runtime.npcs.all())
        relationships = tuple({
            "source_id": item.source_id,
            "target_id": item.target_id,
            "value": item.value,
            "trust": item.trust,
        } for item in runtime.relationships.all())
        factions = tuple({
            "faction_id": faction.faction_id,
            "name": faction.name,
            "description": faction.description,
            "relations": dict(faction.relations),
        } for faction in runtime.factions.all())
        reputation = tuple(runtime.reputation.snapshot().items())
        dialogues = []
        for dialogue_id, dialogue in sorted(runtime.dialogues.items()):
            nodes = []
            for node in dialogue._nodes.values():
                nodes.append({
                    "node_id": node.node_id,
                    "speaker_id": node.speaker_id,
                    "text": node.text,
                    "choices": [{
                        "choice_id": choice.choice_id,
                        "text": choice.text,
                        "next_node_id": choice.next_node_id,
                        "action": choice.action,
                    } for choice in node.choices],
                })
            dialogues.append({
                "dialogue_id": dialogue_id,
                "start_node_id": dialogue.start_node_id,
                "nodes": nodes,
            })
        companions = []
        for state in runtime.companions.all():
            wait_position = None
            if state.wait_position is not None:
                wait_position = {
                    "map_id": state.wait_position.map_id,
                    "x": state.wait_position.point.x,
                    "y": state.wait_position.point.y,
                }
            companions.append({
                "npc_id": state.npc_id,
                "command": state.command.value,
                "wait_position": wait_position,
            })
        return cls(
            npcs, relationships, tuple(dialogues), factions, reputation,
            companions=tuple(companions),
        )

    def restore(self):
        companions = CompanionRegistry()
        runtime = SocialRuntime(companions=companions)
        for item in self.factions:
            runtime.add_faction(Faction(
                item["faction_id"], item["name"],
                item.get("description", ""), dict(item.get("relations", {})),
            ))
        for item in self.npcs:
            runtime.add_npc(NPC(
                item["npc_id"],
                item["name"],
                item.get("role", "civilian"),
                tuple(item.get("faction_ids", ())),
                behavior=BehaviorController(
                    BehaviorState(item.get("behavior_state", "idle"))
                ),
                active=item.get("active", True),
                patrol_route=tuple(
                    LocalHexPosition(q, r)
                    for q, r in item.get("patrol_route", ())
                ),
                patrol_interval_seconds=item.get("patrol_interval_seconds", 0.5),
            ))
        for item in self.companions:
            npc_id = item["npc_id"]
            runtime.companions.add(npc_id)
            command = CompanionCommand(item["command"])
            wait = item.get("wait_position")
            wait_position = None
            if wait is not None:
                wait_position = ContinuousEntityPosition(
                    wait["map_id"], WorldPoint(wait["x"], wait["y"]),
                )
            runtime.companions.set_command(npc_id, command, wait_position)
        runtime.reputation = ReputationLedger(dict(self.reputation))
        for item in self.relationships:
            runtime.relationships.set(Relationship(
                item["source_id"], item["target_id"],
                item.get("value", 0), item.get("trust", 0),
            ))
        for item in self.dialogues:
            nodes = tuple(
                DialogueNode(
                    node["node_id"], node["speaker_id"], node["text"],
                    tuple(DialogueChoice(
                        choice["choice_id"], choice["text"],
                        choice.get("next_node_id"), choice.get("action"),
                    ) for choice in node.get("choices", ())),
                )
                for node in item["nodes"]
            )
            runtime.add_dialogue(Dialogue(
                item["dialogue_id"], nodes, item["start_node_id"],
            ))
        return runtime


@dataclass(frozen=True)
class CombatSnapshot:
    combatants: tuple[dict, ...] = ()
    encounters: tuple[dict, ...] = ()
    schema: str = COMBAT_SCHEMA
    schema_version: int = COMBAT_SCHEMA_VERSION

    def to_dict(self):
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "combatants": list(self.combatants),
            "encounters": list(self.encounters),
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping) or data.get("schema") != COMBAT_SCHEMA or data.get("schema_version") != COMBAT_SCHEMA_VERSION:
            raise ValueError("Unsupported combat snapshot schema.")
        values = data.get("combatants", ())
        if not isinstance(values, list):
            raise ValueError("combatants must be a list.")
        records = tuple(dict(item) for item in values)
        if len({item.get("combatant_id") for item in records}) != len(records):
            raise ValueError("Duplicate combatant ID.")
        encounters = tuple(dict(item) for item in data.get("encounters", []))
        return cls(records, encounters)

    @classmethod
    def from_runtime(cls, runtime: CombatRuntime):
        encounters = tuple({
            "encounter_id": encounter.encounter_id,
            "initiative_order": list(encounter.initiative_order),
            "round_number": encounter.round_number,
            "active_index": encounter.active_index,
        } for encounter in runtime.encounters())
        return cls(tuple({
            "combatant_id": combatant.combatant_id,
            "max_hit_points": combatant.max_hit_points,
            "hit_points": combatant.hit_points,
            "attack": combatant.attack,
            "defense": combatant.defense,
            "statuses": dict(combatant.statuses),
        } for combatant in runtime.all()), encounters)

    def restore(self):
        runtime = CombatRuntime()
        for item in self.combatants:
            runtime.add(Combatant(
                item["combatant_id"], item["max_hit_points"],
                item.get("attack", 1), item.get("defense", 0),
                item.get("hit_points"), dict(item.get("statuses", {})),
            ))
        for item in self.encounters:
            encounter = runtime.create_encounter(
                item["encounter_id"], item["initiative_order"],
            )
            encounter.initiative_order = tuple(item["initiative_order"])
            encounter.round_number = item.get("round_number", 1)
            encounter.active_index = item.get("active_index", 0)
        return runtime


__all__ = ["SocialSnapshot", "CombatSnapshot"]
