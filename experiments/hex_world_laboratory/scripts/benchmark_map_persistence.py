"""Measure map persistence costs at representative cell counts.

Run from the laboratory root with:
    python scripts/benchmark_map_persistence.py
The results are observational; no machine-specific timing threshold is imposed.
"""

from __future__ import annotations

import json
import tempfile
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.persistence import (
    deserialize_map_payload,
    load_map_file,
    map_to_payload,
    save_map_file,
    serialize_map,
)


def build_map(cell_count: int) -> HexMapDefinition:
    cells = {}
    for index in range(cell_count):
        q = index % 100
        r = index // 100
        cells[AxialCoord(q, r)] = HexCellData(
            terrain_id="grass" if index % 5 else "stone",
            is_walkable=True,
            has_obstacle=False,
            metadata={"region": "benchmark", "variant": index % 4},
        )
    return HexMapDefinition(
        world_id=WorldId("benchmark_world"),
        map_id=MapId(f"benchmark_{cell_count}"),
        name=f"Benchmark map ({cell_count} cells)",
        layout=HexLayout(
            HexOrientation.POINTY_TOP,
            radius=1.0,
            origin=WorldPoint(0.0, 0.0),
        ),
        cells=cells,
    )


def timed(callable_):
    started = time.perf_counter()
    result = callable_()
    return result, (time.perf_counter() - started) * 1000.0


def benchmark(cell_count: int) -> dict[str, float | int]:
    definition = build_map(cell_count)
    tracemalloc.start()
    payload, serialize_payload_ms = timed(lambda: map_to_payload(definition))
    json_text, serialize_json_ms = timed(lambda: serialize_map(definition))
    restored, deserialize_ms = timed(lambda: deserialize_map_payload(payload))
    if restored != definition:
        raise AssertionError(f"round-trip mismatch for {cell_count} cells")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "map.json"
        _, save_ms = timed(lambda: save_map_file(definition, path))
        loaded, load_ms = timed(lambda: load_map_file(path))
        if loaded != definition:
            raise AssertionError(f"file round-trip mismatch for {cell_count} cells")
        file_bytes = path.stat().st_size

    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "cells": cell_count,
        "json_bytes": len(json_text.encode("utf-8")),
        "file_bytes": file_bytes,
        "payload_conversion_ms": round(serialize_payload_ms, 3),
        "json_serialization_ms": round(serialize_json_ms, 3),
        "deserialization_ms": round(deserialize_ms, 3),
        "file_save_ms": round(save_ms, 3),
        "file_load_ms": round(load_ms, 3),
        "peak_traced_kib": round(peak_bytes / 1024.0, 1),
    }


if __name__ == "__main__":
    print("Map persistence benchmark (observational; no timing threshold)")
    print(json.dumps([benchmark(size) for size in (100, 1000, 10000)], ensure_ascii=False, indent=2))
