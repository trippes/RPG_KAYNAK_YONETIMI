"""Measure low-poly humanoid rendering cost for representative NPC counts.

This is a diagnostic benchmark, not a fixed-FPS acceptance test. Results depend
on the host CPU, Pygame build, and display backend.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
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


def run_benchmark(frames: int) -> list[dict[str, object]]:
    if frames < 1:
        raise ValueError("frames must be at least 1.")

    pygame.init()
    try:
        target = pygame.Surface((1280, 720))
        renderer = HumanoidBodyRenderer3D()
        body = DEFAULT_HUMANOID_BODY
        rig = DEFAULT_HUMANOID_RIG
        triangle_count = len(body.build_mesh(rig, detail_level="high"))
        if triangle_count > 1300:
            raise RuntimeError(
                f"Body mesh exceeds the 1,300 triangle budget: {triangle_count}."
            )

        pose_bank = tuple(
            {"shoulder_left": (0.0, 0.0, math.sin(index * math.tau / 8.0) * 0.18)}
            for index in range(8)
        )
        results = []
        for actor_count in (1, 10, 25, 50):
            actors = tuple(
                (
                    (90 + (index % 10) * 120, 110 + (index // 10) * 135),
                    (index % 8) * math.tau / 8.0,
                    pose_bank[index % len(pose_bank)],
                    (
                        "high" if actor_count <= 10 or index < max(1, actor_count // 10)
                        else "medium" if index < max(1, actor_count // 10) + actor_count // 5
                        else "low"
                    ),
                )
                for index in range(actor_count)
            )
            renderer.draw(
                target, body, rig, actors[0][0], 110.0,
                yaw=actors[0][1], local_rotations=actors[0][2],
                detail_level=actors[0][3],
            )
            start = time.perf_counter()
            for _ in range(frames):
                target.fill((25, 27, 32))
                for position, yaw, pose, detail_level in actors:
                    renderer.draw(
                        target,
                        body,
                        rig,
                        position,
                        110.0,
                        yaw=yaw,
                        local_rotations=pose,
                        detail_level=detail_level,
                    )
            elapsed = time.perf_counter() - start
            average_ms = elapsed * 1000.0 / frames
            triangle_counts = {
                detail: len(body.build_mesh(rig, detail_level=detail))
                for detail in ("high", "medium", "low")
            }
            triangles_per_frame = sum(
                triangle_counts[detail_level]
                for _, _, _, detail_level in actors
            )
            results.append(
                {
                    "characters": actor_count,
                    "triangles_per_character_high": triangle_count,
                    "triangles_per_frame": triangles_per_frame,
                    "lod_distribution": {
                        detail: sum(actor[3] == detail for actor in actors)
                        for detail in ("high", "medium", "low")
                    },
                    "frames": frames,
                    "average_frame_ms": round(average_ms, 3),
                    "equivalent_fps": round(1000.0 / average_ms, 2),
                }
            )
        return results
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.frames), indent=2))


if __name__ == "__main__":
    main()
