import unittest

from core.actions import Action, ActionDurumu


class TestAction(unittest.TestCase):

    def test_aksiyon_olusturma(self):
        aksiyon = Action(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        self.assertEqual(aksiyon.tur, "dinlenme")
        self.assertEqual(aksiyon.sahip, "karakter_1")
        self.assertEqual(aksiyon.sure, 60)
        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.BEKLIYOR,
        )

    def test_aksiyon_baslatma(self):
        aksiyon = Action(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        aksiyon.baslat(100)

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.AKTIF,
        )

        self.assertEqual(
            aksiyon.baslangic_zamani,
            100,
        )

        self.assertEqual(
            aksiyon.bitis_zamani,
            160,
        )

    def test_aksiyon_tamamlanma(self):
        aksiyon = Action(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        aksiyon.baslat(100)

        self.assertFalse(
            aksiyon.tamamlanma_kontrolu(159)
        )

        self.assertTrue(
            aksiyon.tamamlanma_kontrolu(160)
        )

        aksiyon.tamamla(
            160,
            sonuc="dinlenme tamamlandi",
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.TAMAMLANDI,
        )

        self.assertEqual(
            aksiyon.sonuc,
            "dinlenme tamamlandi",
        )

    def test_aksiyon_iptal(self):
        aksiyon = Action(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        aksiyon.baslat(100)
        aksiyon.iptal_et()

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.IPTAL,
        )

    def test_aksiyon_basarisiz(self):
        aksiyon = Action(
            tur="uret",
            sahip="karakter_1",
            sure=120,
        )

        aksiyon.baslat(100)
        aksiyon.basarisiz("yeterli kaynak yok")

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.BASARISIZ,
        )

        self.assertEqual(
            aksiyon.sonuc,
            "yeterli kaynak yok",
        )

    def test_gecersiz_durum_gecisleri(self):
        aksiyon = Action(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        with self.assertRaises(ValueError):
            aksiyon.tamamla(60)

        with self.assertRaises(ValueError):
            aksiyon.basarisiz()

    def test_negatif_sure(self):
        with self.assertRaises(ValueError):
            Action(
                tur="hata",
                sahip="karakter_1",
                sure=-1,
            )


if __name__ == "__main__":
    unittest.main()
