"""Measure simulation tick orchestration and render snapshot costs separately."""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

import pygame

from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.application.movement_demo import MovementDemo

WARMUP_BATCHES = 3
MEASURED_BATCHES = 20
TICKS_PER_BATCH = 120
SNAPSHOTS_PER_BATCH = 120


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def measure_tick_cost() -> dict[str, float | int]:
    movement = MovementDemo()
    demo = EntityDemo(movement)
    coordinator = movement.tick_coordinator
    next_tick = coordinator.next_tick_number

    def run_batch() -> None:
        nonlocal next_tick
        for _ in range(TICKS_PER_BATCH):
            coordinator.advance_tick(next_tick)
            next_tick += 1

    for _ in range(WARMUP_BATCHES):
        run_batch()
    durations = []
    for _ in range(MEASURED_BATCHES):
        started = time.perf_counter()
        run_batch()
        durations.append((time.perf_counter() - started) * 1000.0)
    mean_ms = statistics.fmean(durations)
    return {
        "ticks_per_batch": TICKS_PER_BATCH,
        "mean_batch_ms": round(mean_ms, 4),
        "p95_batch_ms": round(percentile(durations, 0.95), 4),
        "mean_tick_us": round(mean_ms * 1000.0 / TICKS_PER_BATCH, 4),
    }


def measure_snapshot_cost() -> dict[str, float | int]:
    demo = EntityDemo()
    for _ in range(WARMUP_BATCHES):
        for _ in range(SNAPSHOTS_PER_BATCH):
            demo.build_render_snapshot()
    durations = []
    for _ in range(MEASURED_BATCHES):
        started = time.perf_counter()
        for _ in range(SNAPSHOTS_PER_BATCH):
            demo.build_render_snapshot()
        durations.append((time.perf_counter() - started) * 1000.0)
    mean_ms = statistics.fmean(durations)
    return {
        "snapshots_per_batch": SNAPSHOTS_PER_BATCH,
        "mean_batch_ms": round(mean_ms, 4),
        "p95_batch_ms": round(percentile(durations, 0.95), 4),
        "mean_snapshot_us": round(mean_ms * 1000.0 / SNAPSHOTS_PER_BATCH, 4),
    }


def main() -> int:
    pygame.init()
    try:
        report = {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor() or "unavailable",
            "warmup_batches": WARMUP_BATCHES,
            "measured_batches": MEASURED_BATCHES,
            "simulation_tick": measure_tick_cost(),
            "render_snapshot": measure_snapshot_cost(),
        }
        output = Path("artifacts/phase-10")
        output.mkdir(parents=True, exist_ok=True)
        (output / "simulation-performance.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        return 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    raise SystemExit(main())
