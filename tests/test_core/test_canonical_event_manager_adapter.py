import unittest

from core.compatibility.event_manager_adapter import CanonicalEventManagerAdapter
from core.event_handler import EventHandler
from core.events import Event


class TestCanonicalEventManagerAdapter(unittest.TestCase):
    def test_legacy_queue_api_is_a_view_of_canonical_transport(self):
        manager = CanonicalEventManagerAdapter()
        first = manager.ekle("first", {"id": 1})
        second = Event("second", {"id": 2})
        manager.event_queue.ekle(second)

        self.assertEqual(manager.event_transport.count(), 2)
        self.assertIs(manager.event_queue.al(), first)
        self.assertEqual(manager.event_transport.count(), 1)
        self.assertEqual(manager.event_queue.listele(), [second])

    def test_event_bus_dispatch_keeps_reentrant_legacy_order(self):
        manager = CanonicalEventManagerAdapter()
        received = []

        manager.event_bus.subscribe(EventHandler(
            "outer",
            lambda event: (
                received.append("outer-start"),
                manager.yayinla(Event("inner")),
                received.append("outer-end"),
            ),
        ))
        manager.event_bus.subscribe(EventHandler(
            "inner", lambda event: received.append("inner")
        ))
        manager.ekle("outer")
        self.assertEqual(manager.islet(), (1, 1))
        self.assertEqual(received, ["outer-start", "inner", "outer-end"])
        self.assertEqual(manager.event_transport.count(), 0)

    def test_dispatch_exception_consumes_current_and_preserves_later_events(self):
        manager = CanonicalEventManagerAdapter()
        received = []
        failing = EventHandler(
            "test",
            lambda event: (_ for _ in ()).throw(RuntimeError("dispatch failed")),
        )
        manager.event_bus.subscribe(failing)
        manager.event_bus.subscribe(EventHandler(
            "test", lambda event: received.append(event.veri["id"])
        ))
        manager.ekle("test", {"id": 1})
        manager.ekle("test", {"id": 2})

        with self.assertRaisesRegex(RuntimeError, "dispatch failed"):
            manager.islet()

        self.assertEqual(manager.event_transport.count(), 1)
        self.assertEqual(received, [])
        manager.event_bus.unsubscribe(failing)
        self.assertEqual(manager.islet(), (1, 1))
        self.assertEqual(received, [2])

    def test_clear_removes_canonical_and_legacy_queue_projection(self):
        manager = CanonicalEventManagerAdapter()
        manager.ekle("test")
        manager.temizle()
        self.assertEqual(manager.event_transport.count(), 0)
        self.assertTrue(manager.event_queue.bos_mu())


if __name__ == "__main__":
    unittest.main()
