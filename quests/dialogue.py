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
        self.dialogue_id = dialogue_id; self._nodes = {n.node_id: n for n in nodes}; self.start_node_id = start_node_id
        if start_node_id not in self._nodes: raise ValueError("Dialogue start node is missing.")
    def node(self, node_id): return self._nodes[node_id]
    @property
    def speakers(self): return frozenset(node.speaker_id for node in self._nodes.values())
    def available_choices(self, node_id, context): return tuple(c for c in self.node(node_id).choices if c.available(context))

__all__ = ["Dialogue", "DialogueNode", "DialogueChoice"]
