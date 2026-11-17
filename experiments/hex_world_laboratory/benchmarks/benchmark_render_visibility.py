"""Compare full-map and viewport-culling render costs on deterministic maps."""

from __future__ import annotations

import json
import math
import statistics
import time

import pygame

from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import CellVisual, PygameWorldRenderer, WorldRenderSnapshot
from hex_world_lab.rendering.visibility import VisibleAreaCuller


PROFILES = (61, 128, 256, 1_000, 10_000, 50_000)


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def _measure(operation, repetitions: int) -> dict[str, float]:
    operation()  # warm-up
    samples = []
    for _ in range(repetitions):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1000.0)
    return {
        "avg_ms": statistics.mean(samples),
        "p95_ms": _percentile(samples, 0.95),
        "p99_ms": _percentile(samples, 0.99),
    }


def _make_cells(count: int) -> dict[AxialCoord, None]:
    side = math.ceil(math.sqrt(count))
    start = -(side // 2)
    cells: dict[AxialCoord, None] = {}
    for q in range(start, start + side):
        for r in range(start, start + side):
            if len(cells) >= count:
                return cells
            cells[AxialCoord(q, r)] = None
    return cells


def _snapshot(cells: tuple[CellVisual, ...]) -> WorldRenderSnapshot:
    return WorldRenderSnapshot(
        cells=cells,
        circles=(),
        polygons=(),
        boundaries=(),
        house_lines=(),
        actor_position=WorldPoint(100_000.0, 100_000.0),
        actor_radius=1.0,
    )


def main() -> None:
    pygame.init()
    try:
        layout = HexLayout(HexOrientation.FLAT_TOP, radius=32.0)
        transform = WorldScreenTransform(Viewport(960, 640), WorldPoint(0.0, 0.0), 1.0)
        surface = pygame.Surface((960, 640))
        renderer = PygameWorldRenderer()
        culler = VisibleAreaCuller()
        report = []

        for count in PROFILES:
            cells = _make_cells(count)
            repetitions = 3 if count >= 10_000 else 7
            visible_coords: tuple[AxialCoord, ...] = ()

            culling_metrics = _measure(
                lambda: culler.visible_cells(cells, layout, transform), repetitions
            )
            visible_coords = culler.visible_cells(cells, layout, transform)
            full_visuals = tuple(CellVisual(coord) for coord in cells)
            visible_visuals = tuple(CellVisual(coord) for coord in visible_coords)
            full_snapshot = _snapshot(full_visuals)
            visible_snapshot = _snapshot(visible_visuals)

            full_snapshot_metrics = _measure(lambda: tuple(CellVisual(c) for c in cells), repetitions)
            visible_snapshot_metrics = _measure(
                lambda: tuple(CellVisual(c) for c in visible_coords), repetitions
            )
            full_render_metrics = _measure(
                lambda: renderer.render(surface, full_snapshot, layout, transform), repetitions
            )
            visible_render_metrics = _measure(
                lambda: renderer.render(surface, visible_snapshot, layout, transform), repetitions
            )

            full_pipeline_ms = full_snapshot_metrics["avg_ms"] + full_render_metrics["avg_ms"]
            culled_pipeline_ms = (
                culling_metrics["avg_ms"]
                + visible_snapshot_metrics["avg_ms"]
                + visible_render_metrics["avg_ms"]
            )
            report.append({
                "map_cells": count,
                "visible_cells": len(visible_coords),
                "culled_cells": count - len(visible_coords),
                "culling": culling_metrics,
                "snapshot_full": full_snapshot_metrics,
                "snapshot_visible": visible_snapshot_metrics,
                "render_full": full_render_metrics,
                "render_visible": visible_render_metrics,
                "render_time_reduction_percent": (
                    0.0 if full_render_metrics["avg_ms"] <= 0.0 else
                    100.0 * (1.0 - visible_render_metrics["avg_ms"] / full_render_metrics["avg_ms"])
                ),
                "pipeline_full_avg_ms": full_pipeline_ms,
                "pipeline_culled_avg_ms": culled_pipeline_ms,
                "pipeline_time_reduction_percent": (
                    0.0 if full_pipeline_ms <= 0.0 else
                    100.0 * (1.0 - culled_pipeline_ms / full_pipeline_ms)
                ),
            })

        print(json.dumps({
            "benchmark": "render_visibility",
            "viewport": [960, 640],
            "zoom": 1.0,
            "orientation": "flat_top",
            "repetitions": "7 (small/medium), 3 (large/stress), plus one warm-up",
            "results": report,
        }, indent=2))
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
