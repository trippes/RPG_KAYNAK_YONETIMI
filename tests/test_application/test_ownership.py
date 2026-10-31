import unittest

from core.application import EntityRepository, WorldMembershipService
from core.entity import Entity, EntityType
from core.world import World, WorldManager


class TestWorldMembershipService(unittest.TestCase):
    def setUp(self):
        self.repository = EntityRepository()
        self.worlds = WorldManager()
        self.first_world = self.worlds.create("First")
        self.second_world = self.worlds.create("Second")
        self.service = WorldMembershipService(self.repository, self.worlds)
        self.entity = Entity(EntityType.KARAKTER, "Arin")
        self.repository.add(self.entity)

    def test_add_creates_single_canonical_membership_and_projection(self):
        self.service.add(self.entity.entity_id, self.first_world.world_id)
        self.assertEqual(
            self.service.world_id_for(self.entity.entity_id),
            self.first_world.world_id,
        )
        self.assertTrue(self.service.is_member(
            self.entity.entity_id, self.first_world.world_id
        ))
        self.assertEqual(self.entity.world_id, self.first_world.world_id)

    def test_duplicate_and_cross_world_attach_are_rejected(self):
        self.service.add(self.entity.entity_id, self.first_world.world_id)
        with self.assertRaises(ValueError):
            self.service.add(self.entity.entity_id, self.first_world.world_id)
        with self.assertRaises(ValueError):
            self.service.add(self.entity.entity_id, self.second_world.world_id)
        self.assertEqual(
            self.service.world_id_for(self.entity.entity_id),
            self.first_world.world_id,
        )

    def test_remove_clears_membership_and_projection(self):
        self.service.add(self.entity.entity_id, self.first_world.world_id)
        removed = self.service.remove(self.entity.entity_id)
        self.assertIs(removed, self.entity)
        self.assertIsNone(self.service.world_id_for(self.entity.entity_id))
        self.assertIsNone(self.entity.world_id)
        self.assertFalse(self.first_world.has_entity(self.entity.entity_id))

    def test_wrong_world_remove_is_atomic(self):
        self.service.add(self.entity.entity_id, self.first_world.world_id)
        with self.assertRaises(ValueError):
            self.service.remove(self.entity.entity_id, self.second_world.world_id)
        self.assertTrue(self.first_world.has_entity(self.entity.entity_id))
        self.assertEqual(
            self.service.world_id_for(self.entity.entity_id),
            self.first_world.world_id,
        )

    def test_transfer_updates_both_worlds_atomically(self):
        self.service.add(self.entity.entity_id, self.first_world.world_id)
        self.service.transfer(self.entity.entity_id, self.second_world.world_id)
        self.assertFalse(self.first_world.has_entity(self.entity.entity_id))
        self.assertTrue(self.second_world.has_entity(self.entity.entity_id))
        self.assertEqual(self.entity.world_id, self.second_world.world_id)
        self.assertEqual(
            self.service.world_id_for(self.entity.entity_id),
            self.second_world.world_id,
        )

    def test_missing_entity_or_world_does_not_change_state(self):
        with self.assertRaises(KeyError):
            self.service.add("missing", self.first_world.world_id)
        with self.assertRaises(KeyError):
            self.service.add(self.entity.entity_id, "missing")
        self.assertEqual(self.service.entity_ids_for(self.first_world.world_id), ())
