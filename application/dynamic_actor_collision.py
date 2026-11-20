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

    def resolve_npc_pairs(
        self,
        npc_bodies: Mapping[str, PhysicsBodyDefinition],
    ) -> tuple[str, ...]:
        """Resolve overlapping NPC circles with deterministic inverse-mass splitting."""
        if not isinstance(npc_bodies, Mapping):
            raise TypeError("npc_bodies must be a mapping.")
        valid = {}
        max_radius = 0.0
        for npc_id, body in npc_bodies.items():
            if not isinstance(body, PhysicsBodyDefinition) or not body.enabled:
                continue
            if not isinstance(body.collider, CircleShape):
                continue
            try:
                entity = self._runtime.entity(npc_id)
                if (
                    entity.kind != "npc" or not entity.active
                    or entity.position.map_id != self._snapshot.map_id
                ):
                    continue
                position = self._runtime.continuous_position(npc_id).point
            except KeyError:
                continue
            valid[npc_id] = (entity, body, position)
            max_radius = max(max_radius, body.collider.radius)
        moved = set()
        processed_pairs = set()

        for npc_id in sorted(valid):
            entity_a, body_a, position_a = valid[npc_id]
            margin = body_a.collider.radius + max_radius + self.COLLISION_SKIN
            bounds = AABB(
                position_a.x - margin, position_a.y - margin,
                position_a.x + margin, position_a.y + margin,
            )
            map_id = entity_a.position.map_id
            for other_id in sorted(self._runtime.query_spatial_candidates(map_id, bounds)):
                if other_id <= npc_id or other_id not in valid:
                    continue
                pair = (npc_id, other_id)
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                entity_b, body_b, position_b = valid[other_id]
                if entity_b.position.map_id != map_id:
                    continue

                shape_a = ActorBodyTransform(position_a).transform_shape(body_a)
                shape_b = ActorBodyTransform(position_b).transform_shape(body_b)
                contact = collide_shapes(shape_a, shape_b, other_id)
                if contact is None or contact.penetration_depth <= 0.0:
                    continue

                inverse_a = 1.0 if entity_a.profile.can_move else 0.0
                inverse_b = 1.0 if entity_b.profile.can_move else 0.0
                inverse_total = inverse_a + inverse_b
                if inverse_total <= 0.0:
                    continue
                correction = contact.penetration_depth + self.COLLISION_SKIN
                delta_a = Vector2(
                    contact.normal.x * correction * inverse_a / inverse_total,
                    contact.normal.y * correction * inverse_a / inverse_total,
                )
                delta_b = Vector2(
                    -contact.normal.x * correction * inverse_b / inverse_total,
                    -contact.normal.y * correction * inverse_b / inverse_total,
                )
                resolved_a = self._snapshot.resolve_motion(position_a, delta_a, body_a)
                resolved_b = self._snapshot.resolve_motion(position_b, delta_b, body_b)
                target_a = WorldPoint(
                    position_a.x + resolved_a.applied_displacement.x,
                    position_a.y + resolved_a.applied_displacement.y,
                )
                target_b = WorldPoint(
                    position_b.x + resolved_b.applied_displacement.x,
                    position_b.y + resolved_b.applied_displacement.y,
                )

                moved_a = target_a != position_a
                moved_b = target_b != position_b
                committed_a = False
                committed_b = False
                if moved_a:
                    committed_a = self._runtime.set_continuous_position(
                        npc_id, target_a,
                    ).success
                if moved_b:
                    committed_b = self._runtime.set_continuous_position(
                        other_id, target_b,
                    ).success

                if moved_a and not committed_a and moved_b and not committed_b:
                    continue
                if committed_a:
                    moved.add(npc_id)
                    valid[npc_id] = (entity_a, body_a, target_a)
                if committed_b:
                    moved.add(other_id)
                    valid[other_id] = (entity_b, body_b, target_b)

                # A failed half of a split correction transfers its share to
                # the actor that can still move, preserving non-penetration.
                if moved_a and not committed_a and committed_b and inverse_b > 0:
                    extra = Vector2(
                        -contact.normal.x * correction * inverse_b / inverse_total,
                        -contact.normal.y * correction * inverse_b / inverse_total,
                    )
                    fallback = self._snapshot.resolve_motion(target_b, extra, body_b)
                    fallback_target = WorldPoint(
                        target_b.x + fallback.applied_displacement.x,
                        target_b.y + fallback.applied_displacement.y,
                    )
                    if fallback_target != target_b and self._runtime.set_continuous_position(
                        other_id, fallback_target,
                    ).success:
                        moved.add(other_id)
                        valid[other_id] = (entity_b, body_b, fallback_target)
                elif moved_b and not committed_b and committed_a and inverse_a > 0:
                    extra = Vector2(
                        contact.normal.x * correction * inverse_a / inverse_total,
                        contact.normal.y * correction * inverse_a / inverse_total,
                    )
                    fallback = self._snapshot.resolve_motion(target_a, extra, body_a)
                    fallback_target = WorldPoint(
                        target_a.x + fallback.applied_displacement.x,
                        target_a.y + fallback.applied_displacement.y,
                    )
                    if fallback_target != target_a and self._runtime.set_continuous_position(
                        npc_id, fallback_target,
                    ).success:
                        moved.add(npc_id)
                        valid[npc_id] = (entity_a, body_a, fallback_target)

        return tuple(sorted(moved))

    def resolve_npc_player_contacts(
        self,
        player_id: str,
        player_body: PhysicsBodyDefinition,
        npc_bodies: Mapping[str, PhysicsBodyDefinition],
    ) -> tuple[str, ...]:
        """Keep NPCs from stepping through a stationary player after AI movement."""
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError("player_id must be a non-empty string.")
        if not isinstance(player_body, PhysicsBodyDefinition):
            raise TypeError("player_body must be a PhysicsBodyDefinition.")
        if not isinstance(npc_bodies, Mapping):
            raise TypeError("npc_bodies must be a mapping.")
        if not player_body.enabled or not isinstance(player_body.collider, CircleShape):
            return ()
        player = self._runtime.entity(player_id)
        if (
            player.kind != "player" or not player.active
            or player.position.map_id != self._snapshot.map_id
        ):
            return ()
        player_position = self._runtime.continuous_position(player_id).point
        player_shape = ActorBodyTransform(player_position).transform_shape(player_body)
        moved = []
        for npc_id in sorted(npc_bodies):
            body = npc_bodies[npc_id]
            if (
                not isinstance(body, PhysicsBodyDefinition)
                or not body.enabled
                or not isinstance(body.collider, CircleShape)
            ):
                continue
            try:
                entity = self._runtime.entity(npc_id)
                if entity.kind != "npc" or not entity.active or not entity.profile.can_move:
                    continue
                if entity.position.map_id != player.position.map_id:
                    continue
                previous = self._runtime.continuous_position(npc_id).point
            except KeyError:
                continue
            npc_shape = ActorBodyTransform(previous).transform_shape(body)
            contact = collide_shapes(player_shape, npc_shape, npc_id)
            if contact is None or contact.penetration_depth <= 0.0:
                continue
            correction = contact.penetration_depth + self.COLLISION_SKIN
            displacement = Vector2(
                -contact.normal.x * correction,
                -contact.normal.y * correction,
            )
            resolution = self._snapshot.resolve_motion(previous, displacement, body)
            target = WorldPoint(
                previous.x + resolution.applied_displacement.x,
                previous.y + resolution.applied_displacement.y,
            )
            if target != previous and self._runtime.set_continuous_position(
                npc_id, target,
            ).success:
                moved.append(npc_id)
        return tuple(moved)

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
        if map_id != self._snapshot.map_id:
            raise ValueError("player actor and physics snapshot belong to different maps")
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
