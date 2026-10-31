import unittest
from pathlib import Path

from core.application import GameSession
from core.compatibility import usage_report
from core.domain import WorldDomainState
from core.domain.spatial import Position as CanonicalPosition
from core.entity import Entity, EntityType
from core.foundation import WorldId
from core.simulation import CanonicalEventTransport
from core.world import World


class TestWorldRuntimeSeparation(unittest.TestCase):
    def setUp(self):
        World._id_generator.reset()
        Entity._id_generator.reset()

    def test_world_exposes_runtime_free_domain_contract(self):
        world = World("Domain", width=10, height=20)
        state = world.domain_state
        self.assertIsInstance(state, WorldDomainState)
        self.assertEqual(state.world_id, WorldId(world.world_id))
        self.assertEqual(state.to_dict()["width"], 10)
        self.assertFalse(hasattr(world, "canonical_scheduler"))
        self.assertFalse(hasattr(world, "event_transport"))

    def test_session_owns_canonical_world_runtime_services(self):
        session = GameSession()
        self.assertIs(session.world_runtime.simulation, session.simulation)
        self.assertIsInstance(session.world_runtime.event_transport, CanonicalEventTransport)
        self.assertIs(session.world_runtime.canonical_scheduler, session.simulation.actions.scheduler)

    def test_membership_service_writes_compatibility_projection(self):
        session = GameSession()
        world = session.worlds.create("World")
        entity = Entity(EntityType.KARAKTER, "Guard")
        session.add_entity(entity, world.world_id)
        self.assertEqual(session.membership.world_id_for(entity.entity_id), world.world_id)
        self.assertEqual(entity.world_id, world.world_id)
        self.assertTrue(world.has_entity(entity.entity_id))

    def test_world_event_routing_uses_application_boundary(self):
        session = GameSession()
        world = session.worlds.create("World")
        world.emit_event("world.changed")
        routed = session.dispatch_world_events(world)
        self.assertEqual(len(routed), 1)
        self.assertEqual(session.simulation.event_transport.count(), 1)

    def test_canonical_position_is_accepted_for_world_queries(self):
        session = GameSession()
        world = session.worlds.create("World", width=10, height=10)
        entity = Entity(EntityType.KARAKTER, "Guard")
        session.add_entity(entity, world.world_id)
        entity.position.x = 3
        entity.position.y = 4
        found = world.get_entities_by_position(CanonicalPosition(3, 4))
        self.assertEqual(found, [entity])

    def test_position_remains_bounds_independent(self):
        position = CanonicalPosition(1000, 1000)
        self.assertEqual(position.to_dict(), {"x": 1000, "y": 1000})

    def test_migration_dashboard_shows_reduced_world_id_usage(self):
        root = Path(__file__).parents[2]
        report = usage_report(root)
        row = next(item for item in report if item.legacy_name == "Entity.world_id")
        self.assertLess(row.static_usage_count, 14)


if __name__ == "__main__":
    unittest.main()
