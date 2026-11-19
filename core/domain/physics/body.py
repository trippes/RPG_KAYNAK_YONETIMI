"""Physical body metadata and ground-anchor transforms."""
from __future__ import annotations

from dataclasses import dataclass
import math

from core.domain.spatial import WorldPoint
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape
from .vector2 import Vector2


@dataclass(frozen=True, slots=True)
class PhysicsBodyDefinition:
    body_id: str
    collider: ColliderShape
    local_offset: Vector2 = Vector2(0.0, 0.0)
    body_height: float = 1.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.body_id, str) or not self.body_id.strip():
            raise ValueError("body_id must be a non-empty string.")
        if not isinstance(self.collider, (CircleShape, ConvexPolygonShape)):
            raise TypeError("collider must be a supported shape.")
        if not isinstance(self.local_offset, Vector2):
            raise TypeError("local_offset must be a Vector2.")
        if isinstance(self.body_height, bool) or not isinstance(self.body_height, (int, float)):
            raise TypeError("body_height must be a real number.")
        if not math.isfinite(self.body_height) or self.body_height <= 0:
            raise ValueError("body_height must be finite and greater than zero.")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool.")
        object.__setattr__(self, "body_height", float(self.body_height))


@dataclass(frozen=True, slots=True)
class ActorBodyTransform:
    ground_anchor: WorldPoint
    rotation_radians: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.ground_anchor, WorldPoint):
            raise TypeError("ground_anchor must be a WorldPoint.")
        if isinstance(self.rotation_radians, bool) or not isinstance(self.rotation_radians, (int, float)):
            raise TypeError("rotation_radians must be a real number.")
        if not math.isfinite(self.rotation_radians):
            raise ValueError("rotation_radians must be finite.")
        object.__setattr__(self, "rotation_radians", float(self.rotation_radians))

    def transform_shape(self, body: PhysicsBodyDefinition) -> ColliderShape:
        if not isinstance(body, PhysicsBodyDefinition):
            raise TypeError("body must be a PhysicsBodyDefinition.")
        cosine = math.cos(self.rotation_radians)
        sine = math.sin(self.rotation_radians)

        if isinstance(body.collider, CircleShape):
            offset_x = body.local_offset.x + body.collider.center.x
            offset_y = body.local_offset.y + body.collider.center.y
            center = WorldPoint(
                self.ground_anchor.x + offset_x * cosine - offset_y * sine,
                self.ground_anchor.y + offset_x * sine + offset_y * cosine,
            )
            return CircleShape(body.collider.radius, center)

        transformed = []
        for vertex in body.collider.vertices:
            offset_x = body.local_offset.x + vertex.x
            offset_y = body.local_offset.y + vertex.y
            transformed.append(WorldPoint(
                self.ground_anchor.x + offset_x * cosine - offset_y * sine,
                self.ground_anchor.y + offset_x * sine + offset_y * cosine,
            ))
        return ConvexPolygonShape(tuple(transformed))
