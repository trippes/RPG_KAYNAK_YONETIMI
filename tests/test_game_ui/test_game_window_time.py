import unittest
from types import SimpleNamespace

from application.simulation_time_driver import SimulationTimeDriver
from game_ui.game_window import GameWindow


class _TimedService:
    def __init__(self):
        self.active = True
        self.advances = []

    def has_running_timed_activities(self):
        return self.active

    def advance_game_time(self, ticks):
        self.advances.append(ticks)
        self.active = False


class GameWindowTimeTests(unittest.TestCase):
    def _window(self, service):
        window = SimpleNamespace(
            service=service,
            gameplay_active=True,
            pause_menu_open=False,
            _simulation_time_driver=SimulationTimeDriver(),
            _set_notice=lambda *_args: None,
        )
        window._has_running_timed_activity = (
            lambda: service.has_running_timed_activities()
        )
        return window

    def test_game_window_advances_one_batched_tick_delta(self):
        service = _TimedService()
        window = self._window(service)

        GameWindow._advance_active_time(window, 10.0)

        self.assertEqual(service.advances, [36000])
        self.assertEqual(window._simulation_time_driver.fractional_ticks, 0.0)

    def test_game_window_resets_fraction_when_no_actor_activity_is_running(self):
        service = _TimedService()
        service.active = False
        window = self._window(service)
        window._simulation_time_driver.advance(0.0001)

        GameWindow._advance_active_time(window, 0.5)

        self.assertEqual(service.advances, [])
        self.assertEqual(window._simulation_time_driver.fractional_ticks, 0.0)

    def test_game_window_resets_fraction_while_paused(self):
        service = _TimedService()
        window = self._window(service)
        window.pause_menu_open = True
        window._simulation_time_driver.advance(0.0001)

        GameWindow._advance_active_time(window, 0.5)

        self.assertEqual(service.advances, [])
        self.assertEqual(window._simulation_time_driver.fractional_ticks, 0.0)


if __name__ == "__main__":
    unittest.main()
