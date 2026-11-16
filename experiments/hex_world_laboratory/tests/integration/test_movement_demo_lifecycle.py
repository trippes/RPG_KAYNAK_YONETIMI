"""Application lifecycle regression tests for the movement demo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from hex_world_lab.app import LabApplication
from hex_world_lab.config import AppConfig


def test_application_runs_one_frame_and_shuts_down() -> None:
    app = LabApplication(AppConfig(window_width=320, window_height=240))
    app.run(max_frames=1)
    assert app.movement_demo is None
    assert app.movement_system is None
    assert app._running is False
