"""Map-scoped static obstacle definitions."""

from dataclasses import dataclass

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.world.identity import CellAddress, MapId

from .shapes import CircleShape, ColliderShape, ConvexPolygonShape


@dataclass(frozen=True, slots=True)
class ObstacleDefinition:
    """Immutable obstacle whose shape is expressed relative to its position."""

    obstacle_id: str
    map_id: MapId
    shape: ColliderShape
    position: WorldPoint
    source_cell: CellAddress | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.obstacle_id, str) or not self.obstacle_id.strip():
            raise ValueError("obstacle_id must be a non-empty string")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.shape, (CircleShape, ConvexPolygonShape)):
            raise TypeError("shape must be a supported collider shape")
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint")
        if self.source_cell is not None:
            if not isinstance(self.source_cell, CellAddress):
                raise TypeError("source_cell must be a CellAddress or None")
            if self.source_cell.map_id != self.map_id:
                raise ValueError("source_cell must belong to the obstacle map")

    def world_shape(self) -> ColliderShape:
        """Return the collider translated into world coordinates."""
        if isinstance(self.shape, CircleShape):
            return CircleShape(
                self.shape.radius,
                Vector2(
                    self.position.x + self.shape.center.x,
                    self.position.y + self.shape.center.y,
                ),
            )
        return ConvexPolygonShape(
            tuple(
                Vector2(self.position.x + point.x, self.position.y + point.y)
                for point in self.shape.vertices
            )
        )
