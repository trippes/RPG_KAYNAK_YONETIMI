"""Atomic resource transfer operation between independent inventories."""

from .inventory import Inventory
from .resource import Quantity, ResourceType


def transfer_resources(
    source: Inventory,
    target: Inventory,
    resource_type: ResourceType,
    quantity: Quantity,
) -> None:
    """Atomically transfer ``quantity`` of one resource between inventories."""
    _validate_inputs(source, target, resource_type, quantity)
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

    source_before = source.snapshot()
    target_before = target.snapshot()
    try:
        source.remove(resource_type, quantity)
        target.add(resource_type, quantity)
    except Exception:
        source._restore_snapshot(source_before)
        target._restore_snapshot(target_before)
        raise


def _validate_inputs(
    source: Inventory,
    target: Inventory,
    resource_type: ResourceType,
    quantity: Quantity,
) -> None:
    if not isinstance(source, Inventory):
        raise TypeError("source must be Inventory.")
    if not isinstance(target, Inventory):
        raise TypeError("target must be Inventory.")
    if not isinstance(resource_type, ResourceType):
        raise TypeError("resource_type must be ResourceType.")
    if not isinstance(quantity, Quantity):
        raise TypeError("quantity must be Quantity.")
