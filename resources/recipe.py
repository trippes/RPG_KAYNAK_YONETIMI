"""Immutable recipes for instantaneous resource production."""

from dataclasses import dataclass
from typing import Iterable, Mapping

from core.time import Tick

from .resource import Quantity, ResourceType


RecipeComponent = tuple[ResourceType, Quantity]


class RecipeError(ValueError):
    """Invalid recipe definition."""


@dataclass(frozen=True)
class Recipe:
    """Deterministic, immutable input/output resource definition."""

    recipe_id: str
    inputs: tuple[RecipeComponent, ...]
    outputs: tuple[RecipeComponent, ...]
    processing_time: Tick | int = Tick(1)
    facility_type: str | None = None
    required_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.recipe_id, str):
            raise TypeError("recipe_id must be a string.")
        if not self.recipe_id.strip():
            raise RecipeError("recipe_id cannot be empty.")
        object.__setattr__(self, "inputs", _normalize_components(self.inputs, "inputs"))
        object.__setattr__(self, "outputs", _normalize_components(self.outputs, "outputs"))
        processing_time = self.processing_time if isinstance(self.processing_time, Tick) else Tick(self.processing_time)
        if processing_time.value <= 0:
            raise RecipeError("processing_time must be positive.")
        object.__setattr__(self, "processing_time", processing_time)
        if self.facility_type is not None:
            if not isinstance(self.facility_type, str) or not self.facility_type.strip():
                raise RecipeError("facility_type must be a non-empty string or None.")
        capabilities = tuple(self.required_capabilities)
        if any(not isinstance(capability, str) or not capability.strip() for capability in capabilities):
            raise RecipeError("required_capabilities must contain non-empty strings.")
        if len(set(capabilities)) != len(capabilities):
            raise RecipeError("required_capabilities cannot contain duplicates.")
        object.__setattr__(self, "required_capabilities", tuple(sorted(capabilities)))


def _normalize_components(
    components: Mapping[ResourceType, Quantity] | Iterable[RecipeComponent],
    name: str,
) -> tuple[RecipeComponent, ...]:
    if isinstance(components, Mapping):
        raw_components = tuple(components.items())
    else:
        try:
            raw_components = tuple(components)
        except TypeError as error:
            raise TypeError(f"Recipe {name} must be an iterable of resource components.") from error

    if not raw_components:
        raise RecipeError(f"Recipe {name} cannot be empty.")

    normalized: list[RecipeComponent] = []
    seen: set[ResourceType] = set()
    for component in raw_components:
        if not isinstance(component, (tuple, list)) or len(component) != 2:
            raise TypeError(f"Recipe {name} components must be (ResourceType, Quantity) pairs.")
        resource_type, quantity = component
        if not isinstance(resource_type, ResourceType):
            raise TypeError(f"Recipe {name} resource must be ResourceType.")
        if not isinstance(quantity, Quantity):
            raise TypeError(f"Recipe {name} amount must be Quantity.")
        if quantity.value <= 0:
            raise RecipeError(f"Recipe {name} quantities must be positive.")
        if resource_type in seen:
            raise RecipeError(f"Recipe {name} contains duplicate resource type: {resource_type}.")
        seen.add(resource_type)
        normalized.append((resource_type, quantity))

    return tuple(sorted(normalized, key=lambda item: item[0].value))
