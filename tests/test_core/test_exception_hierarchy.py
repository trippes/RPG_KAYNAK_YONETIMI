"""The project exception root preserves standard-library catch behavior."""
import unittest

from core.errors import RPGError
from application.actor_system import ActorError, ActivityError
from application.content_pack import ContentDefinitionError
from application.gameplay_service import GameplayServiceError
from application.production_capacity import ProductionCapacityError
from application.save_storage import SaveStorageError
from character.persistence import CharacterPersistenceError
from core.persistence.contracts import PersistenceSchemaError
from core.persistence.file_adapter import PersistenceFileError
from quests.persistence import QuestPersistenceError
from resources.node import ResourceNodeError
from resources.persistence import GameplayFileError, GameplayPersistenceError
from resources.recipe import RecipeError
from resources.production import ResourceOperationError


class TestExceptionHierarchy(unittest.TestCase):
    def test_domain_and_application_errors_share_project_root(self):
        error_types = (
            ActorError, ActivityError, ContentDefinitionError, GameplayServiceError,
            ProductionCapacityError, SaveStorageError, CharacterPersistenceError,
            PersistenceSchemaError, PersistenceFileError, QuestPersistenceError,
            ResourceNodeError, GameplayFileError, GameplayPersistenceError,
            RecipeError, ResourceOperationError,
        )
        for error_type in error_types:
            with self.subTest(error_type=error_type.__name__):
                self.assertTrue(issubclass(error_type, RPGError))

    def test_standard_library_exception_compatibility_is_preserved(self):
        self.assertTrue(issubclass(ContentDefinitionError, ValueError))
        self.assertTrue(issubclass(ProductionCapacityError, ValueError))
        self.assertTrue(issubclass(GameplayServiceError, RuntimeError))
        self.assertTrue(issubclass(SaveStorageError, OSError))
        self.assertTrue(issubclass(PersistenceFileError, OSError))
        self.assertTrue(issubclass(GameplayFileError, OSError))


if __name__ == "__main__":
    unittest.main()
