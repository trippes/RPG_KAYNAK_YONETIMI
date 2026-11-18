"""Three-session microbenchmark for Phase 12 environmental-object adapters."""
from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.environment import (
    EnvironmentalObjectDefinition, EnvironmentalObjectPlacement, EnvironmentalObjectScene,
    environment_debug_visuals, environment_obstacles, environment_sprite_visuals,
)
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import Vector2
from hex_world_lab.physics import CircleShape, ConvexPolygonShape
from hex_world_lab.world import MapId, WorldId


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))]


def measure(callable_, repeats: int = 20) -> dict[str, float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        callable_()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return {
        "median_ms": statistics.median(samples),
        "p95_ms": percentile(samples, 0.95),
        "p99_ms": percentile(samples, 0.99),
    }


def build_scene(count: int) -> EnvironmentalObjectScene:
    world, map_id = WorldId("phase-12-benchmark"), MapId("environment-benchmark")
    definitions = (
        EnvironmentalObjectDefinition("tree", "tree", (0.5, 0.94), (0.5, 0.82), (0.05, 0.02, 0.9, 0.7), CircleShape(8.5)),
        EnvironmentalObjectDefinition("rock", "rock", (0.5, 0.92), (0.5, 0.84), None,
            ConvexPolygonShape((Vector2(-9, -7), Vector2(7, -9), Vector2(10, 3), Vector2(-3, 10)))),
        EnvironmentalObjectDefinition("bush", "bush", (0.5, 0.92), (0.5, 0.84), (0.05, 0.08, 0.9, 0.78), None),
    )
    placements = tuple(
        EnvironmentalObjectPlacement(
            f"instance-{index:05d}", ("tree", "rock", "bush")[index % 3],
            world, map_id, WorldPoint(float(index % 100) * 48.0, float(index // 100) * 42.0),
        )
        for index in range(count)
    )
    return EnvironmentalObjectScene(world, map_id, definitions, placements)


def main() -> None:
    asset_sizes = {"tree": (100, 128), "rock": (48, 36), "bush": (62, 44)}
    report = {"phase": 12, "sessions": 3, "profiles": {}}
    for count in (10, 100, 1000):
        sessions = []
        tracemalloc.start()
        for session_index in range(3):
            scene = build_scene(count)
            session = {
                "obstacle_adapter": measure(lambda: environment_obstacles(scene)),
                "sprite_adapter": measure(lambda: environment_sprite_visuals(scene, asset_sizes)),
                "debug_adapter": measure(lambda: environment_debug_visuals(scene, asset_sizes)),
            }
            sessions.append(session)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        report["profiles"][str(count)] = {
            "instances": count,
            "obstacle_count": len(environment_obstacles(scene)),
            "sessions": sessions,
            "peak_traced_bytes": peak,
        }
    output = Path("artifacts/phase-12")
    output.mkdir(parents=True, exist_ok=True)
    path = output / "environment-benchmark.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(path)
    for count, profile in report["profiles"].items():
        medians = [statistics.median(session[key]["median_ms"] for session in profile["sessions"])
                   for key in ("obstacle_adapter", "sprite_adapter", "debug_adapter")]
        print(f"{count} objects: obstacle={medians[0]:.4f}ms sprite={medians[1]:.4f}ms debug={medians[2]:.4f}ms")


if __name__ == "__main__":
    main()
