"""Headless integration test for the Pygame application lifecycle."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from hex_world_lab.app import LabApplication
from hex_world_lab.config import AppConfig


def test_application_initializes_and_shuts_down() -> None:
    app = LabApplication(AppConfig(window_width=320, window_height=240))
    app.run(max_frames=1)
    assert app._running is False
