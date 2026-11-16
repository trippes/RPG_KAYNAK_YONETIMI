"""Pygame application shell for the Hex World movement acceptance demo."""

from __future__ import annotations

import pygame

from .application.movement_demo import MovementDemo
from .config import AppConfig
from .simulation import MovementSystem


class LabApplication:
    """Own the Pygame window and delegate simulation to MovementDemo."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False
        self._demo: MovementDemo | None = None

    @property
    def movement_system(self) -> MovementSystem | None:
        """Preserve the original movement-system inspection API."""
        return None if self._demo is None else self._demo.movement_system

    @property
    def movement_demo(self) -> MovementDemo | None:
        """Expose the active demo for diagnostics and integration tests."""
        return self._demo

    def run(self, *, max_frames: int | None = None) -> None:
        """Run the window loop; max_frames is provided for automated tests."""
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height)
            )
            pygame.display.set_caption(self.config.window_title)
            clock = pygame.time.Clock()
            self._demo = MovementDemo(movement_speed=self.config.movement_speed)
            self._demo.start()

            self._running = True
            frame_count = 0
            while self._running:
                for event in pygame.event.get():
                    self._demo.handle_event(event)
                    if event.type == pygame.QUIT:
                        self._running = False

                if not self._running:
                    break

                self._demo.pump()
                render_fps = clock.get_fps()
                self._demo.render(screen, render_fps)
                pygame.display.flip()
                clock.tick(self.config.target_fps)
                frame_count += 1

                if max_frames is not None and frame_count >= max_frames:
                    self._running = False
        finally:
            self._running = False
            self._demo = None
            pygame.quit()


def main() -> None:
    """Launch the standalone laboratory application."""
    LabApplication().run()
