"""
RPG Kaynak Yönetimi
Çekirdek 1.6 - Olay Türleri

Motor içerisindeki standart olay türlerini merkezi olarak tanımlar.
"""


class EventType:
    """Motor içerisindeki standart olay türlerini tanımlar."""

    OYUN_BASLATILDI = "oyun_baslatildi"
    OYUN_DURAKLATILDI = "oyun_duraklatildi"
    OYUN_DEVAM_ETTIRILDI = "oyun_devam_ettirildi"
    OYUN_BITTI = "oyun_bitti"

    ENTITY_OLUSTURULDU = "entity_olusturuldu"
    ENTITY_YOK_EDILDI = "entity_yok_edildi"
    ENTITY_DURUM_DEGISTI = "entity_durum_degisti"

    POSITION_DEGISTI = "position_degisti"

    AKSIYON_BASLATILDI = "aksiyon_baslatildi"
    AKSIYON_TAMAMLANDI = "aksiyon_tamamlandi"
    AKSIYON_IPTAL_EDILDI = "aksiyon_iptal_edildi"

    ZAMAN_ILERLEDI = "zaman_ilerledi"
