"""Versioned JSON-ready persistence for characters."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .attributes import Attribute, Attributes
from .abilities import Ability
from .character import Character
from .class_ import CharacterClass
from .progression import Progression
from .race import Race
from .skills import Skills

CHARACTER_SCHEMA = "rpg-characters"
CHARACTER_SCHEMA_VERSION = 1


class CharacterPersistenceError(ValueError):
    pass


@dataclass(frozen=True)
class CharacterSnapshot:
    characters: tuple[dict[str, object], ...]

    @classmethod
    def from_characters(cls, characters: Mapping[str, Character] | list[Character] | tuple[Character, ...]):
        values = characters.values() if isinstance(characters, Mapping) else characters
        result = []
        for character in values:
            if not isinstance(character, Character):
                raise TypeError("characters must contain Character instances.")
            data = character.to_dict()
            encode_ability = lambda ability: {"ability_id": ability.ability_id, "name": ability.name, "description": ability.description}
            data["race"] = {"race_id": character.race.race_id, "name": character.race.name, "attribute_modifiers": {str(k.value): v for k, v in character.race.attribute_modifiers.items()}, "abilities": [encode_ability(a) for a in character.race.abilities]}
            data["class"] = {"class_id": character.character_class.class_id, "name": character.character_class.name, "hit_points": character.character_class.hit_points, "skill_ranks": dict(character.character_class.skill_ranks), "abilities": [encode_ability(a) for a in character.character_class.abilities]}
            result.append(data)
        return cls(tuple(sorted(result, key=lambda item: item["character_id"])))

    def to_dict(self) -> dict[str, object]:
        return {"schema": CHARACTER_SCHEMA, "schema_version": CHARACTER_SCHEMA_VERSION, "characters": [dict(item) for item in self.characters]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CharacterSnapshot":
        if not isinstance(data, Mapping) or data.get("schema") != CHARACTER_SCHEMA or data.get("schema_version") != CHARACTER_SCHEMA_VERSION:
            raise CharacterPersistenceError("Unsupported character persistence schema.")
        records = data.get("characters")
        if not isinstance(records, list) or any(not isinstance(item, Mapping) for item in records):
            raise CharacterPersistenceError("characters must be a list of objects.")
        ids = [item.get("character_id") for item in records]
        if any(not isinstance(item, str) or not item.strip() for item in ids) or len(ids) != len(set(ids)):
            raise CharacterPersistenceError("Character IDs must be unique non-empty strings.")
        return cls(tuple(sorted((dict(item) for item in records), key=lambda item: item["character_id"])))

    def restore(self) -> dict[str, Character]:
        restored = {}
        for item in self.characters:
            try:
                race_data, class_data = item["race"], item["class"]
                decode_ability = lambda item: Ability(item["ability_id"], item["name"], item.get("description", ""))
                race = Race(race_data["race_id"], race_data["name"], race_data.get("attribute_modifiers", {}), tuple(decode_ability(a) for a in race_data.get("abilities", [])))
                character_class = CharacterClass(class_data["class_id"], class_data["name"], class_data["hit_points"], class_data.get("skill_ranks", {}), tuple(decode_ability(a) for a in class_data.get("abilities", [])))
                effective = Attributes(item.get("attributes", {}))
                base = {attribute: effective.get(attribute) - race.attribute_modifiers.get(attribute, 0) for attribute in Attribute}
                character = Character(item["character_id"], item["name"], race, character_class, Attributes(base), Skills(item.get("skills", {})), Progression(item.get("level", 1), item.get("experience", 0), item.get("unspent_points", 0)), item.get("actor_id"), item.get("current_hit_points"))
            except (KeyError, TypeError, ValueError) as error:
                raise CharacterPersistenceError("Invalid character record.") from error
            restored[character.character_id] = character
        return restored

