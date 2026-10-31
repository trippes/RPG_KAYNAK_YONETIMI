import unittest

from core.application import EntityRepository, GameSession, WorldMembershipService
from core.domain import WorldDomainState
from core.foundation import WorldId
from core.entity import Entity, EntityType
from core.world import World, WorldManager


class TestWorldModel(unittest.TestCase):
    def test_world_domain_state_is_immutable(self):
        state = WorldDomainState(WorldId("world_1"), "Eldoria", 64, 64)

        for field, value in {
            "world_id": WorldId("world_2"),
            "name": "Changed",
            "width": 32,
            "height": 32,
        }.items():
            with self.subTest(field=field):
                with self.assertRaises((AttributeError, TypeError)):
                    setattr(state, field, value)

    def test_world_domain_state_validates_identity_name_and_bounds(self):
        invalid_values = (
            ("world_id", "world_1", "World", 10, 10, TypeError),
            ("name", WorldId("world_1"), " ", 10, 10, ValueError),
            ("width", WorldId("world_1"), "World", 0, 10, ValueError),
            ("height", WorldId("world_1"), "World", 10, -1, ValueError),
            ("width", WorldId("world_1"), "World", True, 10, TypeError),
            ("height", WorldId("world_1"), "World", 10, "10", TypeError),
        )

        for field, world_id, name, width, height, error in invalid_values:
            with self.subTest(field=field):
                with self.assertRaises(error):
                    WorldDomainState(world_id, name, width, height)

    def test_unbounded_world_keeps_existing_none_contract(self):
        state = WorldDomainState(WorldId("world_1"), "World", None, None)
        self.assertEqual(state.to_dict(), {
            "world_id": "world_1",
            "name": "World",
            "width": None,
            "height": None,
        })

    def test_world_domain_state_representation_is_deterministic(self):
        first = WorldDomainState(WorldId("world_1"), "World", 64, 64)
        second = WorldDomainState(WorldId("world_1"), "World", 64, 64)
        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.to_persistence(), second.to_persistence())

    def test_name_validation_preserves_existing_whitespace_behavior(self):
        state = WorldDomainState(WorldId("world_1"), "  Tamriel  ", 64, 64)
        self.assertEqual(state.name, "  Tamriel  ")

    def test_world_domain_state_round_trips_through_persistence(self):
        state = WorldDomainState(WorldId("world_1"), "World", None, 64)
        restored = WorldDomainState.from_persistence(state.to_persistence())
        self.assertEqual(restored, state)

    def test_persistence_allows_unknown_future_fields(self):
        data = {
            "world_id": "world_1",
            "name": "World",
            "width": 64,
            "height": 64,
            "future_field": {"ignored": True},
        }
        restored = WorldDomainState.from_persistence(data)
        self.assertEqual(restored.to_dict(), {
            "world_id": "world_1",
            "name": "World",
            "width": 64,
            "height": 64,
        })

    def test_world_domain_state_does_not_expose_runtime_state(self):
        state = WorldDomainState(WorldId("world_1"), "World", 10, 10)
        for runtime_field in ("_entities", "clock", "scheduler", "event_queue", "event_transport"):
            self.assertFalse(hasattr(state, runtime_field))

    def test_world_domain_state_is_not_derived_from_runtime_projection(self):
        world = World("World", width=10, height=20)
        state_before = world.domain_state
        entity = Entity(EntityType.NPC, "Guard")
        world._compat_add_entity(entity)
        state_after = world.domain_state

        self.assertEqual(state_before, state_after)
        self.assertNotIn("entity", state_after.to_dict())

    def test_canonical_ownership_does_not_read_compatibility_projection(self):
        repository = EntityRepository()
        worlds = WorldManager()
        world = worlds.create("World")
        service = WorldMembershipService(repository, worlds)
        entity = Entity(EntityType.NPC, "Guard")
        repository.add(entity)

        world._compat_add_entity(entity)
        self.assertIsNone(service.world_id_for(entity.entity_id))
        self.assertFalse(service.is_member(entity.entity_id, world.world_id))

    def test_session_uses_repository_and_membership_as_authoritative_sources(self):
        session = GameSession()
        world = session.worlds.create("World")
        entity = Entity(EntityType.NPC, "Guard")

        session.add_entity(entity, world.world_id)

        self.assertIs(session.entities.get(entity.entity_id), entity)
        self.assertEqual(session.membership.world_id_for(entity.entity_id), world.world_id)
        self.assertEqual(entity.world_id, world.world_id)


if __name__ == "__main__":
    unittest.main()
