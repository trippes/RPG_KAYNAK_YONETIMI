import unittest

from core.world.world_id import WorldIDGenerator


class TestWorldIDGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = WorldIDGenerator()

    def test_ilk_id(self):
        world_id = self.generator.generate()

        self.assertEqual(
            world_id,
            "world_000001"
        )

    def test_idler_sirali_uretilir(self):
        id1 = self.generator.generate()
        id2 = self.generator.generate()
        id3 = self.generator.generate()

        self.assertEqual(id1, "world_000001")
        self.assertEqual(id2, "world_000002")
        self.assertEqual(id3, "world_000003")

    def test_reset(self):
        self.generator.generate()
        self.generator.generate()

        self.generator.reset()

        self.assertEqual(
            self.generator.generate(),
            "world_000001"
        )


if __name__ == "__main__":
    unittest.main()
