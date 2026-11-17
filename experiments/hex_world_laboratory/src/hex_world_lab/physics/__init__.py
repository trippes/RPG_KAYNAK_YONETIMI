"""Pygame-independent physics and collision primitives."""

from .body import ActorBodyTransform, BodyDefinition
from .broadphase import AABB, ObstacleCandidateProvider, gather_candidates
from .contacts import Contact, ContactManifold
from .continuous import (
    ContinuousCollisionResolution,
    SweepHit,
    resolve_continuous_motion,
    sweep_circle_polygon,
)
from .hex_geometry import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
    build_hex_map_collision_geometry,
)
from .narrowphase import collide_shapes
from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape
from .solver import CollisionResolution, resolve_kinematic_motion

__all__ = [
    "AABB",
    "ActorBodyTransform",
    "BodyDefinition",
    "BoundaryPolicy",
    "CircleShape",
    "CollisionResolution",
    "ColliderShape",
    "Contact",
    "ContinuousCollisionResolution",
    "ContactManifold",
    "ConvexPolygonShape",
    "HexBoundaryEdge",
    "HexMapCollisionGeometry",
    "ObstacleDefinition",
    "ObstacleCandidateProvider",
    "SweepHit",
    "build_hex_map_collision_geometry",
    "collide_shapes",
    "gather_candidates",
    "resolve_kinematic_motion",
    "resolve_continuous_motion",
    "sweep_circle_polygon",
]
