import unittest

from core.events import Event, EventQueue
from core.event_handler import EventHandler
from core.event_bus import EventBus


class TestEventBus(unittest.TestCase):

    def test_event_bus_olusturma(self):
        bus = EventBus()

        self.assertEqual(
            bus.handler_sayisi(),
            0
        )

    def test_handler_abone_olur(self):
        bus = EventBus()

        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)

        self.assertEqual(
            bus.handler_sayisi(),
            1
        )

        self.assertEqual(
            bus.handler_sayisi("test"),
            1
        )

    def test_ayni_handler_iki_kez_eklenmez(self):
        bus = EventBus()

        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)
        bus.subscribe(handler)

        self.assertEqual(
            bus.handler_sayisi(),
            1
        )

    def test_event_yayinlanir(self):
        bus = EventBus()
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)

        event = Event(
            tur="test"
        )

        islenen_sayi = bus.publish(event)

        self.assertEqual(
            islenen_sayi,
            1
        )

        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIs(
            sonuc[0],
            event
        )

    def test_ayni_olaya_birden_fazla_handler(self):
        bus = EventBus()
        sonuc = []

        def callback_1(event):
            sonuc.append("bir")

        def callback_2(event):
            sonuc.append("iki")

        handler_1 = EventHandler(
            event_type="test",
            callback=callback_1
        )

        handler_2 = EventHandler(
            event_type="test",
            callback=callback_2
        )

        bus.subscribe(handler_1)
        bus.subscribe(handler_2)

        event = Event(
            tur="test"
        )

        islenen_sayi = bus.publish(event)

        self.assertEqual(
            islenen_sayi,
            2
        )

        self.assertEqual(
            sonuc,
            ["bir", "iki"]
        )

    def test_farkli_olay_handleri_cagirilmaz(self):
        bus = EventBus()
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)

        event = Event(
            tur="baska"
        )

        islenen_sayi = bus.publish(event)

        self.assertEqual(
            islenen_sayi,
            0
        )

        self.assertEqual(
            len(sonuc),
            0
        )

    def test_handler_aboneligi_kaldirilir(self):
        bus = EventBus()
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)
        bus.unsubscribe(handler)

        self.assertEqual(
            bus.handler_sayisi(),
            0
        )

        bus.publish(
            Event(tur="test")
        )

        self.assertEqual(
            len(sonuc),
            0
        )

    def test_var_olmayan_handler_aboneligi_kaldirilabilir(self):
        bus = EventBus()

        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.unsubscribe(handler)

        self.assertEqual(
            bus.handler_sayisi(),
            0
        )

    def test_gecersiz_handler_aboneligi(self):
        bus = EventBus()

        with self.assertRaises(TypeError):
            bus.subscribe("gecersiz")

    def test_gecersiz_handler_aboneligi_kaldirma(self):
        bus = EventBus()

        with self.assertRaises(TypeError):
            bus.unsubscribe("gecersiz")

    def test_gecersiz_event_yayinlama(self):
        bus = EventBus()

        with self.assertRaises(TypeError):
            bus.publish("gecersiz")

    def test_temizle(self):
        bus = EventBus()

        def callback(event):
            pass

        handler_1 = EventHandler(
            event_type="bir",
            callback=callback
        )

        handler_2 = EventHandler(
            event_type="iki",
            callback=callback
        )

        bus.subscribe(handler_1)
        bus.subscribe(handler_2)

        self.assertEqual(
            bus.handler_sayisi(),
            2
        )

        bus.temizle()

        self.assertEqual(
            bus.handler_sayisi(),
            0
        )

    def test_kuyruk_olaylari_sirayla_islenir(self):
        bus = EventBus()
        queue = EventQueue()
        sonuc = []

        def callback(event):
            sonuc.append(event.tur)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        bus.subscribe(handler)

        queue.ekle(
            Event(tur="test", veri={"sira": 1})
        )

        queue.ekle(
            Event(tur="test", veri={"sira": 2})
        )

        queue.ekle(
            Event(tur="test", veri={"sira": 3})
        )

        islenen_olay, islenen_handler = bus.dispatch_queue(
            queue
        )

        self.assertEqual(
            islenen_olay,
            3
        )

        self.assertEqual(
            islenen_handler,
            3
        )

        self.assertEqual(
            sonuc,
            [
                "test",
                "test",
                "test"
            ]
        )

        self.assertTrue(
            queue.bos_mu()
        )

    def test_kuyrukta_handler_olmayan_olay(self):
        bus = EventBus()
        queue = EventQueue()

        queue.ekle(
            Event(tur="test")
        )

        islenen_olay, islenen_handler = bus.dispatch_queue(
            queue
        )

        self.assertEqual(
            islenen_olay,
            1
        )

        self.assertEqual(
            islenen_handler,
            0
        )

        self.assertTrue(
            queue.bos_mu()
        )

    def test_bos_kuyruk_islenebilir(self):
        bus = EventBus()
        queue = EventQueue()

        sonuc = bus.dispatch_queue(
            queue
        )

        self.assertEqual(
            sonuc,
            (0, 0)
        )

        self.assertTrue(
            queue.bos_mu()
        )

    def test_gecersiz_kuyruk(self):
        bus = EventBus()

        with self.assertRaises(TypeError):
            bus.dispatch_queue("gecersiz")


    def test_dispatch_uses_subscription_snapshot(self):
        bus = EventBus()
        received = []
        second = EventHandler("test", lambda event: received.append("second"))

        def first_callback(event):
            received.append("first")
            bus.unsubscribe(second)

        bus.subscribe(EventHandler("test", first_callback))
        bus.subscribe(second)

        bus.publish(Event("test"))
        bus.publish(Event("test"))

        self.assertEqual(received, ["first", "second", "first"])

    def test_handler_added_during_dispatch_starts_on_next_publish(self):
        bus = EventBus()
        received = []
        second = EventHandler("test", lambda event: received.append("second"))
        added = False

        def first_callback(event):
            nonlocal added
            received.append("first")
            if not added:
                bus.subscribe(second)
                added = True

        bus.subscribe(EventHandler("test", first_callback))

        bus.publish(Event("test"))
        self.assertEqual(received, ["first"])

        bus.publish(Event("test"))
        self.assertEqual(received, ["first", "first", "second"])

    def test_reentrant_publish_completes_nested_dispatch_before_outer_continues(self):
        bus = EventBus()
        received = []

        bus.subscribe(EventHandler(
            "outer",
            lambda event: (
                received.append("outer-start"),
                bus.publish(Event("inner")),
                received.append("outer-end"),
            ),
        ))
        bus.subscribe(EventHandler("inner", lambda event: received.append("inner")))

        bus.publish(Event("outer"))

        self.assertEqual(received, ["outer-start", "inner", "outer-end"])

    def test_handler_exception_consumes_current_event_and_preserves_later_queue_items(self):
        bus = EventBus()
        queue = EventQueue()
        received = []

        failing = EventHandler(
            "test",
            lambda event: (_ for _ in ()).throw(RuntimeError("handler failed")),
        )
        later = EventHandler("test", lambda event: received.append(event.veri["id"]))
        bus.subscribe(failing)
        bus.subscribe(later)
        queue.ekle(Event("test", {"id": 1}))
        queue.ekle(Event("test", {"id": 2}))

        with self.assertRaisesRegex(RuntimeError, "handler failed"):
            bus.dispatch_queue(queue)

        self.assertEqual(queue.bekleyen_sayi(), 1)
        self.assertEqual(received, [])

        bus.unsubscribe(failing)
        bus.dispatch_queue(queue)

        self.assertEqual(received, [2])
        self.assertTrue(queue.bos_mu())


if __name__ == "__main__":
    unittest.main()
