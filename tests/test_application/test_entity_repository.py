import unittest

from core.application import EntityRepository
from core.entity import Entity, EntityType


class TestEntityRepository(unittest.TestCase):
    def make_entity(self, name="Arin"):
        return Entity(EntityType.KARAKTER, name)

    def test_add_get_remove_and_deterministic_iteration(self):
        repository = EntityRepository()
        first = self.make_entity("Arin")
        second = self.make_entity("Bora")
        repository.add(first)
        repository.add(second)
        self.assertIs(repository.get(first.entity_id), first)
        self.assertEqual(repository.get_all(), (first, second))
        self.assertIs(repository.remove(first.entity_id), first)
        self.assertEqual(repository.count(), 1)

    def test_duplicate_and_missing_entities_are_rejected(self):
        repository = EntityRepository()
        entity = self.make_entity()
        repository.add(entity)
        with self.assertRaises(ValueError):
            repository.add(entity)
        with self.assertRaises(KeyError):
            repository.remove("missing")

    def test_internal_mapping_is_not_public(self):
        repository = EntityRepository()
        self.assertFalse(hasattr(repository, "entities"))
        self.assertIsInstance(repository.get_all(), tuple)
