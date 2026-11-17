"""Headless integration test for the Pygame application lifecycle."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import hex_world_lab.app as app_module
from hex_world_lab.app import LabApplication
from hex_world_lab.camera import Viewport
from hex_world_lab.config import AppConfig


def test_application_initializes_and_shuts_down() -> None:
    app = LabApplication(AppConfig(window_width=320, window_height=240))
    app.run(max_frames=1)
    assert app._running is False


def test_application_applies_configured_speed_and_initial_viewport(monkeypatch) -> None:
    created_movement_demos = []
    original_entity_demo = app_module.EntityDemo

    class CapturingEntityDemo(original_entity_demo):
        def __init__(self, movement_demo=None):
            created_movement_demos.append(movement_demo)
            super().__init__(movement_demo)

    monkeypatch.setattr(app_module, "EntityDemo", CapturingEntityDemo)
    config = AppConfig(
        window_width=320,
        window_height=240,
        movement_speed=123.0,
    )
    LabApplication(config).run(max_frames=1)

    assert len(created_movement_demos) == 1
    movement_demo = created_movement_demos[0]
    assert movement_demo.camera.state.viewport == Viewport(320, 240)
    assert movement_demo._movement_config.max_speed == 123.0
