import unittest

from core.application import GameSession
from core.domain.spatial import Position
from core.entity import Entity, EntityType
from core.foundation import ActionId
from core.persistence import CanonicalSessionState, RestoreContract
from core.simulation import ActionState, SimulationEvent, CanonicalEventType


class TestCore20Integration(unittest.TestCase):
    def test_game_session_repository_membership_and_projection(self):
        session = GameSession()
        world = session.worlds.create("Main", width=20, height=20)
        entity = Entity(EntityType.KARAKTER, "Arin")
        entity.position.x = 3
        entity.position.y = 4

        session.add_entity(entity, world.world_id)

        self.assertIs(session.entities.get(entity.entity_id), entity)
        self.assertTrue(session.membership.is_member(entity.entity_id, world.world_id))
        self.assertEqual(world.get_entities_by_position(Position(3, 4)), [entity])

    def test_simulation_action_scheduler_and_event_transport(self):
        session = GameSession()
        action = session.simulation.actions.create(
            owner_id=ActionId("actor_1"), duration=2
        )
        session.simulation.actions.schedule(action.action_id, 1)
        events = session.simulation.advance_to(3)

        self.assertEqual(action.state, ActionState.COMPLETED)
        self.assertEqual(action.completed_tick.value, 3)
        self.assertEqual(
            [event.event_type for event in events[-2:]],
            [CanonicalEventType.ACTION_STARTED, CanonicalEventType.ACTION_COMPLETED],
        )
        self.assertEqual(session.simulation.event_transport.count(), len(events))

    def test_world_event_routes_through_canonical_transport_and_dispatcher(self):
        session = GameSession()
        world = session.worlds.create("Main")
        session.worlds.set_active(world.world_id)
        world.emit_event("world.changed", {"value": 1})
        routed = session.dispatch_world_events(world)

        received = []

        class Consumer:
            def consume(self, event: SimulationEvent):
                received.append(event)

        session.simulation.dispatcher.register(Consumer())
        session.simulation.dispatcher.dispatch_pending()

        self.assertEqual(len(routed), 1)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].event_type, "world.changed")

    def test_canonical_session_state_flows_into_restore_plan(self):
        session = GameSession()
        world = session.worlds.create("Main")
        session.worlds.set_active(world.world_id)
        entity = Entity(EntityType.NPC, "Guard")
        session.add_entity(entity, world.world_id)
        canonical = CanonicalSessionState.from_session(session)

        plan = RestoreContract.prepare(canonical)

        self.assertEqual(plan.active_world_id.value, world.world_id)
        self.assertEqual(plan.entities.records[0].entity_id.value, entity.entity_id)
        self.assertEqual(plan.memberships.records[0].world_id.value, world.world_id)

    def test_past_action_schedule_does_not_partially_mutate_action(self):
        session = GameSession()
        session.simulation.advance_to(4)
        action = session.simulation.actions.create(ActionId("actor_2"), 1)

        with self.assertRaises(ValueError):
            session.simulation.actions.schedule(action.action_id, 3)

        self.assertEqual(action.state, ActionState.CREATED)
        self.assertIsNone(action.scheduled_tick)


if __name__ == "__main__":
    unittest.main()
