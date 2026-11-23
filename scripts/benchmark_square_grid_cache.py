"""Measure cold chunk generation, warm cache lookups, and retained memory.

Run from the repository root:
    python scripts/benchmark_square_grid_cache.py
"""
from __future__ import annotations

import argparse
import gc
import json
import time
import tracemalloc
from pathlib import Path

from application.hex_map_definition import parse_hex_map
from application.square_grid_cache import SquareGridChunkCache


def benchmark_resolution(definition, cell_size: int, chunk_size: int) -> dict[str, int | float]:
    gc.collect()
    tracemalloc.start()
    before_current, _ = tracemalloc.get_traced_memory()
    cache = SquareGridChunkCache(chunk_size=chunk_size, max_chunks=512)
    coords = cache.chunk_coords(definition, cell_size=cell_size)

    started = time.perf_counter()
    chunks = [
        cache.get_chunk(definition, coord, cell_size=cell_size)
        for coord in coords
    ]
    cold_ms = (time.perf_counter() - started) * 1000.0
    retained_current, peak_bytes = tracemalloc.get_traced_memory()

    started = time.perf_counter()
    for coord in coords:
        cache.get_chunk(definition, coord, cell_size=cell_size)
    warm_ms = (time.perf_counter() - started) * 1000.0

    stats = cache.stats
    result = {
        "cell_size_world_units": cell_size,
        "chunk_size_cells": chunk_size,
        "chunks": len(chunks),
        "cells": sum(len(chunk.cells) for chunk in chunks),
        "walkable_cells": sum(chunk.walkable_count for chunk in chunks),
        "cold_generation_ms": round(cold_ms, 3),
        "warm_lookup_ms": round(warm_ms, 3),
        "retained_memory_bytes": max(0, retained_current - before_current),
        "peak_memory_bytes": peak_bytes,
        "cache_hits": stats.hits,
        "cache_misses": stats.misses,
        "cache_evictions": stats.evictions,
        "cache_entries": stats.entries,
    }
    tracemalloc.stop()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--map",
        type=Path,
        default=Path("content/demo_eldoria/hex_maps/starting_valley.json"),
    )
    parser.add_argument("--chunk-size", type=int, default=16)
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")

    with args.map.open("r", encoding="utf-8") as stream:
        definition = parse_hex_map(json.load(stream))
    results = [
        benchmark_resolution(definition, cell_size, args.chunk_size)
        for cell_size in (16, 8)
    ]
    print(json.dumps({
        "map_id": definition.map_id,
        "valid_hex_cells": len(definition.valid_cells),
        "results": results,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
