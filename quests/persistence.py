"""Versioned, runtime-free quest state snapshot."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .quest import Quest, QuestLog, QuestState
from .objective import Objective, ObjectiveType
from .reward import Reward

QUEST_SCHEMA = "rpg-quests"
QUEST_SCHEMA_VERSION = 1

class QuestPersistenceError(ValueError): pass

@dataclass(frozen=True)
class QuestSnapshot:
    quests: tuple[dict[str, object], ...]

    @classmethod
    def from_log(cls, log: QuestLog):
        if not isinstance(log, QuestLog): raise TypeError("log must be QuestLog.")
        records = []
        for quest in log.all():
            records.append({
                "quest_id": quest.quest_id, "title": quest.title, "state": quest.state.value,
                "reward": {"experience": quest.reward.experience, "currency": quest.reward.currency, "items": [list(item) for item in quest.reward.items], "reputation": [list(item) for item in quest.reward.reputation]},
                "objectives": [{"objective_id": o.objective_id, "description": o.description, "objective_type": o.objective_type.value, "target_id": o.target_id, "required": o.required, "progress": o.progress, "optional": o.optional} for o in quest.objectives],
            })
        return cls(tuple(records))

    def to_dict(self):
        return {"schema": QUEST_SCHEMA, "schema_version": QUEST_SCHEMA_VERSION, "quests": [dict(q) for q in self.quests]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]):
        if not isinstance(data, Mapping) or data.get("schema") != QUEST_SCHEMA or data.get("schema_version") != QUEST_SCHEMA_VERSION:
            raise QuestPersistenceError("Unsupported quest persistence schema.")
        quests = data.get("quests")
        if not isinstance(quests, list) or any(not isinstance(q, Mapping) for q in quests):
            raise QuestPersistenceError("quests must be a list of objects.")
        ids = [q.get("quest_id") for q in quests]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
            raise QuestPersistenceError("Quest IDs must be unique non-empty strings.")
        return cls(tuple(dict(q) for q in sorted(quests, key=lambda q: q["quest_id"])))

    def restore(self, definitions: Mapping[str, Quest]) -> QuestLog:
        if not isinstance(definitions, Mapping): raise TypeError("definitions must be a mapping.")
        log = QuestLog()
        for record in self.quests:
            source = definitions.get(record["quest_id"])
            if source is None:
                try:
                    source = Quest(
                        record["quest_id"], record["title"], tuple(
                            Objective(item["objective_id"], item["description"], ObjectiveType(item["objective_type"]), item.get("target_id"), item["required"], item.get("progress", 0), item.get("optional", False))
                            for item in record["objectives"]
                        ), Reward(
                            record.get("reward", {}).get("experience", 0),
                            record.get("reward", {}).get("currency", 0),
                            tuple(tuple(item) for item in record.get("reward", {}).get("items", ())),
                            tuple(tuple(item) for item in record.get("reward", {}).get("reputation", ())),
                        ), state=QuestState(record["state"])
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise QuestPersistenceError("Invalid quest definition in snapshot.") from error
            # Definitions own immutable design data; only player progress/state is restored.
            import copy
            quest = copy.deepcopy(source)
            reward = record.get("reward") or {}
            quest.reward = Reward(
                reward.get("experience", quest.reward.experience),
                reward.get("currency", quest.reward.currency),
                tuple(tuple(item) for item in reward.get("items", quest.reward.items)),
                tuple(tuple(item) for item in reward.get("reputation", quest.reward.reputation)),
            )
            try: quest.state = QuestState(record["state"])
            except (KeyError, ValueError) as error: raise QuestPersistenceError("Invalid quest state.") from error
            progress = record.get("objectives")
            if not isinstance(progress, list): raise QuestPersistenceError("objectives must be a list.")
            by_id = {item.objective_id: item for item in quest.objectives}
            for item in progress:
                if not isinstance(item, Mapping) or item.get("objective_id") not in by_id:
                    raise QuestPersistenceError("Unknown quest objective.")
                value = item.get("progress")
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise QuestPersistenceError("Objective progress must be non-negative integer.")
                by_id[item["objective_id"]].progress = min(by_id[item["objective_id"]].required, value)
            log.add(quest)
        return log

__all__ = ["QUEST_SCHEMA", "QUEST_SCHEMA_VERSION", "QuestPersistenceError", "QuestSnapshot"]
