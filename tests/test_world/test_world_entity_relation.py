import unittest

from core.entity import Entity, EntityType
from core.world import World


class TestWorldEntityRelation(unittest.TestCase):

    def setUp(self):
        Entity._id_generator.reset()
        World._id_generator.reset()

    def test_entity_baslangicta_worldsuzdur(self):
        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        self.assertIsNone(entity.world_id)
        self.assertFalse(entity.has_world())

    def test_entity_worlde_baglanir(self):
        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        entity.assign_world("world_000001")

        self.assertEqual(
            entity.world_id,
            "world_000001"
        )

        self.assertTrue(entity.has_world())

    def test_entity_worldden_ayrilir(self):
        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        entity.assign_world("world_000001")
        entity.remove_from_world()

        self.assertIsNone(entity.world_id)
        self.assertFalse(entity.has_world())

    def test_entity_iki_worlde_baglanamaz(self):
        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        entity.assign_world("world_000001")

        with self.assertRaises(ValueError):
            entity.assign_world("world_000002")

    def test_world_entity_ekleyince_baglanti_kurulur(self):
        world = World("Ana Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)

        self.assertEqual(
            entity.world_id,
            world.world_id
        )

        self.assertTrue(entity.has_world())

    def test_worldden_entity_silince_baglanti_kopar(self):
        world = World("Ana Dünya")

        entity = Entity(
            entity_type=EntityType.NPC,
            name="Tüccar"
        )

        world.add_entity(entity)
        world.remove_entity(entity.entity_id)

        self.assertIsNone(entity.world_id)
        self.assertFalse(entity.has_world())

    def test_entity_baska_worlde_eklenemez(self):
        world1 = World("Birinci Dünya")
        world2 = World("kinci Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world1.add_entity(entity)

        with self.assertRaises(ValueError):
            world2.add_entity(entity)

    def test_world_clear_entity_world_baglantisini_temizler(self):
        world = World("Ana Dünya")

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

        world.clear_entities()

        self.assertFalse(entity1.has_world())
        self.assertFalse(entity2.has_world())

        self.assertEqual(
            world.entity_count(),
            0
        )

    def test_entity_bilgisinde_world_id(self):
        world = World("Ana Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world.add_entity(entity)

        bilgi = entity.get_info()

        self.assertEqual(
            bilgi["world_id"],
            world.world_id
        )

    def test_entity_baska_worlde_gecabilir(self):
        world1 = World("Birinci Dünya")
        world2 = World("kinci Dünya")

        entity = Entity(
            entity_type=EntityType.KARAKTER,
            name="Muhafız"
        )

        world1.add_entity(entity)
        world1.remove_entity(entity.entity_id)

        world2.add_entity(entity)

        self.assertEqual(
            entity.world_id,
            world2.world_id
        )

        self.assertTrue(
            world2.has_entity(entity.entity_id)
        )


if __name__ == "__main__":
    unittest.main()
