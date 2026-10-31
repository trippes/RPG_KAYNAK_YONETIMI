import unittest

from core.event_types import EventType
from core.simulation import (
    CanonicalEventDispatcher,
    CanonicalEventTransport,
    CanonicalEventType,
    EventConsumer,
    SimulationEvent,
    canonical_event_type,
)
from core.time import Tick
from core.compatibility import LEGACY_API_MATRIX, compatibility_entry


def make_event(name, tick=0, payload=None):
    return SimulationEvent(name, Tick(tick), None, None, None, payload or {}, {})


class Recorder(EventConsumer):
    def __init__(self, log, transport=None, produce=False, dispatcher=None):
        self.log = log
        self.transport = transport
        self.produce = produce
        self.dispatcher = dispatcher

    def consume(self, event):
        self.log.append(event.event_type)
        if self.produce:
            self.transport.enqueue(make_event("nested", event.simulation_tick.value))
        if self.dispatcher is not None:
            self.dispatcher.dispatch_pending()


class TestDispatcherContract(unittest.TestCase):
    def test_registration_removal_and_order(self):
        transport = CanonicalEventTransport()
        dispatcher = CanonicalEventDispatcher(transport)
        log = []
        first = Recorder(log)
        second = Recorder(log)
        dispatcher.register(first)
        dispatcher.register(second)
        transport.enqueue(make_event("A"))
        self.assertEqual(dispatcher.dispatch_pending(), 1)
        self.assertEqual(log, ["A", "A"])
        self.assertTrue(dispatcher.unregister(first))
        self.assertFalse(dispatcher.unregister(first))

    def test_event_filtering_and_multiple_consumers(self):
        transport = CanonicalEventTransport()
        dispatcher = CanonicalEventDispatcher(transport)
        all_log, action_log = [], []
        dispatcher.register(Recorder(all_log))
        dispatcher.register(Recorder(action_log), {CanonicalEventType.ACTION_CREATED})
        transport.enqueue(make_event(CanonicalEventType.ACTION_CREATED))
        transport.enqueue(make_event("other"))
        dispatcher.dispatch_pending()
        self.assertEqual(all_log, ["ActionCreated", "other"])
        self.assertEqual(action_log, ["ActionCreated"])

    def test_nested_events_are_deferred_to_next_cycle(self):
        transport = CanonicalEventTransport()
        dispatcher = CanonicalEventDispatcher(transport)
        log = []
        dispatcher.register(Recorder(log, transport, produce=True))
        transport.enqueue(make_event("A"))
        self.assertEqual(dispatcher.dispatch_pending(), 1)
        self.assertEqual(log, ["A"])
        self.assertEqual(transport.count(), 1)

    def test_consumer_failure_keeps_event_for_retry(self):
        transport = CanonicalEventTransport()
        dispatcher = CanonicalEventDispatcher(transport)

        class Failing(Recorder):
            def consume(self, event):
                super().consume(event)
                raise RuntimeError("consumer failure")

        dispatcher.register(Failing([]))
        transport.enqueue(make_event("A"))
        with self.assertRaises(RuntimeError):
            dispatcher.dispatch_pending()
        self.assertEqual(transport.count(), 1)

    def test_reentrant_dispatch_is_rejected(self):
        transport = CanonicalEventTransport()
        dispatcher = CanonicalEventDispatcher(transport)
        log = []
        dispatcher.register(Recorder(log, dispatcher=dispatcher))
        transport.enqueue(make_event("A"))
        with self.assertRaises(RuntimeError):
            dispatcher.dispatch_pending()

    def test_schema_version_and_serialization_shape(self):
        event = make_event("A")
        self.assertEqual(event.schema_version, 1)
        explicit = SimulationEvent("B", Tick(2), None, None, None, {}, {}, None, None, 2)
        self.assertEqual(explicit.schema_version, 2)
        data = explicit.to_dict()
        self.assertEqual(set(data), {"event_type", "schema_version", "simulation_tick", "source_id", "target_id", "action_id", "payload", "metadata", "event_id", "insertion_sequence"})

    def test_legacy_aliases_have_canonical_meaning(self):
        self.assertEqual(canonical_event_type(EventType.AKSIYON_BASLATILDI), CanonicalEventType.ACTION_STARTED)
        self.assertEqual(canonical_event_type(EventType.AKSIYON_TAMAMLANDI), CanonicalEventType.ACTION_COMPLETED)

    def test_deprecation_matrix_is_explicit_and_non_destructive(self):
        entry = compatibility_entry("core.events.EventQueue")
        self.assertEqual(entry.status, "compatibility")
        self.assertEqual(entry.canonical_replacement, "CanonicalEventTransport")
        self.assertIn("Game.dunya_olaylarini_aktar", LEGACY_API_MATRIX)


if __name__ == "__main__":
    unittest.main()
