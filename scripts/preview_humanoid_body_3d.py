"""Show an eight-direction turnaround of the Stage 2 humanoid body."""

from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame  # noqa: E402

from game_ui.world_rendering.humanoid_body_3d import DEFAULT_HUMANOID_BODY  # noqa: E402
from game_ui.world_rendering.humanoid_body_renderer_3d import (  # noqa: E402
    HumanoidBodyRenderer3D,
)
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG  # noqa: E402


WIDTH = 1440
HEIGHT = 900
BACKGROUND = (25, 27, 32)


def main() -> None:
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Eldoria - Stage 2 Humanoid Body Preview")
        font = pygame.font.Font(None, 30)
        note_font = pygame.font.Font(None, 22)
        clock = pygame.time.Clock()
        body_renderer = HumanoidBodyRenderer3D()
        views = (
            ("N", 0.0),
            ("NE", math.pi / 4.0),
            ("E", math.pi / 2.0),
            ("SE", 3.0 * math.pi / 4.0),
            ("S", math.pi),
            ("SW", 5.0 * math.pi / 4.0),
            ("W", 3.0 * math.pi / 2.0),
            ("NW", 7.0 * math.pi / 4.0),
        )
        columns = 4
        cell_width = WIDTH // columns
        row_height = HEIGHT // 2
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            screen.fill(BACKGROUND)
            for index, (title, yaw) in enumerate(views):
                row, column = divmod(index, columns)
                center_x = column * cell_width + cell_width // 2
                baseline = row * row_height + 350
                pygame.draw.line(
                    screen,
                    (90, 96, 105),
                    (center_x - 135, baseline),
                    (center_x + 135, baseline),
                    1,
                )
                body_renderer.draw(
                    screen,
                    DEFAULT_HUMANOID_BODY,
                    DEFAULT_HUMANOID_RIG,
                    (center_x, baseline),
                    190.0,
                    yaw=yaw,
                )
                label = font.render(title, True, (235, 235, 235))
                screen.blit(
                    label,
                    label.get_rect(center=(center_x, row * row_height + 38)),
                )

            note = note_font.render(
                "Stage 2 | Eight-direction anatomical turnaround | ESC: close",
                True,
                (180, 185, 194),
            )
            screen.blit(note, note.get_rect(center=(WIDTH // 2, HEIGHT - 24)))
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
