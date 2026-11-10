"""Atomic item and resource transfer operations."""
from .inventory import Inventory
from .resource import Quantity, ResourceType


def transfer_resources(source: Inventory, target: Inventory, resource_type: ResourceType, quantity: Quantity) -> None:
    _validate_inventories(source, target)
    if not isinstance(resource_type, ResourceType):
        raise TypeError("resource_type must be ResourceType.")
    if not isinstance(quantity, Quantity):
        raise TypeError("quantity must be Quantity.")
    if source is target or quantity.value == 0:
        return
    source_stock = source.get(resource_type)
    if source_stock is None:
        raise ValueError("Resource stock is not available in source inventory.")
    if source_stock.unit != quantity.unit:
        raise ValueError("Transfer unit does not match source stock.")
    target_stock = target.get(resource_type)
    if target_stock is not None and target_stock.unit != quantity.unit:
        raise ValueError("Transfer unit does not match target stock.")
    if quantity.value > source_stock.value:
        raise ValueError("Insufficient resource stock in source inventory.")
    before_source, before_target = source.snapshot(), target.snapshot()
    try:
        source.remove(resource_type, quantity)
        target.add(resource_type, quantity)
    except Exception:
        source._restore_snapshot(before_source)
        target._restore_snapshot(before_target)
        raise


def transfer_items(source: Inventory, target: Inventory, item_id: str, quantity: int = 1) -> None:
    """Atomically transfer an item stack quantity between inventories."""
    _validate_inventories(source, target)
    Inventory._validate_item(item_id, quantity)
    if source is target or quantity == 0:
        return
    if source.item_quantity(item_id) < quantity:
        raise ValueError("Insufficient item stock in source inventory.")
    before_source, before_target = source.item_snapshot(), target.item_snapshot()
    try:
        source.remove_item(item_id, quantity)
        target.add_item(item_id, quantity)
    except Exception:
        source._restore_item_snapshot(before_source)
        target._restore_item_snapshot(before_target)
        raise


def _validate_inventories(source: Inventory, target: Inventory) -> None:
    if not isinstance(source, Inventory):
        raise TypeError("source must be Inventory.")
    if not isinstance(target, Inventory):
        raise TypeError("target must be Inventory.")
