"""Bind existing NPC domain records to the canonical hex actor runtime."""

from __future__ import annotations

from core.domain.spatial import (
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    MovementResult,
)
from npc import NPCRegistry
from hex_world_lab.physics import BodyDefinition

from .hex_actor_binding import ActorHexBindingService
from .hex_physics_bridge import HexPhysicsSnapshot
from .hex_world_runtime import HexMovableEntity


class NPCSpatialBindingError(ValueError):
    """NPC domain record and world actor cannot share a spatial binding."""


class NPCSpatialBindingService:
    """Expose NPC spatial operations without duplicating identity or position.

    NPCRegistry owns NPC-specific social/behaviour data. WorldActorRegistry,
    reached through ActorHexBindingService, owns generic world actor identity.
    Both use the same stable NPC ID. HexWorldRuntime remains the only owner of
    map-local position and occupancy.
    """

    __slots__ = ("_npcs", "_actor_binding")

    def __init__(
        self,
        npcs: NPCRegistry,
        actor_binding: ActorHexBindingService,
    ) -> None:
        if not isinstance(npcs, NPCRegistry):
            raise TypeError("npcs must be an NPCRegistry")
        if not isinstance(actor_binding, ActorHexBindingService):
            raise TypeError("actor_binding must be an ActorHexBindingService")
        self._npcs = npcs
        self._actor_binding = actor_binding

    @property
    def world_id(self):
        return self._actor_binding.world_id

    def npc(self, npc_id: str):
        return self._require_npc(npc_id)

    def spatial_entity(self, npc_id: str) -> HexMovableEntity:
        self._require_npc(npc_id)
        return self._actor_binding.spatial_entity(npc_id)

    def register_spatial(
        self,
        npc_id: str,
        position: EntityPosition,
        profile: MovementProfile | None = None,
        *,
        movement_enabled: bool = True,
        blocks_movement: bool = True,
        blocks_occupancy: bool = True,
    ) -> HexMovableEntity:
        npc = self._require_npc(npc_id)
        if not npc.active:
            raise NPCSpatialBindingError(
                f"Inactive NPC cannot be registered for movement: {npc_id}"
            )
        # The generic actor must already exist. This avoids creating a second
        # identity implicitly or leaving half-registered state on failure.
        self._actor_binding.actor(npc_id)
        return self._actor_binding.register_spatial(
            npc_id,
            "npc",
            position,
            profile,
            movement_enabled=movement_enabled,
            blocks_movement=blocks_movement,
            blocks_occupancy=blocks_occupancy,
        )

    def move(self, npc_id: str, direction: HexDirection) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        return self._actor_binding.move(npc_id, direction)

    def move_to(
        self,
        npc_id: str,
        target: LocalHexPosition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        return self._actor_binding.move_to(npc_id, target)

    def move_to_with_physics(
        self,
        npc_id: str,
        target: LocalHexPosition,
        physics_snapshot: HexPhysicsSnapshot,
        body: BodyDefinition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        return self._actor_binding.move_to_with_physics(
            npc_id,
            target,
            physics_snapshot,
            body,
        )

    def move_with_physics(
        self,
        npc_id: str,
        direction: HexDirection,
        physics_snapshot: HexPhysicsSnapshot,
        body: BodyDefinition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        return self._actor_binding.move_with_physics(
            npc_id,
            direction,
            physics_snapshot,
            body,
        )

    def set_movement_enabled(
        self,
        npc_id: str,
        enabled: bool,
    ) -> HexMovableEntity:
        self._require_npc(npc_id)
        return self._actor_binding.set_movement_enabled(npc_id, enabled)

    def unregister_spatial(self, npc_id: str) -> HexMovableEntity:
        self._require_npc(npc_id)
        return self._actor_binding.unregister_spatial(npc_id)

    def _require_npc(self, npc_id: str):
        if not isinstance(npc_id, str) or not npc_id.strip():
            raise ValueError("npc_id must be a non-empty string")
        npc = self._npcs.get(npc_id)
        if npc is None:
            raise KeyError(f"NPC not found: {npc_id}")
        return npc

    def _inactive_result(self, npc_id: str) -> MovementResult:
        entity = self._actor_binding.spatial_entity(npc_id)
        return MovementResult(
            False,
            entity.position,
            MovementFailureReason.MOVEMENT_NOT_ALLOWED,
            "NPC is inactive.",
        )


__all__ = ["NPCSpatialBindingError", "NPCSpatialBindingService"]
