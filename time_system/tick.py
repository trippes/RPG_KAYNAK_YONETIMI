from dataclasses import dataclass


# ============================================================
# ZAMAN SABTLER
# ============================================================

TICKS_PER_SECOND = 60
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30
MONTHS_PER_YEAR = 12

TICKS_PER_MINUTE = TICKS_PER_SECOND * SECONDS_PER_MINUTE
TICKS_PER_HOUR = TICKS_PER_MINUTE * MINUTES_PER_HOUR
TICKS_PER_DAY = TICKS_PER_HOUR * HOURS_PER_DAY
TICKS_PER_MONTH = TICKS_PER_DAY * DAYS_PER_MONTH
TICKS_PER_YEAR = TICKS_PER_MONTH * MONTHS_PER_YEAR


@dataclass(frozen=True, order=True)
class Tick:
    """
    Oyundaki en küçük zaman birimi.

    Tick doğrudan dünya zamanını ilerletmez.
    Bir aksiyon tarafından tüketildiğinde GameClock'a aktarılır.
    """

    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise TypeError("Tick değeri tam sayı olmalıdır.")

        if self.value < 0:
            raise ValueError("Tick değeri negatif olamaz.")

    def __int__(self):
        return self.value

    def __add__(self, other):
        if isinstance(other, Tick):
            return Tick(self.value + other.value)

        if isinstance(other, int):
            return Tick(self.value + other)

        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Tick):
            result = self.value - other.value
        elif isinstance(other, int):
            result = self.value - other
        else:
            return NotImplemented

        if result < 0:
            raise ValueError("Tick değeri negatif olamaz.")

        return Tick(result)

    def __mul__(self, other):
        if isinstance(other, int):
            return Tick(self.value * other)

        return NotImplemented

    def __repr__(self):
        return f"Tick({self.value})"


@dataclass(frozen=True)
class GameTime:
    """
    Toplam tick değerinin okunabilir oyun zamanına dönüşmüş hali.

    Takvim:
        12 ay / yıl
        30 gün / ay
        24 saat / gün
        60 dakika / saat
        60 saniye / dakika
        60 tick / saniye
    """

    total_ticks: int

    def __post_init__(self):
        if not isinstance(self.total_ticks, int):
            raise TypeError("total_ticks tam sayı olmalıdır.")

        if self.total_ticks < 0:
            raise ValueError("Oyun zamanı negatif olamaz.")

    @property
    def tick(self):
        return self.total_ticks % TICKS_PER_SECOND

    @property
    def second(self):
        return (self.total_ticks // TICKS_PER_SECOND) % SECONDS_PER_MINUTE

    @property
    def minute(self):
        return (self.total_ticks // TICKS_PER_MINUTE) % MINUTES_PER_HOUR

    @property
    def hour(self):
        return (self.total_ticks // TICKS_PER_HOUR) % HOURS_PER_DAY

    @property
    def day(self):
        return (self.total_ticks // TICKS_PER_DAY) % DAYS_PER_MONTH + 1

    @property
    def month(self):
        return (self.total_ticks // TICKS_PER_MONTH) % MONTHS_PER_YEAR + 1

    @property
    def year(self):
        return self.total_ticks // TICKS_PER_YEAR + 1

    def as_dict(self):
        return {
            "yil": self.year,
            "ay": self.month,
            "gun": self.day,
            "saat": self.hour,
            "dakika": self.minute,
            "saniye": self.second,
            "tik": self.tick,
            "toplam_tik": self.total_ticks,
        }

    def __str__(self):
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d} "
            f"{self.hour:02d}:{self.minute:02d}:{self.second:02d} "
            f"({self.tick:02d} tık)"
        )
