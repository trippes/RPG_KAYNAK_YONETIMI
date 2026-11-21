"""Visual preview grid for the unintegrated articulated character rig.

Run from the repository root:
    python scripts/preview_character_rig.py

This is a presentation-only preview. Walk/run phases are time-based here; the
movement-distance synchronization contract is planned for gameplay integration.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game_ui import load_backend
from game_ui.world_rendering.character_rig_animation import CharacterRigAnimator
from game_ui.world_rendering.character_rig_renderer import CharacterRigRenderer
from game_ui.world_rendering.character_skeleton import DEFAULT_CHARACTER_SKELETON


WIDTH = 1600
HEIGHT = 900
DIRECTIONS = (
    "north", "north_east", "east", "south_east",
    "south", "south_west", "west", "north_west",
)
STATES = ("idle", "walk", "run")
CELL_WIDTH = WIDTH // len(DIRECTIONS)
ROW_HEIGHT = 270
CHARACTER_SCALE = 168


def main() -> int:
    pygame = load_backend()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Eldoria - Character Rig Visual Preview")
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 34)
    label_font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 19)

    renderer = CharacterRigRenderer()
    draw_context = SimpleNamespace(pg=pygame, surface=screen)
    animators = {
        (state, direction): CharacterRigAnimator(direction=direction, state=state)
        for state in STATES
        for direction in DIRECTIONS
    }

    running = True
    paused = False
    while running:
        delta = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused

        screen.fill((24, 27, 33))
        title = title_font.render(
            "ELDORIA  |  CHARACTER RIG PREVIEW", True, (235, 229, 211)
        )
        screen.blit(title, (24, 15))
        instruction = small_font.render(
            "SPACE: pause/resume    ESC: close    8 directions x 3 animation states",
            True, (174, 181, 190)
        )
        screen.blit(instruction, (26, 46))

        for row, state in enumerate(STATES):
            top = 78 + row * ROW_HEIGHT
            pygame.draw.rect(
                screen, (31, 35, 43),
                pygame.Rect(0, top, WIDTH, ROW_HEIGHT - 2)
            )
            state_label = label_font.render(state.upper(), True, (218, 202, 160))
            screen.blit(state_label, (12, top + 8))

            for column, direction in enumerate(DIRECTIONS):
                left = column * CELL_WIDTH
                if column:
                    pygame.draw.line(
                        screen, (54, 60, 69),
                        (left, top + 2), (left, top + ROW_HEIGHT - 8), 1
                    )
                direction_label = small_font.render(
                    direction.replace("_", " ").upper(),
                    True, (190, 197, 205)
                )
                label_rect = direction_label.get_rect(
                    center=(left + CELL_WIDTH // 2, top + 34)
                )
                screen.blit(direction_label, label_rect)

                foot_position = (
                    left + CELL_WIDTH // 2,
                    top + ROW_HEIGHT - 28,
                )
                pygame.draw.ellipse(
                    screen, (13, 15, 19),
                    pygame.Rect(
                        foot_position[0] - 25, foot_position[1] - 4, 50, 9
                    )
                )
                animator = animators[(state, direction)]
                if not paused:
                    pose = animator.update(delta)
                else:
                    pose = animator.pose
                renderer.draw(
                    draw_context,
                    DEFAULT_CHARACTER_SKELETON,
                    foot_position,
                    CHARACTER_SCALE,
                    local_rotations=pose,
                    facing=direction,
                )

        footer = small_font.render(
            "Preview only: movement-distance / foot-contact synchronization is not implemented yet.",
            True, (224, 177, 125)
        )
        screen.blit(footer, (24, HEIGHT - 27))
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
