"""Fixed-root quadtree; straddling entries remain in their parent node."""
from __future__ import annotations

from dataclasses import dataclass, field
from .entry import SpatialEntry, _validate_bounds
from .protocols import Bounds2D


@dataclass
class _Node:
    bounds: Bounds2D
    depth: int
    entries: dict[str, SpatialEntry] = field(default_factory=dict)
    children: tuple["_Node", ...] = ()


class Quadtree:
    def __init__(self, bounds: Bounds2D, *, capacity: int = 8, max_depth: int = 8) -> None:
        _validate_bounds(bounds)
        if bounds.min_x == bounds.max_x or bounds.min_y == bounds.max_y:
            raise ValueError("root bounds must have positive area")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
            raise ValueError("max_depth must be a non-negative integer")
        self._root_bounds = bounds
        self.capacity = capacity
        self.max_depth = max_depth
        self._root = _Node(bounds, 0)
        self._entries: dict[str, SpatialEntry] = {}

    def _contains(self, outer: Bounds2D, inner: Bounds2D) -> bool:
        return (outer.min_x <= inner.min_x and outer.min_y <= inner.min_y
                and outer.max_x >= inner.max_x and outer.max_y >= inner.max_y)

    def _children(self, node: _Node) -> tuple[_Node, ...]:
        b = node.bounds
        mx, my = (b.min_x + b.max_x) / 2, (b.min_y + b.max_y) / 2
        from ._bounds import Bounds
        return (
            _Node(Bounds(b.min_x, b.min_y, mx, my), node.depth + 1),
            _Node(Bounds(mx, b.min_y, b.max_x, my), node.depth + 1),
            _Node(Bounds(b.min_x, my, mx, b.max_y), node.depth + 1),
            _Node(Bounds(mx, my, b.max_x, b.max_y), node.depth + 1),
        )

    def _child_for(self, node: _Node, bounds: Bounds2D) -> _Node | None:
        if not node.children:
            return None
        matches = [child for child in node.children if self._contains(child.bounds, bounds)]
        return matches[0] if len(matches) == 1 else None

    def _insert_node(self, node: _Node, entry: SpatialEntry) -> None:
        if node.children:
            child = self._child_for(node, entry.bounds)
            if child is not None:
                self._insert_node(child, entry)
                return
        node.entries[entry.item_id] = entry
        if len(node.entries) > self.capacity and node.depth < self.max_depth:
            if not node.children:
                node.children = self._children(node)
            for item_id, current in tuple(node.entries.items()):
                child = self._child_for(node, current.bounds)
                if child is not None:
                    del node.entries[item_id]
                    self._insert_node(child, current)

    def insert(self, item_id: str, bounds: Bounds2D) -> None:
        entry = SpatialEntry(item_id, bounds)
        if item_id in self._entries:
            raise ValueError(f"item already exists: {item_id}")
        if not self._contains(self._root_bounds, bounds):
            raise ValueError("entry bounds must be contained by quadtree root")
        self._entries[item_id] = entry
        self._insert_node(self._root, entry)

    def _rebuild(self) -> None:
        self._root = _Node(self._root_bounds, 0)
        for entry in self._entries.values():
            self._insert_node(self._root, entry)

    def update(self, item_id: str, bounds: Bounds2D) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        entry = SpatialEntry(item_id, bounds)
        if not self._contains(self._root_bounds, bounds):
            raise ValueError("entry bounds must be contained by quadtree root")
        self._entries[item_id] = entry
        self._rebuild()

    def remove(self, item_id: str) -> None:
        if item_id not in self._entries:
            raise KeyError(item_id)
        del self._entries[item_id]
        self._rebuild()

    def _query_node(self, node: _Node, bounds: Bounds2D, found: set[str]) -> None:
        if not node.bounds.intersects(bounds):
            return
        for item_id, entry in node.entries.items():
            if bounds.intersects(entry.bounds):
                found.add(item_id)
        for child in node.children:
            self._query_node(child, bounds, found)

    def query(self, bounds: Bounds2D) -> tuple[str, ...]:
        _validate_bounds(bounds)
        found: set[str] = set()
        self._query_node(self._root, bounds, found)
        return tuple(sorted(found))

    def clear(self) -> None:
        self._entries.clear()
        self._root = _Node(self._root_bounds, 0)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def node_count(self) -> int:
        def count(node: _Node) -> int:
            return 1 + sum(count(child) for child in node.children)
        return count(self._root)
