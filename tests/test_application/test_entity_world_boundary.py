import unittest

from core.application import EntityRepository, GameSession, WorldMembershipService
from core.entity import Entity, EntityType
from core.foundation import EntityId, WorldId
from core.persistence import (
    CanonicalSessionState,
    MembershipRecord,
    RestoreContract,
    RestoreValidationError,
    WorldMembershipState,
)
from core.world import World, WorldManager


class TestEntityWorldBoundary(unittest.TestCase):
    def setUp(self):
        World._id_generator.reset()
        Entity._id_generator.reset()

    def test_entity_can_exist_without_membership(self):
        session = GameSession()
        entity = Entity(EntityType.NPC, "Unassigned")
        session.add_entity(entity)

        self.assertIs(session.entities.get(entity.entity_id), entity)
        self.assertIsNone(session.membership.world_id_for(entity.entity_id))
        self.assertIsNone(entity.world_id)

    def test_membership_rejects_unknown_entity_and_world(self):
        repository = EntityRepository()
        worlds = WorldManager()
        service = WorldMembershipService(repository, worlds)

        with self.assertRaises(KeyError):
            service.add(EntityId("missing"), WorldId("missing_world"))

        world = worlds.create("World", world_id="world_a")
        entity = Entity(EntityType.NPC, "Guard")
        repository.add(entity)
        with self.assertRaises(KeyError):
            service.add(EntityId(entity.entity_id), WorldId("missing_world"))
        self.assertIs(worlds.get(WorldId("world_a")), world)

    def test_canonical_membership_ignores_stale_entity_world_projection(self):
        session = GameSession()
        first = session.worlds.create("First", world_id="world_a")
        second = session.worlds.create("Second", world_id="world_b")
        entity = Entity(EntityType.NPC, "Guard")
        session.entities.add(entity)
        entity.assign_world("legacy_world")

        session.membership.add(EntityId(entity.entity_id), WorldId(first.world_id))

        self.assertEqual(session.membership.world_id_for(entity.entity_id), "world_a")
        self.assertTrue(first.has_entity(entity.entity_id))
        self.assertFalse(second.has_entity(entity.entity_id))
        self.assertEqual(entity.world_id, first.world_id)

    def test_membership_rejects_second_world_without_dual_membership(self):
        session = GameSession()
        first = session.worlds.create("First", world_id="world_a")
        second = session.worlds.create("Second", world_id="world_b")
        entity = Entity(EntityType.NPC, "Guard")
        session.add_entity(entity, first.world_id)

        with self.assertRaises(ValueError):
            session.membership.add(entity.entity_id, second.world_id)

        self.assertEqual(session.membership.world_id_for(entity.entity_id), first.world_id)
        self.assertTrue(first.has_entity(entity.entity_id))
        self.assertFalse(second.has_entity(entity.entity_id))

    def test_canonical_persistence_ignores_legacy_projection_divergence(self):
        session = GameSession()
        world = session.worlds.create("World", world_id="world_a")
        entity = Entity(EntityType.NPC, "Guard", entity_id="entity_a")
        session.add_entity(entity, world.world_id)
        world._entities.clear()
        entity.remove_from_world()

        state = CanonicalSessionState.from_session(session)
        self.assertEqual(state.entities.records[0].entity_id.value, "entity_a")
        self.assertEqual(state.memberships.records[0].world_id.value, "world_a")
        RestoreContract.prepare(state)

    def test_invalid_membership_cannot_reach_activation(self):
        session = GameSession()
        world = session.worlds.create("World", world_id="world_a")
        entity = Entity(EntityType.NPC, "Guard", entity_id="entity_a")
        session.entities.add(entity)
        state = CanonicalSessionState.from_session(session)
        invalid = CanonicalSessionState(
            worlds=state.worlds,
            entities=state.entities,
            memberships=WorldMembershipState((MembershipRecord(EntityId("entity_a"), WorldId("missing")),)),
            active_world_id=WorldId(world.world_id),
            simulation_tick=state.simulation_tick,
        )

        with self.assertRaises(RestoreValidationError):
            RestoreContract.prepare(invalid)


if __name__ == "__main__":
    unittest.main()
