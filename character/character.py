"""Aggregate character entity."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .abilities import Ability
from .attributes import Attributes
from .skills import Skills
from .race import Race
from .class_ import CharacterClass
from .progression import Progression
from .equipment import EquipmentLoadout, ItemDefinition


@dataclass
class Character:
    character_id: str
    name: str
    race: Race
    character_class: CharacterClass
    attributes: Attributes = field(default_factory=Attributes)
    skills: Skills = field(default_factory=Skills)
    progression: Progression = field(default_factory=Progression)
    actor_id: str | None = None
    current_hit_points: int | None = None
    age: int = 20
    equipment: EquipmentLoadout = field(default_factory=EquipmentLoadout)

    def __post_init__(self):
        if not self.character_id.strip() or not self.name.strip():
            raise ValueError("Character id and name are required.")
        if not isinstance(self.race, Race) or not isinstance(self.character_class, CharacterClass):
            raise TypeError("Character requires a Race and CharacterClass.")
        if not isinstance(self.equipment, EquipmentLoadout):
            raise TypeError("equipment must be EquipmentLoadout.")
        if isinstance(self.age, bool) or not isinstance(self.age, int) or not 13 <= self.age <= 120:
            raise ValueError("Character age must be between 13 and 120.")
        self.attributes = self.attributes.with_modifiers(self.race.attribute_modifiers)
        self.skills = self.skills.with_ranks(self.character_class.skill_ranks)
        if self.current_hit_points is None:
            self.current_hit_points = self.max_hit_points
        if not 0 <= self.current_hit_points <= self.max_hit_points:
            raise ValueError("current_hit_points is out of range.")

    @property
    def max_hit_points(self) -> int:
        return self.character_class.hit_points + self.attributes.get("constitution") + self._equipment_bonus("max_hit_points")

    @property
    def attack_bonus(self) -> int:
        return self.attributes.modifier("strength") + self._equipment_bonus("attack")

    @property
    def defense_bonus(self) -> int:
        return self.attributes.modifier("dexterity") + self._equipment_bonus("defense")

    @property
    def initiative_bonus(self) -> int:
        return self.attributes.modifier("dexterity")

    @property
    def weapon_damage(self) -> int:
        return self._equipment_bonus("damage")

    def equip(self, item: ItemDefinition) -> str | None:
        return self.equipment.equip(item)

    def unequip(self, slot) -> str | None:
        return self.equipment.unequip(slot)

    def _equipment_bonus(self, field: str) -> int:
        return sum(
            getattr(item, field)
            for item in getattr(self, "_item_catalog", {}).values()
            if self.equipment.contains(item.item_id)
        )

    def bind_item_catalog(self, catalog) -> None:
        self._item_catalog = dict(catalog)

    @property
    def abilities(self) -> tuple[Ability, ...]:
        return self.race.abilities + self.character_class.abilities

    def bind_actor(self, actor_id: str) -> None:
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id must be a non-empty string.")
        if self.actor_id is not None and self.actor_id != actor_id:
            raise ValueError("Character is already bound to another actor.")
        self.actor_id = actor_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id, "name": self.name,
            "race_id": self.race.race_id, "class_id": self.character_class.class_id,
            "attributes": self.attributes.to_dict(), "skills": self.skills.to_dict(),
            "level": self.progression.level, "experience": self.progression.experience,
            "unspent_points": self.progression.unspent_points,
            "actor_id": self.actor_id, "current_hit_points": self.current_hit_points,
            "age": self.age,
            "equipment": self.equipment.snapshot(),
        }
