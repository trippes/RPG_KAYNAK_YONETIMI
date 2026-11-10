"""Equipment definitions and loadout rules."""
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Mapping


class EquipmentSlot(str, Enum):
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    ACCESSORY = "accessory"


@dataclass(frozen=True)
class ItemDefinition:
    item_id: str
    name: str
    slot: EquipmentSlot | None = None
    weight: float = 0.0
    attack: int = 0
    defense: int = 0
    damage: int = 0
    max_hit_points: int = 0
    attribute_bonuses: Mapping[str, int] = field(default_factory=lambda: MappingProxyType({}))
    description: str = ""
    volume_liters: float = 0.0
    category: str = "misc"
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not self.item_id.strip() or not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Item id and name are required.")
        for name in ("weight", "volume_liters"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Item {name} must be a number.")
            if not isfinite(value) or value < 0:
                raise ValueError(f"Item {name} must be finite and non-negative.")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (self.attack, self.defense, self.damage, self.max_hit_points)):
            raise ValueError("Item combat bonuses must be non-negative integers.")
        if self.slot is not None and not isinstance(self.slot, EquipmentSlot):
            raise TypeError("slot must be EquipmentSlot or None.")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("Item category must be a non-empty string.")
        tags = tuple(self.tags)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("Item tags must be non-empty strings.")
        if len(tags) != len(set(tags)):
            raise ValueError("Item tags must be unique.")
        bonuses = dict(self.attribute_bonuses)
        if any(not isinstance(key, str) or not key.strip() for key in bonuses):
            raise ValueError("Attribute bonus keys must be non-empty strings.")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in bonuses.values()):
            raise ValueError("Attribute bonuses must be non-negative integers.")
        object.__setattr__(self, "attribute_bonuses", MappingProxyType(bonuses))
        object.__setattr__(self, "tags", tuple(sorted(tags)))

    @property
    def equippable(self) -> bool:
        return self.slot is not None


class EquipmentLoadout:
    """One item per equipment slot, with deterministic replacement."""
    def __init__(self, equipped: Mapping[EquipmentSlot | str, str] | None = None):
        self._equipped: dict[EquipmentSlot, str] = {}
        for slot, item_id in (equipped or {}).items():
            self._equipped[self._slot(slot)] = self._item_id(item_id)

    def get(self, slot: EquipmentSlot | str) -> str | None:
        return self._equipped.get(self._slot(slot))

    def equip(self, item: ItemDefinition) -> str | None:
        if not isinstance(item, ItemDefinition):
            raise TypeError("item must be ItemDefinition.")
        if item.slot is None:
            raise ValueError("Only equippable items can be equipped.")
        previous = self._equipped.get(item.slot)
        self._equipped[item.slot] = item.item_id
        return previous

    def unequip(self, slot: EquipmentSlot | str) -> str | None:
        return self._equipped.pop(self._slot(slot), None)

    def contains(self, item_id: str) -> bool:
        return item_id in self._equipped.values()

    def snapshot(self) -> dict[str, str]:
        return {slot.value: self._equipped[slot] for slot in sorted(self._equipped, key=lambda value: value.value)}

    @staticmethod
    def _slot(value: EquipmentSlot | str) -> EquipmentSlot:
        try:
            return value if isinstance(value, EquipmentSlot) else EquipmentSlot(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Unknown equipment slot: {value}") from error

    @staticmethod
    def _item_id(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("item_id must be a non-empty string.")
        return value
