from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ActionDurumu(Enum):
    BEKLIYOR = "bekliyor"
    AKTIF = "aktif"
    TAMAMLANDI = "tamamlandi"
    IPTAL = "iptal"
    BASARISIZ = "basarisiz"


@dataclass
class Action:
    tur: str
    sahip: Any
    sure: int
    veri: dict[str, Any] = field(default_factory=dict)

    id: Optional[int] = None
    durum: ActionDurumu = ActionDurumu.BEKLIYOR

    baslangic_zamani: Optional[int] = None
    bitis_zamani: Optional[int] = None

    sonuc: Any = None

    def __post_init__(self) -> None:
        if self.sure < 0:
            raise ValueError(
                "Aksiyon suresi negatif olamaz."
            )

    def baslat(self, zaman: int) -> None:
        if self.durum != ActionDurumu.BEKLIYOR:
            raise ValueError(
                "Sadece bekleyen aksiyonlar baslatilabilir."
            )

        if self.sure < 0:
            raise ValueError(
                "Aksiyon suresi negatif olamaz."
            )

        self.baslangic_zamani = zaman
        self.bitis_zamani = zaman + self.sure
        self.durum = ActionDurumu.AKTIF

    def tamamla(self, zaman: int, sonuc: Any = None) -> None:
        if self.durum != ActionDurumu.AKTIF:
            raise ValueError(
                "Sadece aktif aksiyonlar tamamlanabilir."
            )

        if self.bitis_zamani is not None and zaman < self.bitis_zamani:
            raise ValueError(
                "Aksiyon suresi dolmadan tamamlanamaz."
            )

        self.sonuc = sonuc
        self.durum = ActionDurumu.TAMAMLANDI

    def iptal_et(self) -> None:
        if self.durum not in (
            ActionDurumu.BEKLIYOR,
            ActionDurumu.AKTIF,
        ):
            raise ValueError(
                "Bu durumdaki aksiyon iptal edilemez."
            )

        self.durum = ActionDurumu.IPTAL

    def basarisiz(self, sonuc: Any = None) -> None:
        if self.durum != ActionDurumu.AKTIF:
            raise ValueError(
                "Sadece aktif aksiyonlar basarisiz olabilir."
            )

        self.sonuc = sonuc
        self.durum = ActionDurumu.BASARISIZ

    def tamamlanma_kontrolu(self, zaman: int) -> bool:
        if self.durum != ActionDurumu.AKTIF:
            return False

        if self.bitis_zamani is None:
            return False

        return zaman >= self.bitis_zamani
