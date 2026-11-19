"""Measure NPC registration and collider-aware spatial-index overhead.

Run from the repository root:
    python scripts/benchmark_npc_spatial_index.py --output npc-spatial-benchmark.json

The report compares the current point-only broadphase with collider AABBs.
It is a measurement harness, not a performance assertion or a CI threshold.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import tracemalloc

from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, WorldPoint
from npc import NPC


MAP_ID = "npc_physics_benchmark"
COLLIDER_BOUNDS = (-4.0, -4.0, 4.0, 4.0)


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
    tracemalloc.start()
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
        local_bounds = (
            AABB(*COLLIDER_BOUNDS)
            if collider_bounds
            else None
        )
        runtime.register_entity(
            npc.npc_id,
            "npc",
            position,
            local_spatial_bounds=local_bounds,
        )
    registration_seconds = time.perf_counter() - registration_started
    retained_bytes, peak_bytes = tracemalloc.get_traced_memory()
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
        for index in range(previous_target, target):
            point = positions[index]
            moved_point = WorldPoint(point.x + 0.1, point.y + 0.1)
            result = runtime.set_continuous_position(
                npcs[index].npc_id,
                moved_point,
            )
            if not result.success:
                raise RuntimeError(
                    f"Benchmark movement failed for {npcs[index].npc_id}: {result.message}"
                )
            positions[index] = moved_point
        update_results.append({
            "moving_percent": percentage,
            "updated_npcs": target,
            "cumulative_update_seconds": time.perf_counter() - cumulative_started,
        })
        previous_target = target

    sample_count = min(entity_count, query_limit)
    stride = max(1, entity_count // sample_count)
    sample_indices = list(range(0, entity_count, stride))[:sample_count]
    query_started = time.perf_counter()
    candidate_total = 0
    for index in sample_indices:
        candidate_total += len(runtime.query_spatial_candidates(
            MAP_ID,
            AABB.around_point(positions[index], 12.0),
        ))
    query_seconds = time.perf_counter() - query_started

    return {
        "npc_count": entity_count,
        "broadphase_mode": "collider_aabb" if collider_bounds else "point_only",
        "registration_seconds": registration_seconds,
        "retained_memory_bytes_after_registration": retained_bytes,
        "peak_memory_bytes_after_registration": peak_bytes,
        "movement_updates": update_results,
        "query_count": len(sample_indices),
        "query_seconds": query_seconds,
        "average_candidates_per_query": (
            candidate_total / len(sample_indices) if sample_indices else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--counts",
        nargs="+",
        type=int,
        default=(100, 500, 1000, 5000),
        help="NPC counts to measure.",
    )
    parser.add_argument(
        "--moving-percentages",
        nargs="+",
        type=int,
        default=(0, 10, 50, 100),
        help="Cumulative percentages of NPCs to update.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path.",
    )
    args = parser.parse_args()

    if any(count < 1 for count in args.counts):
        parser.error("all NPC counts must be positive")
    if any(percent < 0 or percent > 100 for percent in args.moving_percentages):
        parser.error("moving percentages must be between 0 and 100")

    report = {
        "measurement_note": (
            "Compare point_only and collider_aabb on the same machine; "
            "timings are observations, not guaranteed performance."
        ),
        "scenarios": [],
    }
    percentages = tuple(args.moving_percentages)
    for count in args.counts:
        for use_bounds in (False, True):
            report["scenarios"].append(run_scenario(
                count,
                percentages,
                collider_bounds=use_bounds,
            ))

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Benchmark report written to: {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
