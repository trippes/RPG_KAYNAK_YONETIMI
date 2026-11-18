"""Phase 11 repeatable entity spatial performance and memory benchmark."""
from __future__ import annotations

import gc
import json
import platform
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.entities import (
    EntityId, EntityKind, EntityLocation, EntityRecord, EntityRegistry, EntityTransform,
)
from hex_world_lab.entities.spatial_index import EntityAABB, EntitySpatialIndex
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.interaction import InteractionProfile
from hex_world_lab.world import HexWorld, MapId, WorldId


SESSION_COUNT = 3
WARMUP_QUERY_COUNT = 20
WARMUP_UPDATE_COUNT = 20
MEASURED_QUERY_COUNT = 120
MEASURED_UPDATE_LIMIT = 1_000


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def _move_entity(entity: EntityRecord, world_id: WorldId, map_id: MapId, dx: float, dy: float) -> EntityRecord:
    return entity.with_transform(
        EntityTransform(
            EntityLocation(
                world_id,
                map_id,
                WorldPoint(entity.transform.location.position.x + dx, entity.transform.location.position.y + dy),
            )
        )
    )


def run_session(size: int, session: int) -> dict[str, object]:
    seed = 11_600 + size * 10 + session
    rng = random.Random(seed)
    world = HexWorld(WorldId(f"phase-11-benchmark-{size}-{session}"))
    map_id = MapId("benchmark-map")
    world.register_map(map_id, "Benchmark")
    registry = EntityRegistry(world.world_id, world.map_registry)
    profile = InteractionProfile(True, 12.0, frozenset({"inspect"}), 0)
    entities: list[EntityRecord] = []

    tracemalloc.start()
    for number in range(size):
        if number % 4 == 0:
            x = rng.uniform(-250.0, 250.0)
            y = rng.uniform(-250.0, 250.0)
        else:
            x = rng.uniform(-25_000.0, 25_000.0)
            y = rng.uniform(-25_000.0, 25_000.0)
        entity = EntityRecord(
            EntityId(f"phase-11-{number:05d}"),
            EntityKind.NPC if number % 2 else EntityKind.RESOURCE,
            EntityTransform(EntityLocation(world.world_id, map_id, WorldPoint(x, y))),
            interaction_profile=profile,
        )
        registry.register(entity)
        entities.append(entity)

    # Warm-up build is excluded from the measured build duration.
    warmup_index = EntitySpatialIndex(registry, cell_size=128.0)
    warmup_index.activate_map(map_id)
    for _ in range(WARMUP_QUERY_COUNT):
        center_x = rng.uniform(-25_000.0, 25_000.0)
        center_y = rng.uniform(-25_000.0, 25_000.0)
        warmup_index.query(
            map_id,
            EntityAABB(center_x - 100.0, center_y - 100.0, center_x + 100.0, center_y + 100.0),
        )
    # Do not count the disposable warm-up index in measured memory.
    del warmup_index
    gc.collect()

    spatial = EntitySpatialIndex(registry, cell_size=128.0)
    started = time.perf_counter()
    spatial.activate_map(map_id)
    build_ms = (time.perf_counter() - started) * 1000.0

    warmup_updates = min(WARMUP_UPDATE_COUNT, size)
    for number in range(warmup_updates):
        moved = _move_entity(entities[number], world.world_id, map_id, 37.0, -19.0)
        registry.update_transform(moved.entity_id, moved.transform)
        spatial.update_entity(moved)
        entities[number] = moved

    update_durations: list[float] = []
    update_end = min(size, warmup_updates + MEASURED_UPDATE_LIMIT)
    for number in range(warmup_updates, update_end):
        moved = _move_entity(entities[number], world.world_id, map_id, 37.0, -19.0)
        started = time.perf_counter()
        registry.update_transform(moved.entity_id, moved.transform)
        spatial.update_entity(moved)
        update_durations.append((time.perf_counter() - started) * 1000.0)
        entities[number] = moved

    query_durations: list[float] = []
    candidate_counts: list[int] = []
    linear_durations: list[float] = []
    for _ in range(MEASURED_QUERY_COUNT):
        center_x = rng.uniform(-25_000.0, 25_000.0)
        center_y = rng.uniform(-25_000.0, 25_000.0)
        bounds = EntityAABB(center_x - 100.0, center_y - 100.0, center_x + 100.0, center_y + 100.0)

        started = time.perf_counter()
        candidates = spatial.query(map_id, bounds)
        query_durations.append((time.perf_counter() - started) * 1000.0)
        candidate_counts.append(len(candidates))

        started = time.perf_counter()
        tuple(
            entity for entity in registry.entities_for_map(world.world_id, map_id)
            if (entity_bounds := spatial.bounds_for(entity)) is not None
            and bounds.intersects(entity_bounds)
        )
        linear_durations.append((time.perf_counter() - started) * 1000.0)

    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "session": session,
        "seed": seed,
        "entities": size,
        "distribution": "seeded mixed sparse/clustered",
        "warmup_queries": WARMUP_QUERY_COUNT,
        "warmup_updates": warmup_updates,
        "index_build_ms": round(build_ms, 4),
        "index_update_ms": {
            "median": round(statistics.median(update_durations), 5) if update_durations else None,
            "p95": round(percentile(update_durations, 0.95), 5) if update_durations else None,
            "p99": round(percentile(update_durations, 0.99), 5) if update_durations else None,
        },
        "indexed_query_ms": {
            "median": round(statistics.median(query_durations), 5),
            "p95": round(percentile(query_durations, 0.95), 5),
            "p99": round(percentile(query_durations, 0.99), 5),
        },
        "linear_query_ms": {
            "median": round(statistics.median(linear_durations), 5),
            "p95": round(percentile(linear_durations, 0.95), 5),
            "p99": round(percentile(linear_durations, 0.99), 5),
        },
        "mean_indexed_candidates": round(statistics.fmean(candidate_counts), 3),
        "tracemalloc_current_mib": round(current_bytes / (1024 * 1024), 3),
        "tracemalloc_peak_mib": round(peak_bytes / (1024 * 1024), 3),
        "update_samples": len(update_durations),
        "query_samples": len(query_durations),
    }


def _session_median(sessions: list[dict[str, object]], path: tuple[str, ...]) -> float | None:
    values: list[float] = []
    for session in sessions:
        value: object = session
        for key in path:
            value = value[key]  # type: ignore[index]
        if isinstance(value, (int, float)):
            values.append(float(value))
    return round(statistics.median(values), 5) if values else None


def run_profile(size: int) -> dict[str, object]:
    sessions = [run_session(size, session) for session in range(1, SESSION_COUNT + 1)]
    return {
        "entities": size,
        "session_count": SESSION_COUNT,
        "sessions": sessions,
        "median_across_sessions": {
            "index_build_ms": _session_median(sessions, ("index_build_ms",)),
            "index_update_median_ms": _session_median(sessions, ("index_update_ms", "median")),
            "index_update_p95_ms": _session_median(sessions, ("index_update_ms", "p95")),
            "indexed_query_median_ms": _session_median(sessions, ("indexed_query_ms", "median")),
            "indexed_query_p95_ms": _session_median(sessions, ("indexed_query_ms", "p95")),
            "indexed_query_p99_ms": _session_median(sessions, ("indexed_query_ms", "p99")),
            "linear_query_median_ms": _session_median(sessions, ("linear_query_ms", "median")),
            "tracemalloc_peak_mib": _session_median(sessions, ("tracemalloc_peak_mib",)),
        },
    }


def main() -> int:
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unavailable",
        "session_count": SESSION_COUNT,
        "warmup_queries_per_session": WARMUP_QUERY_COUNT,
        "warmup_updates_per_session": WARMUP_UPDATE_COUNT,
        "measurement_note": "Use the median across three independent seeded sessions. Compare only runs on the same runner and Python environment; no cross-machine absolute threshold is implied.",
        "profiles": [run_profile(size) for size in (100, 1_000, 10_000)],
    }
    output = Path("artifacts/phase-11")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase-11-entity-spatial-performance.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
