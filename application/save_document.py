"""Application-level envelope for one Core plus gameplay save document."""

from dataclasses import dataclass
from typing import Mapping

from core.persistence import PersistenceDocument
from core.persistence.contracts import (
    PersistenceSchemaError,
    UnsupportedPersistenceSchemaError,
)
from resources.persistence import GameplayPersistenceError, GameplaySnapshot
from .production_persistence import ProductionSnapshot
from .actor_persistence import ActorSnapshot
from character import CharacterSnapshot
from quests import QuestSnapshot
from economy import EconomySnapshot
from .extended_persistence import SocialSnapshot, CombatSnapshot
from .migrations import migrate_save_data


SAVE_SCHEMA = "rpg-game-save"
SAVE_SCHEMA_VERSION = 1


class SaveDocumentError(PersistenceSchemaError):
    """Invalid application-level save document."""


class UnsupportedSaveSchemaError(UnsupportedPersistenceSchemaError, SaveDocumentError):
    """Unsupported application-level save schema version."""


@dataclass(frozen=True)
class GameSaveDocument:
    """Immutable outer document retaining the existing inner contracts."""

    core: PersistenceDocument
    gameplay: GameplaySnapshot
    schema: str = SAVE_SCHEMA
    schema_version: int = SAVE_SCHEMA_VERSION
    production: ProductionSnapshot | None = None
    actors: ActorSnapshot | None = None
    characters: CharacterSnapshot | None = None
    quests: QuestSnapshot | None = None
    economy: EconomySnapshot | None = None
    social: SocialSnapshot | None = None
    combat: CombatSnapshot | None = None

    def __post_init__(self) -> None:
        if self.schema != SAVE_SCHEMA:
            raise SaveDocumentError("Unknown game save schema identifier.")
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version < 1
        ):
            raise SaveDocumentError("save schema_version must be a positive integer.")
        if self.schema_version > SAVE_SCHEMA_VERSION:
            raise UnsupportedSaveSchemaError(
                "Future game save schema requires migration."
            )
        if not isinstance(self.core, PersistenceDocument):
            raise TypeError("core must be PersistenceDocument.")
        if not isinstance(self.gameplay, GameplaySnapshot):
            raise TypeError("gameplay must be GameplaySnapshot.")
        if self.production is not None and not isinstance(self.production, ProductionSnapshot):
            raise TypeError("production must be ProductionSnapshot or None.")
        if self.actors is not None and not isinstance(self.actors, ActorSnapshot):
            raise TypeError("actors must be ActorSnapshot or None.")
        if self.characters is not None and not isinstance(self.characters, CharacterSnapshot):
            raise TypeError("characters must be CharacterSnapshot or None.")
        if self.quests is not None and not isinstance(self.quests, QuestSnapshot):
            raise TypeError("quests must be QuestSnapshot or None.")
        if self.economy is not None and not isinstance(self.economy, EconomySnapshot):
            raise TypeError("economy must be EconomySnapshot or None.")
        if self.social is not None and not isinstance(self.social, SocialSnapshot): raise TypeError("social must be SocialSnapshot or None.")
        if self.combat is not None and not isinstance(self.combat, CombatSnapshot): raise TypeError("combat must be CombatSnapshot or None.")
        if self.core.simulation_tick.value != self.gameplay.simulation_tick:
            raise SaveDocumentError("Core/gameplay simulation tick mismatch.")

    def to_dict(self) -> dict[str, object]:
        result = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "core": self.core.to_dict(),
            "gameplay": self.gameplay.to_dict(),
        }
        if self.production is not None:
            result["production"] = self.production.to_dict()
        if self.actors is not None:
            result["actors"] = self.actors.to_dict()
        if self.characters is not None:
            result["characters"] = self.characters.to_dict()
        if self.quests is not None:
            result["quests"] = self.quests.to_dict()
        if self.economy is not None:
            result["economy"] = self.economy.to_dict()
        if self.social is not None: result["social"] = self.social.to_dict()
        if self.combat is not None: result["combat"] = self.combat.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "GameSaveDocument":
        if not isinstance(data, Mapping):
            raise SaveDocumentError("Game save document must be an object.")
        data = migrate_save_data(dict(data))

        required = {"schema", "schema_version", "core", "gameplay"}
        missing = required - set(data)
        if missing:
            raise SaveDocumentError(
                f"Game save document is missing required fields: {sorted(missing)}"
            )
        unexpected = set(data) - required - {"production", "actors", "characters", "quests", "economy", "social", "combat"}
        if unexpected:
            raise SaveDocumentError(
                f"Game save document contains unknown fields: {sorted(unexpected)}"
            )
        if data["schema"] != SAVE_SCHEMA:
            raise SaveDocumentError("Unknown game save schema identifier.")
        version = data["schema_version"]
        if isinstance(version, bool) or not isinstance(version, int):
            raise SaveDocumentError("save schema_version must be an integer.")
        if version != SAVE_SCHEMA_VERSION:
            raise UnsupportedSaveSchemaError(
                f"Game save schema version {version} requires a migration boundary."
            )
        if not isinstance(data["core"], Mapping):
            raise SaveDocumentError("core must be an object.")
        if not isinstance(data["gameplay"], Mapping):
            raise SaveDocumentError("gameplay must be an object.")

        core = PersistenceDocument.from_dict(data["core"])
        gameplay = GameplaySnapshot.from_dict(data["gameplay"])
        production = None
        if "production" in data:
            if not isinstance(data["production"], Mapping):
                raise SaveDocumentError("production must be an object.")
            production = ProductionSnapshot.from_dict(data["production"])
        actors = None
        if "actors" in data:
            if not isinstance(data["actors"], Mapping):
                raise SaveDocumentError("actors must be an object.")
            actors = ActorSnapshot.from_dict(data["actors"])
        characters = None
        if "characters" in data:
            if not isinstance(data["characters"], Mapping):
                raise SaveDocumentError("characters must be an object.")
            characters = CharacterSnapshot.from_dict(data["characters"])
        quests = None
        if "quests" in data:
            if not isinstance(data["quests"], Mapping): raise SaveDocumentError("quests must be an object.")
            quests = QuestSnapshot.from_dict(data["quests"])
        economy = None
        if "economy" in data:
            if not isinstance(data["economy"], Mapping): raise SaveDocumentError("economy must be an object.")
            economy = EconomySnapshot.from_dict(data["economy"])
        social = SocialSnapshot.from_dict(data["social"]) if "social" in data else None
        combat = CombatSnapshot.from_dict(data["combat"]) if "combat" in data else None
        return cls(
            core=core,
            gameplay=gameplay,
            production=production,
            actors=actors,
            characters=characters,
            quests=quests,
            economy=economy,
            social=social,
            combat=combat,
            schema=data["schema"],
            schema_version=version,
        )
