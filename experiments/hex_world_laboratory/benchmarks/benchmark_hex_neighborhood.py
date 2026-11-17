"""Compare full-map hex radius scans with direct axial enumeration."""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from hex_world_lab.geometry import AxialCoord, hex_distance, hex_radius_cells


def measure(function, repeats=100):
    values = []
    for _ in range(repeats):
        started = time.perf_counter()
        function()
        values.append((time.perf_counter() - started) * 1000)
    return {"median_ms": statistics.median(values), "p95_ms": sorted(values)[int(.95*(len(values)-1))]}


if __name__ == "__main__":
    cells = tuple(AxialCoord(q, r) for q in range(-100, 101) for r in range(-100, 101))
    center, radius = AxialCoord(0, 0), 12
    expected = tuple(cell for cell in cells if hex_distance(center, cell) <= radius)
    direct = hex_radius_cells(center, radius)
    if set(expected) != set(direct):
        raise AssertionError("direct axial query differs from full scan")
    report = {
        "map_cells": len(cells), "query_radius": radius,
        "full_scan": measure(lambda: tuple(cell for cell in cells if hex_distance(center, cell) <= radius)),
        "axial_enumeration": measure(lambda: hex_radius_cells(center, radius)),
    }
    output = Path("artifacts/phase-08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "hex-neighborhood-benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
