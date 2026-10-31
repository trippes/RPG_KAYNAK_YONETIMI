import unittest

from core.events import Event, EventQueue
from core.event_bus import EventBus
from core.event_handler import EventHandler
from core.event_manager import EventManager


class TestEventManager(unittest.TestCase):

    def test_event_manager_olusturma(self):
        manager = EventManager()

        self.assertIsInstance(
            manager.event_bus,
            EventBus
        )

        self.assertIsInstance(
            manager.event_queue,
            EventQueue
        )

        self.assertEqual(
            manager.bekleyen_sayi(),
            0
        )

    def test_ozel_bus_ve_queue_kullanma(self):
        bus = EventBus()
        queue = EventQueue()

        manager = EventManager(
            event_bus=bus,
            event_queue=queue
        )

        self.assertIs(
            manager.event_bus,
            bus
        )

        self.assertIs(
            manager.event_queue,
            queue
        )

    def test_event_olusturma(self):
        manager = EventManager()

        event = manager.olustur(
            tur="test",
            veri={
                "deger": 10
            }
        )

        self.assertIsInstance(
            event,
            Event
        )

        self.assertEqual(
            event.tur,
            "test"
        )

        self.assertEqual(
            event.veri,
            {
                "deger": 10
            }
        )

        self.assertEqual(
            manager.bekleyen_sayi(),
            0
        )

    def test_event_olusturup_kuyruga_ekleme(self):
        manager = EventManager()

        event = manager.ekle(
            tur="test",
            veri={
                "deger": 10
            }
        )

        self.assertIsInstance(
            event,
            Event
        )

        self.assertEqual(
            manager.bekleyen_sayi(),
            1
        )

        self.assertIs(
            manager.event_queue.listele()[0],
            event
        )

    def test_event_yayinlama(self):
        manager = EventManager()
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        manager.event_bus.subscribe(
            handler
        )

        event = manager.olustur(
            tur="test"
        )

        islenen_sayi = manager.yayinla(
            event
        )

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

    def test_kuyruktaki_olaylari_isletme(self):
        manager = EventManager()
        sonuc = []

        def callback(event):
            sonuc.append(event.tur)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        manager.event_bus.subscribe(
            handler
        )

        manager.ekle(
            "test"
        )

        manager.ekle(
            "test"
        )

        olay_sayisi, handler_sayisi = manager.islet()

        self.assertEqual(
            olay_sayisi,
            2
        )

        self.assertEqual(
            handler_sayisi,
            2
        )

        self.assertEqual(
            sonuc,
            [
                "test",
                "test"
            ]
        )

        self.assertEqual(
            manager.bekleyen_sayi(),
            0
        )

    def test_bekleyen_sayi(self):
        manager = EventManager()

        manager.ekle("bir")
        manager.ekle("iki")
        manager.ekle("uc")

        self.assertEqual(
            manager.bekleyen_sayi(),
            3
        )

        manager.islet()

        self.assertEqual(
            manager.bekleyen_sayi(),
            0
        )

    def test_temizle(self):
        manager = EventManager()

        manager.ekle("bir")
        manager.ekle("iki")

        manager.temizle()

        self.assertEqual(
            manager.bekleyen_sayi(),
            0
        )

    def test_gecersiz_event_bus(self):
        with self.assertRaises(TypeError):
            EventManager(
                event_bus="gecersiz"
            )

    def test_gecersiz_event_queue(self):
        with self.assertRaises(TypeError):
            EventManager(
                event_queue="gecersiz"
            )

    def test_gecersiz_yayinlama(self):
        manager = EventManager()

        with self.assertRaises(TypeError):
            manager.yayinla(
                "gecersiz"
            )


if __name__ == "__main__":
    unittest.main()
