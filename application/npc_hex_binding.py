"""Bind existing NPC domain records to the canonical hex actor runtime."""

from __future__ import annotations

from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.domain.spatial import (
    AABB,
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    MovementResult,
    WorldPoint,
)
from core.foundation import WorldId
from npc import NPC, NPCRegistry

from .hex_actor_binding import ActorHexBindingService
from .hex_physics_bridge import HexPhysicsSnapshot
from .hex_world_runtime import HexMovableEntity


class NPCSpatialBindingError(ValueError):
    """NPC domain record and world actor cannot share a spatial binding."""


def _local_physics_bounds(body: PhysicsBodyDefinition) -> AABB:
    """Return collider bounds relative to the NPC's authoritative ground anchor."""
    if not isinstance(body, PhysicsBodyDefinition):
        raise TypeError("body must be a PhysicsBodyDefinition")
    offset = body.local_offset
    shape = body.collider
    if isinstance(shape, CircleShape):
        center = WorldPoint(offset.x + shape.center.x, offset.y + shape.center.y)
        return AABB.around_point(center, shape.radius)
    points = tuple(
        WorldPoint(offset.x + vertex.x, offset.y + vertex.y)
        for vertex in shape.vertices
    )
    return AABB(
        min(point.x for point in points), min(point.y for point in points),
        max(point.x for point in points), max(point.y for point in points),
    )


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
    def world_id(self) -> WorldId:
        return self._actor_binding.world_id

    def npc(self, npc_id: str) -> NPC:
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
            # A live physics body is the movement blocker. Grid occupancy must
            # allow two actors to share a hex while their colliders remain apart.
            blocks_movement=(blocks_movement and not npc.physics_body.enabled),
            blocks_occupancy=(blocks_occupancy and not npc.physics_body.enabled),
            local_spatial_bounds=_local_physics_bounds(npc.physics_body),
            broadphase_enabled=npc.physics_body.enabled,
        )

    def move(self, npc_id: str, direction: HexDirection) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        snapshot = self._actor_binding.physics_snapshot
        body = npc.physics_body
        if snapshot is not None and body.enabled:
            result = self._actor_binding.move_with_physics(
                npc_id, direction, snapshot, body,
            )
        else:
            result = self._actor_binding.move(npc_id, direction)
        if result.success:
            self._resolve_dynamic_contacts()
        return result

    def move_to(
        self,
        npc_id: str,
        target: LocalHexPosition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        snapshot = self._actor_binding.physics_snapshot
        body = npc.physics_body
        if snapshot is not None and body.enabled:
            result = self._actor_binding.move_to_with_physics(
                npc_id, target, snapshot, body,
            )
        else:
            result = self._actor_binding.move_to(npc_id, target)
        if result.success:
            self._resolve_dynamic_contacts()
        return result

    def move_to_with_physics(
        self,
        npc_id: str,
        target: LocalHexPosition,
        physics_snapshot: HexPhysicsSnapshot,
        body: PhysicsBodyDefinition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        result = self._actor_binding.move_to_with_physics(
            npc_id, target, physics_snapshot, body,
        )
        if result.success:
            self._resolve_dynamic_contacts()
        return result

    def move_with_physics(
        self,
        npc_id: str,
        direction: HexDirection,
        physics_snapshot: HexPhysicsSnapshot,
        body: PhysicsBodyDefinition,
    ) -> MovementResult:
        npc = self._require_npc(npc_id)
        if not npc.active:
            return self._inactive_result(npc_id)
        result = self._actor_binding.move_with_physics(
            npc_id, direction, physics_snapshot, body,
        )
        if result.success:
            self._resolve_dynamic_contacts()
        return result

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

    def _resolve_dynamic_contacts(self) -> None:
        """Resolve NPC pairs and contacts with the active player after direct moves."""
        snapshot = self._actor_binding.physics_snapshot
        player_body = self._actor_binding.player_body
        if snapshot is None or player_body is None:
            return
        from .dynamic_actor_collision import DynamicActorCollisionResolver

        runtime = self._actor_binding.runtime
        bodies = {
            npc.npc_id: npc.physics_body for npc in self._npcs.all()
            if npc.physics_body is not None
        }
        resolver = DynamicActorCollisionResolver(runtime, snapshot)
        resolver.resolve_npc_pairs(bodies)
        player = next(
            (entity for entity in runtime.entities() if entity.kind == "player"),
            None,
        )
        if player is not None:
            resolver.resolve_npc_player_contacts(
                player.entity_id, player_body, bodies,
            )

    def _require_npc(self, npc_id: str) -> NPC:
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
