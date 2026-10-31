"""Persistence adapters for social and combat application state."""
from dataclasses import dataclass
from typing import Mapping
from npc import Faction, NPC, NPCRegistry, Relationship, RelationshipGraph, ReputationLedger
from quests import Dialogue, DialogueChoice, DialogueNode
from core.domain.spatial import Position
from .combat_runtime import Combatant, CombatRuntime
from .social_runtime import SocialRuntime

SOCIAL_SCHEMA = "rpg-social"
SOCIAL_SCHEMA_VERSION = 1
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

    def to_dict(self):
        return {"schema": self.schema, "schema_version": self.schema_version, "npcs": list(self.npcs), "relationships": list(self.relationships), "dialogues": list(self.dialogues), "factions": list(self.factions), "reputation": [list(item) for item in self.reputation]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]):
        if not isinstance(data, Mapping) or data.get("schema") != SOCIAL_SCHEMA or data.get("schema_version") != SOCIAL_SCHEMA_VERSION:
            raise ValueError("Unsupported social snapshot schema.")
        values = [data.get("npcs", []), data.get("relationships", []), data.get("dialogues", []), data.get("factions", [])]
        if any(not isinstance(value, list) for value in values): raise ValueError("Social snapshot collections must be lists.")
        npcs = tuple(dict(x) for x in values[0]); relationships = tuple(dict(x) for x in values[1]); dialogues = tuple(dict(x) for x in values[2])
        if len({x.get("npc_id") for x in npcs}) != len(npcs): raise ValueError("Duplicate NPC ID.")
        if len({x.get("dialogue_id") for x in dialogues}) != len(dialogues): raise ValueError("Duplicate dialogue ID.")
        reputation = tuple((str(item[0]), int(item[1])) for item in data.get("reputation", []))
        return cls(npcs, relationships, dialogues, tuple(dict(x) for x in values[3]), reputation)

    @classmethod
    def from_runtime(cls, runtime: SocialRuntime):
        npcs = tuple({
            "npc_id": n.npc_id,
            "name": n.name,
            "role": n.role,
            "faction_ids": list(n.faction_ids),
            "location_id": n.location_id,
            "active": n.active,
            "position": n.position.to_dict(),
        } for n in runtime.npcs.all())
        relationships = tuple({"source_id": r.source_id, "target_id": r.target_id, "value": r.value, "trust": r.trust} for r in runtime.relationships.all())
        factions = tuple({"faction_id": f.faction_id, "name": f.name, "description": f.description, "relations": dict(f.relations)} for f in runtime.factions.all())
        reputation = tuple(runtime.reputation.snapshot().items())
        dialogues = []
        for dialogue_id, dialogue in sorted(runtime.dialogues.items()):
            nodes = []
            for node in dialogue._nodes.values():
                nodes.append({"node_id": node.node_id, "speaker_id": node.speaker_id, "text": node.text, "choices": [{"choice_id": c.choice_id, "text": c.text, "next_node_id": c.next_node_id, "action": c.action} for c in node.choices]})
            dialogues.append({"dialogue_id": dialogue_id, "start_node_id": dialogue.start_node_id, "nodes": nodes})
        return cls(npcs, relationships, tuple(dialogues), factions, reputation)

    def restore(self):
        runtime = SocialRuntime()
        for item in self.factions:
            runtime.add_faction(Faction(item["faction_id"], item["name"], item.get("description", ""), dict(item.get("relations", {}))))
        for item in self.npcs:
            position_data = item.get("position")
            position = (
                Position.from_dict(position_data)
                if isinstance(position_data, Mapping)
                else Position()
            )
            runtime.add_npc(NPC(
                item["npc_id"],
                item["name"],
                item.get("role", "civilian"),
                tuple(item.get("faction_ids", ())),
                item.get("location_id"),
                active=item.get("active", True),
                position=position,
            ))
        runtime.reputation = ReputationLedger(dict(self.reputation))
        for item in self.relationships:
            runtime.relationships.set(Relationship(item["source_id"], item["target_id"], item.get("value", 0), item.get("trust", 0)))
        for item in self.dialogues:
            nodes = tuple(DialogueNode(n["node_id"], n["speaker_id"], n["text"], tuple(DialogueChoice(c["choice_id"], c["text"], c.get("next_node_id"), c.get("action")) for c in n.get("choices", ()))) for n in item["nodes"])
            runtime.add_dialogue(Dialogue(item["dialogue_id"], nodes, item["start_node_id"]))
        return runtime


@dataclass(frozen=True)
class CombatSnapshot:
    combatants: tuple[dict, ...] = ()
    encounters: tuple[dict, ...] = ()
    schema: str = COMBAT_SCHEMA
    schema_version: int = COMBAT_SCHEMA_VERSION

    def to_dict(self): return {"schema": self.schema, "schema_version": self.schema_version, "combatants": list(self.combatants), "encounters": list(self.encounters)}
    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping) or data.get("schema") != COMBAT_SCHEMA or data.get("schema_version") != COMBAT_SCHEMA_VERSION:
            raise ValueError("Unsupported combat snapshot schema.")
        values = data.get("combatants", ())
        if not isinstance(values, list): raise ValueError("combatants must be a list.")
        records = tuple(dict(x) for x in values)
        if len({x.get("combatant_id") for x in records}) != len(records): raise ValueError("Duplicate combatant ID.")
        encounters = tuple(dict(x) for x in data.get("encounters", []))
        return cls(records, encounters)
    @classmethod
    def from_runtime(cls, runtime: CombatRuntime):
        encounters = tuple({"encounter_id": e.encounter_id, "initiative_order": list(e.initiative_order), "round_number": e.round_number, "active_index": e.active_index} for e in runtime.encounters())
        return cls(tuple({"combatant_id": c.combatant_id, "max_hit_points": c.max_hit_points, "hit_points": c.hit_points, "attack": c.attack, "defense": c.defense, "statuses": dict(c.statuses)} for c in runtime.all()), encounters)
    def restore(self):
        runtime = CombatRuntime()
        for item in self.combatants:
            runtime.add(Combatant(item["combatant_id"], item["max_hit_points"], item.get("attack", 1), item.get("defense", 0), item.get("hit_points"), dict(item.get("statuses", {}))))
        for item in self.encounters:
            encounter = runtime.create_encounter(item["encounter_id"], item["initiative_order"])
            encounter.initiative_order = tuple(item["initiative_order"])
            encounter.round_number = item.get("round_number", 1)
            encounter.active_index = item.get("active_index", 0)
        return runtime


__all__ = ["SocialSnapshot", "CombatSnapshot"]
