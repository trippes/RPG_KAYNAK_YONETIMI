"""Atomic production over resource stocks and item stacks."""
from typing import Iterable
from .inventory import Inventory
from .recipe import Recipe, RecipeComponent
from .resource import Quantity, ResourceType
from core.errors import RPGError

class ResourceOperationError(ValueError, RPGError):
    """Invalid resource consumption or production operation."""
class InsufficientStockError(ResourceOperationError):
    """Required resource stock is unavailable or insufficient."""
class InsufficientItemStockError(ResourceOperationError):
    """Required item stack quantity is unavailable or insufficient."""
class ResourceUnitMismatchError(ResourceOperationError):
    """A resource operation uses an incompatible unit."""

def _restore(inventory, resources, items):
    inventory._restore_snapshot(resources)
    inventory._restore_item_snapshot(items)

def consume_resources(inventory: Inventory, requirements: Iterable[RecipeComponent]) -> None:
    _validate_inventory(inventory)
    components = _normalize_requirements(requirements)
    _validate_resources(inventory, components)
    before = inventory.snapshot()
    try:
        for resource, quantity in components:
            inventory.remove(resource, quantity)
    except Exception:
        inventory._restore_snapshot(before)
        raise

def consume_recipe_inputs(inventory: Inventory, recipe: Recipe) -> None:
    """Consume all recipe inputs atomically across resource and item inventories."""
    _validate_inventory(inventory)
    if not isinstance(recipe, Recipe):
        raise TypeError("recipe must be Recipe.")
    _validate_recipe_units(recipe)
    _validate_resources(inventory, recipe.inputs)
    _validate_items(inventory, recipe.item_inputs)
    before_resources, before_items = inventory.snapshot(), inventory.item_snapshot()
    try:
        for resource, quantity in recipe.inputs:
            inventory.remove(resource, quantity)
        for item_id, quantity in recipe.item_inputs:
            inventory.remove_item(item_id, quantity)
    except Exception:
        _restore(inventory, before_resources, before_items)
        raise

def produce(inventory: Inventory, recipe: Recipe) -> None:
    """Atomically consume all inputs and create every resource/item output."""
    _validate_inventory(inventory)
    if not isinstance(recipe, Recipe):
        raise TypeError("recipe must be Recipe.")
    _validate_recipe_units(recipe)
    _validate_resources(inventory, recipe.inputs)
    _validate_items(inventory, recipe.item_inputs)
    for resource, quantity in recipe.outputs:
        current = inventory.get(resource)
        if current is not None and current.unit != quantity.unit:
            raise ResourceUnitMismatchError(f"Output unit mismatch for resource: {resource}.")
    before_resources, before_items = inventory.snapshot(), inventory.item_snapshot()
    try:
        for resource, quantity in recipe.inputs:
            inventory.remove(resource, quantity)
        for item_id, quantity in recipe.item_inputs:
            inventory.remove_item(item_id, quantity)
        for resource, quantity in recipe.outputs:
            inventory.add(resource, quantity)
        for item_id, quantity in recipe.item_outputs:
            inventory.add_item(item_id, quantity)
    except Exception:
        _restore(inventory, before_resources, before_items)
        raise

def _validate_inventory(inventory):
    if not isinstance(inventory, Inventory):
        raise TypeError("inventory must be Inventory.")

def _normalize_requirements(requirements):
    try:
        components = tuple(requirements)
    except TypeError as error:
        raise TypeError("requirements must be an iterable of resource components.") from error
    if not components:
        raise ResourceOperationError("requirements cannot be empty.")
    result, seen = [], set()
    for pair in components:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise TypeError("requirements must contain (ResourceType, Quantity) pairs.")
        resource, quantity = pair
        if not isinstance(resource, ResourceType) or not isinstance(quantity, Quantity):
            raise TypeError("requirements must contain ResourceType and Quantity values.")
        if quantity.value <= 0 or resource in seen:
            raise ResourceOperationError("Requirements must be positive and unique.")
        seen.add(resource)
        result.append((resource, quantity))
    return tuple(sorted(result, key=lambda pair: pair[0].value))

def _validate_resources(inventory, components):
    for resource, quantity in components:
        current = inventory.get(resource)
        if current is None or current.value < quantity.value:
            raise InsufficientStockError(f"Insufficient stock for resource: {resource}.")
        if current.unit != quantity.unit:
            raise ResourceUnitMismatchError(f"Stock unit mismatch for resource: {resource}.")

def _validate_items(inventory, components):
    for item_id, quantity in components:
        if inventory.item_quantity(item_id) < quantity:
            raise InsufficientItemStockError(f"Insufficient item stock for: {item_id}.")

def _validate_recipe_units(recipe):
    inputs = dict(recipe.inputs)
    for resource, output in recipe.outputs:
        source = inputs.get(resource)
        if source is not None and source.unit != output.unit:
            raise ResourceUnitMismatchError(f"Recipe input/output unit mismatch for resource: {resource}.")
