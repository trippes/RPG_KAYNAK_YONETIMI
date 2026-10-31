"""Factories for the basic character creation flow."""
from __future__ import annotations
from collections.abc import Mapping
from .attributes import Attributes
from .character import Character
from .class_ import CharacterClass
from .progression import Progression
from .race import Race
from .skills import Skills


class CharacterFactory:
    def __init__(self, races: Mapping[str, Race] | None = None, classes: Mapping[str, CharacterClass] | None = None):
        self.races = dict(races or {})
        self.classes = dict(classes or {})

    def register_race(self, race: Race) -> None:
        self.races[race.race_id] = race

    def register_class(self, character_class: CharacterClass) -> None:
        self.classes[character_class.class_id] = character_class

    def create(self, character_id: str, name: str, race_id: str, class_id: str, *, actor_id: str | None = None, attributes=None, skills=None) -> Character:
        try:
            race, character_class = self.races[race_id], self.classes[class_id]
        except KeyError as error:
            raise ValueError(f"Unknown race or class: {error.args[0]}") from error
        return Character(character_id, name, race, character_class, Attributes(attributes or {}), Skills(skills or {}), Progression(), actor_id)

    def create_basic(self, character_id: str, name: str, race_id: str, class_id: str, actor_id: str | None = None) -> Character:
        return self.create(character_id, name, race_id, class_id, actor_id=actor_id)

