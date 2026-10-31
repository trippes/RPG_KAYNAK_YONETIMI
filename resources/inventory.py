"""Independent resource inventory domain object."""

from .resource import Quantity, ResourceType


class Inventory:
    """Deterministic, single-threaded container for resource stock."""

    def __init__(self) -> None:
        self._stocks: dict[ResourceType, Quantity] = {}
        self._items: dict[str, int] = {}

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        self._validate_item(item_id, quantity)
        self._items[item_id] = self._items.get(item_id, 0) + quantity

    def remove_item(self, item_id: str, quantity: int = 1) -> None:
        self._validate_item(item_id, quantity)
        current = self._items.get(item_id, 0)
        if current < quantity:
            raise ValueError("Insufficient item stock.")
        if current == quantity:
            del self._items[item_id]
        else:
            self._items[item_id] = current - quantity

    def item_quantity(self, item_id: str) -> int:
        self._validate_item(item_id, 0)
        return self._items.get(item_id, 0)

    def item_snapshot(self) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(self._items.items()))

    def total_weight(self, item_catalog=None) -> float:
        if item_catalog is None:
            return 0.0
        return sum(
            item_catalog[item_id].weight * quantity
            for item_id, quantity in self._items.items()
            if item_id in item_catalog
        )

    def add(self, resource_type: ResourceType, quantity: Quantity) -> None:
        self._validate_inputs(resource_type, quantity)
        current = self._stocks.get(resource_type)
        if current is not None and current.unit != quantity.unit:
            raise ValueError("Resource unit does not match existing stock.")
        if quantity.value == 0:
            return
        if current is None:
            self._stocks[resource_type] = quantity
            return
        self._stocks[resource_type] = Quantity(
            current.value + quantity.value,
            current.unit,
        )

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
        return not self._stocks

    def resource_type_count(self) -> int:
        return len(self._stocks)

    def snapshot(self) -> tuple[tuple[ResourceType, Quantity], ...]:
        """Return an immutable, resource-identifier-sorted stock view."""
        return tuple(sorted(self._stocks.items(), key=lambda item: item[0].value))

    def _restore_snapshot(self, snapshot: tuple[tuple[ResourceType, Quantity], ...]) -> None:
        """Restore a snapshot for the package-local atomic transfer operation."""
        self._stocks = dict(snapshot)

    def _restore_item_snapshot(self, snapshot: tuple[tuple[str, int], ...]) -> None:
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
