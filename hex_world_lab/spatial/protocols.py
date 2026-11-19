"""Generic spatial indexing contracts, independent of game and physics domains."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Bounds2D(Protocol):
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def intersects(self, other: object) -> bool: ...


@runtime_checkable
class SpatialIndex(Protocol):
    def insert(self, item_id: str, bounds: Bounds2D) -> None: ...
    def update(self, item_id: str, bounds: Bounds2D) -> None: ...
    def remove(self, item_id: str) -> None: ...
    def query(self, bounds: Bounds2D) -> tuple[str, ...]: ...
    def clear(self) -> None: ...
    def __len__(self) -> int: ...
