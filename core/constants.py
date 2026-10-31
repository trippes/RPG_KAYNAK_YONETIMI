"""
RPG Kaynak Yönetimi
Çekirdek 1.2 - Temel Sabitler
"""

# ============================================================
# SAYI SSTEM
# ============================================================

TABAN = 60


# ============================================================
# PARA SSTEM
# ============================================================

GUMUS_SIKKE_BRONZ = 60
ALTIN_SIKKE_GUMUS = 60
ALTIN_SIKKE_BRONZ = GUMUS_SIKKE_BRONZ * ALTIN_SIKKE_GUMUS

TEMEL_PARA_BIRIMI = "bronz"


# ============================================================
# ZAMAN SSTEM
# ============================================================

TICK_SANIYE = 60
SANIYE_DAKIKA = 60
DAKIKA_SAAT = 60
SAAT_GUN = 24

GERCEK_DAKIKA_OYUN_GUNU = 24

GUN_AY = 30
AY_YIL = 12
GUN_YIL = GUN_AY * AY_YIL


# ============================================================
# MESAFE SSTEM
# ============================================================

TEMEL_MESAFE_BIRIMI = 1


# ============================================================
# ÖLÇÜ SSTEM
# ============================================================

OLCU_TABANI = 60


# ============================================================
# GENEL MATEMATK SABTLER
# ============================================================

SIFIR = 0
BIR = 1
YUZDE_TABANI = 100


# ============================================================
# KARAKTER MATEMAT
# ============================================================

OZELLIK_MODIFIKASYON_TABANI = 10
OZELLIK_MODIFIKASYON_BOLENI = 2


# ============================================================
# OYUN DURUMU SABTLER
# ============================================================

OYUN_DURUMU_BASLANGIC = "baslangic"
OYUN_DURUMU_AKTIF = "aktif"
OYUN_DURUMU_DURAKLATILDI = "duraklatildi"
OYUN_DURUMU_BITTI = "bitti"


# ============================================================
# OLAY SSTEM SABTLER
# ============================================================

OLAY_OYUN_BASLATILDI = "oyun_baslatildi"
OLAY_OYUN_DURAKLATILDI = "oyun_duraklatildi"
OLAY_OYUN_DEVAM_ETTIRILDI = "oyun_devam_ettirildi"
OLAY_OYUN_BITTI = "oyun_bitti"
