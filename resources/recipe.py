"""Immutable recipes with resource and stackable-item inputs and outputs."""
from dataclasses import dataclass
from typing import Iterable, Mapping
from core.time import Tick
from .resource import Quantity, ResourceType
from core.errors import RPGError

RecipeComponent = tuple[ResourceType, Quantity]
ItemComponent = tuple[str, int]
StructurePartBinding = tuple[str, str]

class RecipeError(ValueError, RPGError):
    """Invalid recipe definition."""

@dataclass(frozen=True)
class Recipe:
    """Immutable production contract, including explicit structure-part output bindings."""
    recipe_id: str
    inputs: tuple[RecipeComponent, ...]
    outputs: tuple[RecipeComponent, ...]
    processing_time: Tick | int = Tick(1)
    facility_type: str | None = None
    required_capabilities: tuple[str, ...] = ()
    item_inputs: tuple[ItemComponent, ...] = ()
    item_outputs: tuple[ItemComponent, ...] = ()
    structure_part_bindings: tuple[StructurePartBinding, ...] = ()

    @property
    def duration_ticks(self) -> Tick:
        return self.processing_time

    def __post_init__(self) -> None:
        if not isinstance(self.recipe_id, str) or not self.recipe_id.strip():
            raise RecipeError("recipe_id must be a non-empty string.")
        object.__setattr__(self, "inputs", _normalize_resources(self.inputs, "inputs"))
        object.__setattr__(self, "outputs", _normalize_resources(self.outputs, "outputs"))
        object.__setattr__(self, "item_inputs", _normalize_items(self.item_inputs, "item_inputs"))
        object.__setattr__(self, "item_outputs", _normalize_items(self.item_outputs, "item_outputs"))
        if not self.inputs and not self.item_inputs:
            raise RecipeError("Recipe must define at least one resource or item input.")
        if not self.outputs and not self.item_outputs:
            raise RecipeError("Recipe must define at least one resource or item output.")
        duration = self.processing_time if isinstance(self.processing_time, Tick) else Tick(self.processing_time)
        if duration.value <= 0:
            raise RecipeError("processing_time must be positive.")
        object.__setattr__(self, "processing_time", duration)
        if self.facility_type is not None and (not isinstance(self.facility_type, str) or not self.facility_type.strip()):
            raise RecipeError("facility_type must be a non-empty string or None.")
        capabilities = tuple(self.required_capabilities)
        if any(not isinstance(value, str) or not value.strip() for value in capabilities) or len(set(capabilities)) != len(capabilities):
            raise RecipeError("required_capabilities must contain unique non-empty strings.")
        object.__setattr__(self, "required_capabilities", tuple(sorted(capabilities)))
        bindings = _normalize_bindings(self.structure_part_bindings)
        output_ids = {item_id for item_id, _ in self.item_outputs}
        if any(item_id not in output_ids for item_id, _ in bindings):
            raise RecipeError("Every structure-part binding must reference an item output.")
        object.__setattr__(self, "structure_part_bindings", bindings)

def _normalize_resources(values, name):
    raw = tuple(values.items()) if isinstance(values, Mapping) else tuple(values)
    result, seen = [], set()
    for pair in raw:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise TypeError(f"Recipe {name} components must be (ResourceType, Quantity) pairs.")
        resource, quantity = pair
        if not isinstance(resource, ResourceType) or not isinstance(quantity, Quantity):
            raise TypeError(f"Recipe {name} requires ResourceType and Quantity values.")
        if quantity.value <= 0 or resource in seen:
            raise RecipeError(f"Recipe {name} quantities must be positive and resources unique.")
        seen.add(resource)
        result.append((resource, quantity))
    return tuple(sorted(result, key=lambda pair: pair[0].value))

def _normalize_items(values, name):
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of (item_id, quantity) pairs.")
    result, seen = [], set()
    for pair in tuple(values):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise TypeError(f"{name} components must be (item_id, quantity) pairs.")
        item_id, quantity = pair
        if not isinstance(item_id, str) or not item_id.strip() or isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise RecipeError(f"{name} requires non-empty item IDs and positive integer quantities.")
        if item_id in seen:
            raise RecipeError(f"{name} contains duplicate item: {item_id}.")
        seen.add(item_id)
        result.append((item_id, quantity))
    return tuple(sorted(result))

def _normalize_bindings(values):
    if isinstance(values, (str, bytes)):
        raise TypeError("structure_part_bindings must be iterable pairs.")
    result, seen = [], set()
    for pair in tuple(values):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise TypeError("Structure-part bindings must be (item_id, part_definition_id) pairs.")
        item_id, part_id = pair
        if not isinstance(item_id, str) or not item_id.strip() or not isinstance(part_id, str) or not part_id.strip():
            raise RecipeError("Structure-part binding IDs must be non-empty strings.")
        if item_id in seen:
            raise RecipeError(f"Duplicate structure-part binding for item: {item_id}.")
        seen.add(item_id)
        result.append((item_id, part_id))
    return tuple(sorted(result))
