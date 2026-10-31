from typing import Any, Optional

from .action import Action, ActionDurumu


class ActionManager:
    def __init__(self) -> None:
        self._aksiyonlar: dict[int, Action] = {}
        self._siradaki_id: int = 1

    def aksiyon_olustur(
        self,
        tur: str,
        sahip: Any,
        sure: int,
        veri: Optional[dict[str, Any]] = None,
    ) -> Action:

        if sure < 0:
            raise ValueError(
                "Aksiyon suresi negatif olamaz."
            )

        aksiyon = Action(
            id=self._siradaki_id,
            tur=tur,
            sahip=sahip,
            sure=sure,
            veri=veri or {},
        )

        self._aksiyonlar[aksiyon.id] = aksiyon
        self._siradaki_id += 1

        return aksiyon

    def aksiyon_baslat(
        self,
        aksiyon_id: int,
        zaman: int,
    ) -> Action:

        aksiyon = self.aksiyon_getir(aksiyon_id)

        if aksiyon is None:
            raise KeyError(
                f"Aksiyon bulunamadi: {aksiyon_id}"
            )

        aksiyon.baslat(zaman)

        return aksiyon

    def aksiyon_tamamla(
        self,
        aksiyon_id: int,
        zaman: int,
        sonuc: Any = None,
    ) -> Action:

        aksiyon = self.aksiyon_getir(aksiyon_id)

        if aksiyon is None:
            raise KeyError(
                f"Aksiyon bulunamadi: {aksiyon_id}"
            )

        aksiyon.tamamla(zaman, sonuc)

        return aksiyon

    def aksiyon_iptal_et(
        self,
        aksiyon_id: int,
    ) -> Action:

        aksiyon = self.aksiyon_getir(aksiyon_id)

        if aksiyon is None:
            raise KeyError(
                f"Aksiyon bulunamadi: {aksiyon_id}"
            )

        aksiyon.iptal_et()

        return aksiyon

    def aksiyon_basarisiz(
        self,
        aksiyon_id: int,
        sonuc: Any = None,
    ) -> Action:

        aksiyon = self.aksiyon_getir(aksiyon_id)

        if aksiyon is None:
            raise KeyError(
                f"Aksiyon bulunamadi: {aksiyon_id}"
            )

        aksiyon.basarisiz(sonuc)

        return aksiyon

    def aksiyon_getir(
        self,
        aksiyon_id: int,
    ) -> Optional[Action]:

        return self._aksiyonlar.get(aksiyon_id)

    def aktif_aksiyonlar(self) -> list[Action]:

        return [
            aksiyon
            for aksiyon in self._aksiyonlar.values()
            if aksiyon.durum == ActionDurumu.AKTIF
        ]

    def bekleyen_aksiyonlar(self) -> list[Action]:

        return [
            aksiyon
            for aksiyon in self._aksiyonlar.values()
            if aksiyon.durum == ActionDurumu.BEKLIYOR
        ]

    def tamamlanan_aksiyonlar(self) -> list[Action]:

        return [
            aksiyon
            for aksiyon in self._aksiyonlar.values()
            if aksiyon.durum == ActionDurumu.TAMAMLANDI
        ]

    def guncelle(self, zaman: int) -> list[Action]:

        tamamlananlar: list[Action] = []

        for aksiyon in self.aktif_aksiyonlar():

            if aksiyon.tamamlanma_kontrolu(zaman):
                aksiyon.tamamla(zaman)
                tamamlananlar.append(aksiyon)

        return tamamlananlar

    def aksiyon_sayisi(self) -> int:
        return len(self._aksiyonlar)
