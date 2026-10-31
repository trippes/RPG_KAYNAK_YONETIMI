"""
RPG Kaynak Yönetimi
Çekirdek 1.2 - Olay Sistemi

Oyundaki temel olayların merkezi olarak oluşturulmasını
ve taşınmasını sağlar.
"""

from datetime import datetime
from core.compatibility.usage import record_usage


class Event:
    """
    Oyunda gerçekleşen tek bir olayı temsil eder.
    """

    def __init__(self, tur, veri=None):
        if not isinstance(tur, str):
            raise TypeError(
                "Olay türü metin olmalıdır."
            )

        if not tur.strip():
            raise ValueError(
                "Olay türü boş olamaz."
            )

        if veri is not None and not isinstance(veri, dict):
            raise TypeError(
                "Olay verisi sözlük veya None olmalıdır."
            )

        self.tur = tur
        self.veri = veri.copy() if veri is not None else {}
        self.zaman = datetime.now()

    def bilgi(self):
        """Olayı sözlük biçiminde döndürür."""

        return {
            "tur": self.tur,
            "veri": self.veri.copy(),
            "zaman": self.zaman,
        }

    def __repr__(self):
        return (
            f"Event("
            f"tur={self.tur!r}, "
            f"veri={self.veri!r}"
            f")"
        )


class EventQueue:
    """
    Oyun olaylarını sırayla tutan temel olay kuyruğudur.
    """

    def __init__(self):
        record_usage("core.events.EventQueue")
        self._olaylar = []

    def ekle(self, olay):
        """Kuyruğa yeni olay ekler."""

        if not isinstance(olay, Event):
            raise TypeError(
                "Kuyruğa yalnızca Event nesnesi eklenebilir."
            )

        self._olaylar.append(olay)

    def al(self):
        """Kuyruktaki ilk olayı çıkarıp döndürür."""

        if not self._olaylar:
            return None

        return self._olaylar.pop(0)

    def bekleyen_sayi(self):
        """Kuyrukta bekleyen olay sayısını döndürür."""

        return len(self._olaylar)

    def bos_mu(self):
        """Kuyruğun boş olup olmadığını döndürür."""

        return len(self._olaylar) == 0

    def temizle(self):
        """Kuyruğu tamamen temizler."""

        self._olaylar.clear()

    def listele(self):
        """Kuyruktaki olayların kopyasını döndürür."""

        return list(self._olaylar)
