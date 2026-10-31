"""Application boundary for NPCs, dialogue and relationship state."""
from __future__ import annotations

from dataclasses import dataclass
from npc import Faction, FactionRegistry, NPC, NPCRegistry, Relationship, RelationshipGraph, ReputationLedger
from quests import Dialogue, DialogueChoice, DialogueNode


class SocialRuntimeError(ValueError):
    pass


class SocialRuntime:
    def __init__(self, npcs=None, dialogues=None, relationships=None, factions=None, reputation=None):
        self.npcs = npcs if npcs is not None else NPCRegistry()
        self.dialogues: dict[str, Dialogue] = dict(dialogues or {})
        self.relationships = relationships if relationships is not None else RelationshipGraph()
        self.factions = factions if factions is not None else FactionRegistry()
        self.reputation = reputation if reputation is not None else ReputationLedger()

    def add_npc(self, npc: NPC) -> NPC:
        missing = [faction_id for faction_id in npc.faction_ids if faction_id not in self.factions]
        if missing: raise SocialRuntimeError(f"NPC references unknown factions: {missing}")
        self.npcs.add(npc)
        return npc

    def add_faction(self, faction: Faction) -> Faction:
        self.factions.add(faction)
        return faction

    def add_dialogue(self, dialogue: Dialogue) -> Dialogue:
        if dialogue.dialogue_id in self.dialogues:
            raise SocialRuntimeError(f"Duplicate dialogue ID: {dialogue.dialogue_id}")
        self.dialogues[dialogue.dialogue_id] = dialogue
        return dialogue

    def node_for(self, dialogue_id: str, node_id: str, context=None) -> DialogueNode:
        dialogue = self.dialogues.get(dialogue_id)
        if dialogue is None:
            raise KeyError(f"Dialogue not found: {dialogue_id}")
        node = dialogue.node(node_id)
        choices = dialogue.available_choices(node_id, context or {})
        return DialogueNode(node.node_id, node.speaker_id, node.text, choices)

    def change_relationship(self, source_id: str, target_id: str, value=0, trust=0) -> Relationship:
        relationship = self.relationships.ensure(source_id, target_id)
        relationship.change(value, trust)
        return relationship

    def change_reputation(self, faction_id: str, amount: int) -> int:
        if self.factions.get(faction_id) is None:
            raise KeyError(f"Faction not found: {faction_id}")
        return self.reputation.change(faction_id, amount)

    def relation(self, source_id: str, target_id: str) -> Relationship:
        return self.relationships.ensure(source_id, target_id)


__all__ = ["SocialRuntime", "SocialRuntimeError"]
