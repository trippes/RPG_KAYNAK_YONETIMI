"""Management operations for world resource nodes."""

from .inventory import Inventory
from .node import WorldResourceNode
from .resource import Quantity
from core.foundation import WorldId


class WorldResourceNodeManager:
    """Deterministic registry for resource nodes grouped by world identity."""

    def __init__(self, world_registry=None) -> None:
        self._nodes: dict[str, WorldResourceNode] = {}
        self._world_registry = None
        if world_registry is not None:
            self.bind_world_registry(world_registry)

    @property
    def world_registry(self):
        """The optional authoritative world lookup used for registration checks."""
        return self._world_registry

    def bind_world_registry(self, world_registry) -> None:
        """Bind this registry to a WorldManager without copying world state.

        Binding is an application boundary concern; resource nodes retain only
        their stable world ID and remain outside the Entity system.
        """
        if not callable(getattr(world_registry, "exists", None)):
            raise TypeError("world_registry must provide exists(world_id).")
        missing = sorted(
            node.world_id for node in self._nodes.values()
            if not world_registry.exists(node.world_id)
        )
        if missing:
            raise ValueError(f"Resource nodes reference unknown worlds: {missing}")
        self._world_registry = world_registry

    def validate_world_references(self) -> None:
        """Validate every registered node against the bound WorldManager."""
        if self._world_registry is None:
            return
        missing = sorted(
            node.world_id for node in self._nodes.values()
            if not self._world_registry.exists(node.world_id)
        )
        if missing:
            raise ValueError(f"Resource nodes reference unknown worlds: {missing}")

    def add(self, node: WorldResourceNode) -> None:
        if not isinstance(node, WorldResourceNode):
            raise TypeError("node must be WorldResourceNode.")
        if node.node_id in self._nodes:
            raise ValueError(f"Duplicate resource node id: {node.node_id}")
        if self._world_registry is not None and not self._world_registry.exists(node.world_id):
            raise ValueError(f"Resource node references unknown world: {node.world_id}")
        self._nodes[node.node_id] = node

    def get(self, node_id: str) -> WorldResourceNode | None:
        if not isinstance(node_id, str) or not node_id.strip():
            raise TypeError("node_id must be a non-empty string.")
        return self._nodes.get(node_id)

    def for_world(self, world_id: str | WorldId) -> tuple[WorldResourceNode, ...]:
        if isinstance(world_id, WorldId):
            world_id = world_id.value
        if not isinstance(world_id, str) or not world_id.strip():
            raise TypeError("world_id must be a non-empty string.")
        return tuple(
            self._nodes[node_id]
            for node_id in sorted(self._nodes)
            if self._nodes[node_id].world_id == world_id
        )

    def extract(self, node_id: str, inventory: Inventory, quantity: Quantity) -> None:
        self.validate_world_references()
        node = self.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        node.extract_to(inventory, quantity)

    def validate_extraction(self, node_id: str, quantity: Quantity) -> None:
        self.validate_world_references()
        node = self.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        node.validate_extraction(quantity)

    def regenerate_to(self, node_id: str, tick) -> Quantity:
        self.validate_world_references()
        node = self.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        return node.regenerate_to(tick)

    def advance_to(self, tick) -> None:
        """Regenerate all nodes once up to a canonical simulation tick."""
        self.validate_world_references()
        for node in self.nodes():
            # A restored gameplay snapshot may contain a node whose last
            # processed tick is ahead of a separately persisted runtime tick.
            # Do not move that node backwards; resume it when runtime catches
            # up. Direct node.regenerate_to() remains strict about backwards
            # calls for callers that require an explicit validation error.
            target = tick if isinstance(tick, int) else tick.value
            if target >= node.last_simulation_tick.value:
                node.regenerate_to(tick)

    def count(self) -> int:
        return len(self._nodes)

    def nodes(self) -> tuple[WorldResourceNode, ...]:
        return tuple(self._nodes[node_id] for node_id in sorted(self._nodes))
