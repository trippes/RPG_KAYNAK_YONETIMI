"""Shared, immutable domain contracts for axial-hex entity movement."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .local_hex_position import LocalHexPosition


def _require_id(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class EntityPosition:
    """An entity's logical position, scoped to one local hex map."""

    map_id: str
    cell: LocalHexPosition

    def __post_init__(self) -> None:
        _require_id(self.map_id, "map_id")
        if not isinstance(self.cell, LocalHexPosition):
            raise TypeError("cell must be a LocalHexPosition.")


@dataclass(frozen=True, slots=True)
class MovementProfile:
    """Movement capabilities shared by players, NPCs, and movable objects."""

    can_move: bool = True
    allowed_terrain_ids: frozenset[str] | None = None
    can_traverse_blocked_cells: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.can_move, bool):
            raise TypeError("can_move must be a boolean.")
        if not isinstance(self.can_traverse_blocked_cells, bool):
            raise TypeError("can_traverse_blocked_cells must be a boolean.")
        if self.allowed_terrain_ids is not None:
            try:
                values = frozenset(self.allowed_terrain_ids)
            except TypeError as exc:
                raise TypeError("allowed_terrain_ids must be an iterable of strings.") from exc
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError("allowed_terrain_ids must contain non-empty strings.")
            object.__setattr__(self, "allowed_terrain_ids", values)


@dataclass(frozen=True, slots=True)
class MovementRequest:
    """A movement intent; it does not mutate an entity or a map."""

    entity_id: str
    source: EntityPosition
    target: EntityPosition
    profile: MovementProfile = field(default_factory=MovementProfile)

    def __post_init__(self) -> None:
        _require_id(self.entity_id, "entity_id")
        if not isinstance(self.source, EntityPosition):
            raise TypeError("source must be an EntityPosition.")
        if not isinstance(self.target, EntityPosition):
            raise TypeError("target must be an EntityPosition.")
        if not isinstance(self.profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")


class MovementFailureReason(str, Enum):
    NONE = "none"
    MOVEMENT_NOT_ALLOWED = "movement_not_allowed"
    INVALID_SOURCE = "invalid_source"
    INVALID_TARGET = "invalid_target"
    NON_ADJACENT_TARGET = "non_adjacent_target"
    BLOCKED_CELL = "blocked_cell"
    OCCUPIED_CELL = "occupied_cell"
    TERRAIN_NOT_ALLOWED = "terrain_not_allowed"
    INVALID_TRANSITION = "invalid_transition"


@dataclass(frozen=True, slots=True)
class MovementResult:
    """Immutable outcome; failures retain the source position."""

    success: bool
    position: EntityPosition
    reason: MovementFailureReason = MovementFailureReason.NONE
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")
        if not isinstance(self.position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        if not isinstance(self.reason, MovementFailureReason):
            raise TypeError("reason must be a MovementFailureReason.")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string.")
        if self.success and self.reason is not MovementFailureReason.NONE:
            raise ValueError("A successful movement cannot have a failure reason.")
        if not self.success and self.reason is MovementFailureReason.NONE:
            raise ValueError("A failed movement must have a failure reason.")
