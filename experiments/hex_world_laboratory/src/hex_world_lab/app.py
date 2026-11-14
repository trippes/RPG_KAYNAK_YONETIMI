"""Minimal Pygame application shell for laboratory experiments."""

from __future__ import annotations

import pygame

from .config import AppConfig


class LabApplication:
    """Owns the Pygame window and its event/render loop."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False

    def run(self, *, max_frames: int | None = None) -> None:
        """Run the window loop; max_frames is provided for automated tests."""
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height)
            )
            pygame.display.set_caption(self.config.window_title)
            clock = pygame.time.Clock()
            self._running = True
            frame_count = 0

            while self._running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._running = False

                screen.fill((24, 27, 35))
                pygame.display.flip()
                clock.tick(self.config.target_fps)
                frame_count += 1

                if max_frames is not None and frame_count >= max_frames:
                    self._running = False
        finally:
            self._running = False
            pygame.quit()


def main() -> None:
    """Launch the standalone laboratory application."""
    LabApplication().run()
