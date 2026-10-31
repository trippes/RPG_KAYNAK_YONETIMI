import unittest

from core.events import Event, EventQueue
from core.foundation import EventId, EntityId
from core.simulation import (
    ActionProcessor,
    CanonicalEventTransport,
    CanonicalEventType,
    LegacyEventAdapter,
    SimulationEvent,
    SimulationRuntime,
)
from core.time import Tick
from core.world import World


def event(name, tick, payload=None):
    return SimulationEvent(name, Tick(tick), None, None, None, payload or {}, {})


class TestCanonicalEventTransport(unittest.TestCase):
    def test_queue_api_and_identity(self):
        transport = CanonicalEventTransport()
        self.assertTrue(transport.empty())
        queued = transport.enqueue(event("A", 2))
        self.assertEqual(transport.count(), 1)
        self.assertEqual(transport.peek(), queued)
        self.assertIs(transport.dequeue(), queued)
        self.assertTrue(transport.empty())

    def test_order_is_tick_then_insertion_sequence(self):
        transport = CanonicalEventTransport()
        transport.enqueue(event("late", 11))
        transport.enqueue(event("first", 10))
        transport.enqueue(event("second", 10))
        self.assertEqual([e.event_type for e in transport.drain()], ["first", "second", "late"])

    def test_identity_and_duplicate_policy(self):
        transport = CanonicalEventTransport()
        original = event("A", 0)
        identified = SimulationEvent("B", Tick(0), None, None, None, {}, {}, EventId("fixed"))
        queued = transport.enqueue(original)
        self.assertIsNotNone(queued.event_id)
        self.assertEqual(queued.insertion_sequence, 0)
        transport.enqueue(identified)
        with self.assertRaises(ValueError):
            transport.enqueue(identified)

    def test_payload_and_metadata_are_defensively_copied(self):
        payload = {"nested": {"value": 1}}
        transport = CanonicalEventTransport()
        queued = transport.enqueue(event("A", 0, payload))
        payload["nested"]["value"] = 99
        self.assertEqual(queued.payload["nested"]["value"], 1)
        with self.assertRaises(TypeError):
            queued.payload["new"] = 2

    def test_action_processor_publishes_all_lifecycle_events(self):
        processor = ActionProcessor()
        action = processor.create(EntityId("entity_1"), Tick(1))
        processor.schedule(action.action_id, Tick(2))
        processor.advance_to(Tick(3))
        self.assertEqual(
            [event.event_type for event in processor.event_transport.drain()],
            [
                CanonicalEventType.ACTION_CREATED,
                CanonicalEventType.ACTION_SCHEDULED,
                CanonicalEventType.ACTION_STARTED,
                CanonicalEventType.ACTION_COMPLETED,
            ],
        )

    def test_failed_and_cancelled_events_are_transportable(self):
        processor = ActionProcessor()
        failed = processor.create(EntityId("e1"), 1)
        processor.schedule(failed.action_id, 0)
        processor.advance_to(0)
        processor.fail(failed.action_id, "bad input")
        cancelled = processor.create(EntityId("e2"), 1)
        processor.cancel(cancelled.action_id)
        self.assertEqual(
            [e.event_type for e in processor.event_transport.drain()],
            ["ActionCreated", "ActionScheduled", "ActionStarted", "ActionFailed", "ActionCreated", "ActionCancelled"],
        )

    def test_runtime_uses_the_same_transport(self):
        runtime = SimulationRuntime()
        action = runtime.actions.create(EntityId("e"), 0)
        runtime.actions.schedule(action.action_id, 0)
        runtime.advance_to(0)
        self.assertIs(runtime.events, runtime.actions.event_transport)
        self.assertEqual(runtime.events.count(), 4)

    def test_world_events_route_at_world_tick(self):
        world = World("transport-world", start_tick=4)
        world.emit_event("world.changed", {"value": 7})
        runtime = SimulationRuntime()
        routed = runtime.dispatch_world_events(world)
        self.assertEqual(len(routed), 1)
        self.assertEqual(routed[0].simulation_tick, Tick(4))
        self.assertEqual(runtime.events.peek().event_type, "world.changed")
        self.assertEqual(runtime.events.peek().metadata["legacy"], True)
        self.assertFalse(world.has_pending_events())

    def test_legacy_adapter_preserves_legacy_queue_behavior(self):
        legacy_queue = EventQueue()
        legacy_queue.ekle(Event("legacy.event", {"x": 1}))
        transport = CanonicalEventTransport()
        adapter = LegacyEventAdapter(transport)
        canonical = adapter.enqueue(legacy_queue.al(), 3)
        self.assertEqual(canonical.event_type, "legacy.event")
        self.assertEqual(canonical.payload["x"], 1)


if __name__ == "__main__":
    unittest.main()
