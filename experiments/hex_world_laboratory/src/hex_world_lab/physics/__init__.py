"""Pygame-independent physics and collision primitives."""

from .body import ActorBodyTransform, BodyDefinition
from .hex_geometry import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
    build_hex_map_collision_geometry,
)
from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape

__all__ = [
    "ActorBodyTransform",
    "BodyDefinition",
    "BoundaryPolicy",
    "CircleShape",
    "ColliderShape",
    "ConvexPolygonShape",
    "HexBoundaryEdge",
    "HexMapCollisionGeometry",
    "ObstacleDefinition",
    "build_hex_map_collision_geometry",
]
