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
    """Coordinate container custody transitions with canonical hex placement.

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
        """Remove the axial placement while preserving the container capability."""
        instance = self._require_container(container_id)
        return self._runtime.remove_entity(instance.entity_id)

    def carry(self, container_id: str, inventory_id: str, *, validate=None) -> None:
        """Atomically remove world placement before assigning inventory custody."""
        instance = self._require_container(container_id)
        if self._containers.parent_of(container_id) is not None:
            raise ContainerHexBindingError("Nested container cannot be carried directly.")
        if self._containers.inventory_custody(container_id) is not None:
            raise ContainerHexBindingError("Container already has inventory custody.")
        snapshot = self._detach_spatial(instance.entity_id)
        try:
            self._containers.set_inventory_custody(container_id, inventory_id)
            if validate is not None:
                validate()
        except Exception:
            if self._containers.inventory_custody(container_id) == inventory_id:
                self._containers.clear_inventory_custody(container_id, inventory_id)
            self._restore_spatial(snapshot)
            raise

    def contain(self, parent_id: str, child_id: str, *, validate=None) -> ContainerInstance:
        """Atomically remove a child's world placement before nesting it."""
        child = self._require_container(child_id)
        if self._containers.parent_of(child_id) is not None:
            raise ContainerHexBindingError("Nested container already has a parent.")
        if self._containers.inventory_custody(child_id) is not None:
            raise ContainerHexBindingError("Carried container cannot be nested directly.")
        snapshot = self._detach_spatial(child.entity_id)
        try:
            result = self._containers.contain(parent_id, child_id)
            if validate is not None:
                validate()
            return result
        except Exception:
            if self._containers.parent_of(child_id) is not None:
                self._containers.release(child_id)
            self._restore_spatial(snapshot)
            raise

    def place_from_inventory(
        self,
        container_id: str,
        inventory_id: str,
        position: EntityPosition,
        *,
        blocks_movement: bool,
        blocks_occupancy: bool,
        validate=None,
    ) -> HexMovableEntity:
        """Atomically release inventory custody and place the container in the world."""
        instance = self._require_container(container_id)
        if self._containers.inventory_custody(container_id) != inventory_id:
            raise ContainerHexBindingError(
                "Container is not held by the requested inventory."
            )
        self._membership_world_required(instance.entity_id)
        self._containers.clear_inventory_custody(container_id, inventory_id)
        try:
            entity = self.register_spatial(
                container_id,
                position,
                blocks_movement=blocks_movement,
                blocks_occupancy=blocks_occupancy,
            )
            if validate is not None:
                validate()
            return entity
        except Exception:
            try:
                self._runtime.remove_entity(instance.entity_id)
            except KeyError:
                pass
            self._containers.set_inventory_custody(container_id, inventory_id)
            raise

    def release_to_world(
        self,
        child_id: str,
        position: EntityPosition,
        *,
        blocks_movement: bool,
        blocks_occupancy: bool,
        validate=None,
    ) -> HexMovableEntity:
        """Atomically detach a nested container and give it an explicit world placement."""
        child = self._require_container(child_id)
        parent = self._containers.parent_of(child_id)
        if parent is None:
            raise ContainerHexBindingError("Container is not nested.")
        self._membership_world_required(child.entity_id)
        self._containers.release(child_id)
        try:
            entity = self.register_spatial(
                child_id,
                position,
                blocks_movement=blocks_movement,
                blocks_occupancy=blocks_occupancy,
            )
            if validate is not None:
                validate()
            return entity
        except Exception:
            try:
                self._runtime.remove_entity(child.entity_id)
            except KeyError:
                pass
            self._containers.contain(parent.container_id, child_id)
            raise

    def _membership_world_required(self, entity_id: str) -> None:
        membership_world = self._membership.world_id_for(entity_id)
        if membership_world != self._world_id.value:
            raise ContainerHexBindingError(
                f"Container entity '{entity_id}' is not a member of "
                f"world '{self._world_id.value}'."
            )

    def _detach_spatial(self, entity_id: str):
        occupant = self._runtime.occupancy.get(entity_id)
        if occupant is None:
            try:
                self._runtime.entity(entity_id)
            except KeyError:
                return None
            raise RuntimeError(
                f"Hex entity has no authoritative occupancy record: {entity_id}"
            )
        entity = self._runtime.remove_entity(entity_id)
        return (
            entity,
            occupant.blocks_movement,
            occupant.blocks_occupancy,
        )

    def _restore_spatial(self, snapshot) -> None:
        if snapshot is None:
            return
        entity, blocks_movement, blocks_occupancy = snapshot
        self._runtime.register_entity(
            entity.entity_id,
            entity.kind,
            entity.position,
            entity.profile,
            active=entity.active,
            blocks_movement=blocks_movement,
            blocks_occupancy=blocks_occupancy,
        )

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
