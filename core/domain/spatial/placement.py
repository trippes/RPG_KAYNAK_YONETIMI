"""Pure construction placement preview and validation rules.

This module consumes immutable map/occupancy snapshots. It does not mutate
HexWorldRuntime, actor positions, entity ownership, or the world placement
catalog. A caller must revalidate against a current snapshot at commit time.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import (
    ConstructionPosition,
    ConstructionSpaceTransform,
    HexCoord,
    LocalHexPosition,
    WorldPoint,
)


class PlacementFailureReason(str, Enum):
    WRONG_MAP = "wrong_map"
    OUTSIDE_WORLD = "outside_world"
    BLOCKED_TERRAIN = "blocked_terrain"
    OVERLAP = "overlap"
    UNSUPPORTED = "unsupported"
    PERMISSION_DENIED = "permission_denied"
    STALE_STATE = "stale_state"
    INVALID_FOOTPRINT = "invalid_footprint"


@dataclass(frozen=True, slots=True)
class ConstructionPlacementRequest:
    part_definition_id: str
    position: ConstructionPosition
    footprint_local_points: tuple[WorldPoint, ...]
    actor_id: str
    requires_support: bool = False
    has_permission: bool = True

    def __post_init__(self) -> None:
        for name in ("part_definition_id", "actor_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.position, ConstructionPosition):
            raise TypeError("position must be a ConstructionPosition.")
        points = tuple(self.footprint_local_points)
        if not points or any(not isinstance(p, WorldPoint) for p in points):
            raise ValueError("footprint_local_points must contain WorldPoint values.")
        if len(set(points)) != len(points):
            raise ValueError("footprint_local_points cannot contain duplicates.")
        if not isinstance(self.requires_support, bool):
            raise TypeError("requires_support must be boolean.")
        if not isinstance(self.has_permission, bool):
            raise TypeError("has_permission must be boolean.")
        object.__setattr__(self, "footprint_local_points", points)


@dataclass(frozen=True, slots=True)
class ConstructionPlacementSnapshot:
    map_definition: HexMapDefinition
    hex_size: float
    origin: WorldPoint
    occupied_cells: Mapping[HexCoord, str]
    supported_cells: frozenset[HexCoord]
    state_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.map_definition, HexMapDefinition):
            raise TypeError("map_definition must be a HexMapDefinition.")
        if isinstance(self.hex_size, bool) or not isinstance(self.hex_size, (int, float)):
            raise TypeError("hex_size must be a finite positive number.")
        if not math.isfinite(self.hex_size) or self.hex_size <= 0:
            raise ValueError("hex_size must be finite and greater than zero.")
        if not isinstance(self.origin, WorldPoint):
            raise TypeError("origin must be a WorldPoint.")
        if type(self.state_revision) is not int or self.state_revision < 0:
            raise ValueError("state_revision must be a non-negative integer.")
        occupied = dict(self.occupied_cells)
        if any(not isinstance(k, HexCoord) for k in occupied):
            raise TypeError("occupied_cells keys must be HexCoord values.")
        if any(not isinstance(v, str) or not v.strip() for v in occupied.values()):
            raise ValueError("occupied_cells values must be non-empty structure IDs.")
        supported = frozenset(self.supported_cells)
        if any(not isinstance(cell, HexCoord) for cell in supported):
            raise TypeError("supported_cells must contain HexCoord values.")
        object.__setattr__(self, "hex_size", float(self.hex_size))
        object.__setattr__(self, "occupied_cells", MappingProxyType(occupied))
        object.__setattr__(self, "supported_cells", supported)


@dataclass(frozen=True, slots=True)
class ConstructionPlacementResult:
    valid: bool
    footprint_cells: tuple[HexCoord, ...]
    reasons: tuple[PlacementFailureReason, ...]
    snapshot_revision: int

    def __post_init__(self) -> None:
        if self.valid != (not self.reasons):
            raise ValueError("valid must be true exactly when reasons is empty.")
        if self.valid and not self.footprint_cells:
            raise ValueError("A valid placement must have a non-empty footprint.")
        if type(self.snapshot_revision) is not int or self.snapshot_revision < 0:
            raise ValueError("snapshot_revision must be a non-negative integer.")


def _rotated(point: WorldPoint, degrees: float) -> WorldPoint:
    radians = math.radians(degrees)
    cosine, sine = math.cos(radians), math.sin(radians)
    return WorldPoint(
        point.x * cosine - point.y * sine,
        point.x * sine + point.y * cosine,
    )


class ConstructionPlacementValidator:
    """Deterministic validator over a caller-supplied immutable snapshot."""

    @staticmethod
    def validate(
        request: ConstructionPlacementRequest,
        snapshot: ConstructionPlacementSnapshot,
    ) -> ConstructionPlacementResult:
        if not isinstance(request, ConstructionPlacementRequest):
            raise TypeError("request must be a ConstructionPlacementRequest.")
        if not isinstance(snapshot, ConstructionPlacementSnapshot):
            raise TypeError("snapshot must be a ConstructionPlacementSnapshot.")

        reasons: list[PlacementFailureReason] = []
        if request.position.map_id != snapshot.map_definition.map_id:
            return ConstructionPlacementResult(
                False, (), (PlacementFailureReason.WRONG_MAP,), snapshot.state_revision
            )
        if not request.has_permission:
            reasons.append(PlacementFailureReason.PERMISSION_DENIED)

        transform = ConstructionSpaceTransform(
            snapshot.map_definition.map_id, snapshot.hex_size, snapshot.origin
        )
        cells: set[HexCoord] = set()
        for local_point in request.footprint_local_points:
            rotated = _rotated(local_point, request.position.rotation_degrees)
            world = request.position.point.translated(rotated.x, rotated.y)
            cells.add(transform.position_to_hex(
                ConstructionPosition(request.position.map_id, world)
            ))
        footprint = tuple(sorted(cells, key=lambda cell: (cell.q, cell.r)))
        if not footprint:
            reasons.append(PlacementFailureReason.INVALID_FOOTPRINT)
        outside = any(
            not snapshot.map_definition.has_cell(LocalHexPosition.from_hex_coord(cell))
            for cell in footprint
        )
        if outside:
            reasons.append(PlacementFailureReason.OUTSIDE_WORLD)
        valid_cells = [
            cell for cell in footprint
            if snapshot.map_definition.has_cell(
                type(next(iter(snapshot.map_definition.valid_cells)))(cell.q, cell.r)
            )
        ]
        if any(
            snapshot.map_definition.is_blocked(
                type(next(iter(snapshot.map_definition.valid_cells)))(cell.q, cell.r)
            )
            for cell in valid_cells
        ):
            reasons.append(PlacementFailureReason.BLOCKED_TERRAIN)
        if any(cell in snapshot.occupied_cells for cell in footprint):
            reasons.append(PlacementFailureReason.OVERLAP)
        if request.requires_support and any(
            cell not in snapshot.supported_cells for cell in footprint
        ):
            reasons.append(PlacementFailureReason.UNSUPPORTED)

        ordered_reasons = tuple(dict.fromkeys(reasons))
        return ConstructionPlacementResult(
            not ordered_reasons,
            footprint,
            ordered_reasons,
            snapshot.state_revision,
        )


def check_placement_revision(
    result: ConstructionPlacementResult, current_revision: int
) -> ConstructionPlacementResult:
    """Reject a preview if its snapshot is stale; caller must then revalidate."""
    if type(current_revision) is not int or current_revision < 0:
        raise ValueError("current_revision must be a non-negative integer.")
    if current_revision == result.snapshot_revision:
        return result
    reasons = tuple(dict.fromkeys(
        (*result.reasons, PlacementFailureReason.STALE_STATE)
    ))
    return ConstructionPlacementResult(
        False, result.footprint_cells, reasons, result.snapshot_revision
    )


__all__ = [
    "PlacementFailureReason",
    "ConstructionPlacementRequest",
    "ConstructionPlacementSnapshot",
    "ConstructionPlacementResult",
    "ConstructionPlacementValidator",
    "check_placement_revision",
]
