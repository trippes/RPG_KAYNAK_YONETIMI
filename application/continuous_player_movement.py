"""Application orchestration for native continuous player movement."""

from __future__ import annotations

from dataclasses import dataclass

from core.domain.movement import MovementConfig, MovementIntegrator, MovementIntent, MovementState
from core.domain.physics import PhysicsBodyDefinition, Vector2
from core.domain.spatial import MovementFailureReason, MovementResult, WorldPoint

from .hex_actor_binding import ActorHexBindingService
from .hex_physics_bridge import HexPhysicsSnapshot


@dataclass(frozen=True, slots=True)
class ContinuousPlayerMovementStep:
    """Outcome of one fixed-duration player movement step."""

    movement: MovementResult
    state: MovementState
    collision_resolution: object | None = None


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
    )

    def __init__(
        self,
        binding: ActorHexBindingService,
        physics_snapshot: HexPhysicsSnapshot,
        body: PhysicsBodyDefinition,
        config: MovementConfig,
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

    @property
    def last_state(self) -> MovementState | None:
        return self._last_state

    @property
    def last_collision_resolution(self):
        return self._last_collision_resolution

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
        if not actor.active or not entity.active:
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

        movement = self._binding.runtime.set_continuous_position(
            actor_id,
            final_position,
        )
        if movement.success:
            state = MovementState(final_position, final_velocity, intent.mode)
        else:
            state = current

        self._last_state = state
        self._last_collision_resolution = resolution
        return ContinuousPlayerMovementStep(movement, state, resolution)


__all__ = [
    "ContinuousPlayerMovementController",
    "ContinuousPlayerMovementStep",
]
