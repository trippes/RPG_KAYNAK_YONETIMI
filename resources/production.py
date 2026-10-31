"""Atomic resource consumption and instantaneous recipe production."""

from typing import Iterable

from .inventory import Inventory
from .recipe import Recipe, RecipeComponent, RecipeError
from .resource import Quantity, ResourceType


class ResourceOperationError(ValueError):
    """Invalid resource consumption or production operation."""


class InsufficientStockError(ResourceOperationError):
    """Required resource stock is unavailable or insufficient."""


class ResourceUnitMismatchError(ResourceOperationError):
    """A resource operation uses an incompatible unit."""


def consume_resources(
    inventory: Inventory,
    requirements: Iterable[RecipeComponent],
) -> None:
    """Atomically consume all positive resource requirements from an inventory."""
    _validate_inventory(inventory)
    components = _normalize_requirements(requirements)
    _validate_available_stock(inventory, components)

    before = inventory.snapshot()
    try:
        for resource_type, quantity in components:
            inventory.remove(resource_type, quantity)
    except Exception:
        inventory._restore_snapshot(before)
        raise


def produce(inventory: Inventory, recipe: Recipe) -> None:
    """Atomically consume a recipe's inputs and add all of its outputs."""
    _validate_inventory(inventory)
    if not isinstance(recipe, Recipe):
        raise TypeError("recipe must be Recipe.")

    _validate_recipe_units(recipe)
    _validate_available_stock(inventory, recipe.inputs)
    _validate_output_units(inventory, recipe.outputs)

    before = inventory.snapshot()
    try:
        for resource_type, quantity in recipe.inputs:
            inventory.remove(resource_type, quantity)
        for resource_type, quantity in recipe.outputs:
            inventory.add(resource_type, quantity)
    except Exception:
        inventory._restore_snapshot(before)
        raise


def _validate_inventory(inventory: Inventory) -> None:
    if not isinstance(inventory, Inventory):
        raise TypeError("inventory must be Inventory.")


def _normalize_requirements(requirements: Iterable[RecipeComponent]) -> tuple[RecipeComponent, ...]:
    try:
        components = tuple(requirements)
    except TypeError as error:
        raise TypeError("requirements must be an iterable of resource components.") from error

    if not components:
        raise ResourceOperationError("requirements cannot be empty.")

    normalized: list[RecipeComponent] = []
    seen: set[ResourceType] = set()
    for component in components:
        if not isinstance(component, (tuple, list)) or len(component) != 2:
            raise TypeError("requirements must contain (ResourceType, Quantity) pairs.")
        resource_type, quantity = component
        if not isinstance(resource_type, ResourceType):
            raise TypeError("requirement resource must be ResourceType.")
        if not isinstance(quantity, Quantity):
            raise TypeError("requirement amount must be Quantity.")
        if quantity.value <= 0:
            raise ResourceOperationError("requirement quantities must be positive.")
        if resource_type in seen:
            raise ResourceOperationError(f"Duplicate requirement resource type: {resource_type}.")
        seen.add(resource_type)
        normalized.append((resource_type, quantity))
    return tuple(sorted(normalized, key=lambda item: item[0].value))


def _validate_available_stock(
    inventory: Inventory,
    components: tuple[RecipeComponent, ...],
) -> None:
    for resource_type, quantity in components:
        current = inventory.get(resource_type)
        if current is None or current.value < quantity.value:
            raise InsufficientStockError(f"Insufficient stock for resource: {resource_type}.")
        if current.unit != quantity.unit:
            raise ResourceUnitMismatchError(f"Stock unit mismatch for resource: {resource_type}.")


def _validate_output_units(
    inventory: Inventory,
    outputs: tuple[RecipeComponent, ...],
) -> None:
    for resource_type, quantity in outputs:
        current = inventory.get(resource_type)
        if current is not None and current.unit != quantity.unit:
            raise ResourceUnitMismatchError(f"Output unit mismatch for resource: {resource_type}.")


def _validate_recipe_units(recipe: Recipe) -> None:
    inputs = dict(recipe.inputs)
    for resource_type, output_quantity in recipe.outputs:
        input_quantity = inputs.get(resource_type)
        if input_quantity is not None and input_quantity.unit != output_quantity.unit:
            raise ResourceUnitMismatchError(
                f"Recipe input/output unit mismatch for resource: {resource_type}."
            )
