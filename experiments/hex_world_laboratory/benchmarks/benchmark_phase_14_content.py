"""Measure cold vector rendering and bounded-cache hits for Phase 14 profiles."""
from __future__ import annotations
import json
import statistics
import time
from pathlib import Path
from hex_world_lab.rendering.procedural import (
    ProceduralSurfaceCache, build_profile_document, render_visual_document,
)

def main():
    cache = ProceduralSurfaceCache(max_entries=16, max_bytes=8_000_000)
    report = {"phase": 14, "profiles": {}}
    for key in ("tree", "rock", "bush", "grass", "flower"):
        document = build_profile_document(key, seed=23)
        cold = []
        for _ in range(25):
            started = time.perf_counter_ns()
            render_visual_document(document)
            cold.append((time.perf_counter_ns() - started) / 1_000)
        warm = []
        for _ in range(25):
            started = time.perf_counter_ns()
            cache.get_or_create((key, 1), lambda: render_visual_document(document))
            warm.append((time.perf_counter_ns() - started) / 1_000)
        report["profiles"][key] = {
            "cold_render_median_us": round(statistics.median(cold), 3),
            "cache_lookup_median_us": round(statistics.median(warm), 3),
        }
    stats = cache.stats()
    report["cache"] = {"hits": stats.hits, "misses": stats.misses, "entries": stats.entries,
                       "bytes": stats.bytes}
    output = Path("artifacts/phase-14")
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
