"""Eldoria-native physical geometry and body contracts."""
from .body import ActorBodyTransform, PhysicsBodyDefinition
from .hex_map_geometry import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
)
from .contacts import Contact, ContactManifold
from .kinematic_solver import CollisionResolution, resolve_kinematic_motion
from .narrowphase import collide_shapes
from .obstacle import StaticObstacle
from .obstacle_index import StaticObstacleIndex, obstacle_bounds
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape
from .vector2 import Vector2

__all__ = [
    "ActorBodyTransform",
    "BoundaryPolicy",
    "CircleShape",
    "CollisionResolution",
    "Contact",
    "ContactManifold",
    "ColliderShape",
    "ConvexPolygonShape",
    "HexBoundaryEdge",
    "HexMapCollisionGeometry",
    "PhysicsBodyDefinition",
    "StaticObstacle",
    "StaticObstacleIndex",
    "Vector2",
    "collide_shapes",
    "obstacle_bounds",
    "resolve_kinematic_motion",
]
