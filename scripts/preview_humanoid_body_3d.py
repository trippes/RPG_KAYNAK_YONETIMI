"""Show front, three-quarter, and side views of the Stage 2 body volumes."""

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


WIDTH = 1120
HEIGHT = 620
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
            ("FRONT", 0.0, 190),
            ("THREE-QUARTER", math.pi / 4.0, 560),
            ("SIDE", math.pi / 2.0, 930),
        )
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            screen.fill(BACKGROUND)
            for title, yaw, center_x in views:
                pygame.draw.line(
                    screen, (90, 96, 105),
                    (center_x - 170, 520), (center_x + 170, 520), 1,
                )
                body_renderer.draw(
                    screen,
                    DEFAULT_HUMANOID_BODY,
                    DEFAULT_HUMANOID_RIG,
                    (center_x, 520),
                    300.0,
                    yaw=yaw,
                )
                label = font.render(title, True, (235, 235, 235))
                screen.blit(label, label.get_rect(center=(center_x, 54)))

            note = note_font.render(
                "Stage 2 | Parametric low-poly body volumes | ESC: close",
                True,
                (180, 185, 194),
            )
            screen.blit(note, note.get_rect(center=(WIDTH // 2, 585)))
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
