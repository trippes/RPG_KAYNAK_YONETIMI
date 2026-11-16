"""Measure movement plus hex-cell resolution for 1/10/100/1000 actors.

Run from the laboratory directory:
    python benchmarks/benchmark_movement_demo.py
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time

from hex_world_lab.application.movement_demo import MAP_ID, build_demo_world
from hex_world_lab.geometry import AxialCoord, WorldPoint
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.simulation import MovementCellTracker, MovementSystem
from hex_world_lab.world import MovementWorldContext

ACTOR_COUNTS = (1, 10, 100, 1000)
WARMUP_BATCHES = 3
MEASURED_BATCHES = 20
TICKS_PER_BATCH = 10


class Actor:
    __slots__ = ("movement", "tracker")

    def __init__(self, context: MovementWorldContext) -> None:
        self.movement = MovementSystem(
            MovementState(WorldPoint(0.0, 0.0)),
            MovementConfig(max_speed=60.0),
        )
        self.tracker = MovementCellTracker(context)


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(0.95 * len(ordered)) - 1)]


def measure(actor_count: int) -> dict[str, float | int]:
    world, map_id = build_demo_world()
    context = MovementWorldContext(world, map_id)
    actors = [Actor(context) for _ in range(actor_count)]
    intent = MovementIntent(Vector2(1.0, 0.0))
    tick_number = 0

    def run_batch() -> None:
        nonlocal tick_number
        for _ in range(TICKS_PER_BATCH):
            for actor in actors:
                state = actor.movement.step(tick_number, intent)
                actor.tracker.update(state.position)
            tick_number += 1

    for _ in range(WARMUP_BATCHES):
        run_batch()

    durations_ms: list[float] = []
    for _ in range(MEASURED_BATCHES):
        started = time.perf_counter()
        run_batch()
        durations_ms.append((time.perf_counter() - started) * 1000.0)

    mean_ms = statistics.fmean(durations_ms)
    p95_ms = percentile_95(durations_ms)
    return {
        "actors": actor_count,
        "ticks_per_batch": TICKS_PER_BATCH,
        "mean_batch_ms": round(mean_ms, 4),
        "p95_batch_ms": round(p95_ms, 4),
        "mean_actor_tick_us": round(
            mean_ms * 1000.0 / (actor_count * TICKS_PER_BATCH), 4
        ),
    }


def main() -> None:
    results = [measure(count) for count in ACTOR_COUNTS]
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unavailable",
        "warmup_batches": WARMUP_BATCHES,
        "measured_batches": MEASURED_BATCHES,
        "results": results,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
