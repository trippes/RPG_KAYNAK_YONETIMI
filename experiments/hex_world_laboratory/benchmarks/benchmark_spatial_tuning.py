"""Parameter sweep for uniform-grid cell sizes and quadtree configurations."""
from __future__ import annotations

import json
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.physics.broadphase import AABB
from hex_world_lab.spatial import Quadtree, UniformGrid


def dataset(size, profile, seed):
    rng = random.Random(seed)
    centers = tuple((rng.uniform(-40000, 40000), rng.uniform(-40000, 40000)) for _ in range(8))
    records = {}
    for number in range(size):
        if profile == "clustered":
            cx, cy = centers[number % len(centers)]
            x, y = rng.gauss(cx, 700), rng.gauss(cy, 700)
            extent = rng.choice((8.0, 16.0, 32.0))
        elif profile == "mixed-size":
            x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
            extent = rng.choice((8.0, 16.0, 32.0, 256.0, 512.0))
        else:
            x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
            extent = rng.choice((8.0, 16.0, 32.0))
        records[str(number)] = AABB(x, y, x + extent, y + extent)
    queries = []
    for number in range(16):
        if profile == "clustered":
            cx, cy = centers[number % len(centers)]
            x, y = rng.gauss(cx, 700), rng.gauss(cy, 700)
        else:
            x, y = rng.uniform(-50000, 50000), rng.uniform(-50000, 50000)
        queries.append(AABB(x, y, x + 160, y + 160))
    return records, queries


def measure(index, records, queries):
    samples, counts = [], []
    for query in queries:
        started = time.perf_counter()
        found = index.query(query)
        samples.append((time.perf_counter() - started) * 1000)
        counts.append(len(found))
        expected = tuple(sorted(
            item_id for item_id, bounds in records.items()
            if query.intersects(bounds)
        ))
        if found != expected:
            raise AssertionError("index tuning configuration differs from linear reference")
    ordered = sorted(samples)
    return {
        "query_median_ms": statistics.median(samples),
        "query_p95_ms": ordered[int(.95 * (len(ordered) - 1))],
        "mean_candidates": statistics.mean(counts),
    }


def run(size, profile):
    seed = 91000 + size + sum(ord(c) for c in profile)
    records, queries = dataset(size, profile, seed)
    root = AABB(-1_100_000, -1_100_000, 1_100_000, 1_100_000)
    configurations = []
    grid_sizes = (64, 128, 256) if profile == "mixed-size" else (32, 64, 128)
    for cell_size in grid_sizes:
        configurations.append((f"grid-{cell_size}", lambda cell_size=cell_size: UniformGrid(cell_size)))
    for capacity in (4, 8, 16):
        for depth in (8, 10):
            configurations.append((
                f"quadtree-c{capacity}-d{depth}",
                lambda capacity=capacity, depth=depth: Quadtree(root, capacity=capacity, max_depth=depth),
            ))
    results = {}
    for name, factory in configurations:
        tracemalloc.start()
        started = time.perf_counter()
        index = factory()
        for item_id, bounds in records.items():
            index.insert(item_id, bounds)
        build_ms = (time.perf_counter() - started) * 1000
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[name] = {
            "build_ms": build_ms,
            "peak_bytes": peak_bytes,
            **measure(index, records, queries),
        }
    return {"profile": profile, "obstacles": size, "results": results}


if __name__ == "__main__":
    report = {
        "seed_policy": "91000 + obstacle_count + profile_name_codepoints",
        "python": sys.version,
        "scenarios": [
            run(size, profile)
            for profile in ("uniform", "clustered", "mixed-size")
            for size in (1000, 10000, 50000)
        ],
    }
    output = Path("artifacts/phase-08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "spatial-tuning-benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
