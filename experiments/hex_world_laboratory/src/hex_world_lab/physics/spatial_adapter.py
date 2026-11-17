"""Map-scoped adapter between obstacle snapshots and generic spatial indexes."""
from __future__ import annotations

from collections.abc import Iterable

from hex_world_lab.spatial import UniformGrid
from hex_world_lab.world.identity import MapId

from .broadphase import AABB
from .obstacle import ObstacleDefinition


class ObstacleSpatialIndex:
    """Maintain one map's immutable obstacle snapshot in a reusable grid."""

    __slots__ = ("map_id", "_obstacles", "_index")

    def __init__(self, obstacles: Iterable[ObstacleDefinition], *, cell_size: float = 64.0) -> None:
        values = tuple(obstacles)
        if any(not isinstance(item, ObstacleDefinition) for item in values):
            raise TypeError("obstacles must contain ObstacleDefinition values")
        maps = {item.map_id for item in values}
        if len(maps) > 1:
            raise ValueError("an obstacle index cannot span multiple maps")
        self.map_id = next(iter(maps), None)
        self._obstacles = {}
        self._index = UniformGrid(cell_size)
        ids = [item.obstacle_id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("obstacle IDs must be unique")
        for item in sorted(values, key=lambda value: value.obstacle_id):
            self._add(item)

    def _add(self, obstacle: ObstacleDefinition) -> None:
        if obstacle.obstacle_id in self._obstacles:
            raise ValueError(f"obstacle already exists: {obstacle.obstacle_id}")
        self._obstacles[obstacle.obstacle_id] = obstacle
        self._index.insert(obstacle.obstacle_id, AABB.from_shape(obstacle.world_shape()))

    def insert(self, obstacle: ObstacleDefinition) -> None:
        if not isinstance(obstacle, ObstacleDefinition):
            raise TypeError("obstacle must be an ObstacleDefinition")
        if self.map_id is not None and obstacle.map_id != self.map_id:
            raise ValueError("obstacle belongs to a different map")
        if self.map_id is None:
            self.map_id = obstacle.map_id
        self._add(obstacle)

    def update(self, obstacle: ObstacleDefinition) -> None:
        if not isinstance(obstacle, ObstacleDefinition):
            raise TypeError("obstacle must be an ObstacleDefinition")
        if obstacle.obstacle_id not in self._obstacles:
            raise KeyError(obstacle.obstacle_id)
        if obstacle.map_id != self.map_id:
            raise ValueError("obstacle belongs to a different map")
        bounds = AABB.from_shape(obstacle.world_shape())
        self._index.update(obstacle.obstacle_id, bounds)
        self._obstacles[obstacle.obstacle_id] = obstacle

    def remove(self, obstacle_id: str) -> None:
        self._index.remove(obstacle_id)
        del self._obstacles[obstacle_id]

    def query(self, query_bounds: AABB) -> tuple[ObstacleDefinition, ...]:
        if not isinstance(query_bounds, AABB):
            raise TypeError("query_bounds must be an AABB")
        return tuple(self._obstacles[item_id] for item_id in self._index.query(query_bounds))

    def clear(self) -> None:
        self._index.clear()
        self._obstacles.clear()
        self.map_id = None

    def __len__(self) -> int:
        return len(self._obstacles)
