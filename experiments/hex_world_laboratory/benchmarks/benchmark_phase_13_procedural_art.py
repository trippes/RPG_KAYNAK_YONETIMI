"""Benchmark procedural profile generation against warm bounded-cache hits."""
from __future__ import annotations

import json
from pathlib import Path
import statistics
import time

from hex_world_lab.rendering.procedural import (
    PROFILE_DEFINITIONS,
    ProceduralSurfaceCache,
    build_environment_profile,
)


def _measure(callable_, repetitions: int) -> float:
    started = time.perf_counter()
    for _ in range(repetitions):
        callable_()
    return (time.perf_counter() - started) / repetitions * 1_000_000


def run_benchmark(repetitions: int = 20, sessions: int = 3) -> dict:
    if repetitions < 2 or sessions < 1:
        raise ValueError("repetitions must be >= 2 and sessions must be >= 1")
    report = {
        "repetitions": repetitions,
        "sessions": sessions,
        "profiles": {},
    }
    for key in PROFILE_DEFINITIONS:
        uncached_samples = []
        cached_samples = []
        cache_stats = None
        for session in range(sessions):
            uncached_samples.append(
                _measure(
                    lambda: build_environment_profile(key, seed=17),
                    repetitions,
                )
            )
            cache = ProceduralSurfaceCache(max_entries=8, max_bytes=8 * 1024 * 1024)
            cache.get_or_create(
                (key, session), lambda: build_environment_profile(key, seed=17)
            )
            cached_samples.append(
                _measure(
                    lambda: cache.get_or_create(
                        (key, session), lambda: build_environment_profile(key, seed=17)
                    ),
                    repetitions,
                )
            )
            cache_stats = cache.stats()
        uncached_median = statistics.median(uncached_samples)
        cached_median = statistics.median(cached_samples)
        report["profiles"][key] = {
            "uncached_us_per_build_median": round(uncached_median, 3),
            "cached_us_per_hit_median": round(cached_median, 3),
            "speedup": round(uncached_median / cached_median, 2),
            "surface_bytes": cache_stats.estimated_bytes,
            "cache_evictions": cache_stats.evictions,
        }
    return report


def main() -> None:
    report = run_benchmark()
    output = Path("artifacts/phase-13")
    output.mkdir(parents=True, exist_ok=True)
    path = output / "procedural-benchmark.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Benchmark report: {path}")


if __name__ == "__main__":
    main()
