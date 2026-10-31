import unittest

from core.actions.action import ActionDurumu
from core.entity import Entity
from core.game import Game
from core.event_types import EventType


class TestGameIntegration(unittest.TestCase):

    def test_varlik_aktif_dunyaya_eklenir(self):
        game = Game()
        world = game.dunya_olustur("Ana Dünya")
        entity = Entity("karakter", "Arin")

        game.varlik_ekle(entity)

        self.assertIs(game.entities.get(entity.entity_id), entity)
        self.assertTrue(world.has_entity(entity.entity_id))
        self.assertEqual(entity.world_id, world.world_id)

    def test_zaman_aksiyonu_tamamlar_ve_olay_uretir(self):
        game = Game()
        game.dunya_olustur("Ana Dünya")
        game.baslat()
        game.olay_al()  # başlatma olayı

        action = game.aksiyon_baslat("toplama", "oyuncu", 5)
        game.zamani_ilerlet(5)

        self.assertEqual(action.durum, ActionDurumu.TAMAMLANDI)
        event_types = []
        while game.bekleyen_olay_sayisi():
            event_types.append(game.olay_al().tur)
        self.assertIn(EventType.ZAMAN_ILERLEDI, event_types)
        self.assertIn(EventType.AKSIYON_TAMAMLANDI, event_types)

    def test_duraklatilan_oyunda_zaman_ilerlemez(self):
        game = Game()
        world = game.dunya_olustur("Ana Dünya")
        game.baslat()
        game.duraklat()

        with self.assertRaises(RuntimeError):
            game.zamani_ilerlet(1)
        self.assertEqual(world.total_ticks, 0)

    def test_dunya_zamanlayici_olayi_ana_kuyruga_aktarilir(self):
        game = Game()
        world = game.dunya_olustur("Ana Dünya")
        world.schedule_event(
            3,
            lambda: world.emit_event("hasat_hazir", {"miktar": 2}),
        )
        game.baslat()
        game.olay_al()

        game.zamani_ilerlet(3)

        events = []
        while game.bekleyen_olay_sayisi():
            events.append(game.olay_al())
        hasat = next(event for event in events if event.tur == "hasat_hazir")
        self.assertEqual(hasat.veri, {"miktar": 2})


if __name__ == "__main__":
    unittest.main()
