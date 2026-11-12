"""Map-scoped movement contracts for the axial hex world.

These value objects are deliberately independent from Pygame and from the
legacy square-tile MovementManager.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from core.domain.spatial import LocalHexPosition


def _non_empty(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


@dataclass(frozen=True, slots=True)
class EntityPosition:
    """Authoritative logical position scoped to one local hex map."""

    map_id: str
    cell: LocalHexPosition

    def __post_init__(self) -> None:
        _non_empty(self.map_id, "map_id")
        if not isinstance(self.cell, LocalHexPosition):
            raise TypeError("cell must be a LocalHexPosition.")


@dataclass(frozen=True, slots=True)
class MovementProfile:
    """Capabilities used by the shared hex movement rules."""

    can_move: bool = True
    allowed_terrain_ids: frozenset[str] | None = None
    can_traverse_blocked_cells: bool = False
    ignores_occupancy: bool = False

    def __post_init__(self) -> None:
        for name in ("can_move", "can_traverse_blocked_cells", "ignores_occupancy"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")
        if self.allowed_terrain_ids is not None:
            values = frozenset(self.allowed_terrain_ids)
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError("allowed_terrain_ids must contain non-empty strings.")
            object.__setattr__(self, "allowed_terrain_ids", values)


@dataclass(frozen=True, slots=True)
class MovementRequest:
    """A request to move one entity from a source to a target position."""

    entity_id: str
    source: EntityPosition
    target: EntityPosition
    profile: MovementProfile = field(default_factory=MovementProfile)

    def __post_init__(self) -> None:
        _non_empty(self.entity_id, "entity_id")
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
    """Stable result returned by movement application services."""

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
