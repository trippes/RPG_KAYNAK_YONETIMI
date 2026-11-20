"""Application orchestration for native continuous player movement."""

from __future__ import annotations

from dataclasses import dataclass

from core.domain.movement import MovementConfig, MovementIntegrator, MovementIntent, MovementState
from core.domain.physics import PhysicsBodyDefinition, Vector2
from core.domain.spatial import MovementFailureReason, MovementResult, WorldPoint

from .hex_actor_binding import ActorHexBindingService
from .hex_physics_bridge import HexPhysicsSnapshot
from .dynamic_actor_collision import DynamicActorCollisionResolver


@dataclass(frozen=True, slots=True)
class ContinuousPlayerMovementStep:
    """Outcome of one fixed-duration player movement step."""

    movement: MovementResult
    state: MovementState
    collision_resolution: object | None = None
    dynamic_pushes: tuple[str, ...] = ()


class ContinuousPlayerMovementController:
    """Compose native integration, static collision, and canonical hex position.

    Actor identity remains in WorldActorRegistry through ActorHexBindingService.
    Continuous position and occupancy remain owned by HexWorldRuntime.
    The caller supplies elapsed seconds and the authoritative movement config.
    """

    __slots__ = (
        "_binding",
        "_physics_snapshot",
        "_body",
        "_integrator",
        "_last_state",
        "_last_collision_resolution",
        "_npc_bodies",
        "_last_dynamic_pushes",
    )

    def __init__(
        self,
        binding: ActorHexBindingService,
        physics_snapshot: HexPhysicsSnapshot,
        body: PhysicsBodyDefinition,
        config: MovementConfig,
        *,
        npc_bodies=None,
    ) -> None:
        if not isinstance(binding, ActorHexBindingService):
            raise TypeError("binding must be an ActorHexBindingService")
        if not isinstance(physics_snapshot, HexPhysicsSnapshot):
            raise TypeError("physics_snapshot must be a HexPhysicsSnapshot")
        if not isinstance(body, PhysicsBodyDefinition):
            raise TypeError("body must be a PhysicsBodyDefinition")
        if not isinstance(config, MovementConfig):
            raise TypeError("config must be a MovementConfig")
        if binding.world_id != physics_snapshot.world_id:
            raise ValueError("physics snapshot belongs to a different world")
        self._binding = binding
        self._physics_snapshot = physics_snapshot
        self._body = body
        self._integrator = MovementIntegrator(config)
        self._last_state: MovementState | None = None
        self._last_collision_resolution = None
        self._npc_bodies = dict(npc_bodies or {})
        self._last_dynamic_pushes = ()

    @property
    def last_state(self) -> MovementState | None:
        return self._last_state

    @property
    def last_collision_resolution(self):
        return self._last_collision_resolution

    @property
    def last_dynamic_pushes(self) -> tuple[str, ...]:
        return self._last_dynamic_pushes

    def step(
        self,
        actor_id: str,
        intent: MovementIntent,
        delta_seconds: float,
    ) -> ContinuousPlayerMovementStep:
        """Advance one actor, then atomically commit through HexWorldRuntime."""
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent")

        actor = self._binding.actor(actor_id)
        entity = self._binding.spatial_entity(actor_id)
        if entity.kind != "player":
            raise ValueError("continuous player movement requires a player actor")
        if entity.position.map_id != self._physics_snapshot.map_id:
            raise ValueError("physics snapshot belongs to a different map")

        start = entity.continuous_position.point
        current = MovementState(start)
        if not actor.active or not entity.active or not entity.profile.can_move:
            result = MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor cannot move.",
            )
            self._last_state = current
            self._last_collision_resolution = None
            return ContinuousPlayerMovementStep(result, current)

        proposed = self._integrator.step(current, intent, delta_seconds)
        displacement = Vector2(
            proposed.position.x - start.x,
            proposed.position.y - start.y,
        )
        if displacement.length_squared == 0.0:
            result = MovementResult(True, entity.position)
            self._last_state = proposed
            self._last_collision_resolution = None
            return ContinuousPlayerMovementStep(result, proposed)

        resolution = None
        final_position = proposed.position
        final_velocity = proposed.velocity
        if self._body.enabled:
            resolution = self._physics_snapshot.resolve_motion(
                start,
                displacement,
                self._body,
            )
            if resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    "collision resolution left unresolved penetration: "
                    f"{resolution.unresolved_penetration}"
                )
            final_position = WorldPoint(
                start.x + resolution.applied_displacement.x,
                start.y + resolution.applied_displacement.y,
            )
            final_velocity = resolution.applied_displacement * (
                1.0 / float(delta_seconds)
            )

        dynamic_result = DynamicActorCollisionResolver(
            self._binding.runtime, self._physics_snapshot,
        ).resolve_player_motion(
            actor_id, start, final_position, self._body, self._npc_bodies,
        )
        final_position = dynamic_result.player_position
        final_velocity = Vector2(
            (final_position.x - start.x) / float(delta_seconds),
            (final_position.y - start.y) / float(delta_seconds),
        )
        self._last_dynamic_pushes = tuple(
            item.entity_id for item in dynamic_result.pushes
        )
        movement = self._binding.runtime.set_continuous_position(
            actor_id,
            final_position,
        )
        if movement.success:
            state = MovementState(final_position, final_velocity, intent.mode)
        else:
            # Dynamic pushes remain provisional until the player commit succeeds.
            # Roll them back in reverse order to preserve an atomic contact step.
            for push in reversed(dynamic_result.pushes):
                rollback = self._binding.runtime.set_continuous_position(
                    push.entity_id, push.previous_position,
                )
                if not rollback.success:
                    raise RuntimeError(
                        "could not roll back NPC after rejected player movement: "
                        f"{push.entity_id}"
                    )
            state = current

        self._last_state = state
        self._last_collision_resolution = resolution
        return ContinuousPlayerMovementStep(
            movement, state, resolution, self._last_dynamic_pushes,
        )


__all__ = [
    "ContinuousPlayerMovementController",
    "ContinuousPlayerMovementStep",
]
