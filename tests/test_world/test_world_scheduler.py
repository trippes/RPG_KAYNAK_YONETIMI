import unittest

from core.world import World


class TestWorldScheduler(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()

    def test_world_scheduler_olusturur(self):
        world = World("Ana Dünya")

        self.assertIsNotNone(
            world.scheduler
        )

    def test_baslangicta_zamanlanmis_olay_yoktur(self):
        world = World("Ana Dünya")

        self.assertEqual(
            world.scheduled_event_count,
            0
        )

    def test_olay_zamanlanabilir(self):
        world = World("Ana Dünya")
        calisti = []

        event_id = world.schedule_event(
            trigger_tick=100,
            callback=lambda: calisti.append(True),
            description="Test olayı",
        )

        self.assertEqual(
            event_id,
            1
        )

        self.assertEqual(
            world.scheduled_event_count,
            1
        )

    def test_zaman_ilerleyince_olay_calısır(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            trigger_tick=100,
            callback=lambda: calisti.append(True),
        )

        world.advance(99)

        self.assertEqual(
            calisti,
            []
        )

        world.advance(1)

        self.assertEqual(
            calisti,
            [True]
        )

    def test_zaman_gectikten_sonra_olay_kuyruktan_cikar(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            trigger_tick=100,
            callback=lambda: calisti.append(True),
        )

        world.advance(100)

        self.assertEqual(
            world.scheduled_event_count,
            0
        )

    def test_gelecekteki_olay_calısmaz(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            trigger_tick=200,
            callback=lambda: calisti.append(True),
        )

        world.advance(100)

        self.assertEqual(
            calisti,
            []
        )

        self.assertEqual(
            world.scheduled_event_count,
            1
        )

    def test_birden_fazla_olay_sirasiyla_calısır(self):
        world = World("Ana Dünya")
        sonuc = []

        world.schedule_event(
            trigger_tick=200,
            callback=lambda: sonuc.append("iki"),
        )

        world.schedule_event(
            trigger_tick=100,
            callback=lambda: sonuc.append("bir"),
        )

        world.schedule_event(
            trigger_tick=300,
            callback=lambda: sonuc.append("uc"),
        )

        world.advance(300)

        self.assertEqual(
            sonuc,
            ["bir", "iki", "uc"]
        )

    def test_olay_iptal_edilebilir(self):
        world = World("Ana Dünya")
        calisti = []

        event_id = world.schedule_event(
            trigger_tick=100,
            callback=lambda: calisti.append(True),
        )

        sonuc = world.cancel_scheduled_event(
            event_id
        )

        self.assertTrue(
            sonuc
        )

        world.advance(100)

        self.assertEqual(
            calisti,
            []
        )

        self.assertEqual(
            world.scheduled_event_count,
            0
        )

    def test_olmayan_olay_iptal_edilince_false(self):
        world = World("Ana Dünya")

        sonuc = world.cancel_scheduled_event(
            999
        )

        self.assertFalse(
            sonuc
        )

    def test_zamanlanmis_olaylar_temizlenebilir(self):
        world = World("Ana Dünya")

        world.schedule_event(
            100,
            lambda: None,
        )

        world.schedule_event(
            200,
            lambda: None,
        )

        world.clear_scheduled_events()

        self.assertEqual(
            world.scheduled_event_count,
            0
        )

    def test_pause_iken_zamanlanmis_olay_calısmaz(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            100,
            lambda: calisti.append(True),
        )

        world.pause()
        world.advance(100)

        self.assertEqual(
            calisti,
            []
        )

        self.assertEqual(
            world.total_ticks,
            0
        )

    def test_resume_sonrasi_olay_calısır(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            100,
            lambda: calisti.append(True),
        )

        world.pause()
        world.advance(100)

        world.resume()
        world.advance(100)

        self.assertEqual(
            calisti,
            [True]
        )

    def test_set_time_scheduleri_calıstırır(self):
        world = World("Ana Dünya")
        calisti = []

        world.schedule_event(
            500,
            lambda: calisti.append(True),
        )

        world.set_time(500)

        self.assertEqual(
            calisti,
            [True]
        )

    def test_get_info_scheduler_sayisini_icerir(self):
        world = World("Ana Dünya")

        world.schedule_event(
            100,
            lambda: None,
        )

        bilgi = world.get_info()

        self.assertEqual(
            bilgi["zamanlanmis_olay_sayisi"],
            1
        )

    def test_oyun_zamani_ilerleyince_event_callback_worlde_event_ekleyebilir(self):
        world = World("Ana Dünya")

        def olay_uret():
            world.emit_event(
                "zamanlanmis_olay"
            )

        world.schedule_event(
            100,
            olay_uret,
        )

        world.advance(100)

        self.assertEqual(
            world.pending_event_count(),
            1
        )

        olay = world.get_event()

        self.assertEqual(
            olay.tur,
            "zamanlanmis_olay"
        )


if __name__ == "__main__":
    unittest.main()
