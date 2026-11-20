"""Measure reproducible NPC spatial-index registration, update and query costs.

Run from the repository root:
    python scripts/benchmark_npc_spatial_index.py --output npc-spatial-benchmark.json

This is an observational benchmark, not a performance assertion or CI threshold.
Point-only and collider-AABB scenarios use identical deterministic workloads.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time
import tracemalloc

from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, WorldPoint
from npc import NPC


MAP_ID = "npc_physics_benchmark"
COLLIDER_BOUNDS = (-4.0, -4.0, 4.0, 4.0)


def _percentile(values: list[float], percentile: float) -> float:
    """Return a deterministic nearest-rank percentile."""
    if not values:
        return 0.0
    if not 0.0 <= percentile <= 100.0:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100.0 * len(ordered)))
    return ordered[rank - 1]


def _build_map(entity_count: int):
    """Build enough deterministic, unique axial cells for the requested NPC count."""
    columns = 100
    cells = [[index % columns, index // columns] for index in range(entity_count)]
    return parse_hex_map({
        "schema_version": 2,
        "map_id": MAP_ID,
        "name": "NPC Physics Benchmark",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": cells,
        "cell_overrides": [],
        "transitions": [],
    })


def run_scenario(
    entity_count: int,
    moving_percentages: tuple[int, ...],
    *,
    collider_bounds: bool,
    query_limit: int = 1000,
) -> dict:
    """Measure one count/mode pair with deterministic registration and movement."""
    if entity_count < 1:
        raise ValueError("entity_count must be positive")
    if query_limit < 1:
        raise ValueError("query_limit must be positive")
    if any(percent < 0 or percent > 100 for percent in moving_percentages):
        raise ValueError("moving percentages must be between 0 and 100")

    tracemalloc.start()
    try:
        map_definition = _build_map(entity_count)
        runtime = HexWorldRuntime({MAP_ID: map_definition})
        npcs = [
            NPC(f"benchmark_npc_{index:05d}", f"Benchmark NPC {index}")
            for index in range(entity_count)
        ]

        registration_started = time.perf_counter()
        for index, npc in enumerate(npcs):
            position = EntityPosition(
                MAP_ID,
                LocalHexPosition(index % 100, index // 100),
            )
            local_bounds = AABB(*COLLIDER_BOUNDS) if collider_bounds else None
            runtime.register_entity(
                npc.npc_id,
                "npc",
                position,
                local_spatial_bounds=local_bounds,
            )
        registration_seconds = time.perf_counter() - registration_started
        retained_bytes, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    positions = [
        runtime.continuous_position(npc.npc_id).point
        for npc in npcs
    ]
    update_results = []
    cumulative_started = time.perf_counter()
    previous_target = 0
    for percentage in sorted(set(moving_percentages)):
        target = entity_count * percentage // 100
        update_started = time.perf_counter()
        for index in range(previous_target, target):
            point = positions[index]
            moved_point = WorldPoint(point.x + 0.1, point.y + 0.1)
            result = runtime.set_continuous_position(npcs[index].npc_id, moved_point)
            if not result.success:
                raise RuntimeError(
                    f"Benchmark movement failed for {npcs[index].npc_id}: {result.message}"
                )
            positions[index] = moved_point
        update_results.append({
            "moving_percent": percentage,
            "updated_npcs": target,
            "interval_seconds": time.perf_counter() - update_started,
            "cumulative_update_seconds": time.perf_counter() - cumulative_started,
        })
        previous_target = target

    sample_count = min(entity_count, query_limit)
    stride = max(1, entity_count // sample_count)
    sample_indices = list(range(0, entity_count, stride))[:sample_count]
    query_latencies = []
    candidate_total = 0
    for index in sample_indices:
        query = AABB.around_point(positions[index], 12.0)
        query_started = time.perf_counter()
        candidates = runtime.query_spatial_candidates(MAP_ID, query)
        query_latencies.append(time.perf_counter() - query_started)
        candidate_total += len(candidates)

    return {
        "npc_count": entity_count,
        "broadphase_mode": "collider_aabb" if collider_bounds else "point_only",
        "registration_seconds": registration_seconds,
        "retained_memory_bytes_after_registration": retained_bytes,
        "peak_memory_bytes_after_registration": peak_bytes,
        "movement_updates": update_results,
        "query_count": len(sample_indices),
        "query_seconds": sum(query_latencies),
        "query_latency_seconds": {
            "p50": _percentile(query_latencies, 50),
            "p95": _percentile(query_latencies, 95),
            "p99": _percentile(query_latencies, 99),
        },
        "average_candidates_per_query": (
            candidate_total / len(sample_indices) if sample_indices else 0.0
        ),
    }


def _summarize_repetitions(samples: list[dict]) -> dict:
    """Summarize independent scenario repetitions without hiding raw observations."""
    registration = [sample["registration_seconds"] for sample in samples]
    query = [sample["query_seconds"] for sample in samples]
    memory = [sample["retained_memory_bytes_after_registration"] for sample in samples]
    return {
        "repetitions": len(samples),
        "registration_seconds": {
            "median": statistics.median(registration),
            "p95": _percentile(registration, 95),
        },
        "query_seconds": {
            "median": statistics.median(query),
            "p95": _percentile(query, 95),
        },
        "retained_memory_bytes": {
            "median": statistics.median(memory),
            "min": min(memory),
            "max": max(memory),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--counts", nargs="+", type=int, default=(100, 500, 1000, 5000),
        help="NPC counts to measure.",
    )
    parser.add_argument(
        "--moving-percentages", nargs="+", type=int, default=(0, 10, 50, 100),
        help="Cumulative percentages of NPCs to update.",
    )
    parser.add_argument(
        "--repeats", type=int, default=5,
        help="Independent repetitions per scenario (default: 5).",
    )
    parser.add_argument(
        "--output", type=Path,
        help="Optional JSON report path.",
    )
    args = parser.parse_args()

    if any(count < 1 for count in args.counts):
        parser.error("all NPC counts must be positive")
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    if any(percent < 0 or percent > 100 for percent in args.moving_percentages):
        parser.error("moving percentages must be between 0 and 100")

    report = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "measurement_note": (
            "Point-only and collider-AABB use the same deterministic workload. "
            "Each scenario is independently repeated; timings are observations, "
            "not guaranteed performance. Run on the same machine and Python build "
            "when comparing revisions."
        ),
        "scenarios": [],
    }
    percentages = tuple(args.moving_percentages)
    for count in args.counts:
        for use_bounds in (False, True):
            samples = [
                run_scenario(
                    count,
                    percentages,
                    collider_bounds=use_bounds,
                )
                for _ in range(args.repeats)
            ]
            report["scenarios"].append({
                "npc_count": count,
                "broadphase_mode": "collider_aabb" if use_bounds else "point_only",
                "summary": _summarize_repetitions(samples),
                "samples": samples,
            })

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Benchmark report written to: {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
