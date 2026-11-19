"""Bind only world-placed containers to the canonical hex runtime."""

from __future__ import annotations

from core.application.ownership import WorldMembershipService
from core.domain.spatial import EntityPosition, MovementProfile
from core.foundation import WorldId
from containers import ContainerManager, ContainerInstance

from .hex_world_runtime import HexMovableEntity, HexWorldRuntime


class ContainerHexBindingError(ValueError):
    """A container is not eligible for the requested world spatial binding."""


class ContainerHexBindingService:
    """Register world-placed container entities without owning their position.

    ContainerManager owns capability, contents, nesting and inventory custody.
    WorldMembershipService owns Core entity-to-world membership.
    HexWorldRuntime owns the explicit axial position and occupancy record.
    The Core Entity's legacy square Position is never read or converted.
    """

    __slots__ = ("_containers", "_membership", "_runtime", "_world_id")

    def __init__(
        self,
        containers: ContainerManager,
        membership: WorldMembershipService,
        runtime: HexWorldRuntime,
        world_id: WorldId,
    ) -> None:
        if not isinstance(containers, ContainerManager):
            raise TypeError("containers must be a ContainerManager")
        if not isinstance(membership, WorldMembershipService):
            raise TypeError("membership must be a WorldMembershipService")
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime")
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId")
        if runtime.world_id is None:
            raise ContainerHexBindingError("runtime must be bound to a WorldId")
        if runtime.world_id != world_id:
            raise ContainerHexBindingError(
                f"Runtime belongs to world '{runtime.world_id.value}', "
                f"not '{world_id.value}'."
            )
        self._containers = containers
        self._membership = membership
        self._runtime = runtime
        self._world_id = world_id

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    def container(self, container_id: str) -> ContainerInstance:
        return self._require_container(container_id)

    def spatial_entity(self, container_id: str) -> HexMovableEntity:
        instance = self._require_world_placed(container_id)
        return self._runtime.entity(instance.entity_id)

    def position(self, container_id: str) -> EntityPosition:
        return self.spatial_entity(container_id).position

    def register_spatial(
        self,
        container_id: str,
        position: EntityPosition,
        *,
        blocks_movement: bool,
        blocks_occupancy: bool,
    ) -> HexMovableEntity:
        """Register a one-cell container placement with explicit blocking flags."""
        if not isinstance(blocks_movement, bool):
            raise TypeError("blocks_movement must be a boolean.")
        if not isinstance(blocks_occupancy, bool):
            raise TypeError("blocks_occupancy must be a boolean.")
        instance = self._require_world_placed(container_id)
        return self._runtime.register_entity(
            instance.entity_id,
            "object",
            position,
            MovementProfile(can_move=False),
            active=True,
            blocks_movement=blocks_movement,
            blocks_occupancy=blocks_occupancy,
        )

    def unregister_spatial(self, container_id: str) -> HexMovableEntity:
        """Remove the axial placement before moving a container into custody."""
        instance = self._require_container(container_id)
        return self._runtime.remove_entity(instance.entity_id)

    def _require_container(self, container_id: str) -> ContainerInstance:
        if not isinstance(container_id, str) or not container_id.strip():
            raise ValueError("container_id must be a non-empty string.")
        instance = self._containers.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        return instance

    def _require_world_placed(self, container_id: str) -> ContainerInstance:
        instance = self._require_container(container_id)
        if self._containers.parent_of(container_id) is not None:
            raise ContainerHexBindingError(
                f"Nested container cannot have a world position: {container_id}"
            )
        if self._containers.inventory_custody(container_id) is not None:
            raise ContainerHexBindingError(
                f"Carried container cannot have a world position: {container_id}"
            )
        membership_world = self._membership.world_id_for(instance.entity_id)
        if membership_world != self._world_id.value:
            raise ContainerHexBindingError(
                f"Container entity '{instance.entity_id}' is not a member of "
                f"world '{self._world_id.value}'."
            )
        return instance


__all__ = ["ContainerHexBindingError", "ContainerHexBindingService"]
