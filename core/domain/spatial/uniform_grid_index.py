"""Map-scoped uniform-grid broadphase index for continuous world bounds."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from numbers import Real
from typing import DefaultDict

from .aabb import AABB


@dataclass(frozen=True, slots=True)
class _IndexedBounds:
    map_id: str
    bounds: AABB


class UniformGridIndex:
    """Sparse spatial hash with exact AABB filtering and stable query order.

    The index stores only derived bounds keyed by an existing stable entity ID.
    It does not own entity identity, map definitions, or authoritative position.
    """

    def __init__(self, cell_size: float = 128.0) -> None:
        if isinstance(cell_size, bool) or not isinstance(cell_size, Real):
            raise TypeError("cell_size must be a real number.")
        if not math.isfinite(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be finite and positive.")
        self.cell_size = float(cell_size)
        self._entries: dict[str, _IndexedBounds] = {}
        self._buckets: DefaultDict[tuple[str, int, int], set[str]] = defaultdict(set)
        self._entry_buckets: dict[str, tuple[tuple[str, int, int], ...]] = {}

    def _keys(self, map_id: str, bounds: AABB) -> tuple[tuple[str, int, int], ...]:
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(bounds, AABB):
            raise TypeError("bounds must be an AABB.")
        x0 = math.floor(bounds.min_x / self.cell_size)
        x1 = math.floor(bounds.max_x / self.cell_size)
        y0 = math.floor(bounds.min_y / self.cell_size)
        y1 = math.floor(bounds.max_y / self.cell_size)
        return tuple(
            (map_id, x, y)
            for x in range(x0, x1 + 1)
            for y in range(y0, y1 + 1)
        )

    @staticmethod
    def _validate_item_id(item_id: str) -> None:
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("item_id must be a non-empty string.")

    def insert(self, item_id: str, map_id: str, bounds: AABB) -> None:
        self._validate_item_id(item_id)
        if item_id in self._entries:
            raise ValueError(f"spatial item already exists: {item_id}")
        keys = self._keys(map_id, bounds)
        self._entries[item_id] = _IndexedBounds(map_id, bounds)
        self._entry_buckets[item_id] = keys
        for key in keys:
            self._buckets[key].add(item_id)

    def _remove_bucket_memberships(self, item_id: str) -> None:
        for key in self._entry_buckets.pop(item_id):
            bucket = self._buckets[key]
            bucket.remove(item_id)
            if not bucket:
                del self._buckets[key]

    def update(self, item_id: str, map_id: str, bounds: AABB) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        keys = self._keys(map_id, bounds)
        # All validation is complete before the previous index entry is removed.
        self._remove_bucket_memberships(item_id)
        self._entries[item_id] = _IndexedBounds(map_id, bounds)
        self._entry_buckets[item_id] = keys
        for key in keys:
            self._buckets[key].add(item_id)

    def remove(self, item_id: str) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        self._remove_bucket_memberships(item_id)
        del self._entries[item_id]

    def query(self, map_id: str, bounds: AABB) -> tuple[str, ...]:
        keys = self._keys(map_id, bounds)
        candidates: set[str] = set()
        for key in keys:
            candidates.update(self._buckets.get(key, ()))
        return tuple(sorted(
            item_id
            for item_id in candidates
            if self._entries[item_id].map_id == map_id
            and bounds.intersects(self._entries[item_id].bounds)
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
