"""Reproducible linear/grid/quadtree benchmark; timings are diagnostic, not CI gates."""
from __future__ import annotations

import json
import random
import statistics
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.physics.broadphase import AABB
from hex_world_lab.spatial import Quadtree, UniformGrid


def timed_queries(index, queries):
    samples = []
    for query in queries:
        started = time.perf_counter()
        index.query(query)
        samples.append((time.perf_counter() - started) * 1000)
    return {"median_ms": statistics.median(samples), "p95_ms": sorted(samples)[int(.95*(len(samples)-1))]}


def run(size: int) -> dict:
    rng = random.Random(8080 + size)
    entries = {}
    for number in range(size):
        x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
        extent = rng.choice((8.0, 16.0, 32.0, 128.0))
        entries[str(number)] = AABB(x, y, x + extent, y + extent)
    queries = []
    for _ in range(40):
        x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
        queries.append(AABB(x, y, x + 80, y + 80))
    results = {}
    for name, factory in (
        ("grid", lambda: UniformGrid(64)),
        ("quadtree", lambda: Quadtree(AABB(-51000, -51000, 51000, 51000), capacity=8, max_depth=10)),
    ):
        tracemalloc.start()
        started = time.perf_counter()
        index = factory()
        for item_id, bounds in entries.items():
            index.insert(item_id, bounds)
        build_ms = (time.perf_counter() - started) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[name] = {"build_ms": build_ms, "peak_bytes": peak, **timed_queries(index, queries)}
    def linear_query(query):
        return tuple(sorted(key for key, bounds in entries.items() if query.intersects(bounds)))
    results["linear"] = timed_queries(type("Linear", (), {"query": staticmethod(linear_query)})(), queries)
    # Differential guard is part of the benchmark itself.
    for query in queries:
        expected = linear_query(query)
        for name in ("grid", "quadtree"):
            index = locals()[name]
            if index.query(query) != expected:
                raise AssertionError(f"{name} mismatch at size {size}")
    return {"obstacles": size, "results": results}


if __name__ == "__main__":
    report = {
        "seed": 8080,
        "python": __import__("sys").version,
        "platform": __import__("platform").platform(),
        "scenarios": [run(size) for size in (100, 1000, 10000, 50000)],
    }
    output = Path("artifacts/phase-08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "spatial-index-benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
