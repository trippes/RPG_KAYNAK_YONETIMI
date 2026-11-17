"""Reproducible linear/grid/quadtree benchmark across scale and spatial profiles."""
from __future__ import annotations

import json
import platform
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.physics.broadphase import AABB
from hex_world_lab.spatial import Quadtree, UniformGrid


def timed_queries(query_function, queries):
    samples, counts = [], []
    for query in queries:
        started = time.perf_counter()
        found = query_function(query)
        samples.append((time.perf_counter() - started) * 1000)
        counts.append(len(found))
    ordered = sorted(samples)
    return {
        "median_ms": statistics.median(samples),
        "p95_ms": ordered[int(.95 * (len(ordered) - 1))],
        "total_ms": sum(samples),
        "mean_candidates": statistics.mean(counts),
        "total_candidates": sum(counts),
    }


def make_entries(size: int, profile: str, seed: int):
    rng = random.Random(seed)
    entries = {}
    centers = tuple((rng.uniform(-40000, 40000), rng.uniform(-40000, 40000)) for _ in range(8))
    for number in range(size):
        if profile == "clustered":
            cx, cy = centers[number % len(centers)]
            x, y = rng.gauss(cx, 700), rng.gauss(cy, 700)
            extent = rng.choice((8.0, 16.0, 32.0))
        elif profile == "sparse":
            x, y = rng.uniform(-1_000_000, 1_000_000), rng.uniform(-1_000_000, 1_000_000)
            extent = rng.choice((8.0, 16.0, 32.0))
        else:
            x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
            extent = rng.choice((8.0, 16.0, 32.0, 256.0, 512.0)) if profile == "mixed-size" else rng.choice((8.0, 16.0, 32.0))
        entries[str(number)] = AABB(x, y, x + extent, y + extent)
    return entries, centers


def make_queries(profile, centers, seed):
    rng = random.Random(seed)
    queries = []
    for number in range(24):
        if profile == "clustered":
            cx, cy = centers[number % len(centers)]
            x, y = rng.gauss(cx, 700), rng.gauss(cy, 700)
        elif profile == "sparse":
            x, y = rng.uniform(-1_000_000, 1_000_000), rng.uniform(-1_000_000, 1_000_000)
        else:
            x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
        queries.append(AABB(x, y, x + 160, y + 160))
    return queries


def measure_churn(index, entries, seed):
    rng = random.Random(seed)
    ids = list(entries)
    low_count = min(max(1, len(ids) // 100), 100)
    high_count = min(max(1, len(ids) // 20), 250)
    def update_sample(count):
        selected = rng.sample(ids, count)
        started = time.perf_counter()
        for item_id in selected:
            old = entries[item_id]
            moved = AABB(old.min_x + 3.0, old.min_y + 2.0, old.max_x + 3.0, old.max_y + 2.0)
            index.update(item_id, moved)
        return (time.perf_counter() - started) * 1000 / count
    low_ms = update_sample(low_count)
    high_ms = update_sample(high_count)
    insert_values = []
    started = time.perf_counter()
    for number in range(20):
        item_id = f"temporary-{number}"
        bounds = AABB(-100 + number, -100 + number, -90 + number, -90 + number)
        index.insert(item_id, bounds)
        insert_values.append(item_id)
    insert_ms = (time.perf_counter() - started) * 1000 / len(insert_values)
    started = time.perf_counter()
    for item_id in insert_values:
        index.remove(item_id)
    remove_ms = (time.perf_counter() - started) * 1000 / len(insert_values)
    return {
        "low_churn_updates": low_count, "low_churn_avg_update_ms": low_ms,
        "high_churn_updates": high_count, "high_churn_avg_update_ms": high_ms,
        "avg_insert_ms": insert_ms, "avg_remove_ms": remove_ms,
    }


def run(size: int, profile: str) -> dict:
    seed = 8080 + size + sum(ord(char) for char in profile)
    entries, centers = make_entries(size, profile, seed)
    queries = make_queries(profile, centers, seed + 1)
    root = AABB(-1_100_000, -1_100_000, 1_100_000, 1_100_000)
    results = {}
    indexes = {}
    for name, factory in (
        ("grid", lambda: UniformGrid(128)),
        ("quadtree", lambda: Quadtree(root, capacity=8, max_depth=10)),
    ):
        tracemalloc.start()
        started = time.perf_counter()
        index = factory()
        for item_id, bounds in entries.items():
            index.insert(item_id, bounds)
        build_ms = (time.perf_counter() - started) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        indexes[name] = index
        results[name] = {
            "build_ms": build_ms, "peak_bytes": peak,
            "structure_count": getattr(index, "bucket_count", getattr(index, "node_count", None)),
            **timed_queries(index.query, queries),
        }
    def linear_query(query):
        return tuple(sorted(key for key, bounds in entries.items() if query.intersects(bounds)))
    results["linear"] = timed_queries(linear_query, queries)
    for query in queries:
        expected = linear_query(query)
        for name, index in indexes.items():
            if index.query(query) != expected:
                raise AssertionError(f"{name} mismatch at {profile}/{size}")
    for name, index in indexes.items():
        results[name]["churn"] = measure_churn(index, entries, seed + 2)
    for name in ("grid", "quadtree"):
        results[name]["query_speedup_vs_linear"] = (
            results["linear"]["median_ms"] / results[name]["median_ms"]
            if results[name]["median_ms"] else None
        )
    return {"profile": profile, "obstacles": size, "query_count": len(queries), "results": results}


if __name__ == "__main__":
    report = {
        "seed_policy": "8080 + obstacle_count + profile_name_codepoints",
        "python": sys.version,
        "platform": platform.platform(),
        "scenarios": [
            run(size, profile)
            for profile in ("uniform", "clustered", "sparse", "mixed-size")
            for size in (100, 1000, 10000, 50000)
        ],
    }
    output = Path("artifacts/phase-08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "spatial-index-benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
