"""Content-driven quest graph definitions and validation.

This module contains only generic relationships between quest identifiers.
It does not know NPC names, demo quests, UI screens or gameplay services.
Content packages can create a QuestGraph and attach any quest IDs to it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class QuestLinkType(str, Enum):
    """General semantic relationship between two quests."""

    UNLOCKS = "unlocks"
    ALTERNATIVE = "alternative"
    SIDE = "side"


@dataclass(frozen=True)
class QuestLink:
    """A directed relationship declared by content.

    The source and target are stable quest IDs. Runtime code decides when a
    link becomes eligible; the graph itself only describes and validates the
    content relationship.
    """

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
        if self.branch_group is not None:
            if not isinstance(self.branch_group, str) or not self.branch_group.strip():
                raise ValueError("branch_group must be a non-empty string or None.")


class QuestGraph:
    """Validated, content-defined graph of quest relationships.

    The graph is deliberately independent from Quest instances so content can
    be loaded, validated and inspected without changing runtime quest logic.
    Cycles are rejected because ordinary progression graphs must be acyclic.
    Repeatable loops, if introduced later, should use an explicit repeat
    mechanism rather than an implicit graph cycle.
    """

    def __init__(
        self,
        quest_ids: Iterable[str] = (),
        links: Iterable[QuestLink] = (),
    ) -> None:
        self._quest_ids = set()
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
        return tuple(
            sorted(
                self._links,
                key=lambda link: (
                    link.source_quest_id,
                    link.target_quest_id,
                    link.link_type.value,
                    link.branch_group or "",
                ),
            )
        )

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


__all__ = ["QuestGraph", "QuestLink", "QuestLinkType"]
