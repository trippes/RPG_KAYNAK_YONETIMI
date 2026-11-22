"""Open a three-view debug preview of the Stage 1 humanoid rig."""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Allow direct execution from any working directory without requiring an
# editable install of the project.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame  # noqa: E402

from game_ui.world_rendering.humanoid_rig_3d import (
    DEFAULT_HUMANOID_RIG,
    project_point_orthographic,
)  # noqa: E402


WIDTH = 1120
HEIGHT = 620
BACKGROUND = (25, 27, 32)
BONE_COLOR = (190, 174, 145)
JOINT_COLOR = (232, 218, 190)
CONTROL_COLOR = (112, 177, 214)
TEXT_COLOR = (235, 235, 235)


def _screen_positions(
    yaw: float, origin: tuple[int, int], scale: float
) -> dict[str, tuple[int, int]]:
    positions = DEFAULT_HUMANOID_RIG.joint_positions()
    return {
        name: tuple(
            round(value)
            for value in project_point_orthographic(
                point, yaw=yaw, scale=scale, origin=origin
            )
        )
        for name, point in positions.items()
    }


def _draw_view(
    surface: pygame.Surface,
    font: pygame.font.Font,
    *,
    title: str,
    yaw: float,
    center_x: int,
) -> None:
    # Fit the full arm span inside each view while keeping the feet on the
    # shared ground baseline.
    scale = 300.0
    origin = (center_x, 353)
    positions = _screen_positions(yaw, origin, scale)

    pygame.draw.line(surface, (90, 96, 105), (center_x - 150, 500), (center_x + 150, 500), 1)
    for bone in DEFAULT_HUMANOID_RIG.bones:
        start = positions[bone.start_joint]
        end = positions[bone.end_joint]
        pygame.draw.line(surface, BONE_COLOR, start, end, 5)

    control_names = set(DEFAULT_HUMANOID_RIG.control_joint_names)
    for name, position in positions.items():
        color = CONTROL_COLOR if name in control_names else JOINT_COLOR
        radius = 6 if name in control_names else 4
        pygame.draw.circle(surface, color, position, radius)

    label = font.render(title, True, TEXT_COLOR)
    surface.blit(label, label.get_rect(center=(center_x, 54)))


def main() -> None:
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Eldoria - Stage 1 Humanoid Rig Preview")
        font = pygame.font.Font(None, 30)
        small_font = pygame.font.Font(None, 22)
        clock = pygame.time.Clock()
        views = (
            ("FRONT", 0.0, 210),
            ("THREE-QUARTER", math.pi / 4.0, 560),
            ("SIDE", math.pi / 2.0, 910),
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
                _draw_view(screen, font, title=title, yaw=yaw, center_x=center_x)
            note = small_font.render(
                "A-Pose rest rig | X: anatomical right | Y: forward | Z: up | ESC: close",
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
