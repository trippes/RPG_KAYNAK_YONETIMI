import unittest

from core.event_types import EventType


class TestEventType(unittest.TestCase):

    def test_oyun_olaylari(self):
        self.assertEqual(
            EventType.OYUN_BASLATILDI,
            "oyun_baslatildi"
        )

        self.assertEqual(
            EventType.OYUN_DURAKLATILDI,
            "oyun_duraklatildi"
        )

        self.assertEqual(
            EventType.OYUN_DEVAM_ETTIRILDI,
            "oyun_devam_ettirildi"
        )

        self.assertEqual(
            EventType.OYUN_BITTI,
            "oyun_bitti"
        )

    def test_entity_olaylari(self):
        self.assertEqual(
            EventType.ENTITY_OLUSTURULDU,
            "entity_olusturuldu"
        )

        self.assertEqual(
            EventType.ENTITY_YOK_EDILDI,
            "entity_yok_edildi"
        )

        self.assertEqual(
            EventType.ENTITY_DURUM_DEGISTI,
            "entity_durum_degisti"
        )

    def test_position_olayi(self):
        self.assertEqual(
            EventType.POSITION_DEGISTI,
            "position_degisti"
        )

    def test_aksiyon_olaylari(self):
        self.assertEqual(
            EventType.AKSIYON_BASLATILDI,
            "aksiyon_baslatildi"
        )

        self.assertEqual(
            EventType.AKSIYON_TAMAMLANDI,
            "aksiyon_tamamlandi"
        )

        self.assertEqual(
            EventType.AKSIYON_IPTAL_EDILDI,
            "aksiyon_iptal_edildi"
        )

    def test_zaman_olayi(self):
        self.assertEqual(
            EventType.ZAMAN_ILERLEDI,
            "zaman_ilerledi"
        )


if __name__ == "__main__":
    unittest.main()
