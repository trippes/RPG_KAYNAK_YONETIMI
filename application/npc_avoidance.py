"""Fixed-step NPC flee routing, separate from physical player pushing."""
from __future__ import annotations

import math

from core.domain.physics import CircleShape, PhysicsBodyDefinition, Vector2
from core.domain.spatial import AABB, EntityPosition, HexDirection, LocalHexPosition, WorldPoint
from .dynamic_actor_collision import DynamicActorCollisionResolver
from npc import BehaviorState, NPCRegistry
from .npc_simulation_metrics import timed_npc_step


class NPCAvoidanceSystem:
    """Route FLEE-state NPCs away from threats without crossing static obstacles.

    A bounded local search selects a farther reachable cell; native hex
    pathfinding routes around blocked cells and the physics snapshot validates
    every edge. Continuous collision resolution owns the final displacement.
    Dynamic NPC separation remains a separate physics responsibility.
    """

    AVOIDANCE_RADIUS = 64.0
    SEARCH_RADIUS_CELLS = 3
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

    def _escape_path(self, npc_id, entity, threat_cell, body):
        map_definition = self._runtime.map_definition(entity.position.map_id)
        current_cell = entity.position.cell
        current_distance = current_cell.to_hex_coord().distance_to(
            threat_cell.to_hex_coord(),
        )
        edge_validator = lambda source, destination: (
            self._snapshot.can_reach_cell(source, destination, body)
        )
        nearby = {current_cell}
        frontier = {current_cell}
        for _ in range(self.SEARCH_RADIUS_CELLS):
            next_frontier = set()
            for cell in frontier:
                for direction in HexDirection:
                    neighbor = LocalHexPosition.from_hex_coord(
                        cell.to_hex_coord().neighbor(direction),
                    )
                    if neighbor not in nearby:
                        nearby.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier

        candidates = []
        metrics = getattr(self._runtime, "metrics", None)
        for cell in nearby:
            if metrics is not None:
                metrics.increment("escape_cells_considered")
            if (
                cell == current_cell
                or not map_definition.has_cell(cell)
                or map_definition.is_blocked(cell)
            ):
                continue
            threat_distance = cell.to_hex_coord().distance_to(
                threat_cell.to_hex_coord(),
            )
            if threat_distance <= current_distance:
                continue
            destination = EntityPosition(entity.position.map_id, cell)
            if not self._runtime.occupancy.can_enter(
                destination, excluding=npc_id,
            ):
                continue
            travel_distance = current_cell.to_hex_coord().distance_to(
                cell.to_hex_coord(),
            )
            candidates.append((
                -threat_distance, travel_distance, cell.q, cell.r, cell,
            ))

        # Prefer the greatest threat separation, then the shortest local route.
        for _threat_score, _travel_score, _q, _r, cell in sorted(candidates):
            path = self._runtime.path_to(
                npc_id, cell, edge_validator=edge_validator,
            )
            if path is not None and len(path) > 1:
                return path
        return None

    @timed_npc_step("npc_avoidance")
    def step(self, delta_seconds: float) -> tuple[str, ...]:
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds) or delta_seconds < 0:
            raise ValueError("delta_seconds must be finite and non-negative.")
        if delta_seconds == 0:
            return ()

        player = self._runtime.entity(self._player_id)
        threat_position = self._runtime.continuous_position(self._player_id).point
        threat_cell = player.position.cell
        moved = []
        metrics = getattr(self._runtime, "metrics", None)
        for npc in self._npcs.all():
            if metrics is not None:
                metrics.increment("avoidance_registry_scanned")
            if not npc.active or npc.behavior_state is not BehaviorState.FLEE:
                continue
            if metrics is not None:
                metrics.increment("avoidance_eligible")
            try:
                entity = self._runtime.entity(npc.npc_id)
                current = self._runtime.continuous_position(npc.npc_id).point
            except KeyError:
                continue
            if entity.position.map_id != player.position.map_id:
                continue
            if self._snapshot.map_id != entity.position.map_id:
                continue
            body = npc.physics_body
            if (
                not isinstance(body, PhysicsBodyDefinition)
                or not body.enabled
                or not isinstance(body.collider, CircleShape)
            ):
                continue
            if metrics is not None:
                metrics.increment("avoidance_threat_distance_checks")
            if math.hypot(
                current.x - threat_position.x,
                current.y - threat_position.y,
            ) >= self.AVOIDANCE_RADIUS:
                if metrics is not None:
                    metrics.increment("avoidance_radius_rejects")
                continue

            path = self._escape_path(
                npc.npc_id, entity, threat_cell, body,
            )
            if path is None:
                continue
            next_cell = path[1]
            target_point = self._snapshot.cell_center(next_cell)
            dx, dy = target_point.x - current.x, target_point.y - current.y
            distance = math.hypot(dx, dy)
            if distance <= 1e-8:
                continue

            # Repel nearby NPCs slightly while retaining the path's escape direction.
            steering_x, steering_y = dx / distance, dy / distance
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
                ox, oy = current.x - other_point.x, current.y - other_point.y
                separation = math.hypot(ox, oy)
                if 1e-8 < separation < self.SEPARATION_RADIUS:
                    weight = (
                        self.SEPARATION_RADIUS - separation
                    ) / self.SEPARATION_RADIUS
                    steering_x += ox / separation * weight
                    steering_y += oy / separation * weight

            magnitude = math.hypot(steering_x, steering_y)
            if magnitude <= 1e-8:
                continue
            speed = float(getattr(npc, "avoidance_speed", self.DEFAULT_SPEED))
            step_distance = min(distance, speed * delta_seconds)
            displacement = Vector2(
                steering_x / magnitude * step_distance,
                steering_y / magnitude * step_distance,
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

        pair_moves = DynamicActorCollisionResolver(
            self._runtime, self._snapshot,
        ).resolve_npc_pairs({
            npc.npc_id: npc.physics_body
            for npc in self._npcs.all()
            if npc.physics_body is not None
        })
        moved.extend(pair_moves)
        return tuple(sorted(set(moved)))


__all__ = ["NPCAvoidanceSystem"]
