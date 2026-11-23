"""Chunked, deterministic LRU cache for derived square-grid coverage.

The cache is derived from immutable HexMapDefinition inputs. It is deliberately
separate from UniformGridIndex, actor occupancy, persistence, and pathfinding.
"""
from __future__ import annotations

import hashlib
import math
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock

from application.hex_map_definition import HexMapDefinition
from application.square_grid_coverage import (
    SquareGridCoverageMap,
    build_square_grid_coverage,
)
from core.domain.spatial import SquareGridCoord, WorldPoint, pointy_top_hex_corners


@dataclass(frozen=True, order=True, slots=True)
class SquareGridChunkCoord:
    x: int
    y: int

    def __post_init__(self) -> None:
        if type(self.x) is not int or type(self.y) is not int:
            raise TypeError("chunk coordinates must be integers (bool is not allowed).")


@dataclass(frozen=True, slots=True)
class SquareGridCacheStats:
    hits: int
    misses: int
    evictions: int
    entries: int


def square_grid_geometry_fingerprint(
    map_definition: HexMapDefinition,
    *,
    cell_size: int | float,
    hex_size: int | float = 32.0,
    grid_origin: WorldPoint = WorldPoint(0.0, 0.0),
    hex_origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> str:
    """Return a stable content fingerprint for every geometry-relevant input."""
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition.")
    size = _positive_finite(cell_size, "cell_size")
    radius = _positive_finite(hex_size, "hex_size")
    _validate_origin(grid_origin, "grid_origin")
    _validate_origin(hex_origin, "hex_origin")
    digest = hashlib.sha256()
    header = (
        map_definition.map_id,
        size,
        radius,
        (grid_origin.x, grid_origin.y),
        (hex_origin.x, hex_origin.y),
    )
    digest.update(repr(header).encode("utf-8"))
    for position in sorted(map_definition.valid_cells):
        cell = map_definition.get_cell(position)
        record = (position.q, position.r, cell.terrain_id, cell.blocked)
        digest.update(repr(record).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _positive_finite(value: int | float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite real number.")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and greater than zero.")
    return result


def _validate_origin(origin: WorldPoint, name: str) -> None:
    if not isinstance(origin, WorldPoint):
        raise TypeError(f"{name} must be a WorldPoint.")


def _map_grid_bounds(
    map_definition: HexMapDefinition,
    *,
    cell_size: float,
    hex_size: float,
    grid_origin: WorldPoint,
    hex_origin: WorldPoint,
) -> tuple[int, int, int, int]:
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf
    for position in map_definition.valid_cells:
        for point in pointy_top_hex_corners(
            position.to_hex_coord(), hex_size, hex_origin,
        ):
            min_x = min(min_x, point.x)
            min_y = min(min_y, point.y)
            max_x = max(max_x, point.x)
            max_y = max(max_y, point.y)
    return (
        math.floor((min_x - grid_origin.x) / cell_size + 0.5),
        math.floor((min_y - grid_origin.y) / cell_size + 0.5),
        math.floor((max_x - grid_origin.x) / cell_size + 0.5),
        math.floor((max_y - grid_origin.y) / cell_size + 0.5),
    )


class SquareGridChunkCache:
    """Thread-safe LRU cache of immutable coverage chunks.

    Chunk coordinates use floor-division semantics, including negative cells.
    The cache stores no actor state and is never serialized. Geometry metadata
    is memoized per immutable map instance so cache hits do not rescan the map.
    """

    def __init__(self, *, chunk_size: int = 16, max_chunks: int = 64) -> None:
        if type(chunk_size) is not int or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if type(max_chunks) is not int or max_chunks <= 0:
            raise ValueError("max_chunks must be a positive integer.")
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self._entries: OrderedDict[tuple[object, ...], SquareGridCoverageMap] = OrderedDict()
        self._metadata: OrderedDict[
            tuple[object, ...],
            tuple[HexMapDefinition, str, tuple[int, int, int, int]],
        ] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = RLock()

    @property
    def stats(self) -> SquareGridCacheStats:
        with self._lock:
            return SquareGridCacheStats(
                self._hits, self._misses, self._evictions, len(self._entries),
            )

    def clear(self, *, reset_stats: bool = False) -> None:
        with self._lock:
            self._entries.clear()
            self._metadata.clear()
            if reset_stats:
                self._hits = self._misses = self._evictions = 0

    def _geometry_metadata(
        self,
        map_definition: HexMapDefinition,
        *,
        cell_size: float,
        hex_size: float,
        grid_origin: WorldPoint,
        hex_origin: WorldPoint,
    ) -> tuple[str, tuple[int, int, int, int]]:
        metadata_key = (
            id(map_definition),
            cell_size,
            hex_size,
            grid_origin,
            hex_origin,
        )
        with self._lock:
            cached = self._metadata.get(metadata_key)
            if cached is not None and cached[0] is map_definition:
                self._metadata.move_to_end(metadata_key)
                return cached[1], cached[2]

        fingerprint = square_grid_geometry_fingerprint(
            map_definition,
            cell_size=cell_size,
            hex_size=hex_size,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )
        bounds = _map_grid_bounds(
            map_definition,
            cell_size=cell_size,
            hex_size=hex_size,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )
        with self._lock:
            existing = self._metadata.get(metadata_key)
            if existing is not None and existing[0] is map_definition:
                self._metadata.move_to_end(metadata_key)
                return existing[1], existing[2]
            self._metadata[metadata_key] = (map_definition, fingerprint, bounds)
            while len(self._metadata) > 16:
                self._metadata.popitem(last=False)
        return fingerprint, bounds

    def chunk_coords(
        self,
        map_definition: HexMapDefinition,
        *,
        cell_size: int | float,
        hex_size: int | float = 32.0,
        grid_origin: WorldPoint = WorldPoint(0.0, 0.0),
        hex_origin: WorldPoint = WorldPoint(0.0, 0.0),
    ) -> tuple[SquareGridChunkCoord, ...]:
        size = _positive_finite(cell_size, "cell_size")
        radius = _positive_finite(hex_size, "hex_size")
        _validate_origin(grid_origin, "grid_origin")
        _validate_origin(hex_origin, "hex_origin")
        _, bounds = self._geometry_metadata(
            map_definition,
            cell_size=size,
            hex_size=radius,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )
        min_x, min_y, max_x, max_y = bounds
        first_x, last_x = min_x // self.chunk_size, max_x // self.chunk_size
        first_y, last_y = min_y // self.chunk_size, max_y // self.chunk_size
        return tuple(
            SquareGridChunkCoord(x, y)
            for x in range(first_x, last_x + 1)
            for y in range(first_y, last_y + 1)
        )

    def get_chunk(
        self,
        map_definition: HexMapDefinition,
        chunk_coord: SquareGridChunkCoord,
        *,
        cell_size: int | float,
        hex_size: int | float = 32.0,
        grid_origin: WorldPoint = WorldPoint(0.0, 0.0),
        hex_origin: WorldPoint = WorldPoint(0.0, 0.0),
    ) -> SquareGridCoverageMap:
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be a HexMapDefinition.")
        if not isinstance(chunk_coord, SquareGridChunkCoord):
            raise TypeError("chunk_coord must be a SquareGridChunkCoord.")
        size = _positive_finite(cell_size, "cell_size")
        radius = _positive_finite(hex_size, "hex_size")
        _validate_origin(grid_origin, "grid_origin")
        _validate_origin(hex_origin, "hex_origin")
        fingerprint, bounds = self._geometry_metadata(
            map_definition,
            cell_size=size,
            hex_size=radius,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )
        key = (fingerprint, self.chunk_size, chunk_coord)
        with self._lock:
            cached = self._entries.get(key)
            if cached is not None:
                self._entries.move_to_end(key)
                self._hits += 1
                return cached
            self._misses += 1

        min_x, min_y, max_x, max_y = bounds
        chunk_min_x = max(min_x, chunk_coord.x * self.chunk_size)
        chunk_min_y = max(min_y, chunk_coord.y * self.chunk_size)
        chunk_max_x = min(max_x, (chunk_coord.x + 1) * self.chunk_size - 1)
        chunk_max_y = min(max_y, (chunk_coord.y + 1) * self.chunk_size - 1)
        if chunk_min_x > chunk_max_x or chunk_min_y > chunk_max_y:
            raise ValueError("chunk_coord does not intersect the map's grid bounds.")

        built = build_square_grid_coverage(
            map_definition,
            size,
            hex_size=radius,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
            grid_bounds=(chunk_min_x, chunk_min_y, chunk_max_x, chunk_max_y),
        )
        with self._lock:
            existing = self._entries.get(key)
            if existing is not None:
                self._entries.move_to_end(key)
                return existing
            self._entries[key] = built
            while len(self._entries) > self.max_chunks:
                self._entries.popitem(last=False)
                self._evictions += 1
            return built


__all__ = [
    "SquareGridChunkCoord",
    "SquareGridCacheStats",
    "SquareGridChunkCache",
    "square_grid_geometry_fingerprint",
]
