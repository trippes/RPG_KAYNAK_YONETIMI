"""Export idle, walk and run sprite sheets for eight facing directions."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import pygame

from game_ui.world_rendering.humanoid_body_3d import DEFAULT_HUMANOID_BODY
from game_ui.world_rendering.humanoid_body_animation_3d import HumanoidBodyAnimator3D
from game_ui.world_rendering.humanoid_body_renderer_3d import HumanoidBodyRenderer3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


DIRECTION_VECTORS = {
    "east": (1.0, 0.0),
    "south_east": (math.sqrt(0.5), math.sqrt(0.5)),
    "south": (0.0, 1.0),
    "south_west": (-math.sqrt(0.5), math.sqrt(0.5)),
    "west": (-1.0, 0.0),
    "north_west": (-math.sqrt(0.5), -math.sqrt(0.5)),
    "north": (0.0, -1.0),
    "north_east": (math.sqrt(0.5), -math.sqrt(0.5)),
}
LABELS = {
    "east": "E",
    "south_east": "SE",
    "south": "S",
    "south_west": "SW",
    "west": "W",
    "north_west": "NW",
    "north": "N",
    "north_east": "NE",
}
CELL_WIDTH = 128
CELL_HEIGHT = 160
LABEL_WIDTH = 64
HEADER_HEIGHT = 28
COLUMNS = 16


def build_sheet(state: str, output_path: Path) -> dict:
    rows = len(HumanoidBodyAnimator3D.DIRECTIONS)
    surface = pygame.Surface(
        (LABEL_WIDTH + COLUMNS * CELL_WIDTH, HEADER_HEIGHT + rows * CELL_HEIGHT),
        pygame.SRCALPHA,
    )
    surface.fill((27, 30, 35, 255))
    font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 15)
    for column in range(COLUMNS):
        label = small_font.render(f"{column:02d}", True, (190, 196, 205))
        surface.blit(label, (LABEL_WIDTH + column * CELL_WIDTH + 5, 7))

    renderer = HumanoidBodyRenderer3D()
    triangle_count = 0
    for row, direction in enumerate(HumanoidBodyAnimator3D.DIRECTIONS):
        vector = DIRECTION_VECTORS[direction]
        yaw = -math.atan2(vector[0], vector[1])
        row_top = HEADER_HEIGHT + row * CELL_HEIGHT
        label = font.render(LABELS[direction], True, (225, 228, 233))
        surface.blit(label, (12, row_top + 70))
        for column in range(COLUMNS):
            cell_left = LABEL_WIDTH + column * CELL_WIDTH
            pygame.draw.rect(
                surface, (37, 41, 47, 255),
                (cell_left, row_top, CELL_WIDTH, CELL_HEIGHT),
            )
            pygame.draw.rect(
                surface, (58, 63, 71, 255),
                (cell_left, row_top, CELL_WIDTH, CELL_HEIGHT), 1,
            )
            animator = HumanoidBodyAnimator3D(direction=direction, state=state)
            position = (0.0, 0.0)
            if state == "idle":
                animator._idle_clock = (column % 8) * 3.2 / 8.0
                traveled = 0.0
                delta = 0.0
            else:
                cycle_distance = (
                    animator.RUN_CYCLE_DISTANCE if state == "run"
                    else animator.WALK_CYCLE_DISTANCE
                )
                traveled = cycle_distance / COLUMNS if column else 0.0
                delta = 1.0 / 60.0
                for _ in range(column):
                    position = (
                        position[0] + vector[0] * cycle_distance / COLUMNS,
                        position[1] + vector[1] * cycle_distance / COLUMNS,
                    )
                # The animator phase is initialized at the exact sample before
                # drawing; the root position represents the matching distance.
                animator.phase = math.tau * column / COLUMNS
                animator._foot_lock.reset()
                traveled = 0.0

            animator.advance(
                traveled,
                delta,
                world_position=position,
                yaw=yaw,
                world_scale=100.0,
            )
            foot = (
                cell_left + CELL_WIDTH // 2,
                row_top + CELL_HEIGHT - 14,
            )
            triangle_count += renderer.draw(
                surface,
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                foot,
                100.0,
                yaw=yaw,
                local_rotations=animator.pose,
                local_translations=animator.translations,
                detail_level="medium",
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(output_path))
    return {
        "state": state,
        "path": str(output_path),
        "triangles_drawn": triangle_count,
        "cache": renderer.cache_info(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("humanoid-preview"))
    args = parser.parse_args()
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        results = [
            build_sheet(state, args.output_dir / f"humanoid-{state}-8dir.png")
            for state in ("idle", "walk", "run")
        ]
        print(json.dumps(results, indent=2))
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
