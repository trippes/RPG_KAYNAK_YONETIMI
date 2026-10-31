import unittest

from core.world import World, WorldManager


class TestWorldManagerActiveTime(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()
        self.manager = WorldManager()

    def test_aktif_world_tick_ilerletme(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.advance_active(100)

        self.assertEqual(world.total_ticks, 100)

    def test_aktif_world_saat_ilerletme(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.advance_active_hours(1)

        self.assertEqual(world.total_ticks, 216000)

    def test_aktif_world_dakika_ilerletme(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.advance_active_minutes(1)

        self.assertEqual(world.total_ticks, 3600)

    def test_aktif_world_gun_ilerletme(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.advance_active_days(1)

        self.assertEqual(world.total_ticks, 5184000)

    def test_aktif_world_zaman_bilgisi(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.advance_active(123)

        self.assertEqual(
            self.manager.get_active_ticks(),
            123
        )

        self.assertEqual(
            self.manager.get_active_time().total_ticks,
            world.time.total_ticks
        )

    def test_aktif_world_pause(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.assertTrue(
            self.manager.is_active_running()
        )

        self.manager.pause_active()

        self.assertFalse(
            self.manager.is_active_running()
        )

        self.manager.advance_active(100)

        self.assertEqual(world.total_ticks, 0)

    def test_aktif_world_resume(self):
        world = self.manager.create(name="Ana Dünya")
        self.manager.set_active(world.world_id)

        self.manager.pause_active()
        self.manager.resume_active()
        self.manager.advance_active(100)

        self.assertTrue(
            self.manager.is_active_running()
        )

        self.assertEqual(world.total_ticks, 100)

    def test_aktif_world_yokken_zaman_ilerletilemez(self):
        with self.assertRaises(RuntimeError):
            self.manager.advance_active(100)

    def test_aktif_world_yokken_zaman_alinamaz(self):
        with self.assertRaises(RuntimeError):
            self.manager.get_active_ticks()

    def test_aktif_world_yokken_pause_yapilamaz(self):
        with self.assertRaises(RuntimeError):
            self.manager.pause_active()

    def test_aktif_world_degisince_zaman_islemleri_yeni_worlde_uygulanir(self):
        world1 = self.manager.create(name="Birinci Dünya")
        world2 = self.manager.create(name="kinci Dünya")

        self.manager.set_active(world1.world_id)
        self.manager.advance_active(100)

        self.manager.switch(world2.world_id)
        self.manager.advance_active(200)

        self.assertEqual(world1.total_ticks, 100)
        self.assertEqual(world2.total_ticks, 200)

    def test_aktif_world_pause_ve_switch_bagimsizdir(self):
        world1 = self.manager.create(name="Birinci Dünya")
        world2 = self.manager.create(name="kinci Dünya")

        self.manager.set_active(world1.world_id)
        self.manager.pause_active()

        self.manager.switch(world2.world_id)
        self.manager.advance_active(100)

        self.assertEqual(world1.total_ticks, 0)
        self.assertEqual(world2.total_ticks, 100)

        self.assertTrue(
            self.manager.is_active_running()
        )


if __name__ == "__main__":
    unittest.main()
