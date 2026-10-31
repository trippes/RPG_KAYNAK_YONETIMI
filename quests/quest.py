"""Quest lifecycle, objective updates and player quest log."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .condition import AllConditions
from .objective import Objective
from .reward import Reward

class QuestState(Enum): AVAILABLE="available"; ACTIVE="active"; COMPLETED="completed"; FAILED="failed"

@dataclass
class Quest:
    quest_id: str
    title: str
    objectives: tuple[Objective, ...]
    reward: Reward = Reward()
    prerequisites: AllConditions = AllConditions()
    state: QuestState = QuestState.AVAILABLE
    def __post_init__(self):
        if not self.quest_id or not self.title: raise ValueError("Quest ID and title are required.")
        self.state = QuestState(self.state)
        ids = [o.objective_id for o in self.objectives]
        if len(ids) != len(set(ids)): raise ValueError("Objective IDs must be unique.")
    def can_start(self, context): return self.state == QuestState.AVAILABLE and self.prerequisites.evaluate(context)
    def start(self, context=None):
        if not self.can_start(context or {}): raise ValueError("Quest prerequisites are not met or quest is not available.")
        self.state = QuestState.ACTIVE
    def update(self, objective_id, amount=1):
        if self.state != QuestState.ACTIVE: raise ValueError("Only active quests can be updated.")
        objective = next((o for o in self.objectives if o.objective_id == objective_id), None)
        if objective is None: raise KeyError(objective_id)
        objective.advance(amount)
        if all(o.completed for o in self.objectives if not o.optional): self.state = QuestState.COMPLETED
        return self.state
    def fail(self):
        if self.state == QuestState.COMPLETED: raise ValueError("Completed quest cannot fail.")
        self.state = QuestState.FAILED

class QuestLog:
    def __init__(self, quests=()): self._quests = {}; [self.add(q) for q in quests]
    def add(self, quest):
        if not isinstance(quest, Quest): raise TypeError("quest must be Quest.")
        if quest.quest_id in self._quests: raise ValueError("Duplicate quest ID.")
        self._quests[quest.quest_id] = quest
    def get(self, quest_id): return self._quests.get(quest_id)
    def all(self): return tuple(self._quests[k] for k in sorted(self._quests))
    def active(self): return tuple(q for q in self.all() if q.state is QuestState.ACTIVE)
    def completed(self): return tuple(q for q in self.all() if q.state is QuestState.COMPLETED)
    def failed(self): return tuple(q for q in self.all() if q.state is QuestState.FAILED)
    def available(self): return tuple(q for q in self.all() if q.state is QuestState.AVAILABLE)

__all__ = ["Quest", "QuestLog", "QuestState"]
