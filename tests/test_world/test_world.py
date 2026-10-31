import unittest

from core.entity import Entity, EntityType, Position
from core.world import World


class TestWorld(unittest.TestCase):

    def setUp(self):
        World._id_generator.reset()
        Entity._id_generator.reset()

    def test_world_olusturma(self):
        world = World(
            name="Ana Dünya"
        )

        self.assertEqual(
            world.world_id,
            "world_000001"
        )

        self.assertEqual(
            world.name,
            "Ana Dünya"
        )

    def test_world_boyutlari(self):
        world = World(
            name="Dünya",
            width=100,
            height=200
        )

        self.assertEqual(world.width, 100)
        self.assertEqual(world.height, 200)

    def test_world_boyutlari_none_olabilir(self):
        world = World(
            name="Dünya"
        )

        self.assertIsNone(world.width)
        self.assertIsNone(world.height)

    def test_world_ozel_id(self):
        world = World(
            name="Dünya",
            world_id="ana_dunya"
        )

        self.assertEqual(
            world.world_id,
            "ana_dunya"
        )

    def test_bos_isim_hata(self):
        with self.assertRaises(ValueError):
            World(name="")

    def test_gecersiz_isim_tipi_hata(self):
        with self.assertRaises(TypeError):
            World(name=123)

    def test_gecersiz_genislik_hata(self):
        with self.assertRaises(ValueError):
            World(
                name="Dünya",
                width=0
            )

    def test_gecersiz_yukseklik_hata(self):
        with self.assertRaises(ValueError):
            World(
                name="Dünya",
                height=-1
            )

    def test_entity_ekleme(self):
        world = World("Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)

        self.assertEqual(
            world.entity_count(),
            1
        )

        self.assertTrue(
            world.has_entity(entity.entity_id)
        )

    def test_entity_getirme(self):
        world = World("Dünya")

        entity = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar"
        )

        world.add_entity(entity)

        bulunan = world.get_entity(
            entity.entity_id
        )

        self.assertIs(
            bulunan,
            entity
        )

    def test_entity_bulunamazsa_none(self):
        world = World("Dünya")

        self.assertIsNone(
            world.get_entity("entity_999999")
        )

    def test_gecersiz_entity_ekleme(self):
        world = World("Dünya")

        with self.assertRaises(TypeError):
            world.add_entity("entity")

    def test_ayni_entity_iki_kez_eklenemez(self):
        world = World("Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)

        with self.assertRaises(ValueError):
            world.add_entity(entity)

    def test_entity_silme(self):
        world = World("Dünya")

        entity = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar"
        )

        world.add_entity(entity)

        silinen = world.remove_entity(
            entity.entity_id
        )

        self.assertIs(
            silinen,
            entity
        )

        self.assertEqual(
            world.entity_count(),
            0
        )

    def test_olmayan_entity_silme(self):
        world = World("Dünya")

        with self.assertRaises(KeyError):
            world.remove_entity(
                "entity_999999"
            )

    def test_tum_entityleri_getirme(self):
        world = World("Dünya")

        entity1 = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        entity2 = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar"
        )

        world.add_entity(entity1)
        world.add_entity(entity2)

        entities = world.get_entities()

        self.assertEqual(
            len(entities),
            2
        )

        self.assertIn(entity1, entities)
        self.assertIn(entity2, entities)

    def test_ture_gore_entity_getirme(self):
        world = World("Dünya")

        karakter = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        npc = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar"
        )

        world.add_entity(karakter)
        world.add_entity(npc)

        sonuc = world.get_entities_by_type(
            EntityType.KARAKTER
        )

        self.assertEqual(
            sonuc,
            [karakter]
        )

    def test_konuma_gore_entity_getirme(self):
        world = World("Dünya")

        entity1 = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız",
            position=Position(10, 20)
        )

        entity2 = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar",
            position=Position(10, 20)
        )

        entity3 = Entity(
            entity_type=EntityType.HAYVAN,
            name="At",
            position=Position(30, 40)
        )

        world.add_entity(entity1)
        world.add_entity(entity2)
        world.add_entity(entity3)

        sonuc = world.get_entities_by_position(
            Position(10, 20)
        )

        self.assertEqual(
            len(sonuc),
            2
        )

        self.assertIn(entity1, sonuc)
        self.assertIn(entity2, sonuc)
        self.assertNotIn(entity3, sonuc)

    def test_entityleri_temizleme(self):
        world = World("Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)
        world.clear_entities()

        self.assertEqual(
            world.entity_count(),
            0
        )

    def test_world_bilgi(self):
        world = World(
            name="Ana Dünya",
            width=100,
            height=200
        )

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)

        bilgi = world.get_info()

        self.assertEqual(
            bilgi["id"],
            "world_000001"
        )

        self.assertEqual(
            bilgi["ad"],
            "Ana Dünya"
        )

        self.assertEqual(
            bilgi["genislik"],
            100
        )

        self.assertEqual(
            bilgi["yukseklik"],
            200
        )

        self.assertEqual(
            bilgi["entity_sayisi"],
            1
        )


if __name__ == "__main__":
    unittest.main()
