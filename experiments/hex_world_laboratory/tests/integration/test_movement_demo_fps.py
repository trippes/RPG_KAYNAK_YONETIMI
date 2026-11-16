"""Deterministic render-rate equivalence tests for the acceptance demo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.application.movement_demo import MovementDemo


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class PressedKeys:
    def __init__(self, active: set[int]) -> None:
        self.active = active

    def __getitem__(self, key: int) -> bool:
        return key in self.active


class TickSequenceProvider:
    """Return the same input sequence regardless of render-frame grouping."""

    def __init__(self) -> None:
        self.tick = 0

    def __call__(self) -> PressedKeys:
        current = self.tick
        self.tick += 1
        if current < 20:
            return PressedKeys({pygame.K_d})
        if current < 40:
            return PressedKeys({pygame.K_d, pygame.K_LSHIFT})
        if current < 60:
            return PressedKeys({pygame.K_d, pygame.K_LALT, pygame.K_LSHIFT})
        return PressedKeys(set())


def run_for_one_simulated_second(render_fps: int):
    clock = FakeClock()
    demo = MovementDemo(
        movement_speed=60.0,
        key_state_provider=TickSequenceProvider(),
        clock=clock,
    )
    demo.start()
    for _ in range(render_fps):
        clock.advance(1.0 / render_fps)
        demo.pump()
    return demo.state, demo.current_resolution, demo.tick_pump.diagnostics


def test_30_60_and_120_render_fps_produce_equivalent_60_tick_state() -> None:
    pygame.init()
    try:
        results = [
            run_for_one_simulated_second(fps)
            for fps in (30, 60, 120)
        ]
        states = [result[0] for result in results]
        resolutions = [result[1] for result in results]
        diagnostics = [result[2] for result in results]

        assert all(item.total_ticks == 60 for item in diagnostics)
        assert states[0] == states[1] == states[2]
        assert resolutions[0] == resolutions[1] == resolutions[2]
        assert all(item.pending_full_ticks == 0 for item in diagnostics)

        # 20 normal ticks + 20 running ticks + 20 stealth ticks:
        # 20*1.0 + 20*1.5 + 20*0.5 = 60 world units.
        from hex_world_lab.movement import MovementMode

        assert states[0].position.x == 60.0
        assert states[0].position.y == 0.0
        assert states[0].mode is MovementMode.STEALTH
        assert states[0].velocity.x == 30.0
    finally:
        pygame.quit()
