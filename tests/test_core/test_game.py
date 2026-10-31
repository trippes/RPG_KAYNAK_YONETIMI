import unittest

from core.game import Game
from core.event_manager import EventManager
from core.events import Event
from core.constants import (
    OLAY_OYUN_BASLATILDI,
    OLAY_OYUN_DURAKLATILDI,
    OLAY_OYUN_DEVAM_ETTIRILDI,
    OLAY_OYUN_BITTI,
)


class TestGame(unittest.TestCase):

    def test_game_olusturma(self):
        game = Game()

        self.assertIsNotNone(
            game.state
        )

        self.assertIsInstance(
            game.event_manager,
            EventManager
        )

        self.assertIs(
            game.events,
            game.event_manager.event_queue
        )

        self.assertEqual(
            game.bekleyen_olay_sayisi(),
            0
        )

    def test_game_baslatma_olayi(self):
        game = Game()

        game.baslat()

        self.assertEqual(
            game.bekleyen_olay_sayisi(),
            1
        )

        event = game.olay_al()

        self.assertIsInstance(
            event,
            Event
        )

        self.assertEqual(
            event.tur,
            OLAY_OYUN_BASLATILDI
        )

    def test_game_duraklatma_olayi(self):
        game = Game()

        game.baslat()
        game.olay_al()

        game.duraklat()

        event = game.olay_al()

        self.assertEqual(
            event.tur,
            OLAY_OYUN_DURAKLATILDI
        )

    def test_game_devam_ettirme_olayi(self):
        game = Game()

        game.baslat()
        game.olay_al()

        game.duraklat()
        game.olay_al()

        game.devam_ettir()

        event = game.olay_al()

        self.assertEqual(
            event.tur,
            OLAY_OYUN_DEVAM_ETTIRILDI
        )

    def test_game_bitis_olayi(self):
        game = Game()

        game.baslat()
        game.olay_al()

        game.bitir()

        event = game.olay_al()

        self.assertEqual(
            event.tur,
            OLAY_OYUN_BITTI
        )

    def test_game_sifirlama(self):
        game = Game()

        game.baslat()
        game.duraklat()

        self.assertEqual(
            game.bekleyen_olay_sayisi(),
            2
        )

        game.sifirla()

        self.assertEqual(
            game.bekleyen_olay_sayisi(),
            0
        )

    def test_game_bilgi(self):
        game = Game()

        bilgi = game.bilgi()

        self.assertIn(
            "state",
            bilgi
        )

        self.assertIn(
            "bekleyen_olay_sayisi",
            bilgi
        )

        self.assertEqual(
            bilgi["bekleyen_olay_sayisi"],
            0
        )

    def test_game_olaylari_isletme(self):
        game = Game()
        sonuc = []

        def callback(event):
            sonuc.append(event.tur)

        from core.event_handler import EventHandler

        handler = EventHandler(
            event_type=OLAY_OYUN_BASLATILDI,
            callback=callback
        )

        game.event_manager.event_bus.subscribe(
            handler
        )

        game.baslat()

        olay_sayisi, handler_sayisi = game.olaylari_islet()

        self.assertEqual(
            olay_sayisi,
            1
        )

        self.assertEqual(
            handler_sayisi,
            1
        )

        self.assertEqual(
            sonuc,
            [
                OLAY_OYUN_BASLATILDI
            ]
        )

        self.assertEqual(
            game.bekleyen_olay_sayisi(),
            0
        )

    def test_mevcut_events_api_korunur(self):
        game = Game()

        game.baslat()

        self.assertEqual(
            game.events.bekleyen_sayi(),
            1
        )

        event = game.events.al()

        self.assertEqual(
            event.tur,
            OLAY_OYUN_BASLATILDI
        )


if __name__ == "__main__":
    unittest.main()
