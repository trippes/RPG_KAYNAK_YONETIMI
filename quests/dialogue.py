"""Branching dialogue records used by NPC conversations."""
from __future__ import annotations
from dataclasses import dataclass
from .condition import AllConditions

@dataclass(frozen=True)
class DialogueChoice:
    choice_id: str
    text: str
    next_node_id: str | None = None
    action: str | None = None
    conditions: AllConditions = AllConditions()
    def available(self, context): return self.conditions.evaluate(context)

@dataclass(frozen=True)
class DialogueNode:
    node_id: str
    speaker_id: str
    text: str
    choices: tuple[DialogueChoice, ...] = ()

class Dialogue:
    def __init__(self, dialogue_id: str, nodes, start_node_id: str):
        if not isinstance(dialogue_id, str) or not dialogue_id.strip():
            raise ValueError("Dialogue ID is required.")
        node_list = tuple(nodes)
        if not node_list or any(not isinstance(node, DialogueNode) for node in node_list):
            raise ValueError("Dialogue must contain at least one valid node.")
        if any(not node.node_id or not node.text.strip() for node in node_list):
            raise ValueError("Dialogue nodes require an ID and text.")
        if len({node.node_id for node in node_list}) != len(node_list):
            raise ValueError("Dialogue node IDs must be unique.")
        self.dialogue_id = dialogue_id; self._nodes = {n.node_id: n for n in node_list}; self.start_node_id = start_node_id
        if start_node_id not in self._nodes: raise ValueError("Dialogue start node is missing.")
        missing = {
            choice.next_node_id
            for node in node_list
            for choice in node.choices
            if choice.next_node_id is not None and choice.next_node_id not in self._nodes
        }
        if missing:
            raise ValueError(f"Dialogue choices reference missing nodes: {sorted(missing)}")
    def node(self, node_id): return self._nodes[node_id]
    @property
    def speakers(self): return frozenset(node.speaker_id for node in self._nodes.values())
    def available_choices(self, node_id, context): return tuple(c for c in self.node(node_id).choices if c.available(context))

__all__ = ["Dialogue", "DialogueNode", "DialogueChoice"]
