"""Bind world resource nodes to explicit axial positions without moving node state."""

from __future__ import annotations

from core.domain.spatial import EntityPosition, MovementProfile
from core.foundation import WorldId
from resources import WorldResourceNode, WorldResourceNodeManager

from .hex_world_runtime import HexMovableEntity, HexWorldRuntime


class ResourceNodeHexBindingError(ValueError):
    """Resource node and hex runtime do not share the requested world scope."""


class ResourceNodeHexBindingService:
    """Register fixed resource-node positions in the canonical hex occupancy.

    WorldResourceNodeManager remains authoritative for node identity, world
    membership, quantity and regeneration. HexWorldRuntime owns only the
    explicit map-local spatial registration. Resource nodes are non-movable
    and do not block actor movement; physical obstacles remain a separate
    collision-geometry concern.
    """

    __slots__ = ("_nodes", "_runtime", "_world_id")

    def __init__(
        self,
        nodes: WorldResourceNodeManager,
        runtime: HexWorldRuntime,
        world_id: WorldId,
    ) -> None:
        if not isinstance(nodes, WorldResourceNodeManager):
            raise TypeError("nodes must be a WorldResourceNodeManager")
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime")
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId")
        if runtime.world_id is None:
            raise ValueError("runtime must be bound to a WorldId")
        if runtime.world_id != world_id:
            raise ResourceNodeHexBindingError(
                f"Runtime belongs to world '{runtime.world_id.value}', "
                f"not '{world_id.value}'."
            )
        self._nodes = nodes
        self._runtime = runtime
        self._world_id = world_id

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def runtime(self) -> HexWorldRuntime:
        return self._runtime

    def resource_node(self, node_id: str) -> WorldResourceNode:
        return self._require_node(node_id)

    def spatial_entity(self, node_id: str) -> HexMovableEntity:
        self._require_node(node_id)
        return self._runtime.entity(node_id)

    def register_spatial(
        self,
        node_id: str,
        position: EntityPosition,
    ) -> HexMovableEntity:
        """Register an existing resource node at an explicit map-local position."""
        self._require_node(node_id)
        return self._runtime.register_entity(
            node_id,
            "object",
            position,
            MovementProfile(can_move=False),
            active=True,
            blocks_movement=False,
            blocks_occupancy=False,
        )

    def unregister_spatial(self, node_id: str) -> HexMovableEntity:
        """Remove only the spatial registration; preserve quantity/regeneration."""
        self._require_node(node_id)
        return self._runtime.remove_entity(node_id)

    def _require_node(self, node_id: str) -> WorldResourceNode:
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be a non-empty string")
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        if node.world_id != self._world_id.value:
            raise ResourceNodeHexBindingError(
                f"Resource node '{node_id}' belongs to world '{node.world_id}', "
                f"not '{self._world_id.value}'."
            )
        return node


__all__ = ["ResourceNodeHexBindingError", "ResourceNodeHexBindingService"]
