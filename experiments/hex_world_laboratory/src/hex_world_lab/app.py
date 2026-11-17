"""Unified Pygame entry point for the Hex World laboratory.

The original `python -m hex_world_lab` launcher now opens the current
multi-entity acceptance scene. MovementDemo remains the movement authority
inside EntityDemo, so the earlier movement laboratory is preserved.
"""
from __future__ import annotations

import pygame

from .application.entity_demo import EntityDemo
from .application.movement_demo import MovementDemo
from .camera import Viewport
from .config import AppConfig
from .rendering import RenderDebugOptions


class LabApplication:
    """Own the Pygame window and run the current laboratory scene."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False
        self._demo: EntityDemo | None = None
        self._show_colliders = True

    @property
    def movement_system(self):
        """Keep the legacy movement-system inspection API available."""
        if self._demo is None:
            return None
        return self._demo.movement.movement_system

    @property
    def movement_demo(self):
        """Expose the underlying movement demo for existing diagnostics."""
        return None if self._demo is None else self._demo.movement

    @property
    def entity_demo(self) -> EntityDemo | None:
        """Expose the active multi-entity scene for diagnostics and tests."""
        return self._demo

    def run(self, *, max_frames: int | None = None) -> None:
        """Run the unified laboratory loop; max_frames supports headless tests."""
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height),
                pygame.RESIZABLE,
            )
            pygame.display.set_caption(self.config.window_title)
            clock = pygame.time.Clock()
            movement_demo = MovementDemo(
                movement_speed=self.config.movement_speed,
                viewport=Viewport(*screen.get_size()),
            )
            self._demo = EntityDemo(movement_demo)
            self._demo.movement.start()
            self._show_colliders = True

            self._running = True
            frame_count = 0
            while self._running:
                delta = min(clock.tick(self.config.target_fps) / 1000.0, 0.1)
                for event in pygame.event.get():
                    if event.type == pygame.VIDEORESIZE:
                        screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    if event.type == pygame.QUIT:
                        self._running = False
                        continue
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self._running = False
                            continue
                        if event.key == pygame.K_F3:
                            self._show_colliders = not self._show_colliders
                            continue
                    self._demo.handle_event(event)

                if not self._running:
                    break

                self._demo.movement.pump()
                self._demo.movement.update_camera(delta)
                self._demo.render(
                    screen,
                    clock.get_fps(),
                    RenderDebugOptions(
                        show_hex_edges=True,
                        show_collider_debug=self._show_colliders,
                    ),
                )
                pygame.display.flip()
                frame_count += 1

                if max_frames is not None and frame_count >= max_frames:
                    self._running = False
        finally:
            self._running = False
            self._demo = None
            pygame.quit()


def main() -> None:
    """Launch the unified standalone laboratory application."""
    LabApplication().run()
