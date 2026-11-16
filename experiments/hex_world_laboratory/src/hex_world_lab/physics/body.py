"""Physical body definitions and ground-anchor transforms."""

from dataclasses import dataclass
import math

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2

from .shapes import CircleShape, ColliderShape, ConvexPolygonShape


@dataclass(frozen=True, slots=True)
class BodyDefinition:
    """Immutable physical properties, independent of visual sprites."""

    body_id: str
    collider: ColliderShape
    local_offset: Vector2 = Vector2(0.0, 0.0)
    body_height: float = 1.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.body_id, str) or not self.body_id.strip():
            raise ValueError("body_id must be a non-empty string")
        if not isinstance(self.collider, (CircleShape, ConvexPolygonShape)):
            raise TypeError("collider must be a supported collider shape")
        if not isinstance(self.local_offset, Vector2):
            raise TypeError("local_offset must be a Vector2")
        if isinstance(self.body_height, bool) or not isinstance(self.body_height, (int, float)):
            raise TypeError("body_height must be a real number")
        if not math.isfinite(self.body_height) or self.body_height <= 0:
            raise ValueError("body_height must be finite and greater than zero")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")


@dataclass(frozen=True, slots=True)
class ActorBodyTransform:
    """World transform whose position is the actor's ground anchor."""

    ground_anchor: WorldPoint
    rotation_radians: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.ground_anchor, WorldPoint):
            raise TypeError("ground_anchor must be a WorldPoint")
        if isinstance(self.rotation_radians, bool) or not isinstance(self.rotation_radians, (int, float)):
            raise TypeError("rotation_radians must be a real number")
        if not math.isfinite(self.rotation_radians):
            raise ValueError("rotation_radians must be finite")

    def transform_shape(self, body: BodyDefinition) -> ColliderShape:
        """Return the body's collider in world space."""
        if not isinstance(body, BodyDefinition):
            raise TypeError("body must be a BodyDefinition")

        cosine = math.cos(self.rotation_radians)
        sine = math.sin(self.rotation_radians)
        offset_x = self.ground_anchor.x + body.local_offset.x * cosine - body.local_offset.y * sine
        offset_y = self.ground_anchor.y + body.local_offset.x * sine + body.local_offset.y * cosine

        if isinstance(body.collider, CircleShape):
            return CircleShape(body.collider.radius, Vector2(offset_x, offset_y))

        transformed = tuple(
            Vector2(
                offset_x + point.x * cosine - point.y * sine,
                offset_y + point.x * sine + point.y * cosine,
            )
            for point in body.collider.vertices
        )
        return ConvexPolygonShape(transformed)
