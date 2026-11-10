"""Capacity calculations shared by container operations and validation."""
from dataclasses import dataclass
from .definition import ContainerDefinition


@dataclass(frozen=True)
class ContainerCapacityUsage:
    weight_kg: float
    slots: int
    volume_liters: float


@dataclass(frozen=True)
class ContainerCapacity:
    max_weight_kg: float | None
    max_slots: int | None
    max_volume_liters: float | None

    def fits(self, usage: ContainerCapacityUsage) -> bool:
        return (
            (self.max_weight_kg is None or usage.weight_kg <= self.max_weight_kg)
            and (self.max_slots is None or usage.slots <= self.max_slots)
            and (self.max_volume_liters is None or usage.volume_liters <= self.max_volume_liters)
        )


def capacity_for(definition: ContainerDefinition) -> ContainerCapacity:
    if not isinstance(definition, ContainerDefinition):
        raise TypeError("definition must be ContainerDefinition.")
    return ContainerCapacity(
        definition.max_contents_weight_kg,
        definition.max_slots,
        definition.max_contents_volume_liters,
    )
