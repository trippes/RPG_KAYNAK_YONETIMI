import unittest

from core.entity import Entity
from core.entity import EntityManager


class TestEntityManager(unittest.TestCase):

    def setUp(self):
        Entity._id_generator.reset()

    def test_manager_olusturma(self):
        manager = EntityManager()

        self.assertEqual(
            manager.count(),
            0
        )

    def test_entity_ekleme(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        self.assertEqual(
            manager.count(),
            1
        )

    def test_entity_bulma(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        bulunan = manager.get(
            entity.entity_id
        )

        self.assertIs(
            bulunan,
            entity
        )

    def test_bulunamayan_entity(self):
        manager = EntityManager()

        self.assertIsNone(
            manager.get("entity_999999")
        )

    def test_entity_varlik_kontrolu(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        self.assertTrue(
            manager.exists(entity.entity_id)
        )

    def test_olmayan_entity_varlik_kontrolu(self):
        manager = EntityManager()

        self.assertFalse(
            manager.exists("entity_999999")
        )

    def test_tum_entityleri_getirme(self):
        manager = EntityManager()

        entity1 = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity2 = Entity(
            entity_type="npc",
            name="Tüccar"
        )

        manager.add(entity1)
        manager.add(entity2)

        entities = manager.get_all()

        self.assertEqual(
            len(entities),
            2
        )

        self.assertIn(
            entity1,
            entities
        )

        self.assertIn(
            entity2,
            entities
        )

    def test_entity_silme(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        manager.remove(
            entity.entity_id
        )

        self.assertEqual(
            manager.count(),
            0
        )

        self.assertFalse(
            manager.exists(entity.entity_id)
        )

    def test_silinen_entity_bulunamaz(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        manager.remove(
            entity.entity_id
        )

        self.assertIsNone(
            manager.get(entity.entity_id)
        )

    def test_olmayan_entity_silinemez(self):
        manager = EntityManager()

        with self.assertRaises(KeyError):
            manager.remove("entity_999999")

    def test_gecersiz_entity_eklenemez(self):
        manager = EntityManager()

        with self.assertRaises(TypeError):
            manager.add("Muhafız")

    def test_none_entity_eklenemez(self):
        manager = EntityManager()

        with self.assertRaises(TypeError):
            manager.add(None)

    def test_ayni_entity_iki_kez_eklenemez(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        with self.assertRaises(ValueError):
            manager.add(entity)

    def test_ayni_id_iki_kez_kullanilamaz(self):
        manager = EntityManager()

        entity1 = Entity(
            entity_type="karakter",
            name="Muhafız",
            entity_id="entity_test"
        )

        entity2 = Entity(
            entity_type="npc",
            name="Tüccar",
            entity_id="entity_test"
        )

        manager.add(entity1)

        with self.assertRaises(ValueError):
            manager.add(entity2)

        self.assertIs(
            manager.get("entity_test"),
            entity1
        )

    def test_get_all_kopya_liste_dondurur(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        entities = manager.get_all()

        entities.clear()

        self.assertEqual(
            manager.count(),
            1
        )

    def test_coklu_entity_sayisi(self):
        manager = EntityManager()

        for i in range(5):
            entity = Entity(
                entity_type="karakter",
                name=f"Muhafız {i}"
            )

            manager.add(entity)

        self.assertEqual(
            manager.count(),
            5
        )

    def test_get_by_type(self):
        manager = EntityManager()

        karakter = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        npc = Entity(
            entity_type="npc",
            name="Tüccar"
        )

        manager.add(karakter)
        manager.add(npc)

        sonuc = manager.get_by_type("karakter")

        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIn(
            karakter,
            sonuc
        )

        self.assertNotIn(
            npc,
            sonuc
        )

    def test_get_by_status(self):
        manager = EntityManager()

        aktif = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        pasif = Entity(
            entity_type="npc",
            name="Tüccar"
        )

        pasif.deactivate()

        manager.add(aktif)
        manager.add(pasif)

        sonuc = manager.get_by_status("pasif")

        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIn(
            pasif,
            sonuc
        )

    def test_get_alive(self):
        manager = EntityManager()

        canli = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        olu = Entity(
            entity_type="npc",
            name="Düşman"
        )

        olu.kill()

        manager.add(canli)
        manager.add(olu)

        sonuc = manager.get_alive()

        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIn(
            canli,
            sonuc
        )

        self.assertNotIn(
            olu,
            sonuc
        )

    def test_get_active(self):
        manager = EntityManager()

        aktif = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        pasif = Entity(
            entity_type="npc",
            name="Tüccar"
        )

        pasif.deactivate()

        manager.add(aktif)
        manager.add(pasif)

        sonuc = manager.get_active()

        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIn(
            aktif,
            sonuc
        )

        self.assertNotIn(
            pasif,
            sonuc
        )

    def test_get_by_name(self):
        manager = EntityManager()

        entity1 = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        entity2 = Entity(
            entity_type="npc",
            name="Muhafız"
        )

        manager.add(entity1)
        manager.add(entity2)

        sonuc = manager.get_by_name("Muhafız")

        self.assertEqual(
            len(sonuc),
            2
        )

        self.assertIn(
            entity1,
            sonuc
        )

        self.assertIn(
            entity2,
            sonuc
        )

    def test_sorgu_sonucu_liste_kopyasidir(self):
        manager = EntityManager()

        entity = Entity(
            entity_type="karakter",
            name="Muhafız"
        )

        manager.add(entity)

        sonuc = manager.get_alive()

        sonuc.clear()

        self.assertEqual(
            manager.count(),
            1
        )


if __name__ == "__main__":
    unittest.main()