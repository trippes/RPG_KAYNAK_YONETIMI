import unittest

from core.entity import Entity
from core.entity import EntityManager
from core.entity import Position


class TestEntityIntegration(unittest.TestCase):

    def setUp(self):
        Entity._id_generator.reset()
        self.manager = EntityManager()

    def test_entity_manager_entity_entegrasyonu(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        bulunan = self.manager.get(
            entity.entity_id
        )

        self.assertIs(
            bulunan,
            entity
        )

    def test_entity_tam_yasam_dongusu(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        self.assertTrue(
            entity.is_alive()
        )

        self.manager.deactivate(
            entity.entity_id
        )

        self.assertFalse(
            entity.is_active()
        )

        self.assertTrue(
            entity.is_alive()
        )

        self.manager.activate(
            entity.entity_id
        )

        self.assertTrue(
            entity.is_active()
        )

        self.manager.kill(
            entity.entity_id
        )

        self.assertFalse(
            entity.is_alive()
        )

        self.manager.revive(
            entity.entity_id
        )

        self.assertTrue(
            entity.is_alive()
        )

        self.assertTrue(
            entity.is_active()
        )

    def test_manager_durum_sorgusu_entity_durumunu_yansitir(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        self.assertIn(
            entity,
            self.manager.get_by_status("aktif")
        )

        self.manager.deactivate(
            entity.entity_id
        )

        self.assertIn(
            entity,
            self.manager.get_by_status("pasif")
        )

        self.assertNotIn(
            entity,
            self.manager.get_by_status("aktif")
        )

    def test_manager_canli_sorgusu(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        self.assertIn(
            entity,
            self.manager.get_alive()
        )

        self.manager.kill(
            entity.entity_id
        )

        self.assertNotIn(
            entity,
            self.manager.get_alive()
        )

    def test_manager_aktif_sorgusu(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        self.assertIn(
            entity,
            self.manager.get_active()
        )

        self.manager.deactivate(
            entity.entity_id
        )

        self.assertNotIn(
            entity,
            self.manager.get_active()
        )

    def test_diriltilen_entity_sorgulara_geri_doner(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        self.manager.kill(
            entity.entity_id
        )

        self.assertNotIn(
            entity,
            self.manager.get_alive()
        )

        self.manager.revive(
            entity.entity_id
        )

        self.assertIn(
            entity,
            self.manager.get_alive()
        )

        self.assertIn(
            entity,
            self.manager.get_active()
        )

    def test_entity_position_entegrasyonu(self):
        position = Position(
            x=10,
            y=20
        )

        entity = Entity(
            entity_type="karakter",
            name="Muhafız",
            position=position
        )

        self.manager.add(entity)

        self.assertIs(
            entity.position,
            position
        )

        self.assertEqual(
            entity.position.x,
            10
        )

        self.assertEqual(
            entity.position.y,
            20
        )

    def test_entity_position_degistirme(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        entity.position.set_position(
            15,
            25
        )

        self.assertEqual(
            entity.position.x,
            15
        )

        self.assertEqual(
            entity.position.y,
            25
        )

    def test_entity_bilgileri_tum_temel_verileri_icerir(self):
        position = Position(
            x=5,
            y=10
        )

        entity = Entity(
            entity_type="karakter",
            name="Muhafız",
            position=position
        )

        self.manager.add(entity)

        bilgiler = entity.get_info()

        self.assertEqual(
            bilgiler["id"],
            entity.entity_id
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

        self.assertEqual(
            bilgiler["konum"]["x"],
            5
        )

        self.assertEqual(
            bilgiler["konum"]["y"],
            10
        )

    def test_manager_entity_silindiginde_durum(self):
        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        self.manager.add(entity)

        entity_id = entity.entity_id

        self.manager.remove(
            entity_id
        )

        self.assertFalse(
            self.manager.exists(entity_id)
        )

        self.assertIsNone(
            self.manager.get(entity_id)
        )

        self.assertEqual(
            self.manager.count(),
            0
        )


if __name__ == "__main__":
    unittest.main()