"""Sparse uniform spatial hash grid with exact AABB filtering."""
from __future__ import annotations

from collections import defaultdict
from math import floor
from .entry import SpatialEntry, _validate_bounds
from .protocols import Bounds2D


class UniformGrid:
    def __init__(self, cell_size: float = 128.0) -> None:
        if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)):
            raise TypeError("cell_size must be a real number")
        if not 0 < cell_size < float("inf"):
            raise ValueError("cell_size must be finite and positive")
        self.cell_size = float(cell_size)
        self._entries: dict[str, SpatialEntry] = {}
        self._buckets: dict[tuple[int, int], set[str]] = defaultdict(set)
        self._entry_buckets: dict[str, tuple[tuple[int, int], ...]] = {}

    def _keys(self, bounds: Bounds2D) -> tuple[tuple[int, int], ...]:
        _validate_bounds(bounds)
        x0, x1 = floor(bounds.min_x / self.cell_size), floor(bounds.max_x / self.cell_size)
        y0, y1 = floor(bounds.min_y / self.cell_size), floor(bounds.max_y / self.cell_size)
        return tuple((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))

    def insert(self, item_id: str, bounds: Bounds2D) -> None:
        entry = SpatialEntry(item_id, bounds)
        if item_id in self._entries:
            raise ValueError(f"item already exists: {item_id}")
        keys = self._keys(bounds)
        self._entries[item_id] = entry
        self._entry_buckets[item_id] = keys
        for key in keys:
            self._buckets[key].add(item_id)

    def update(self, item_id: str, bounds: Bounds2D) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        entry = SpatialEntry(item_id, bounds)
        keys = self._keys(bounds)
        self._remove_memberships(item_id)
        self._entries[item_id] = entry
        self._entry_buckets[item_id] = keys
        for key in keys:
            self._buckets[key].add(item_id)

    def _remove_memberships(self, item_id: str) -> None:
        for key in self._entry_buckets.pop(item_id):
            bucket = self._buckets[key]
            bucket.remove(item_id)
            if not bucket:
                del self._buckets[key]

    def remove(self, item_id: str) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        self._remove_memberships(item_id)
        del self._entries[item_id]

    def query(self, bounds: Bounds2D) -> tuple[str, ...]:
        keys = self._keys(bounds)
        candidates: set[str] = set()
        for key in keys:
            candidates.update(self._buckets.get(key, ()))
        return tuple(sorted(
            item_id for item_id in candidates
            if bounds.intersects(self._entries[item_id].bounds)
        ))

    def clear(self) -> None:
        self._entries.clear()
        self._entry_buckets.clear()
        self._buckets.clear()

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def bucket_count(self) -> int:
        return len(self._buckets)
