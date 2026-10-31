import unittest

from core.actions import ActionDurumu, ActionManager


class TestActionManager(unittest.TestCase):

    def test_aksiyon_olusturma(self):
        manager = ActionManager()

        aksiyon = manager.aksiyon_olustur(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        self.assertEqual(aksiyon.id, 1)
        self.assertEqual(manager.aksiyon_sayisi(), 1)

    def test_id_artisi(self):
        manager = ActionManager()

        birinci = manager.aksiyon_olustur(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        ikinci = manager.aksiyon_olustur(
            tur="yurume",
            sahip="karakter_1",
            sure=120,
        )

        self.assertEqual(birinci.id, 1)
        self.assertEqual(ikinci.id, 2)

    def test_aksiyon_yasam_dongusu(self):
        manager = ActionManager()

        aksiyon = manager.aksiyon_olustur(
            tur="dinlenme",
            sahip="karakter_1",
            sure=60,
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.BEKLIYOR,
        )

        manager.aksiyon_baslat(
            aksiyon.id,
            100,
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.AKTIF,
        )

        tamamlananlar = manager.guncelle(159)

        self.assertEqual(
            len(tamamlananlar),
            0,
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.AKTIF,
        )

        tamamlananlar = manager.guncelle(160)

        self.assertEqual(
            len(tamamlananlar),
            1,
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.TAMAMLANDI,
        )

    def test_aktif_aksiyonlar(self):
        manager = ActionManager()

        birinci = manager.aksiyon_olustur(
            "dinlenme",
            "karakter_1",
            60,
        )

        ikinci = manager.aksiyon_olustur(
            "yurume",
            "karakter_1",
            120,
        )

        manager.aksiyon_baslat(
            birinci.id,
            0,
        )

        aktif = manager.aktif_aksiyonlar()

        self.assertEqual(len(aktif), 1)
        self.assertEqual(aktif[0].id, birinci.id)

        self.assertEqual(
            ikinci.durum,
            ActionDurumu.BEKLIYOR,
        )

    def test_iptal(self):
        manager = ActionManager()

        aksiyon = manager.aksiyon_olustur(
            "dinlenme",
            "karakter_1",
            60,
        )

        manager.aksiyon_baslat(
            aksiyon.id,
            0,
        )

        manager.aksiyon_iptal_et(
            aksiyon.id
        )

        self.assertEqual(
            aksiyon.durum,
            ActionDurumu.IPTAL,
        )

        self.assertEqual(
            len(manager.aktif_aksiyonlar()),
            0,
        )

    def test_olmayan_aksiyon(self):
        manager = ActionManager()

        with self.assertRaises(KeyError):
            manager.aksiyon_baslat(
                999,
                0,
            )


if __name__ == "__main__":
    unittest.main()
