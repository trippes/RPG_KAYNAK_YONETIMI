import unittest

from application import GameApplication, SessionBundle
from core.entity.entity import Entity
from core.entity.entity_type import EntityType


class TestGameApplication(unittest.TestCase):
    def test_create_default_has_one_active_bundle(self):
        application = GameApplication.create_default()
        self.assertIs(application.holder.current, application.holder.current)
        self.assertIs(
            application.holder.current.simulation,
            application.holder.current.session.simulation,
        )

    def test_legacy_start_world_and_info_match_game_surface(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Ana Dünya")
        application.baslat()

        info = application.bilgi()
        self.assertEqual(info["world_sayisi"], 1)
        self.assertIsNotNone(info["aktif_world_id"])
        self.assertEqual(info["entity_sayisi"], 0)
        self.assertEqual(info["aksiyon_sayisi"], 0)
        self.assertTrue(info["state"]["calisiyor"])

    def test_advance_simulation_uses_active_bundle_runtime(self):
        application = GameApplication.create_default()
        runtime = application.holder.current.simulation

        application.advance_simulation(4)

        self.assertEqual(runtime.current_tick.value, 4)
        self.assertEqual(application.holder.current.simulation.current_tick.value, 4)

    def test_publication_redirects_next_operations_to_candidate(self):
        application = GameApplication.create_default()
        old = application.holder.current
        old_world = application.dunya_olustur("Eski")
        candidate = SessionBundle.create_default()
        application.holder.publish(candidate)

        new_world = application.dunya_olustur("Yeni")

        self.assertIs(application.holder.current, candidate)
        self.assertIsNone(candidate.session.worlds.get(old_world.world_id))
        self.assertIs(old_world, old.session.worlds.get(old_world.world_id))
        self.assertIs(new_world, candidate.session.worlds.get(new_world.world_id))
        self.assertEqual(old.session.worlds.count(), 1)
        self.assertEqual(candidate.session.worlds.count(), 1)

    def test_invalid_publication_keeps_old_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current

        with self.assertRaises(TypeError):
            application.holder.publish(object())

        self.assertIs(application.holder.current, old)

    def test_entity_operations_use_current_bundle(self):
        application = GameApplication.create_default()
        entity = Entity(EntityType.NPC, "İşçi")
        application.varlik_ekle(entity)
        self.assertIs(application.holder.current.session.entities.get(entity.entity_id), entity)

        removed = application.varlik_cikar(entity.entity_id)
        self.assertIs(removed, entity)
        self.assertIsNone(application.holder.current.session.entities.get(entity.entity_id))

    def test_production_manager_uses_canonical_runtime(self):
        bundle = SessionBundle.create_default()
        application = GameApplication.create_default()
        application.holder.publish(bundle)

        self.assertIs(bundle.production_jobs.runtime, bundle.session.simulation)
        self.assertIs(bundle.production_jobs.runtime, application.holder.current.simulation)

    def test_legacy_actions_remain_separate_from_canonical_runtime(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Ana Dünya")
        application.baslat()
        legacy_action = application.aksiyon_baslat("toplama", "oyuncu", 2)

        self.assertEqual(application.holder.current.simulation.current_tick.value, 0)
        self.assertEqual(application.actions.aksiyon_sayisi(), 1)
        self.assertEqual(legacy_action.id, 1)

    def test_legacy_action_surface_is_backed_by_canonical_processor(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Ana Dünya")
        application.baslat()
        self.assertIs(application.actions.processor, application.holder.current.simulation.actions)

        action = application.aksiyon_baslat("toplama", "oyuncu", 2)
        application.zamani_ilerlet(2)
        self.assertEqual(action.durum.value, "tamamlandi")
        self.assertEqual(application.holder.current.simulation.current_tick.value, 2)


if __name__ == "__main__":
    unittest.main()
