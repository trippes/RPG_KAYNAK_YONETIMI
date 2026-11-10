"""Inventory for resource stock and stackable item quantities."""
from collections.abc import Mapping
from .resource import Quantity, ResourceType


class Inventory:
    """Deterministic, single-threaded inventory."""
    def __init__(self) -> None:
        self._stocks: dict[ResourceType, Quantity] = {}
        self._items: dict[str, int] = {}

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        self._validate_item(item_id, quantity)
        if quantity:
            self._items[item_id] = self._items.get(item_id, 0) + quantity

    def remove_item(self, item_id: str, quantity: int = 1) -> None:
        self._validate_item(item_id, quantity)
        current = self._items.get(item_id, 0)
        if current < quantity:
            raise ValueError("Insufficient item stock.")
        if quantity == 0:
            return
        if current == quantity:
            del self._items[item_id]
        else:
            self._items[item_id] = current - quantity

    def item_quantity(self, item_id: str) -> int:
        self._validate_item(item_id, 0)
        return self._items.get(item_id, 0)

    @property
    def items(self) -> tuple[tuple[str, int], ...]:
        return self.item_snapshot()

    def item_snapshot(self) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(self._items.items()))

    def total_weight(self, item_catalog=None, resource_catalog=None) -> float:
        """Combined weight in kg. Missing physical definitions are errors."""
        total = 0.0
        if self._items:
            if not isinstance(item_catalog, Mapping):
                raise ValueError("An item catalog is required to calculate item weight.")
            for item_id, quantity in self._items.items():
                definition = item_catalog.get(item_id)
                if definition is None:
                    raise ValueError(f"Missing item definition for weight calculation: {item_id}")
                total += definition.weight * quantity
        if self._stocks:
            if not isinstance(resource_catalog, Mapping):
                raise ValueError("A resource catalog is required to calculate resource weight.")
            for resource, quantity in self._stocks.items():
                definition = resource_catalog.get(resource.value)
                if definition is None:
                    raise ValueError(f"Missing resource definition for weight calculation: {resource.value}")
                if definition.unit != quantity.unit:
                    raise ValueError(f"Resource unit mismatch for weight calculation: {resource.value}")
                total += definition.weight_kg_per_unit * quantity.value
        return total

    def total_volume(self, item_catalog=None, resource_catalog=None) -> float:
        """Combined occupied volume in liters. Missing definitions are errors."""
        total = 0.0
        if self._items:
            if not isinstance(item_catalog, Mapping):
                raise ValueError("An item catalog is required to calculate item volume.")
            for item_id, quantity in self._items.items():
                definition = item_catalog.get(item_id)
                if definition is None:
                    raise ValueError(f"Missing item definition for volume calculation: {item_id}")
                total += definition.volume_liters * quantity
        if self._stocks:
            if not isinstance(resource_catalog, Mapping):
                raise ValueError("A resource catalog is required to calculate resource volume.")
            for resource, quantity in self._stocks.items():
                definition = resource_catalog.get(resource.value)
                if definition is None:
                    raise ValueError(f"Missing resource definition for volume calculation: {resource.value}")
                if definition.unit != quantity.unit:
                    raise ValueError(f"Resource unit mismatch for volume calculation: {resource.value}")
                total += definition.volume_liters_per_unit * quantity.value
        return total

    def add(self, resource_type: ResourceType, quantity: Quantity) -> None:
        self._validate_inputs(resource_type, quantity)
        current = self._stocks.get(resource_type)
        if current is not None and current.unit != quantity.unit:
            raise ValueError("Resource unit does not match existing stock.")
        if quantity.value == 0:
            return
        if current is None:
            self._stocks[resource_type] = quantity
        else:
            self._stocks[resource_type] = Quantity(current.value + quantity.value, current.unit)

    def remove(self, resource_type: ResourceType, quantity: Quantity) -> None:
        self._validate_inputs(resource_type, quantity)
        current = self._stocks.get(resource_type)
        if current is None:
            if quantity.value == 0:
                return
            raise ValueError("Resource stock is not available.")
        if current.unit != quantity.unit:
            raise ValueError("Resource unit does not match existing stock.")
        if quantity.value == 0:
            return
        if quantity.value > current.value:
            raise ValueError("Insufficient resource stock.")
        remaining = current.value - quantity.value
        if remaining == 0:
            del self._stocks[resource_type]
        else:
            self._stocks[resource_type] = Quantity(remaining, current.unit)

    def get(self, resource_type: ResourceType) -> Quantity | None:
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        return self._stocks.get(resource_type)

    def is_empty(self) -> bool:
        return not self._stocks and not self._items

    def resource_type_count(self) -> int:
        return len(self._stocks)

    def item_type_count(self) -> int:
        return len(self._items)

    def slot_count(self) -> int:
        """One occupied slot per distinct item stack or resource type."""
        return len(self._items) + len(self._stocks)

    def snapshot(self) -> tuple[tuple[ResourceType, Quantity], ...]:
        return tuple(sorted(self._stocks.items(), key=lambda item: item[0].value))

    def _restore_snapshot(self, snapshot) -> None:
        self._stocks = dict(snapshot)

    def _restore_item_snapshot(self, snapshot) -> None:
        self._items = dict(snapshot)

    @staticmethod
    def _validate_item(item_id: str, quantity: int) -> None:
        if not isinstance(item_id, str) or not item_id.strip():
            raise TypeError("item_id must be a non-empty string.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise ValueError("Item quantity must be a non-negative integer.")

    @staticmethod
    def _validate_inputs(resource_type: ResourceType, quantity: Quantity) -> None:
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        if not isinstance(quantity, Quantity):
            raise TypeError("quantity must be Quantity.")
