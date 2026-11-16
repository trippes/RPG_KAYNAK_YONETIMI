"""Pygame-independent physics and collision primitives."""

from .body import ActorBodyTransform, BodyDefinition
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape

__all__ = [
    "ActorBodyTransform",
    "BodyDefinition",
    "CircleShape",
    "ColliderShape",
    "ConvexPolygonShape",
]
