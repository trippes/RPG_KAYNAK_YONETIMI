import unittest

from core.world import World, WorldManager


class TestWorldManagerLifecycle(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()
        self.manager = WorldManager()

    def test_create_world_olusturur(self):
        world = self.manager.create(
            name="Ana Dünya"
        )

        self.assertIsInstance(
            world,
            World
        )

        self.assertEqual(
            world.name,
            "Ana Dünya"
        )

        self.assertTrue(
            self.manager.exists(world.world_id)
        )

    def test_create_worldu_otomatik_aktif_yapmaz(self):
        world = self.manager.create(
            name="Ana Dünya"
        )

        self.assertIsNone(
            self.manager.get_active()
        )

        self.assertFalse(
            self.manager.has_active()
        )

        self.assertNotEqual(
            self.manager.get_active_id(),
            world.world_id
        )

    def test_set_active(self):
        world = self.manager.create(
            name="Ana Dünya"
        )

        self.manager.set_active(
            world.world_id
        )

        self.assertIs(
            self.manager.get_active(),
            world
        )

        self.assertEqual(
            self.manager.get_active_id(),
            world.world_id
        )

        self.assertTrue(
            self.manager.has_active()
        )

    def test_olmayan_world_aktif_yapilamaz(self):
        with self.assertRaises(KeyError):
            self.manager.set_active(
                "world_999999"
            )

    def test_aktif_world_degistirme(self):
        world1 = self.manager.create(
            name="Birinci Dünya"
        )

        world2 = self.manager.create(
            name="kinci Dünya"
        )

        self.manager.set_active(
            world1.world_id
        )

        self.assertIs(
            self.manager.get_active(),
            world1
        )

        self.manager.set_active(
            world2.world_id
        )

        self.assertIs(
            self.manager.get_active(),
            world2
        )

        self.assertEqual(
            self.manager.get_active_id(),
            world2.world_id
        )

    def test_switch(self):
        world1 = self.manager.create(
            name="Birinci Dünya"
        )

        world2 = self.manager.create(
            name="kinci Dünya"
        )

        self.manager.set_active(
            world1.world_id
        )

        self.manager.switch(
            world2.world_id
        )

        self.assertIs(
            self.manager.get_active(),
            world2
        )

    def test_clear_active_worldu_silmez(self):
        world = self.manager.create(
            name="Ana Dünya"
        )

        self.manager.set_active(
            world.world_id
        )

        self.manager.clear_active()

        self.assertIsNone(
            self.manager.get_active()
        )

        self.assertFalse(
            self.manager.has_active()
        )

        self.assertTrue(
            self.manager.exists(world.world_id)
        )

    def test_aktif_world_silinirse_aktiflik_temizlenir(self):
        world = self.manager.create(
            name="Ana Dünya"
        )

        self.manager.set_active(
            world.world_id
        )

        self.manager.remove(
            world.world_id
        )

        self.assertIsNone(
            self.manager.get_active()
        )

        self.assertIsNone(
            self.manager.get_active_id()
        )

        self.assertFalse(
            self.manager.has_active()
        )

    def test_aktif_olmayan_world_silinirse_aktif_world_korunur(self):
        world1 = self.manager.create(
            name="Ana Dünya"
        )

        world2 = self.manager.create(
            name="Yan Dünya"
        )

        self.manager.set_active(
            world1.world_id
        )

        self.manager.remove(
            world2.world_id
        )

        self.assertIs(
            self.manager.get_active(),
            world1
        )

    def test_clear_tum_worldleri_ve_aktifligi_temizler(self):
        world1 = self.manager.create(
            name="Birinci Dünya"
        )

        self.manager.create(
            name="kinci Dünya"
        )

        self.manager.set_active(
            world1.world_id
        )

        self.manager.clear()

        self.assertEqual(
            self.manager.count(),
            0
        )

        self.assertIsNone(
            self.manager.get_active()
        )

        self.assertIsNone(
            self.manager.get_active_id()
        )

        self.assertFalse(
            self.manager.has_active()
        )

    def test_birden_fazla_world_olabilir(self):
        world1 = self.manager.create(
            name="Birinci Dünya"
        )

        world2 = self.manager.create(
            name="kinci Dünya"
        )

        world3 = self.manager.create(
            name="Üçüncü Dünya"
        )

        self.assertEqual(
            self.manager.count(),
            3
        )

        self.assertIn(
            world1,
            self.manager.get_all()
        )

        self.assertIn(
            world2,
            self.manager.get_all()
        )

        self.assertIn(
            world3,
            self.manager.get_all()
        )

    def test_create_boyutlari_aktarir(self):
        world = self.manager.create(
            name="Ana Dünya",
            width=100,
            height=200
        )

        self.assertEqual(
            world.width,
            100
        )

        self.assertEqual(
            world.height,
            200
        )

    def test_create_ozel_id_aktarir(self):
        world = self.manager.create(
            name="Ana Dünya",
            world_id="world_ana"
        )

        self.assertEqual(
            world.world_id,
            "world_ana"
        )

        self.assertIs(
            self.manager.get("world_ana"),
            world
        )


if __name__ == "__main__":
    unittest.main()
