import unittest

from core.application import GameSession
from core.application.entity_repository import EntityRepository
from core.entity import Entity, EntityType
from core.persistence import CanonicalSessionState, RestoreContract
from core.time import Tick
from core.world.world_manager import WorldManager


class TestGameSession(unittest.TestCase):
    def test_initializes_runtime_services(self):
        session = GameSession()
        self.assertIsNotNone(session.worlds)
        self.assertIsNotNone(session.entities)
        self.assertIsNotNone(session.membership)
        self.assertIsNone(session.active_world())

    def test_empty_injected_registries_are_preserved(self):
        class FalsyWorldManager(WorldManager):
            def __bool__(self):
                return False

        worlds = FalsyWorldManager()
        entities = EntityRepository()
        session = GameSession(world_registry=worlds, entity_repository=entities)
        self.assertIs(session.worlds, worlds)
        self.assertIs(session.entities, entities)

    def test_ownership_operations_use_membership_service(self):
        session = GameSession()
        world = session.worlds.create("Main")
        entity = Entity(EntityType.KARAKTER, "Arin")
        session.add_entity(entity, world.world_id)
        self.assertIs(session.entities.get(entity.entity_id), entity)
        self.assertTrue(session.membership.is_member(entity.entity_id, world.world_id))
        session.remove_entity(entity.entity_id)
        self.assertIsNone(session.entities.get(entity.entity_id))

    def test_valid_restore_replaces_session_runtime(self):
        source = GameSession()
        first = source.worlds.create("First", world_id="world_a")
        second = source.worlds.create("Second", world_id="world_b")
        source.worlds.set_active(second.world_id)
        first_entity = Entity(EntityType.NPC, "Guard", entity_id="entity_a")
        second_entity = Entity(EntityType.KARAKTER, "Hero", entity_id="entity_b")
        source.add_entity(first_entity, first.world_id)
        source.add_entity(second_entity, second.world_id)
        source.simulation.advance_to(7)
        plan = RestoreContract.prepare(CanonicalSessionState.from_session(source))

        target = GameSession()
        target.activate_restore(plan)

        self.assertEqual([world.world_id for world in target.worlds.get_all()], ["world_a", "world_b"])
        self.assertIsNotNone(target.entities.get("entity_a"))
        self.assertIsNotNone(target.entities.get("entity_b"))
        self.assertEqual(target.membership.world_id_for("entity_a"), "world_a")
        self.assertEqual(target.membership.world_id_for("entity_b"), "world_b")
        self.assertEqual(target.worlds.get_active_id(), "world_b")
        self.assertEqual(target.simulation.current_tick.value, 7)

    def test_restore_preserves_runtime_observers(self):
        source = GameSession()
        source.worlds.create("Main", world_id="world_a")
        plan = RestoreContract.prepare(CanonicalSessionState.from_session(source))

        target = GameSession()
        ticks = []

        class Consumer:
            def consume(self, event):
                pass

        class Listener:
            def advance_to(self, tick):
                ticks.append(tick)

        target.simulation.dispatcher.register(Consumer())
        target.simulation.register_tick_listener(Listener())
        target.activate_restore(plan)

        self.assertEqual(target.simulation.dispatcher.consumer_count(), 1)
        target.simulation.advance_to(Tick(1))
        self.assertEqual(ticks, [Tick(1)])
