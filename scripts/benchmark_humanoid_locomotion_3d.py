"""Profile the shared 3D humanoid locomotion renderer at several actor counts.

Run with:
    python scripts/benchmark_humanoid_locomotion_3d.py --frames 120

The benchmark reports update and raster/blit costs separately. It deliberately
does not impose a hardware-specific pass/fail threshold.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
from pathlib import Path
from time import perf_counter_ns

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game_ui.world_rendering.humanoid_body_3d import DEFAULT_HUMANOID_BODY
from game_ui.world_rendering.humanoid_body_animation_3d import HumanoidBodyAnimator3D
from game_ui.world_rendering.humanoid_body_renderer_3d import HumanoidBodyRenderer3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


DIRECTIONS = HumanoidBodyAnimator3D.DIRECTIONS
NPC_PALETTE = {
    "skin": (178, 132, 96),
    "tunic": (105, 83, 59),
    "trousers": (59, 70, 76),
    "boots": (57, 43, 34),
}


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


def run_scenario(actor_count: int, frames: int, warmup_frames: int) -> dict:
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    renderer = HumanoidBodyRenderer3D()
    actors = []
    for index in range(actor_count):
        animator = HumanoidBodyAnimator3D(
            direction=DIRECTIONS[index % len(DIRECTIONS)],
            state="walk",
        )
        animator.phase = (
            index % animator.PHASE_STEPS
        ) * math.tau / animator.PHASE_STEPS
        actors.append({
            "animator": animator,
            "position": [180.0 + (index % 10) * 90.0, 160.0 + (index // 10) * 85.0],
            "direction": DIRECTIONS[index % len(DIRECTIONS)],
            "yaw": (index % len(DIRECTIONS)) * math.tau / len(DIRECTIONS),
        })

    update_samples = []
    render_samples = []
    for frame in range(warmup_frames + frames):
        update_started = perf_counter_ns()
        for actor in actors:
            actor["position"][0] += 1.2 * math.cos(actor["yaw"])
            actor["position"][1] += 1.2 * math.sin(actor["yaw"])
            actor["animator"].advance(
                1.2,
                1.0 / 60.0,
                world_position=tuple(actor["position"]),
                yaw=actor["yaw"],
                world_scale=54.0,
            )
        update_ms = (perf_counter_ns() - update_started) / 1_000_000.0

        render_started = perf_counter_ns()
        surface.fill((0, 0, 0, 0))
        for actor in actors:
            animator = actor["animator"]
            renderer.draw(
                surface,
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                tuple(actor["position"]),
                54.0,
                yaw=actor["yaw"],
                local_rotations=animator.pose,
                local_translations=animator.translations,
                palette=NPC_PALETTE,
                detail_level="low",
            )
        render_ms = (perf_counter_ns() - render_started) / 1_000_000.0
        if frame >= warmup_frames:
            update_samples.append(update_ms)
            render_samples.append(render_ms)

    cache = renderer.cache_info()
    return {
        "actors": actor_count,
        "frames": frames,
        "update_ms_p50": round(statistics.median(update_samples), 4),
        "update_ms_p95": round(percentile(update_samples, 0.95), 4),
        "render_ms_p50": round(statistics.median(render_samples), 4),
        "render_ms_p95": round(percentile(render_samples, 0.95), 4),
        "combined_ms_p50": round(
            statistics.median(update_samples) + statistics.median(render_samples), 4
        ),
        "cache": cache,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--counts", type=int, nargs="+", default=[1, 10, 25, 50])
    parser.add_argument("--warmup-frames", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (
        args.frames < 1
        or args.warmup_frames < 0
        or any(count < 1 for count in args.counts)
    ):
        parser.error("frames and actor counts must be positive; warmup cannot be negative")

    pygame.init()
    try:
        results = [
            run_scenario(count, args.frames, args.warmup_frames)
            for count in args.counts
        ]
        payload = {
            "benchmark": "eldoria_humanoid_locomotion",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "frames": args.frames,
            "warmup_frames": args.warmup_frames,
            "scenarios": results,
        }
        output = json.dumps(payload, indent=2)
        print(output)
        if args.output is not None:
            args.output.write_text(output + "\\n", encoding="utf-8")
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
