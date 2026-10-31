import unittest

from core.entity import EntityState


class TestEntityState(unittest.TestCase):

    def test_baslangic_durumu(self):
        state = EntityState()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_active()
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_durum_degistirme(self):
        state = EntityState()

        state.set_status("pasif")

        self.assertEqual(
            state.get_status(),
            "pasif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_pasiflestirme(self):
        state = EntityState()

        state.deactivate()

        self.assertEqual(
            state.get_status(),
            "pasif"
        )

        self.assertFalse(
            state.is_active()
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_aktiflestirme(self):
        state = EntityState()

        state.deactivate()
        state.activate()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_active()
        )

    def test_olum(self):
        state = EntityState()

        state.kill()

        self.assertEqual(
            state.get_status(),
            "olu"
        )

        self.assertFalse(
            state.is_active()
        )

        self.assertFalse(
            state.is_alive()
        )

    def test_diriltme(self):
        state = EntityState()

        state.kill()
        state.revive()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_active()
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_durum_bilgisi(self):
        state = EntityState()

        state.deactivate()

        bilgiler = state.get_state()

        self.assertEqual(
            bilgiler["durum"],
            "pasif"
        )

        self.assertTrue(
            bilgiler["canli"]
        )

    def test_gecerli_durum_aktif(self):
        state = EntityState()

        state.set_status("aktif")

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

    def test_gecerli_durum_pasif(self):
        state = EntityState()

        state.set_status("pasif")

        self.assertEqual(
            state.get_status(),
            "pasif"
        )

    def test_gecerli_durum_olu(self):
        state = EntityState()

        state.set_status("olu")

        self.assertEqual(
            state.get_status(),
            "olu"
        )

        self.assertFalse(
            state.is_alive()
        )

    def test_gecersiz_durum(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.set_status("asdf")

    def test_bos_durum(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.set_status("")

    def test_none_durum(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.set_status(None)

    def test_aktiften_pasife_gecis(self):
        state = EntityState()

        state.set_status("pasif")

        self.assertEqual(
            state.get_status(),
            "pasif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_aktiften_oluye_gecis(self):
        state = EntityState()

        state.set_status("olu")

        self.assertEqual(
            state.get_status(),
            "olu"
        )

        self.assertFalse(
            state.is_alive()
        )

    def test_pasiften_aktive_gecis(self):
        state = EntityState()

        state.set_status("pasif")
        state.set_status("aktif")

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_pasiften_oluye_gecis(self):
        state = EntityState()

        state.set_status("pasif")
        state.set_status("olu")

        self.assertEqual(
            state.get_status(),
            "olu"
        )

        self.assertFalse(
            state.is_alive()
        )

    def test_oluden_aktive_gecis_sadece_diriltme_ile(self):
        state = EntityState()

        state.kill()

        with self.assertRaises(ValueError):
            state.set_status("aktif")

        state.revive()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_oluden_pasife_gecis_engellenir(self):
        state = EntityState()

        state.kill()

        with self.assertRaises(ValueError):
            state.set_status("pasif")

    def test_aktif_durum_canli_tutarliligi(self):
        state = EntityState()

        state.activate()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_pasif_durum_canli_tutarliligi(self):
        state = EntityState()

        state.deactivate()

        self.assertEqual(
            state.get_status(),
            "pasif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_olu_durum_canli_tutarliligi(self):
        state = EntityState()

        state.kill()

        self.assertEqual(
            state.get_status(),
            "olu"
        )

        self.assertFalse(
            state.is_alive()
        )

    def test_olu_entity_aktiflestirilemez(self):
        state = EntityState()

        state.kill()

        with self.assertRaises(ValueError):
            state.activate()

    def test_olu_entity_pasiflestirilemez(self):
        state = EntityState()

        state.kill()

        with self.assertRaises(ValueError):
            state.deactivate()

    def test_aktif_entity_diriltilemez(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.revive()

    def test_pasif_entity_diriltilemez(self):
        state = EntityState()

        state.deactivate()

        with self.assertRaises(ValueError):
            state.revive()

    def test_diriltme_sonrasi_tutarlilik(self):
        state = EntityState()

        state.kill()
        state.revive()

        self.assertEqual(
            state.get_status(),
            "aktif"
        )

        self.assertTrue(
            state.is_alive()
        )

    def test_baslangic_gecmisi(self):
        state = EntityState()

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            ["aktif"]
        )

    def test_pasiflestirme_gecmise_eklenir(self):
        state = EntityState()

        state.deactivate()

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            [
                "aktif",
                "pasif"
            ]
        )

    def test_durum_degisiklikleri_sirali_tutulur(self):
        state = EntityState()

        state.deactivate()
        state.activate()
        state.kill()

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            [
                "aktif",
                "pasif",
                "aktif",
                "olu"
            ]
        )

    def test_diriltme_gecmise_eklenir(self):
        state = EntityState()

        state.kill()
        state.revive()

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            [
                "aktif",
                "olu",
                "aktif"
            ]
        )

    def test_gecersiz_durum_gecmise_eklenmez(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.set_status("asdf")

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            ["aktif"]
        )

    def test_olu_entity_gecersiz_gecis_gecmisi_bozmaz(self):
        state = EntityState()

        state.kill()

        with self.assertRaises(ValueError):
            state.set_status("pasif")

        gecmis = state.get_history()

        self.assertEqual(
            gecmis,
            [
                "aktif",
                "olu"
            ]
        )

    def test_get_history_kopya_dondurur(self):
        state = EntityState()

        state.deactivate()

        gecmis = state.get_history()

        gecmis.append("hack")

        self.assertEqual(
            state.get_history(),
            [
                "aktif",
                "pasif"
            ]
        )
    def test_onceki_durum_baslangicta_none(self):
        state = EntityState()

        self.assertIsNone(
            state.get_previous_status()
        )

    def test_onceki_durum_dogru_dondurulur(self):
        state = EntityState()

        state.deactivate()

        self.assertEqual(
            state.get_previous_status(),
            "aktif"
        )

    def test_onceki_durum_coklu_geciste(self):
        state = EntityState()

        state.deactivate()
        state.activate()
        state.kill()

        self.assertEqual(
            state.get_previous_status(),
            "aktif"
        )

    def test_gecmis_uzunlugu_baslangicta(self):
        state = EntityState()

        self.assertEqual(
            state.get_history_length(),
            1
        )

    def test_gecmis_uzunlugu_durum_degisikliklerinde(self):
        state = EntityState()

        state.deactivate()
        state.activate()
        state.kill()

        self.assertEqual(
            state.get_history_length(),
            4
        )

    def test_gecmiste_bulunan_durum(self):
        state = EntityState()

        state.deactivate()
        state.activate()
        state.kill()

        self.assertTrue(
            state.has_status("aktif")
        )

        self.assertTrue(
            state.has_status("pasif")
        )

        self.assertTrue(
            state.has_status("olu")
        )

    def test_gecmiste_bulunmayan_durum(self):
        state = EntityState()

        self.assertFalse(
            state.has_status("pasif")
        )

        self.assertFalse(
            state.has_status("olu")
        )

    def test_has_status_gecersiz_durum(self):
        state = EntityState()

        with self.assertRaises(ValueError):
            state.has_status("asdf") 


if __name__ == "__main__":
    unittest.main()