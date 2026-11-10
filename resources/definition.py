"""Physical metadata for resource stacks."""
from dataclasses import dataclass
from math import isfinite
from .resource import ResourceUnit


@dataclass(frozen=True)
class ResourceDefinition:
    resource_id: str
    name: str
    unit: ResourceUnit
    weight_kg_per_unit: float = 0.0
    volume_liters_per_unit: float = 0.0
    category: str = "misc"
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise ValueError("resource_id must be a non-empty string.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Resource name is required.")
        if not isinstance(self.unit, ResourceUnit):
            raise TypeError("unit must be ResourceUnit.")
        for name in ("weight_kg_per_unit", "volume_liters_per_unit"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a number.")
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("category must be a non-empty string.")
        tags = tuple(self.tags)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("Resource tags must be non-empty strings.")
        if len(tags) != len(set(tags)):
            raise ValueError("Resource tags must be unique.")
        object.__setattr__(self, "tags", tuple(sorted(tags)))
