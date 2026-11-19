"""Map-scoped static collision obstacle definitions."""
from __future__ import annotations

from dataclasses import dataclass

from core.domain.spatial import WorldPoint
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape


@dataclass(frozen=True, slots=True)
class StaticObstacle:
    obstacle_id: str
    map_id: str
    shape: ColliderShape
    position: WorldPoint

    def __post_init__(self) -> None:
        if not isinstance(self.obstacle_id, str) or not self.obstacle_id.strip():
            raise ValueError("obstacle_id must be a non-empty string.")
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(self.shape, (CircleShape, ConvexPolygonShape)):
            raise TypeError("shape must be a supported collider shape.")
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint.")

    def world_shape(self) -> ColliderShape:
        if isinstance(self.shape, CircleShape):
            return CircleShape(
                self.shape.radius,
                WorldPoint(
                    self.position.x + self.shape.center.x,
                    self.position.y + self.shape.center.y,
                ),
            )
        return ConvexPolygonShape(tuple(
            WorldPoint(self.position.x + point.x, self.position.y + point.y)
            for point in self.shape.vertices
        ))
