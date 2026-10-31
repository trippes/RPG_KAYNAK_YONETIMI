import unittest

from core.entity import EntityIDGenerator


class TestEntityIDGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = EntityIDGenerator()

    def test_ilk_id(self):
        entity_id = self.generator.generate()

        self.assertEqual(
            entity_id,
            "entity_000001"
        )

    def test_id_siralama(self):
        id_1 = self.generator.generate()
        id_2 = self.generator.generate()
        id_3 = self.generator.generate()

        self.assertEqual(id_1, "entity_000001")
        self.assertEqual(id_2, "entity_000002")
        self.assertEqual(id_3, "entity_000003")

    def test_idler_farkli(self):
        id_1 = self.generator.generate()
        id_2 = self.generator.generate()

        self.assertNotEqual(id_1, id_2)

    def test_id_format(self):
        entity_id = self.generator.generate()

        self.assertTrue(
            entity_id.startswith("entity_")
        )

        self.assertEqual(
            len(entity_id),
            13
        )

    def test_reset(self):
        self.generator.generate()
        self.generator.generate()

        self.generator.reset()

        entity_id = self.generator.generate()

        self.assertEqual(
            entity_id,
            "entity_000001"
        )


if __name__ == "__main__":
    unittest.main()