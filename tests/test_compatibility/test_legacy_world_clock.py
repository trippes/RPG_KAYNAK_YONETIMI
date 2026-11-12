import unittest

from core.world import World


class TestWorldClock(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()

    def test_world_baslangic_zamani_sifirdir(self):
        world = World("Ana Dünya")

        self.assertEqual(
            world.total_ticks,
            0
        )

    def test_world_start_tick_kullanabilir(self):
        world = World(
            "Ana Dünya",
            start_tick=120
        )

        self.assertEqual(
            world.total_ticks,
            120
        )

    def test_world_clock_erisilebilir(self):
        world = World("Ana Dünya")

        self.assertIsNotNone(
            world.clock
        )

    def test_world_advance(self):
        world = World("Ana Dünya")

        world.advance(60)

        self.assertEqual(
            world.total_ticks,
            60
        )

    def test_world_advance_seconds(self):
        world = World("Ana Dünya")

        world.advance_seconds(2)

        self.assertEqual(
            world.total_ticks,
            120
        )

    def test_world_advance_minutes(self):
        world = World("Ana Dünya")

        world.advance_minutes(2)

        self.assertEqual(
            world.total_ticks,
            7200
        )

    def test_world_advance_hours(self):
        world = World("Ana Dünya")

        world.advance_hours(1)

        self.assertEqual(
            world.total_ticks,
            216000
        )

    def test_world_advance_days(self):
        world = World("Ana Dünya")

        world.advance_days(1)

        self.assertEqual(
            world.total_ticks,
            5184000
        )

    def test_world_pause(self):
        world = World("Ana Dünya")

        world.pause()
        world.advance(100)

        self.assertEqual(
            world.total_ticks,
            0
        )

    def test_world_resume(self):
        world = World("Ana Dünya")

        world.pause()
        world.resume()
        world.advance(100)

        self.assertEqual(
            world.total_ticks,
            100
        )

    def test_world_set_time(self):
        world = World("Ana Dünya")

        world.set_time(1000)

        self.assertEqual(
            world.total_ticks,
            1000
        )

    def test_world_zamani_geriye_alinamaz(self):
        world = World(
            "Ana Dünya",
            start_tick=1000
        )

        with self.assertRaises(ValueError):
            world.set_time(999)

    def test_world_negatif_baslangic_zamani(self):
        with self.assertRaises(ValueError):
            World(
                "Ana Dünya",
                start_tick=-1
            )

    def test_world_gecersiz_baslangic_zamani(self):
        with self.assertRaises(TypeError):
            World(
                "Ana Dünya",
                start_tick="100"
            )

    def test_world_reset_time(self):
        world = World(
            "Ana Dünya",
            start_tick=1000
        )

        world.reset_time()

        self.assertEqual(
            world.total_ticks,
            0
        )

    def test_world_get_info_zamani_icerir(self):
        world = World(
            "Ana Dünya",
            start_tick=500
        )

        bilgi = world.get_info()

        self.assertEqual(
            bilgi["total_ticks"],
            500
        )


if __name__ == "__main__":
    unittest.main()
