"""Measure low-poly humanoid rendering cost for representative NPC counts.

This is a diagnostic benchmark, not a fixed-FPS acceptance test. Results depend
on the host CPU, Pygame build, and display backend.
"""

from __future__ import annotations

import argparse
import json
import math
import time

import pygame

from game_ui.world_rendering.humanoid_body_3d import (
    DEFAULT_HUMANOID_BODY,
    _build_mesh_cached,
)
from game_ui.world_rendering.humanoid_body_renderer_3d import HumanoidBodyRenderer3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


def run_benchmark(frames: int) -> list[dict[str, float | int]]:
    if frames < 1:
        raise ValueError("frames must be at least 1.")

    pygame.init()
    try:
        target = pygame.Surface((1280, 720))
        renderer = HumanoidBodyRenderer3D()
        body = DEFAULT_HUMANOID_BODY
        rig = DEFAULT_HUMANOID_RIG
        triangle_count = len(body.build_mesh(rig))
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
                )
                for index in range(actor_count)
            )
            renderer.draw(
                target, body, rig, actors[0][0], 110.0,
                yaw=actors[0][1], local_rotations=actors[0][2],
            )
            start = time.perf_counter()
            for _ in range(frames):
                target.fill((25, 27, 32))
                for position, yaw, pose in actors:
                    renderer.draw(
                        target,
                        body,
                        rig,
                        position,
                        110.0,
                        yaw=yaw,
                        local_rotations=pose,
                    )
            elapsed = time.perf_counter() - start
            average_ms = elapsed * 1000.0 / frames
            results.append(
                {
                    "characters": actor_count,
                    "triangles_per_character": triangle_count,
                    "triangles_per_frame": actor_count * triangle_count,
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
