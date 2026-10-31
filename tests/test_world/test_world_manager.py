import unittest

from core.world import World, WorldManager


class TestWorldManager(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()

        self.manager = WorldManager()

    def test_world_ekleme(self):
        world = World("Ana Dünya")

        self.manager.add(world)

        self.assertEqual(
            self.manager.count(),
            1
        )

        self.assertTrue(
            self.manager.exists(world.world_id)
        )

    def test_world_getirme(self):
        world = World("Ana Dünya")

        self.manager.add(world)

        bulunan = self.manager.get(
            world.world_id
        )

        self.assertIs(
            bulunan,
            world
        )

    def test_world_bulunamazsa_none(self):
        self.assertIsNone(
            self.manager.get("world_999999")
        )

    def test_gecersiz_world_ekleme(self):
        with self.assertRaises(TypeError):
            self.manager.add("world")

    def test_ayni_world_id_iki_kez_eklenemez(self):
        world1 = World(
            name="Birinci",
            world_id="world_test"
        )

        world2 = World(
            name="Ikinci",
            world_id="world_test"
        )

        self.manager.add(world1)

        with self.assertRaises(ValueError):
            self.manager.add(world2)

    def test_world_silme(self):
        world = World("Ana Dünya")

        self.manager.add(world)

        silinen = self.manager.remove(
            world.world_id
        )

        self.assertIs(
            silinen,
            world
        )

        self.assertEqual(
            self.manager.count(),
            0
        )

    def test_olmayan_world_silme(self):
        with self.assertRaises(KeyError):
            self.manager.remove(
                "world_999999"
            )

    def test_tum_worldleri_getirme(self):
        world1 = World("Ana Dünya")
        world2 = World("Yan Dünya")

        self.manager.add(world1)
        self.manager.add(world2)

        worlds = self.manager.get_all()

        self.assertEqual(
            len(worlds),
            2
        )

        self.assertIn(world1, worlds)
        self.assertIn(world2, worlds)

    def test_ada_gore_world_getirme(self):
        world1 = World("Ana Dünya")
        world2 = World("Ana Dünya")
        world3 = World("Yan Dünya")

        self.manager.add(world1)
        self.manager.add(world2)
        self.manager.add(world3)

        sonuc = self.manager.get_by_name(
            "Ana Dünya"
        )

        self.assertEqual(
            len(sonuc),
            2
        )

        self.assertIn(world1, sonuc)
        self.assertIn(world2, sonuc)
        self.assertNotIn(world3, sonuc)

    def test_temizleme(self):
        self.manager.add(
            World("Ana Dünya")
        )

        self.manager.add(
            World("Yan Dünya")
        )

        self.manager.clear()

        self.assertEqual(
            self.manager.count(),
            0
        )


if __name__ == "__main__":
    unittest.main()
