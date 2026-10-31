from time_system import (
    Tick,
    GameTime,
    Calendar,
    Scheduler,
    TICKS_PER_SECOND,
    TICKS_PER_MINUTE,
    TICKS_PER_HOUR,
    TICKS_PER_DAY,
    TICKS_PER_MONTH,
    TICKS_PER_YEAR,
)


class GameClock:
    """
    Oyunun merkezi zaman motoru.

    ÖNEML:
    GameClock zamanı kendi kendine ilerletmez.

    Diğer sistemler bir aksiyon gerçekleştirdiğinde
    harcanan zaman miktarını GameClock'a bildirir.

    Örnek:

        clock.advance(60)

    60 tick zaman ilerletir.

    Oyuncunun beklemesi:

        clock.advance_hours(1)

    1 saatlik zaman ilerletir.
    """

    def __init__(self, start_tick: int = 0):
        if not isinstance(start_tick, int):
            raise TypeError("start_tick tam sayı olmalıdır.")

        if start_tick < 0:
            raise ValueError("Başlangıç zamanı negatif olamaz.")

        self._total_ticks = start_tick
        self._running = True
        self._scheduler = None

    @property
    def total_ticks(self):
        return self._total_ticks

    @property
    def time(self):
        return GameTime(self._total_ticks)

    @property
    def running(self):
        return self._running

    @property
    def scheduler(self):
        return self._scheduler

    def attach_scheduler(self, scheduler):
        self._scheduler = scheduler

    def pause(self):
        self._running = False

    def resume(self):
        self._running = True

    def set_time(self, total_ticks: int):
        if not isinstance(total_ticks, int):
            raise TypeError("total_ticks tam sayı olmalıdır.")

        if total_ticks < 0:
            raise ValueError("Oyun zamanı negatif olamaz.")

        if total_ticks < self._total_ticks:
            raise ValueError(
                "Oyun zamanı geriye alınamaz."
            )

        self._total_ticks = total_ticks

        self._process_events()

    def advance(self, ticks):
        """
        Dünyayı verilen tick kadar ileri taşır.

        ticks:
            int veya Tick

        Örnek:
            advance(60)
            advance(Tick(30))
        """

        if isinstance(ticks, Tick):
            ticks = ticks.value

        if not isinstance(ticks, int):
            raise TypeError(
                "Zaman ilerlemesi tam sayı veya Tick olmalıdır."
            )

        if ticks < 0:
            raise ValueError(
                "Oyun zamanı geriye alınamaz."
            )

        if not self._running:
            return self.time

        self._total_ticks += ticks

        self._process_events()

        return self.time

    def advance_seconds(self, seconds):
        return self.advance(
            seconds * TICKS_PER_SECOND
        )

    def advance_minutes(self, minutes):
        return self.advance(
            minutes * TICKS_PER_MINUTE
        )

    def advance_hours(self, hours):
        return self.advance(
            hours * TICKS_PER_HOUR
        )

    def advance_days(self, days):
        return self.advance(
            days * TICKS_PER_DAY
        )

    def advance_months(self, months):
        return self.advance(
            months * TICKS_PER_MONTH
        )

    def advance_years(self, years):
        return self.advance(
            years * TICKS_PER_YEAR
        )

    def _process_events(self):
        if self._scheduler is not None:
            self._scheduler.process_until(
                self._total_ticks
            )

    def get_time(self):
        return self.time

    def reset(self):
        self._total_ticks = 0
        self._running = True

        if self._scheduler is not None:
            self._scheduler.clear()
