"""Eldoria-native physical geometry and body contracts."""
from .body import ActorBodyTransform, PhysicsBodyDefinition
from .hex_map_geometry import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
)
from .obstacle import StaticObstacle
from .obstacle_index import StaticObstacleIndex, obstacle_bounds
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape
from .vector2 import Vector2

__all__ = [
    "ActorBodyTransform",
    "BoundaryPolicy",
    "CircleShape",
    "ColliderShape",
    "ConvexPolygonShape",
    "HexBoundaryEdge",
    "HexMapCollisionGeometry",
    "PhysicsBodyDefinition",
    "StaticObstacle",
    "StaticObstacleIndex",
    "Vector2",
    "obstacle_bounds",
]
