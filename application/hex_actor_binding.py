"""Bind canonical Eldoria actors to the session's hex spatial runtime."""

from __future__ import annotations

from core.domain.spatial import (
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    MovementResult,
)
from core.foundation import WorldId
from hex_world_lab.entities.identity import EntityId as LabEntityId
from hex_world_lab.physics import BodyDefinition

from .actor_system import ActorView, WorldActorRegistry
from .hex_physics_bridge import HexPhysicsSnapshot
from .hex_world_runtime import HexMovableEntity, HexWorldRuntime


class ActorHexBindingError(ValueError):
    """Actor and hex runtime belong to different world scopes."""


def actor_id_to_lab_entity_id(actor_id: str) -> LabEntityId:
    """Wrap an existing actor ID; never generate a second entity identity."""
    return LabEntityId(actor_id)


def lab_entity_id_to_actor_id(entity_id: LabEntityId) -> str:
    """Unwrap the same stable ID at the Eldoria application boundary."""
    if not isinstance(entity_id, LabEntityId):
        raise TypeError("entity_id must be a lab EntityId")
    return entity_id.value


class ActorHexBindingService:
    """Coordinate actor eligibility with one world's authoritative hex runtime.

    WorldActorRegistry remains the owner of actor identity and gameplay state.
    HexWorldRuntime remains the owner of map-local position and occupancy.
    Its movement-enabled flag is intentionally distinct from actor.active:
    an active actor can be immobilized without changing gameplay identity.
    """

    __slots__ = ("_actors", "_runtime", "_world_id")

    def __init__(
        self,
        actors: WorldActorRegistry,
        runtime: HexWorldRuntime,
        world_id: WorldId,
    ) -> None:
        if not isinstance(actors, WorldActorRegistry):
            raise TypeError("actors must be a WorldActorRegistry")
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime")
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId")
        if runtime.world_id is None:
            raise ValueError("runtime must be bound to a WorldId before actor integration")
        if runtime.world_id != world_id:
            raise ActorHexBindingError(
                f"Runtime belongs to world '{runtime.world_id.value}', "
                f"not '{world_id.value}'."
            )
        self._actors = actors
        self._runtime = runtime
        self._world_id = world_id

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def runtime(self) -> HexWorldRuntime:
        return self._runtime

    def actor(self, actor_id: str) -> ActorView:
        return self._require_actor(actor_id)

    def spatial_entity(self, actor_id: str) -> HexMovableEntity:
        self._require_actor(actor_id)
        return self._runtime.entity(actor_id)

    def register_spatial(
        self,
        actor_id: str,
        kind: str,
        position: EntityPosition,
        profile: MovementProfile | None = None,
        *,
        movement_enabled: bool = True,
        blocks_movement: bool = True,
        blocks_occupancy: bool = True,
    ) -> HexMovableEntity:
        """Register the existing actor ID in the spatial runtime exactly once."""
        self._require_actor(actor_id)
        actor_id_to_lab_entity_id(actor_id)  # Validate the lab boundary representation.
        if not isinstance(position, EntityPosition):
            raise TypeError("position must be an EntityPosition")
        if not isinstance(movement_enabled, bool):
            raise TypeError("movement_enabled must be a bool")
        return self._runtime.register_entity(
            actor_id,
            kind,
            position,
            profile,
            active=movement_enabled,
            blocks_movement=blocks_movement,
            blocks_occupancy=blocks_occupancy,
        )

    def move(self, actor_id: str, direction: HexDirection) -> MovementResult:
        actor = self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        if not actor.active:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor is inactive.",
            )
        return self._runtime.move(actor_id, direction)

    def move_toward(
        self, actor_id: str, goal: LocalHexPosition,
    ) -> MovementResult:
        """Move one pathfinding step toward a map-local goal."""
        actor = self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        if not actor.active:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor is inactive.",
            )
        return self._runtime.move_toward(actor_id, goal)

    def transition(self, actor_id: str, transition_id: str) -> MovementResult:
        """Move an existing actor across a validated local-map transition."""
        actor = self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        if not actor.active:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor is inactive.",
            )
        return self._runtime.transition(actor_id, transition_id)

    def move_to(
        self,
        actor_id: str,
        target: LocalHexPosition,
    ) -> MovementResult:
        actor = self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        if not actor.active:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor is inactive.",
            )
        return self._runtime.move_to(actor_id, target)

    def move_to_with_physics(
        self,
        actor_id: str,
        target: LocalHexPosition,
        physics_snapshot: HexPhysicsSnapshot,
        body: BodyDefinition,
    ) -> MovementResult:
        """Validate a cell transition with static physics before committing occupancy."""
        actor = self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        if not actor.active:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Actor is inactive.",
            )
        if not isinstance(physics_snapshot, HexPhysicsSnapshot):
            raise TypeError("physics_snapshot must be a HexPhysicsSnapshot")
        if not isinstance(body, BodyDefinition):
            raise TypeError("body must be a BodyDefinition")
        if physics_snapshot.world_id != self._world_id:
            raise ValueError("physics snapshot belongs to a different world")
        if physics_snapshot.map_id != entity.position.map_id:
            raise ValueError("physics snapshot belongs to a different map")

        preflight = self._runtime.validate_move_to(actor_id, target)
        if not preflight.success:
            return preflight
        if not physics_snapshot.can_reach_cell(entity.position.cell, target, body):
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.PHYSICAL_COLLISION,
                "A static physical obstacle blocks the cell transition.",
            )
        return self._runtime.move_to(actor_id, target)

    def move_with_physics(
        self,
        actor_id: str,
        direction: HexDirection,
        physics_snapshot,
        body,
    ) -> MovementResult:
        """Move one adjacent cell after static physics preflight."""
        if not isinstance(direction, HexDirection):
            raise TypeError("direction must be a HexDirection")
        self._require_actor(actor_id)
        entity = self._runtime.entity(actor_id)
        target = LocalHexPosition.from_hex_coord(
            entity.position.cell.to_hex_coord().neighbor(direction)
        )
        return self.move_to_with_physics(actor_id, target, physics_snapshot, body)

    def set_movement_enabled(
        self,
        actor_id: str,
        enabled: bool,
    ) -> HexMovableEntity:
        self._require_actor(actor_id)
        return self._runtime.set_active(actor_id, enabled)

    def unregister_spatial(self, actor_id: str) -> HexMovableEntity:
        """Remove only the spatial binding; keep the actor and its gameplay links."""
        self._require_actor(actor_id)
        return self._runtime.remove_entity(actor_id)

    def _require_actor(self, actor_id: str) -> ActorView:
        actor_id_to_lab_entity_id(actor_id)
        actor = self._actors.get(actor_id)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        if actor.world_id != self._world_id.value:
            raise ActorHexBindingError(
                f"Actor '{actor_id}' belongs to world '{actor.world_id}', "
                f"not '{self._world_id.value}'."
            )
        return actor


__all__ = [
    "ActorHexBindingError",
    "ActorHexBindingService",
    "actor_id_to_lab_entity_id",
    "lab_entity_id_to_actor_id",
]
