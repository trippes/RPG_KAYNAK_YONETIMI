"""Measure integrated fixed-tick movement plus continuous collision costs.

Run from the laboratory root:
    python benchmarks/benchmark_collision_aware_movement.py

Results are observational and deliberately impose no machine-specific threshold.
"""
from __future__ import annotations

import json
import platform
import statistics
import sys
import time

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.physics import BodyDefinition, CircleShape, ConvexPolygonShape, ObstacleDefinition
from hex_world_lab.simulation import CollisionAwareMovementSystem
from hex_world_lab.world import MapId

ACTOR_COUNTS = (1, 10, 100, 1000)
WARMUP_BATCHES = 2
MEASURED_BATCHES = 8
TICKS_PER_BATCH = 10
MAP_ID = MapId("collision_benchmark")


def build_obstacle(actor_count: int) -> ObstacleDefinition:
    half_height = max(3.0, actor_count * 1.5)
    return ObstacleDefinition(
        "benchmark_wall",
        MAP_ID,
        ConvexPolygonShape((
            Vector2(-0.25, -half_height),
            Vector2(0.25, -half_height),
            Vector2(0.25, half_height),
            Vector2(-0.25, half_height),
        )),
        WorldPoint(2.0, 0.0),
    )


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(0.95 * len(ordered)) - 1))]


def measure(actor_count: int) -> dict[str, float | int]:
    obstacle = build_obstacle(actor_count)
    config = MovementConfig(max_speed=60.0)
    body = BodyDefinition("benchmark_player", CircleShape(0.25))
    actors = [
        CollisionAwareMovementSystem(
            MovementState(WorldPoint(0.0, index * 2.5)),
            config,
            body,
            (obstacle,),
        )
        for index in range(actor_count)
    ]
    intent = MovementIntent(Vector2(1.0, 0.0))
    tick_number = 0

    def run_batch() -> None:
        nonlocal tick_number
        for _ in range(TICKS_PER_BATCH):
            for actor in actors:
                actor.step(tick_number, intent)
            tick_number += 1

    for _ in range(WARMUP_BATCHES):
        run_batch()

    durations_ms: list[float] = []
    for _ in range(MEASURED_BATCHES):
        started = time.perf_counter()
        run_batch()
        durations_ms.append((time.perf_counter() - started) * 1000.0)

    mean_ms = statistics.fmean(durations_ms)
    return {
        "actors": actor_count,
        "ticks_per_batch": TICKS_PER_BATCH,
        "mean_batch_ms": round(mean_ms, 4),
        "p95_batch_ms": round(percentile_95(durations_ms), 4),
        "mean_actor_tick_us": round(
            mean_ms * 1000.0 / (actor_count * TICKS_PER_BATCH), 4
        ),
    }


def main() -> None:
    report = {
        "benchmark": "collision_aware_movement",
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unavailable",
        "warmup_batches": WARMUP_BATCHES,
        "measured_batches": MEASURED_BATCHES,
        "results": [measure(count) for count in ACTOR_COUNTS],
        "scope": (
            "MovementIntegrator + swept circle collision against one static "
            "convex wall per shared benchmark scene; excludes rendering, "
            "input polling, NPC logic, and world simulation."
        ),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
