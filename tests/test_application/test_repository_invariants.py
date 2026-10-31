import unittest

from core.application import EntityRepository, GameSession
from core.entity import Entity, EntityType


class TestRepositoryInvariants(unittest.TestCase):
    def test_owned_entity_cannot_bypass_membership_service(self):
        session = GameSession()
        world = session.worlds.create("Main")
        entity = Entity(EntityType.KARAKTER, "Arin")
        session.add_entity(entity, world.world_id)
        with self.assertRaises(RuntimeError):
            session.entities.remove(entity.entity_id)

    def test_unowned_entity_can_be_removed_directly(self):
        repository = EntityRepository()
        entity = Entity(EntityType.KARAKTER, "Arin")
        repository.add(entity)
        self.assertIs(repository.remove(entity.entity_id), entity)
