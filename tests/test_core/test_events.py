import unittest

from core.events import Event


class TestEvent(unittest.TestCase):

    def test_event_olusturma(self):
        event = Event(
            tur="oyun_baslatildi"
        )

        self.assertEqual(
            event.tur,
            "oyun_baslatildi"
        )

        self.assertEqual(
            event.veri,
            {}
        )

        self.assertIsNotNone(
            event.zaman
        )

    def test_event_veri_ile_olusturma(self):
        veri = {
            "oyuncu": "Muhafız",
            "seviye": 5
        }

        event = Event(
            tur="karakter_olusturuldu",
            veri=veri
        )

        self.assertEqual(
            event.tur,
            "karakter_olusturuldu"
        )

        self.assertEqual(
            event.veri,
            veri
        )

    def test_event_veri_kopyalanir(self):
        veri = {
            "deger": 10
        }

        event = Event(
            tur="test",
            veri=veri
        )

        veri["deger"] = 20

        self.assertEqual(
            event.veri["deger"],
            10
        )

    def test_event_bilgi(self):
        event = Event(
            tur="oyun_baslatildi",
            veri={
                "test": True
            }
        )

        bilgi = event.bilgi()

        self.assertEqual(
            bilgi["tur"],
            "oyun_baslatildi"
        )

        self.assertEqual(
            bilgi["veri"],
            {
                "test": True
            }
        )

        self.assertEqual(
            bilgi["zaman"],
            event.zaman
        )

    def test_event_gecersiz_tur(self):
        with self.assertRaises(TypeError):
            Event(
                tur=123
            )

    def test_event_bos_tur(self):
        with self.assertRaises(ValueError):
            Event(
                tur=""
            )

    def test_event_sadece_bosluk_tur(self):
        with self.assertRaises(ValueError):
            Event(
                tur="   "
            )

    def test_event_gecersiz_veri(self):
        with self.assertRaises(TypeError):
            Event(
                tur="test",
                veri="gecersiz"
            )

    def test_event_repr(self):
        event = Event(
            tur="test",
            veri={
                "deger": 5
            }
        )

        sonuc = repr(event)

        self.assertIn(
            "Event",
            sonuc
        )

        self.assertIn(
            "test",
            sonuc
        )


if __name__ == "__main__":
    unittest.main()
