import unittest

from core.entity import Entity
from core.entity.position import Position


class TestEntity(unittest.TestCase):

    def setUp(self):
        Entity._id_generator.reset()

    def test_entity_olusturma(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.assertEqual(
            entity.entity_id,
            "entity_000001"
        )

        self.assertEqual(
            entity.entity_type,
            "karakter"
        )

        self.assertEqual(
            entity.name,
            "Muhafız"
        )

        self.assertTrue(
            entity.is_active()
        )

        self.assertTrue(
            entity.is_alive()
        )

    def test_gecerli_entity_turu(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.assertEqual(
            entity.entity_type,
            "karakter"
        )

    def test_gecersiz_entity_turu(self):
        with self.assertRaises(ValueError):
            Entity(
                entity_type="uzayli",
                name="Bilinmeyen Varlık"
            )

    def test_entity_pasiflestirme(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.deactivate()

        self.assertFalse(
            entity.is_active()
        )

        self.assertTrue(
            entity.is_alive()
        )

    def test_entity_aktiflestirme(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.deactivate()
        entity.activate()

        self.assertTrue(
            entity.is_active()
        )

    def test_entity_olum(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.kill()

        self.assertFalse(
            entity.is_alive()
        )

        self.assertFalse(
            entity.is_active()
        )

        self.assertEqual(
            entity.state.get_status(),
            "olu"
        )

    def test_entity_diriltme(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.kill()
        entity.revive()

        self.assertTrue(
            entity.is_alive()
        )

        self.assertTrue(
            entity.is_active()
        )

def test_entity_state_degistirme(self):
    entity = Entity(
        entity_type="karakter",
        name="Muhafız"
    )

    entity.state.set_status("pasif")

    self.assertEqual(
        entity.state.get_status(),
        "pasif"
    )

    def test_entity_bilgileri(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        bilgiler = entity.get_info()

        self.assertEqual(
            bilgiler["id"],
            "entity_000001"
        )

        self.assertEqual(
            bilgiler["tur"],
            "karakter"
        )

        self.assertEqual(
            bilgiler["ad"],
            "Muhafız"
        )

        self.assertEqual(
            bilgiler["durum"]["durum"],
            "aktif"
        )

        self.assertTrue(
            bilgiler["durum"]["canli"]
        )

        self.assertIsNotNone(
            bilgiler["olusturma_zamani"]
        )

    def test_entity_varsayilan_konum(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.assertEqual(
            entity.position.x,
            0
        )

        self.assertEqual(
            entity.position.y,
            0
        )

    def test_entity_baslangic_konumu(self):
        position = Position(10, 20)

        entity = Entity(
            entity_type="karakter",
            name="Muhafız",
            position=position
        )

        self.assertEqual(
            entity.position.x,
            10
        )

        self.assertEqual(
            entity.position.y,
            20
        )

    def test_entity_konum_degisimi(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.position.move(5, 10)

        self.assertEqual(
            entity.position.x,
            5
        )

        self.assertEqual(
            entity.position.y,
            10
        )

    def test_entity_bilgilerinde_konum(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.position.move(15, 25)

        bilgiler = entity.get_info()

        self.assertEqual(
            bilgiler["konum"],
            {
                "x": 15,
                "y": 25
            }
        )
    def test_entity_durum_sorgulama(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.assertEqual(
        entity.get_status(),
        "aktif"
        )

        self.assertTrue(
        entity.is_alive()
        )


    def test_entity_durum_degisikligi(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.deactivate()

        self.assertEqual(
        entity.get_status(),
        "pasif"
        )

        self.assertTrue(
        entity.is_alive()
        )


    def test_entity_durum_gecmisi(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity.deactivate()
        entity.activate()
        entity.kill()

        self.assertEqual(
        entity.get_history(),
        [
            "aktif",
            "pasif",
            "aktif",
            "olu"
        ]
        )


    def test_entity_onceki_durum(self):
        entity = Entity(
        entity_type="karakter",
        name="Muhafız"
        )

        entity.deactivate()
        entity.activate()

        self.assertEqual(
        entity.get_previous_status(),
        "pasif"
        )


if __name__ == "__main__":
    unittest.main()