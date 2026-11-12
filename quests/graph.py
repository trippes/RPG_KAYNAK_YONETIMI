"""Content-driven quest graph definitions and runtime availability rules."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class QuestLinkType(str, Enum):
    """Semantic relationship between two quest definitions."""

    UNLOCKS = "unlocks"
    ALTERNATIVE = "alternative"
    SIDE = "side"


def _state_value(value: object) -> str:
    return str(getattr(value, "value", value))


class QuestGraphProgress:
    """Player-owned choices made inside a quest graph.

    Content definitions stay immutable; branch selections belong to the
    player's progress and can be serialized independently from quest content.
    """

    def __init__(self, selections: Mapping[tuple[str, str], str] | None = None) -> None:
        self._selections: dict[tuple[str, str], str] = {}
        for key, target in (selections or {}).items():
            if (
                not isinstance(key, tuple)
                or len(key) != 2
                or any(not isinstance(part, str) or not part.strip() for part in key)
                or not isinstance(target, str)
                or not target.strip()
            ):
                raise ValueError("Invalid quest branch selection.")
            self._selections[key] = target

    def selected_branch(self, source_quest_id: str, branch_group: str) -> str | None:
        return self._selections.get((source_quest_id, branch_group))

    def choose_branch(
        self,
        graph: "QuestGraph",
        source_quest_id: str,
        branch_group: str,
        target_quest_id: str,
        quest_states: Mapping[str, object],
    ) -> str:
        options = graph.branch_options(source_quest_id, branch_group)
        if len(options) < 2:
            raise ValueError("The requested branch group has no choice to make.")
        if target_quest_id not in options:
            raise KeyError(f"Quest is not an option in this branch: {target_quest_id}")
        if _state_value(quest_states.get(source_quest_id, "available")) != "completed":
            raise ValueError("The source quest must be completed before choosing a branch.")
        key = (source_quest_id, branch_group)
        selected = self._selections.get(key)
        if selected is not None and selected != target_quest_id:
            raise ValueError("A branch choice cannot be changed once selected.")
        self._selections[key] = target_quest_id
        return target_quest_id

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_branches": [
                {
                    "source_quest_id": source,
                    "branch_group": group,
                    "target_quest_id": target,
                }
                for (source, group), target in sorted(self._selections.items())
            ]
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, object],
        graph: "QuestGraph",
    ) -> "QuestGraphProgress":
        if not isinstance(data, Mapping):
            raise TypeError("Quest graph progress must be a mapping.")
        records = data.get("selected_branches", [])
        if not isinstance(records, list):
            raise ValueError("selected_branches must be a list.")
        progress = cls()
        for record in records:
            if not isinstance(record, Mapping):
                raise ValueError("Branch selection records must be objects.")
            source = record.get("source_quest_id")
            group = record.get("branch_group")
            target = record.get("target_quest_id")
            options = graph.branch_options(source, group)
            if len(options) < 2 or target not in options:
                raise ValueError("Saved branch selection does not match quest content.")
            key = (source, group)
            if key in progress._selections:
                raise ValueError("Duplicate saved branch selection.")
            progress._selections[key] = target
        return progress


@dataclass(frozen=True)
class QuestLink:
    """A directed relationship declared by content."""

    source_quest_id: str
    target_quest_id: str
    link_type: QuestLinkType = QuestLinkType.UNLOCKS
    branch_group: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_quest_id, str) or not self.source_quest_id.strip():
            raise ValueError("source_quest_id must be a non-empty string.")
        if not isinstance(self.target_quest_id, str) or not self.target_quest_id.strip():
            raise ValueError("target_quest_id must be a non-empty string.")
        if self.source_quest_id == self.target_quest_id:
            raise ValueError("A quest link cannot target itself.")
        object.__setattr__(self, "link_type", QuestLinkType(self.link_type))
        if self.link_type is QuestLinkType.ALTERNATIVE:
            if not isinstance(self.branch_group, str) or not self.branch_group.strip():
                raise ValueError("Alternative links require a non-empty branch_group.")
        elif self.branch_group is not None:
            raise ValueError("branch_group is only valid for alternative links.")


class QuestGraph:
    """Validated, acyclic quest progression graph.

    Runtime rules:
    - Root quests have no graph prerequisite.
    - UNLOCKS and SIDE incoming links are all required (AND).
    - ALTERNATIVE incoming links sharing a branch_group are OR alternatives.
    - A source with multiple outgoing alternatives in one group requires an
      explicit, persistent player choice before the selected target unlocks.
    - A single alternative link needs no choice.
    - Quest-local prerequisites are evaluated separately by can_start().
    """

    def __init__(
        self,
        quest_ids: Iterable[str] = (),
        links: Iterable[QuestLink] = (),
    ) -> None:
        self._quest_ids: set[str] = set()
        for quest_id in quest_ids:
            self.add_quest(quest_id)
        self._links: list[QuestLink] = []
        for link in links:
            self.add_link(link)
        self.validate()

    def add_quest(self, quest_id: str) -> None:
        if not isinstance(quest_id, str) or not quest_id.strip():
            raise ValueError("quest_id must be a non-empty string.")
        if quest_id in self._quest_ids:
            raise ValueError(f"Duplicate quest ID in graph: {quest_id}")
        self._quest_ids.add(quest_id)

    def add_link(self, link: QuestLink) -> None:
        if not isinstance(link, QuestLink):
            raise TypeError("link must be QuestLink.")
        if link.source_quest_id not in self._quest_ids:
            raise KeyError(f"Unknown source quest: {link.source_quest_id}")
        if link.target_quest_id not in self._quest_ids:
            raise KeyError(f"Unknown target quest: {link.target_quest_id}")
        if link in self._links:
            raise ValueError("Duplicate quest link.")
        self._links.append(link)
        try:
            self.validate()
        except Exception:
            self._links.pop()
            raise

    def quest_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._quest_ids))

    def links(self) -> tuple[QuestLink, ...]:
        return tuple(sorted(
            self._links,
            key=lambda link: (
                link.source_quest_id, link.target_quest_id,
                link.link_type.value, link.branch_group or "",
            ),
        ))

    def outgoing(self, quest_id: str) -> tuple[QuestLink, ...]:
        self._require_known(quest_id)
        return tuple(link for link in self.links() if link.source_quest_id == quest_id)

    def incoming(self, quest_id: str) -> tuple[QuestLink, ...]:
        self._require_known(quest_id)
        return tuple(link for link in self.links() if link.target_quest_id == quest_id)

    def successors(self, quest_id: str) -> tuple[str, ...]:
        return tuple(link.target_quest_id for link in self.outgoing(quest_id))

    def predecessors(self, quest_id: str) -> tuple[str, ...]:
        return tuple(link.source_quest_id for link in self.incoming(quest_id))

    def branch_options(self, source_quest_id: str, branch_group: str) -> tuple[str, ...]:
        self._require_known(source_quest_id)
        if not isinstance(branch_group, str) or not branch_group.strip():
            raise ValueError("branch_group must be a non-empty string.")
        return tuple(sorted({
            link.target_quest_id for link in self.outgoing(source_quest_id)
            if link.link_type is QuestLinkType.ALTERNATIVE
            and link.branch_group == branch_group
        }))

    def is_unlocked(
        self,
        quest_id: str,
        quest_states: Mapping[str, object],
        progress: QuestGraphProgress | None = None,
    ) -> bool:
        self._require_known(quest_id)
        if not isinstance(quest_states, Mapping):
            raise TypeError("quest_states must be a mapping.")
        progress = progress or QuestGraphProgress()
        incoming = self.incoming(quest_id)
        if not incoming:
            return True

        required = [
            link for link in incoming
            if link.link_type in (QuestLinkType.UNLOCKS, QuestLinkType.SIDE)
        ]
        if any(_state_value(quest_states.get(link.source_quest_id, "available")) != "completed"
               for link in required):
            return False

        alternatives: dict[str, list[QuestLink]] = {}
        for link in incoming:
            if link.link_type is QuestLinkType.ALTERNATIVE:
                alternatives.setdefault(link.branch_group, []).append(link)

        for group_links in alternatives.values():
            satisfied = False
            for link in group_links:
                if _state_value(quest_states.get(link.source_quest_id, "available")) != "completed":
                    continue
                options = self.branch_options(link.source_quest_id, link.branch_group)
                if len(options) > 1:
                    selected = progress.selected_branch(link.source_quest_id, link.branch_group)
                    if selected != link.target_quest_id:
                        continue
                satisfied = True
                break
            if not satisfied:
                return False
        return True

    def can_start(
        self,
        quest: object,
        quest_states: Mapping[str, object],
        context: Mapping[str, object] | None = None,
        progress: QuestGraphProgress | None = None,
    ) -> bool:
        quest_id = getattr(quest, "quest_id", None)
        if quest_id not in self._quest_ids:
            raise KeyError(f"Quest is not registered in graph: {quest_id}")
        local_check = getattr(quest, "can_start", None)
        if not callable(local_check):
            raise TypeError("quest must provide can_start(context).")
        return bool(local_check(context or {})) and self.is_unlocked(
            quest_id, quest_states, progress
        )

    def available_quests(
        self,
        quests: Iterable[object],
        quest_states: Mapping[str, object],
        context: Mapping[str, object] | None = None,
        progress: QuestGraphProgress | None = None,
    ) -> tuple[object, ...]:
        return tuple(
            quest for quest in quests
            if self.can_start(quest, quest_states, context, progress)
        )

    def validate(self) -> None:
        self._validate_references()
        self._validate_acyclic()

    def _require_known(self, quest_id: str) -> None:
        if quest_id not in self._quest_ids:
            raise KeyError(f"Unknown quest: {quest_id}")

    def _validate_references(self) -> None:
        for link in self._links:
            if link.source_quest_id not in self._quest_ids:
                raise KeyError(f"Unknown source quest: {link.source_quest_id}")
            if link.target_quest_id not in self._quest_ids:
                raise KeyError(f"Unknown target quest: {link.target_quest_id}")

    def _validate_acyclic(self) -> None:
        adjacency = {quest_id: [] for quest_id in self._quest_ids}
        for link in self._links:
            adjacency[link.source_quest_id].append(link.target_quest_id)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(quest_id: str) -> None:
            if quest_id in visiting:
                raise ValueError("Quest graph contains a cycle.")
            if quest_id in visited:
                return
            visiting.add(quest_id)
            for target in adjacency[quest_id]:
                visit(target)
            visiting.remove(quest_id)
            visited.add(quest_id)

        for quest_id in sorted(self._quest_ids):
            visit(quest_id)


__all__ = ["QuestGraph", "QuestGraphProgress", "QuestLink", "QuestLinkType"]
