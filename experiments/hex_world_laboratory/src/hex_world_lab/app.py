"""Minimal Pygame application shell for laboratory experiments."""

from __future__ import annotations

import pygame

from .application import DemoTickPump
from .config import AppConfig
from .geometry import WorldPoint
from .input import PygameKeyboardAdapter
from .movement import MovementConfig, MovementState
from .simulation import MovementSystem


class LabApplication:
    """Owns the Pygame window, input adapter and demo movement loop."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False
        self._keyboard: PygameKeyboardAdapter | None = None
        self._movement_system: MovementSystem | None = None
        self._tick_pump: DemoTickPump | None = None

    @property
    def movement_system(self) -> MovementSystem | None:
        """Expose the demo movement state for diagnostics and integration tests."""
        return self._movement_system

    def run(self, *, max_frames: int | None = None) -> None:
        """Run the window loop; max_frames is provided for automated tests."""
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height)
            )
            pygame.display.set_caption(self.config.window_title)
            clock = pygame.time.Clock()

            self._keyboard = PygameKeyboardAdapter()
            self._movement_system = MovementSystem(
                MovementState(position=WorldPoint(0.0, 0.0)),
                MovementConfig(max_speed=self.config.movement_speed),
            )

            def advance_movement(tick_number: int) -> None:
                assert self._keyboard is not None
                assert self._movement_system is not None
                self._movement_system.step(tick_number, self._keyboard.read_intent())

            self._tick_pump = DemoTickPump(advance_movement)
            self._tick_pump.start()

            self._running = True
            frame_count = 0

            while self._running:
                for event in pygame.event.get():
                    if self._keyboard is not None:
                        self._keyboard.handle_event(event)
                    if event.type == pygame.QUIT:
                        self._running = False

                if self._tick_pump is not None:
                    self._tick_pump.pump()

                screen.fill((24, 27, 35))
                pygame.display.flip()
                clock.tick(self.config.target_fps)
                frame_count += 1

                if max_frames is not None and frame_count >= max_frames:
                    self._running = False
        finally:
            self._running = False
            self._keyboard = None
            self._tick_pump = None
            pygame.quit()


def main() -> None:
    """Launch the standalone laboratory application."""
    LabApplication().run()
