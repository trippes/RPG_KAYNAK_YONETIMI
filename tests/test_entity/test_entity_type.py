import unittest

from core.entity import EntityType

class TestEntityType(unittest.TestCase):

    def test_karakter_turu(self):
        self.assertEqual(
            EntityType.KARAKTER,
            "karakter"
        )

    def test_npc_turu(self):
        self.assertEqual(
            EntityType.NPC,
            "npc"
        )

    def test_esya_turu(self):
        self.assertEqual(
            EntityType.ESYA,
            "esya"
        )

    def test_tum_turler(self):
        turler = EntityType.all()

        self.assertIn(
            EntityType.KARAKTER,
            turler
        )

        self.assertIn(
            EntityType.NPC,
            turler
        )

        self.assertIn(
            EntityType.ESYA,
            turler
        )

        self.assertIn(
            EntityType.HAYVAN,
            turler
        )

        self.assertIn(
            EntityType.YAPI,
            turler
        )

        self.assertIn(
            EntityType.KAYNAK,
            turler
        )

        self.assertIn(
            EntityType.ARAC,
            turler
        )

    def test_gecerli_tur(self):
        self.assertTrue(
            EntityType.is_valid(
                EntityType.KARAKTER
            )
        )

        self.assertTrue(
            EntityType.is_valid(
                EntityType.NPC
            )
        )

    def test_gecersiz_tur(self):
        self.assertFalse(
            EntityType.is_valid(
                "uzayli"
            )
        )


if __name__ == "__main__":
    unittest.main()