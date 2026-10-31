from dataclasses import dataclass

from .tick import (
    TICKS_PER_DAY,
    TICKS_PER_MONTH,
    TICKS_PER_YEAR,
    GameTime,
)


@dataclass(frozen=True)
class Calendar:
    """
    Oyunun takvim sistemi.

    Bir yıl:
        12 ay

    Bir ay:
        30 gün

    Bir yıl:
        360 gün
    """

    months_per_year: int = 12
    days_per_month: int = 30

    @property
    def days_per_year(self):
        return self.months_per_year * self.days_per_month

    def from_ticks(self, total_ticks: int) -> GameTime:
        return GameTime(total_ticks)

    def to_ticks(
        self,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        tick: int = 0,
    ) -> int:

        if year < 1:
            raise ValueError("Yıl 1 veya daha büyük olmalıdır.")

        if not 1 <= month <= self.months_per_year:
            raise ValueError("Geçersiz ay.")

        if not 1 <= day <= self.days_per_month:
            raise ValueError("Geçersiz gün.")

        if not 0 <= hour < 24:
            raise ValueError("Geçersiz saat.")

        if not 0 <= minute < 60:
            raise ValueError("Geçersiz dakika.")

        if not 0 <= second < 60:
            raise ValueError("Geçersiz saniye.")

        if not 0 <= tick < 60:
            raise ValueError("Geçersiz tık.")

        total_days = (
            (year - 1) * self.days_per_year
            + (month - 1) * self.days_per_month
            + (day - 1)
        )

        return (
            total_days * TICKS_PER_DAY
            + hour * 60 * 60 * 60
            + minute * 60 * 60
            + second * 60
            + tick
        )
