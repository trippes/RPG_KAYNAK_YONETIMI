"""Fixed-step NPC avoidance steering, separate from physical player pushing."""
from __future__ import annotations

import math

from core.domain.physics import CircleShape, PhysicsBodyDefinition, Vector2
from core.domain.spatial import AABB, WorldPoint
from npc import BehaviorState, NPCRegistry


class NPCAvoidanceSystem:
    """Move only NPCs explicitly in FLEE state away from nearby threats.

    Player/NPC collision pushing is handled by DynamicActorCollisionResolver.
    This system is proactive steering: it produces a small desired displacement,
    then delegates static obstacle resolution and position ownership to the
    existing native physics snapshot and HexWorldRuntime.
    """

    AVOIDANCE_RADIUS = 64.0
    SEPARATION_RADIUS = 18.0
    DEFAULT_SPEED = 38.0

    def __init__(self, npcs: NPCRegistry, runtime, physics_snapshot, player_id: str):
        if not isinstance(npcs, NPCRegistry):
            raise TypeError("npcs must be an NPCRegistry.")
        if runtime is None or physics_snapshot is None:
            raise TypeError("runtime and physics_snapshot are required.")
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError("player_id must be a non-empty string.")
        self._npcs = npcs
        self._runtime = runtime
        self._snapshot = physics_snapshot
        self._player_id = player_id

    def step(self, delta_seconds: float) -> tuple[str, ...]:
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds) or delta_seconds < 0:
            raise ValueError("delta_seconds must be finite and non-negative.")
        if delta_seconds == 0:
            return ()

        player = self._runtime.entity(self._player_id)
        threat = self._runtime.continuous_position(self._player_id).point
        moved = []
        for npc in self._npcs.all():
            if not npc.active or npc.behavior_state is not BehaviorState.FLEE:
                continue
            try:
                entity = self._runtime.entity(npc.npc_id)
                current = self._runtime.continuous_position(npc.npc_id).point
            except KeyError:
                continue
            if entity.position.map_id != player.position.map_id:
                continue
            body = npc.physics_body
            if (
                not isinstance(body, PhysicsBodyDefinition)
                or not body.enabled
                or not isinstance(body.collider, CircleShape)
            ):
                continue

            away_x = current.x - threat.x
            away_y = current.y - threat.y
            distance = math.hypot(away_x, away_y)
            if distance >= self.AVOIDANCE_RADIUS:
                continue
            if distance <= 1e-8:
                seed = sum(ord(char) for char in npc.npc_id)
                away_x = 1.0 if seed % 2 == 0 else -1.0
                away_y = 1.0 if seed % 3 == 0 else -1.0
                distance = math.hypot(away_x, away_y)

            steering_x = away_x / distance
            steering_y = away_y / distance
            bounds = AABB(
                current.x - self.SEPARATION_RADIUS,
                current.y - self.SEPARATION_RADIUS,
                current.x + self.SEPARATION_RADIUS,
                current.y + self.SEPARATION_RADIUS,
            )
            for other_id in self._runtime.query_spatial_candidates(
                entity.position.map_id, bounds,
            ):
                if other_id == npc.npc_id:
                    continue
                try:
                    other = self._runtime.entity(other_id)
                    if other.kind != "npc" or not other.active:
                        continue
                    other_point = self._runtime.continuous_position(other_id).point
                except KeyError:
                    continue
                dx = current.x - other_point.x
                dy = current.y - other_point.y
                separation = math.hypot(dx, dy)
                if 1e-8 < separation < self.SEPARATION_RADIUS:
                    weight = (self.SEPARATION_RADIUS - separation) / self.SEPARATION_RADIUS
                    steering_x += (dx / separation) * weight
                    steering_y += (dy / separation) * weight

            magnitude = math.hypot(steering_x, steering_y)
            if magnitude <= 1e-8:
                continue
            speed = float(getattr(npc, "avoidance_speed", self.DEFAULT_SPEED))
            displacement = Vector2(
                steering_x / magnitude * speed * delta_seconds,
                steering_y / magnitude * speed * delta_seconds,
            )
            resolution = self._snapshot.resolve_motion(
                current, displacement, body,
            )
            if resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    f"NPC '{npc.npc_id}' avoidance left unresolved static penetration."
                )
            target = WorldPoint(
                current.x + resolution.applied_displacement.x,
                current.y + resolution.applied_displacement.y,
            )
            if target == current:
                continue
            result = self._runtime.set_continuous_position(npc.npc_id, target)
            if result.success:
                moved.append(npc.npc_id)
        return tuple(moved)


__all__ = ["NPCAvoidanceSystem"]
