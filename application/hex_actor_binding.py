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

from .actor_system import ActorView, WorldActorRegistry
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
