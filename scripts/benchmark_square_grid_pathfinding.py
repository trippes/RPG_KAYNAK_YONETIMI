"""Measure square-grid A* route search on the demo starting map."""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from application.hex_map_definition import load_hex_map_definition
from application.square_grid_coverage import build_square_grid_coverage
from application.square_grid_pathfinding import (
    SquareGridNavigationProfile,
    SquareGridPathfinder,
)
from core.domain.spatial import SquareGridCoord


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _benchmark_resolution(map_definition, cell_size: int) -> dict[str, object]:
    started = time.perf_counter()
    coverage = build_square_grid_coverage(map_definition, cell_size)
    coverage_ms = (time.perf_counter() - started) * 1000.0

    walkable = sorted(
        coord for coord, cell in coverage.cells.items() if cell.walkable
    )
    if not walkable:
        return {
            "cell_size": cell_size,
            "coverage_cells": len(coverage.cells),
            "walkable_cells": 0,
            "coverage_generation_ms": round(coverage_ms, 3),
            "routes_measured": 0,
        }

    origin = SquareGridCoord(0, 0)
    start = min(
        walkable,
        key=lambda coord: (
            (coord.x - origin.x) ** 2 + (coord.y - origin.y) ** 2,
            coord.y,
            coord.x,
        ),
    )
    goals = sorted(
        (coord for coord in walkable if coord != start),
        key=lambda coord: (
            -((coord.x - start.x) ** 2 + (coord.y - start.y) ** 2),
            coord.y,
            coord.x,
        ),
    )[:20]

    timings: list[float] = []
    route_lengths: list[int] = []
    profile = SquareGridNavigationProfile(collider_radius=4.0)
    for goal in goals:
        began = time.perf_counter()
        route = SquareGridPathfinder.find_path(
            coverage, start, goal, profile=profile
        )
        timings.append((time.perf_counter() - began) * 1000.0)
        if route is not None:
            route_lengths.append(len(route))

    return {
        "cell_size": cell_size,
        "coverage_cells": len(coverage.cells),
        "walkable_cells": coverage.walkable_count,
        "coverage_generation_ms": round(coverage_ms, 3),
        "routes_measured": len(timings),
        "reachable_routes": len(route_lengths),
        "route_search_p50_ms": round(statistics.median(timings), 3) if timings else 0.0,
        "route_search_p95_ms": round(_percentile(timings, 0.95), 3),
        "longest_route_cells": max(route_lengths, default=0),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    map_path = root / "content" / "demo_eldoria" / "hex_maps" / "starting_valley.json"
    definition = load_hex_map_definition(map_path)
    results = {
        "map_id": definition.map_id,
        "valid_hex_cells": len(definition.valid_cells),
        "resolutions": [
            _benchmark_resolution(definition, 16),
            _benchmark_resolution(definition, 8),
        ],
        "note": (
            "Hosted/local benchmark timing is comparative only; final acceptance "
            "requires measurement on the target low-end PC."
        ),
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
