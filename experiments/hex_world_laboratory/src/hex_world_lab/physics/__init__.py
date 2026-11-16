"""Pygame-independent physics and collision primitives."""

from .body import ActorBodyTransform, BodyDefinition
from .broadphase import AABB, gather_candidates
from .contacts import Contact, ContactManifold
from .hex_geometry import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
    build_hex_map_collision_geometry,
)
from .narrowphase import collide_shapes
from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape

__all__ = [
    "AABB",
    "ActorBodyTransform",
    "BodyDefinition",
    "BoundaryPolicy",
    "CircleShape",
    "ColliderShape",
    "Contact",
    "ContactManifold",
    "ConvexPolygonShape",
    "HexBoundaryEdge",
    "HexMapCollisionGeometry",
    "ObstacleDefinition",
    "build_hex_map_collision_geometry",
    "collide_shapes",
    "gather_candidates",
]
