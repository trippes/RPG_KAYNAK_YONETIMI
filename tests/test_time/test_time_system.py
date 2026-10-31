import unittest

from core.clock import GameClock
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
    random_start_tick,
)


class TestTick(unittest.TestCase):

    def test_random_start_tick_is_a_valid_non_epoch_date(self):
        tick = random_start_tick()
        game_time = GameTime(tick)

        self.assertGreaterEqual(game_time.year, 100)
        self.assertLessEqual(game_time.year, 9999)
        self.assertGreater(tick, 0)

    def test_tick_creation(self):
        tick = Tick(60)

        self.assertEqual(tick.value, 60)
        self.assertEqual(int(tick), 60)

    def test_tick_operations(self):
        self.assertEqual(
            Tick(30) + Tick(30),
            Tick(60),
        )

        self.assertEqual(
            Tick(30) + 30,
            Tick(60),
        )

        self.assertEqual(
            Tick(30) * 2,
            Tick(60),
        )


class TestGameTime(unittest.TestCase):

    def test_zero_time(self):
        time = GameTime(0)

        self.assertEqual(time.year, 1)
        self.assertEqual(time.month, 1)
        self.assertEqual(time.day, 1)
        self.assertEqual(time.hour, 0)
        self.assertEqual(time.minute, 0)
        self.assertEqual(time.second, 0)
        self.assertEqual(time.tick, 0)

    def test_one_minute(self):
        time = GameTime(TICKS_PER_MINUTE)

        self.assertEqual(time.minute, 1)
        self.assertEqual(time.second, 0)

    def test_one_hour(self):
        time = GameTime(TICKS_PER_HOUR)

        self.assertEqual(time.hour, 1)

    def test_one_day(self):
        time = GameTime(TICKS_PER_DAY)

        self.assertEqual(time.day, 2)
        self.assertEqual(time.hour, 0)

    def test_one_month(self):
        time = GameTime(TICKS_PER_MONTH)

        self.assertEqual(time.month, 2)
        self.assertEqual(time.day, 1)

    def test_one_year(self):
        time = GameTime(TICKS_PER_YEAR)

        self.assertEqual(time.year, 2)
        self.assertEqual(time.month, 1)
        self.assertEqual(time.day, 1)


class TestCalendar(unittest.TestCase):

    def test_calendar_conversion(self):
        calendar = Calendar()

        ticks = calendar.to_ticks(
            year=1,
            month=1,
            day=1,
            hour=3,
            minute=15,
            second=20,
            tick=30,
        )

        time = calendar.from_ticks(ticks)

        self.assertEqual(time.year, 1)
        self.assertEqual(time.month, 1)
        self.assertEqual(time.day, 1)
        self.assertEqual(time.hour, 3)
        self.assertEqual(time.minute, 15)
        self.assertEqual(time.second, 20)
        self.assertEqual(time.tick, 30)


class TestScheduler(unittest.TestCase):

    def test_event_triggers(self):
        scheduler = Scheduler()
        triggered = []

        scheduler.schedule(
            100,
            lambda: triggered.append("olay"),
        )

        scheduler.process_until(50)

        self.assertEqual(triggered, [])

        scheduler.process_until(100)

        self.assertEqual(triggered, ["olay"])

        self.assertEqual(
            scheduler.pending_count,
            0,
        )


class TestGameClock(unittest.TestCase):

    def test_action_advances_time(self):
        clock = GameClock()

        clock.advance(60)

        self.assertEqual(
            clock.total_ticks,
            60,
        )

        self.assertEqual(
            clock.time.second,
            1,
        )

    def test_walking_action(self):
        clock = GameClock()

        walking_time = 60

        clock.advance(walking_time)

        self.assertEqual(
            clock.total_ticks,
            60,
        )

    def test_running_action(self):
        clock = GameClock()

        running_time = 30

        clock.advance(running_time)

        self.assertEqual(
            clock.total_ticks,
            30,
        )

    def test_wait_one_hour(self):
        clock = GameClock()

        clock.advance_hours(1)

        self.assertEqual(
            clock.time.hour,
            1,
        )

    def test_wait_three_hours(self):
        clock = GameClock()

        clock.advance_hours(3)

        self.assertEqual(
            clock.time.hour,
            3,
        )

    def test_scheduler_with_clock(self):
        clock = GameClock()
        scheduler = Scheduler()

        triggered = []

        scheduler.schedule(
            TICKS_PER_HOUR,
            lambda: triggered.append("npc"),
        )

        clock.attach_scheduler(scheduler)

        clock.advance_minutes(30)

        self.assertEqual(triggered, [])

        clock.advance_minutes(30)

        self.assertEqual(
            triggered,
            ["npc"],
        )

    def test_pause(self):
        clock = GameClock()

        clock.pause()
        clock.advance(600)

        self.assertEqual(
            clock.total_ticks,
            0,
        )

        clock.resume()
        clock.advance(600)

        self.assertEqual(
            clock.total_ticks,
            600,
        )


if __name__ == "__main__":
    unittest.main()
