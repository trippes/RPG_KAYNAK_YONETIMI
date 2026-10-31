import unittest

from core.application import GameSession
from core.entity import Entity, EntityType
from core.foundation import WorldId
from core.persistence import CanonicalSessionState, RestoreContract, RestoreValidationError
from core.world import World, WorldManager


class TestWorldRegistryContract(unittest.TestCase):
    def setUp(self):
        World._id_generator.reset()

    def test_empty_registry_is_valid(self):
        manager = WorldManager()
        self.assertEqual(manager.get_all(), [])
        self.assertIsNone(manager.get_active())
        self.assertIsNone(manager.get_active_id())

    def test_registry_accepts_canonical_world_id_lookup(self):
        manager = WorldManager()
        world = manager.create("Alpha", world_id="alpha")

        self.assertIs(manager.get(WorldId("alpha")), world)
        self.assertTrue(manager.exists(WorldId("alpha")))
        manager.set_active(WorldId("alpha"))
        self.assertIs(manager.get_active(), world)

    def test_registry_enumeration_is_world_id_sorted(self):
        manager = WorldManager()
        manager.create("Zulu", world_id="zulu")
        manager.create("Alpha", world_id="alpha")
        manager.create("Middle", world_id="middle")

        self.assertEqual(
            [world.world_id for world in manager.get_all()],
            ["alpha", "middle", "zulu"],
        )

    def test_duplicate_world_id_is_rejected_without_overwrite(self):
        manager = WorldManager()
        first = manager.create("First", world_id="same")
        second = World("Second", world_id="same")

        with self.assertRaises(ValueError):
            manager.add(second)

        self.assertIs(manager.get("same"), first)
        self.assertEqual(manager.count(), 1)

    def test_removing_active_world_clears_only_active_projection(self):
        manager = WorldManager()
        first = manager.create("First", world_id="first")
        second = manager.create("Second", world_id="second")
        manager.set_active(first.world_id)

        manager.remove(first.world_id)

        self.assertIsNone(manager.get_active())
        self.assertIsNone(manager.get_active_id())
        self.assertIs(manager.get("second"), second)

    def test_world_with_membership_cannot_be_removed_orphaning_entity(self):
        session = GameSession()
        world = session.worlds.create("World", world_id="world_a")
        entity = Entity(EntityType.NPC, "Guard")
        session.add_entity(entity, world.world_id)

        with self.assertRaises(ValueError):
            session.remove_world(WorldId("world_a"))

        self.assertIs(session.entities.get(entity.entity_id), entity)
        self.assertEqual(session.membership.world_id_for(entity.entity_id), "world_a")

    def test_active_world_switch_does_not_mutate_other_world_state(self):
        session = GameSession()
        first = session.worlds.create("First", world_id="first")
        second = session.worlds.create("Second", world_id="second")
        session.worlds.set_active(first.world_id)
        first_state = first.domain_state
        second_state = second.domain_state

        session.worlds.switch(WorldId("second"))

        self.assertEqual(first.domain_state, first_state)
        self.assertEqual(second.domain_state, second_state)
        self.assertEqual(session.simulation.current_tick.value, 0)

    def test_multiple_world_session_persistence_is_sorted_and_active_is_session_state(self):
        session = GameSession()
        session.worlds.create("Zulu", world_id="zulu", width=20, height=20)
        session.worlds.create("Alpha", world_id="alpha", width=10, height=10)
        session.worlds.set_active(WorldId("zulu"))

        state = CanonicalSessionState.from_session(session)

        self.assertEqual(
            [world["world_id"] for world in state.worlds],
            ["alpha", "zulu"],
        )
        self.assertEqual(state.active_world_id, WorldId("zulu"))
        self.assertNotIn("active", state.worlds[0])

    def test_multiple_world_restore_and_invalid_active_world(self):
        session = GameSession()
        session.worlds.create("Zulu", world_id="zulu")
        session.worlds.create("Alpha", world_id="alpha")
        session.worlds.set_active("alpha")
        state = CanonicalSessionState.from_session(session)

        plan = RestoreContract.prepare(state)
        self.assertEqual([world.world_id.value for world in plan.worlds], ["alpha", "zulu"])

        invalid = CanonicalSessionState(
            worlds=state.worlds,
            entities=state.entities,
            memberships=state.memberships,
            active_world_id=WorldId("missing"),
            simulation_tick=state.simulation_tick,
        )
        with self.assertRaises(RestoreValidationError):
            RestoreContract.prepare(invalid)


if __name__ == "__main__":
    unittest.main()
