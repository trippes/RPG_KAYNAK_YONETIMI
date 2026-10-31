import unittest

from core.events import Event
from core.world import World


class TestWorldEvents(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()

    def test_world_baslangicta_event_kuyrugu_bostur(self):
        world = World("Ana Dünya")

        self.assertEqual(
            world.pending_event_count(),
            0
        )

        self.assertFalse(
            world.has_pending_events()
        )

    def test_event_olusturup_kuyruga_ekler(self):
        world = World("Ana Dünya")

        olay = world.emit_event(
            "oyun_basladi"
        )

        self.assertIsInstance(
            olay,
            Event
        )

        self.assertEqual(
            world.pending_event_count(),
            1
        )

    def test_event_verisi_korunur(self):
        world = World("Ana Dünya")

        olay = world.emit_event(
            "karakter_olusturuldu",
            {
                "entity_id": "entity_000001"
            }
        )

        self.assertEqual(
            olay.tur,
            "karakter_olusturuldu"
        )

        self.assertEqual(
            olay.veri["entity_id"],
            "entity_000001"
        )

    def test_get_event_ilk_olayi_cikarir(self):
        world = World("Ana Dünya")

        ilk = world.emit_event(
            "ilk_olay"
        )

        world.emit_event(
            "ikinci_olay"
        )

        sonuc = world.get_event()

        self.assertIs(
            sonuc,
            ilk
        )

        self.assertEqual(
            world.pending_event_count(),
            1
        )

    def test_eventler_sirasiyla_alinir(self):
        world = World("Ana Dünya")

        ilk = world.emit_event("bir")
        ikinci = world.emit_event("iki")
        ucuncu = world.emit_event("uc")

        self.assertIs(
            world.get_event(),
            ilk
        )

        self.assertIs(
            world.get_event(),
            ikinci
        )

        self.assertIs(
            world.get_event(),
            ucuncu
        )

        self.assertFalse(
            world.has_pending_events()
        )

    def test_bos_kuyruktan_event_alininca_none(self):
        world = World("Ana Dünya")

        self.assertIsNone(
            world.get_event()
        )

    def test_mevcut_event_worlde_eklenebilir(self):
        world = World("Ana Dünya")

        olay = Event(
            "test_olayi",
            {
                "deger": 10
            }
        )

        world.add_event(olay)

        self.assertEqual(
            world.pending_event_count(),
            1
        )

        self.assertIs(
            world.get_event(),
            olay
        )

    def test_gecersiz_event_eklenemez(self):
        world = World("Ana Dünya")

        with self.assertRaises(TypeError):
            world.add_event("gecersiz")

    def test_event_listesi_kopya_dondurur(self):
        world = World("Ana Dünya")

        world.emit_event("bir")
        world.emit_event("iki")

        olaylar = world.list_events()

        self.assertEqual(
            len(olaylar),
            2
        )

        olaylar.clear()

        self.assertEqual(
            world.pending_event_count(),
            2
        )

    def test_clear_events(self):
        world = World("Ana Dünya")

        world.emit_event("bir")
        world.emit_event("iki")
        world.emit_event("uc")

        world.clear_events()

        self.assertEqual(
            world.pending_event_count(),
            0
        )

        self.assertFalse(
            world.has_pending_events()
        )

    def test_event_sayisi_bilgiye_yansir(self):
        world = World("Ana Dünya")

        world.emit_event("bir")
        world.emit_event("iki")

        bilgi = world.get_info()

        self.assertEqual(
            bilgi["bekleyen_olay_sayisi"],
            2
        )

    def test_event_queue_dogrudan_erisilebilir(self):
        world = World("Ana Dünya")

        self.assertIsNotNone(
            world.event_queue
        )

        world.event_queue.ekle(
            Event("test")
        )

        self.assertEqual(
            world.pending_event_count(),
            1
        )


if __name__ == "__main__":
    unittest.main()
