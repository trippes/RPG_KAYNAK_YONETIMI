"""Deterministic player-to-NPC pushing on the canonical continuous world plane."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from core.domain.physics import (
    ActorBodyTransform, CircleShape, PhysicsBodyDefinition, Vector2, collide_shapes,
)
from core.domain.spatial import AABB, WorldPoint


@dataclass(frozen=True, slots=True)
class DynamicActorPush:
    entity_id: str
    previous_position: WorldPoint
    new_position: WorldPoint
    penetration_depth: float


@dataclass(frozen=True, slots=True)
class DynamicActorCollisionResolution:
    player_position: WorldPoint
    pushes: tuple[DynamicActorPush, ...]


class DynamicActorCollisionResolver:
    """Push movable NPC circles away from a moving player, respecting map solids.

    The fixed-step player controller invokes this after static map collision.
    NPC identity and occupancy remain owned by HexWorldRuntime. Only enabled
    circle bodies participate in this first dynamic-body contract.
    """

    COLLISION_SKIN = 0.05

    def __init__(self, runtime, physics_snapshot):
        if runtime is None or physics_snapshot is None:
            raise TypeError("runtime and physics_snapshot are required.")
        self._runtime = runtime
        self._snapshot = physics_snapshot

    def resolve_player_motion(
        self,
        actor_id: str,
        start: WorldPoint,
        proposed: WorldPoint,
        player_body: PhysicsBodyDefinition,
        npc_bodies: Mapping[str, PhysicsBodyDefinition],
    ) -> DynamicActorCollisionResolution:
        if not isinstance(start, WorldPoint) or not isinstance(proposed, WorldPoint):
            raise TypeError("start and proposed must be WorldPoint values.")
        if not isinstance(player_body, PhysicsBodyDefinition):
            raise TypeError("player_body must be a PhysicsBodyDefinition.")
        if not isinstance(npc_bodies, Mapping):
            raise TypeError("npc_bodies must be a mapping.")
        if not player_body.enabled or not isinstance(player_body.collider, CircleShape):
            return DynamicActorCollisionResolution(proposed, ())
        if proposed == start:
            return DynamicActorCollisionResolution(proposed, ())

        player_radius = player_body.collider.radius
        npc_radii = [
            body.collider.radius
            for body in npc_bodies.values()
            if isinstance(body, PhysicsBodyDefinition)
            and body.enabled and isinstance(body.collider, CircleShape)
        ]
        if not npc_radii:
            return DynamicActorCollisionResolution(proposed, ())
        broadphase_margin = player_radius + max(npc_radii) + self.COLLISION_SKIN
        bounds = AABB(
            min(start.x, proposed.x) - broadphase_margin,
            min(start.y, proposed.y) - broadphase_margin,
            max(start.x, proposed.x) + broadphase_margin,
            max(start.y, proposed.y) + broadphase_margin,
        )
        map_id = self._runtime.entity(actor_id).position.map_id
        candidate_ids = self._runtime.query_spatial_candidates(map_id, bounds)
        player_position = proposed
        pushes = []

        for npc_id in sorted(candidate_ids):
            if npc_id == actor_id:
                continue
            entity = self._runtime.entity(npc_id)
            if entity.kind != "npc" or not entity.active or not entity.profile.can_move:
                continue
            body = npc_bodies.get(npc_id)
            if (
                not isinstance(body, PhysicsBodyDefinition)
                or not body.enabled
                or not isinstance(body.collider, CircleShape)
            ):
                continue

            try:
                previous = self._runtime.continuous_position(npc_id).point
            except KeyError:
                continue
            player_shape = ActorBodyTransform(player_position).transform_shape(player_body)
            npc_shape = ActorBodyTransform(previous).transform_shape(body)
            contact = collide_shapes(player_shape, npc_shape, npc_id)
            if contact is None or contact.penetration_depth <= 0.0:
                continue

            push_amount = contact.penetration_depth + self.COLLISION_SKIN
            push_vector = Vector2(
                -contact.normal.x * push_amount,
                -contact.normal.y * push_amount,
            )
            npc_resolution = self._snapshot.resolve_motion(
                previous, push_vector, body,
            )
            if npc_resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    f"NPC '{npc_id}' push left unresolved static penetration."
                )
            next_position = WorldPoint(
                previous.x + npc_resolution.applied_displacement.x,
                previous.y + npc_resolution.applied_displacement.y,
            )
            moved = next_position != previous
            if moved:
                movement = self._runtime.set_continuous_position(
                    npc_id, next_position,
                )
                moved = movement.success
                if not moved:
                    next_position = previous
            if moved:
                pushes.append(DynamicActorPush(
                    npc_id, previous, next_position,
                    contact.penetration_depth,
                ))

            # If the NPC could not clear the overlap (e.g. occupied cell or
            # a wall), move the player back along the contact normal.
            current_npc_shape = ActorBodyTransform(next_position).transform_shape(body)
            current_player_shape = ActorBodyTransform(player_position).transform_shape(player_body)
            remaining = collide_shapes(current_player_shape, current_npc_shape, npc_id)
            if remaining is not None and remaining.penetration_depth > 0.0:
                correction = remaining.penetration_depth + self.COLLISION_SKIN
                desired = Vector2(
                    player_position.x - start.x + remaining.normal.x * correction,
                    player_position.y - start.y + remaining.normal.y * correction,
                )
                player_resolution = self._snapshot.resolve_motion(
                    start, desired, player_body,
                )
                player_position = WorldPoint(
                    start.x + player_resolution.applied_displacement.x,
                    start.y + player_resolution.applied_displacement.y,
                )

        return DynamicActorCollisionResolution(player_position, tuple(pushes))


__all__ = [
    "DynamicActorCollisionResolution",
    "DynamicActorCollisionResolver",
    "DynamicActorPush",
]
