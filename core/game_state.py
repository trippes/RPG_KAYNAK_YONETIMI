"""
RPG Kaynak Yönetimi
Çekirdek 1.2 - Oyun Durumu

Oyunun temel durumunu merkezi olarak yönetir.
"""

from core.constants import (
    OYUN_DURUMU_BASLANGIC,
    OYUN_DURUMU_AKTIF,
    OYUN_DURUMU_DURAKLATILDI,
    OYUN_DURUMU_BITTI,
)


GECERLI_OYUN_DURUMLARI = {
    OYUN_DURUMU_BASLANGIC,
    OYUN_DURUMU_AKTIF,
    OYUN_DURUMU_DURAKLATILDI,
    OYUN_DURUMU_BITTI,
}


class GameState:
    """
    Oyunun merkezi durum nesnesidir.

    Bu sınıf henüz karakter, dünya veya ekonomi gibi
    üst sistemleri içermez. Sadece çekirdek oyun durumunu yönetir.
    """

    def __init__(self):
        self._durum = OYUN_DURUMU_BASLANGIC
        self._calisiyor = False
        self._bitmis = False

    @property
    def durum(self):
        """Mevcut oyun durumunu döndürür."""
        return self._durum

    @property
    def calisiyor(self):
        """Oyunun aktif olup olmadığını döndürür."""
        return self._calisiyor

    @property
    def bitmis(self):
        """Oyunun bitip bitmediğini döndürür."""
        return self._bitmis

    def baslat(self):
        """Oyunu başlatır."""

        if self._bitmis:
            raise RuntimeError(
                "Bitmiş bir oyun yeniden başlatılamaz."
            )

        self._durum = OYUN_DURUMU_AKTIF
        self._calisiyor = True

    def duraklat(self):
        """Aktif oyunu duraklatır."""

        if not self._calisiyor:
            raise RuntimeError(
                "Aktif olmayan oyun duraklatılamaz."
            )

        self._durum = OYUN_DURUMU_DURAKLATILDI
        self._calisiyor = False

    def devam_ettir(self):
        """Duraklatılmış oyunu devam ettirir."""

        if self._bitmis:
            raise RuntimeError(
                "Bitmiş oyun devam ettirilemez."
            )

        if self._durum != OYUN_DURUMU_DURAKLATILDI:
            raise RuntimeError(
                "Sadece duraklatılmış oyun devam ettirilebilir."
            )

        self._durum = OYUN_DURUMU_AKTIF
        self._calisiyor = True

    def bitir(self):
        """Oyunu sonlandırır."""

        if self._bitmis:
            raise RuntimeError(
                "Oyun zaten bitmiş durumda."
            )

        self._durum = OYUN_DURUMU_BITTI
        self._calisiyor = False
        self._bitmis = True

    def sifirla(self):
        """Oyun durumunu başlangıç durumuna döndürür."""

        self._durum = OYUN_DURUMU_BASLANGIC
        self._calisiyor = False
        self._bitmis = False

    def durum_kontrol(self, durum):
        """
        Verilen durumun geçerli bir oyun durumu olup olmadığını
        kontrol eder.
        """

        if durum not in GECERLI_OYUN_DURUMLARI:
            raise ValueError(
                f"Geçersiz oyun durumu: {durum}"
            )

        return True

    def bilgi(self):
        """Oyun durumunu sözlük olarak döndürür."""

        return {
            "durum": self._durum,
            "calisiyor": self._calisiyor,
            "bitmis": self._bitmis,
        }
