"""World-scoped resource nodes and deterministic regeneration."""

from __future__ import annotations

from core.time import Tick
from core.foundation import WorldId

from .inventory import Inventory
from .resource import Quantity, ResourceType


class ResourceNodeError(ValueError):
    """Invalid resource-node configuration or operation."""


class ResourceNodeInsufficientError(ResourceNodeError):
    """A node does not contain enough resource for an extraction."""


class WorldResourceNode:
    """A mutable, runtime-only resource source belonging to a world identity.

    The node stores only a string world identity; it is not an entity and does
    not participate in ``WorldMembershipService``. Regeneration is explicit:
    callers must invoke :meth:`regenerate_to` with a canonical simulation tick.
    """

    def __init__(
        self,
        node_id: str,
        world_id: str | WorldId,
        resource_type: ResourceType,
        initial_quantity: Quantity,
        capacity: Quantity,
        regeneration_rate: Quantity,
        last_simulation_tick: Tick | int = Tick(0),
        location_id: str | None = None,
    ) -> None:
        self._node_id = self._validate_text(node_id, "node_id")
        self._world_id = self._validate_world_id(world_id)
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        self._validate_quantity(initial_quantity, "initial_quantity")
        self._validate_quantity(capacity, "capacity")
        self._validate_quantity(regeneration_rate, "regeneration_rate")
        self._validate_tick(last_simulation_tick)
        if not (initial_quantity.unit == capacity.unit == regeneration_rate.unit):
            raise ResourceNodeError("Node quantities must use the same resource unit.")
        if initial_quantity.value > capacity.value:
            raise ResourceNodeError("Initial quantity cannot exceed node capacity.")

        self._resource_type = resource_type
        self._capacity = capacity
        self._regeneration_rate = regeneration_rate
        self._quantity = initial_quantity
        self._last_simulation_tick = self._as_tick(last_simulation_tick)
        if location_id is not None and (not isinstance(location_id, str) or not location_id.strip()):
            raise ValueError("location_id must be a non-empty string when provided.")
        self._location_id = location_id

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def resource_type(self) -> ResourceType:
        return self._resource_type

    @property
    def location_id(self) -> str | None:
        return self._location_id

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @property
    def current_quantity(self) -> Quantity:
        return self._quantity

    @property
    def capacity(self) -> Quantity:
        return self._capacity

    @property
    def regeneration_rate(self) -> Quantity:
        return self._regeneration_rate

    @property
    def last_simulation_tick(self) -> Tick:
        return self._last_simulation_tick

    def regenerate_to(self, tick: Tick | int) -> Quantity:
        """Apply integer regeneration for ticks after the last processed tick."""
        self._validate_tick(tick)
        target = self._as_tick(tick)
        if target < self._last_simulation_tick:
            raise ValueError("Regeneration tick cannot move backwards.")
        elapsed = target.value - self._last_simulation_tick.value
        if elapsed:
            available_capacity = self._capacity.value - self._quantity.value
            added = min(available_capacity, elapsed * self._regeneration_rate.value)
            self._quantity = Quantity(self._quantity.value + added, self._quantity.unit)
        self._last_simulation_tick = target
        return self._quantity

    def extract_to(self, inventory: Inventory, quantity: Quantity) -> None:
        """Atomically move a positive quantity from this node to an inventory."""
        if not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        self.validate_extraction(quantity)
        before = inventory.snapshot()
        try:
            inventory.add(self._resource_type, quantity)
            self._quantity = Quantity(self._quantity.value - quantity.value, self._quantity.unit)
        except Exception:
            inventory._restore_snapshot(before)
            raise

    def validate_extraction(self, quantity: Quantity) -> None:
        """Validate an extraction without changing node or inventory state."""
        self._validate_quantity(quantity, "quantity")
        if quantity.value <= 0:
            raise ResourceNodeError("Extraction quantity must be positive.")
        if quantity.unit != self._quantity.unit:
            raise ResourceNodeError("Extraction unit does not match node unit.")
        if quantity.value > self._quantity.value:
            raise ResourceNodeInsufficientError("Node does not contain enough resource.")

    @staticmethod
    def _validate_text(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        if not value.strip():
            raise ValueError(f"{name} cannot be empty.")
        return value

    @staticmethod
    def _validate_world_id(value: str | WorldId) -> str:
        if isinstance(value, WorldId):
            return value.value
        return WorldResourceNode._validate_text(value, "world_id")

    @staticmethod
    def _validate_quantity(value: Quantity, name: str) -> None:
        if not isinstance(value, Quantity):
            raise TypeError(f"{name} must be Quantity.")

    @staticmethod
    def _validate_tick(value: Tick | int) -> None:
        if isinstance(value, bool) or not isinstance(value, (Tick, int)):
            raise TypeError("tick must be Tick or integer.")
        if isinstance(value, int) and value < 0:
            raise ValueError("tick cannot be negative.")

    @staticmethod
    def _as_tick(value: Tick | int) -> Tick:
        return value if isinstance(value, Tick) else Tick(value)
