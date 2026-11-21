"""Benchmark real HexWorldRuntime click-to-move path queries and route caching."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from time import perf_counter_ns

from application.click_move_route import ClickMoveRouteController
from application.hex_map_definition import parse_hex_map
from application.hex_map_physics import build_hex_map_collision_geometry
from application.hex_physics_bridge import HexPhysicsSnapshot
from application.hex_world_runtime import HexWorldRuntime
from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile, WorldPoint
from core.foundation import WorldId


def _percentile(samples: list[float], percentile: float) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    index = int(round((len(ordered) - 1) * percentile))
    return round(ordered[index], 6)


def _map_definition(route_cells: int, topology: str):
    map_id = f"click_move_benchmark_{topology}_{route_cells}"
    valid_cells = (
        [[q, 0] for q in range(route_cells + 1)]
        if topology == "corridor"
        else [
            [q, r]
            for q in range(route_cells + 1)
            for r in range(-2, 3)
        ]
    )
    landmarks = []
    if topology == "broad_obstacle" and route_cells >= 3:
        landmarks.append({
            "id": "benchmark_obstacle",
            "name": "Benchmark Obstacle",
            "position": [route_cells // 2, 0],
            "walkable": False,
        })
    return parse_hex_map({
        "schema_version": 2,
        "map_id": map_id,
        "name": f"Click Move Benchmark {topology} {route_cells}",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": valid_cells,
        "landmarks": landmarks,
    })


def _scenario(route_cells: int, topology: str):
    map_definition = _map_definition(route_cells, topology)
    origin = WorldPoint(0.0, 0.0)
    geometry = build_hex_map_collision_geometry(
        map_definition, 32.0, origin=origin,
    )
    snapshot = HexPhysicsSnapshot(
        WorldId("player-click-move-benchmark"),
        map_definition,
        32.0,
        origin,
        geometry,
    )
    runtime = HexWorldRuntime({map_definition.map_id: map_definition})
    start = LocalHexPosition(0, 0)
    goal = LocalHexPosition(route_cells, 0)
    runtime.register_entity(
        "hero",
        "player",
        EntityPosition(map_definition.map_id, start),
        MovementProfile(),
    )
    body = PhysicsBodyDefinition("hero", CircleShape(8.0))
    return runtime, goal, snapshot, body


def _edge_validator(snapshot, body):
    return lambda source, destination: snapshot.can_reach_cell(
        source, destination, body,
    )


def _baseline_samples(route_cells: int, topology: str, iterations: int):
    runtime, goal, snapshot, body = _scenario(route_cells, topology)
    validate_edge = _edge_validator(snapshot, body)
    samples = []
    for _ in range(iterations):
        started = perf_counter_ns()
        path = runtime.path_to("hero", goal, edge_validator=validate_edge)
        samples.append((perf_counter_ns() - started) / 1_000_000.0)
        if path is None or path[0] != LocalHexPosition(0, 0) or path[-1] != goal:
            raise RuntimeError(
                f"Baseline path failed for {topology} {route_cells}-cell route: {path!r}",
            )
    return {
        "path_queries": iterations,
        "path_cells": route_cells,
        "path_nodes": len(path),
        "path_planning_p50_ms": _percentile(samples, 0.50),
        "path_planning_p95_ms": _percentile(samples, 0.95),
        "path_planning_p99_ms": _percentile(samples, 0.99),
    }


def _controller_samples(route_cells: int, topology: str, iterations: int):
    runtime, goal, snapshot, body = _scenario(route_cells, topology)
    controller = ClickMoveRouteController(timing_enabled=True)
    for _ in range(iterations):
        controller.cancel("independent_benchmark_sample")
        intent = controller.intent(runtime, "hero", goal, snapshot, body)
        if not intent.is_moving:
            raise RuntimeError(
                f"Controller produced no intent for {route_cells}-cell route.",
            )
    metrics = controller.metrics_snapshot()
    return {
        "path_queries": metrics["player_click_path_queries"],
        "path_planning_p50_ms": metrics["player_click_path_planning_p50_ms"],
        "path_planning_p95_ms": metrics["player_click_path_planning_p95_ms"],
        "path_planning_p99_ms": metrics["player_click_path_planning_p99_ms"],
    }


def _cache_probe(route_cells: int, topology: str, iterations: int):
    runtime, goal, snapshot, body = _scenario(route_cells, topology)
    controller = ClickMoveRouteController(timing_enabled=True)
    initial_started = perf_counter_ns()
    initial_intent = controller.intent(runtime, "hero", goal, snapshot, body)
    initial_plan_ms = (perf_counter_ns() - initial_started) / 1_000_000.0
    if not initial_intent.is_moving:
        raise RuntimeError(
            f"Cached route produced no intent for {route_cells}-cell route.",
        )
    intent_samples = []
    for _ in range(iterations - 1):
        started = perf_counter_ns()
        intent = controller.intent(runtime, "hero", goal, snapshot, body)
        intent_samples.append((perf_counter_ns() - started) / 1_000_000.0)
        if not intent.is_moving:
            raise RuntimeError(
                f"Cached route produced no intent for {route_cells}-cell route.",
            )
    metrics = controller.metrics_snapshot()
    return {
        "intent_calls": iterations,
        "initial_plan_ms": round(initial_plan_ms, 6),
        "cached_intent_calls": len(intent_samples),
        "path_queries": metrics["player_click_path_queries"],
        "cache_hits": metrics["player_click_route_cache_hits"],
        "cache_misses": metrics["player_click_route_cache_misses"],
        "replans": metrics["player_click_route_replans"],
        "invalidations": metrics["player_click_route_invalidations"],
        "blocked_steps": metrics["player_click_route_blocked_steps"],
        "failures": metrics["player_click_route_failures"],
        "cache_hit_ratio_percent": round(
            100.0 * metrics["player_click_route_cache_hits"] / iterations,
            3,
        ),
        "cached_intent_step_p50_ms": _percentile(intent_samples, 0.50),
        "cached_intent_step_p95_ms": _percentile(intent_samples, 0.95),
        "cached_intent_step_p99_ms": _percentile(intent_samples, 0.99),
    }



def _edge_validation_profile(route_cells: int, topology: str, samples: int = 7) -> dict:
    """Measure physical edge validation separately from the A* core.

    The no-validator run is diagnostic only: it is not a gameplay mode and
    must never be used to accept a route in production.
    """
    warmups = 2
    measured = samples
    full_samples = []
    core_samples = []
    edge_time_samples = []
    edge_call_samples = []

    for sample_index in range(warmups + measured):
        runtime, goal, snapshot, body = _scenario(route_cells, topology)
        edge_calls = 0
        edge_elapsed_ns = 0

        def measured_edge_validator(source, destination):
            nonlocal edge_calls, edge_elapsed_ns
            edge_calls += 1
            started = perf_counter_ns()
            try:
                return snapshot.can_reach_cell(source, destination, body)
            finally:
                edge_elapsed_ns += perf_counter_ns() - started

        started = perf_counter_ns()
        full_path = runtime.path_to(
            "hero", goal, edge_validator=measured_edge_validator,
        )
        full_elapsed_ns = perf_counter_ns() - started

        core_runtime, core_goal, _, _ = _scenario(route_cells, topology)
        started = perf_counter_ns()
        core_path = core_runtime.path_to("hero", core_goal)
        core_elapsed_ns = perf_counter_ns() - started

        if (
            full_path is None or core_path is None
            or full_path[0] != LocalHexPosition(0, 0)
            or full_path[-1] != goal
            or core_path[0] != LocalHexPosition(0, 0)
            or core_path[-1] != core_goal
        ):
            raise RuntimeError(
                f"Diagnostic path failed for {topology} {route_cells}-cell route.",
            )

        if sample_index >= warmups:
            full_samples.append(full_elapsed_ns / 1_000_000.0)
            core_samples.append(core_elapsed_ns / 1_000_000.0)
            edge_time_samples.append(edge_elapsed_ns / 1_000_000.0)
            edge_call_samples.append(edge_calls)

    shares = [
        edge_ms / full_ms * 100.0
        for edge_ms, full_ms in zip(
            edge_time_samples, full_samples, strict=True,
        )
    ]
    deltas = [
        full_ms - core_ms
        for full_ms, core_ms in zip(full_samples, core_samples, strict=True)
    ]
    return {
        "samples": measured,
        "warmup_samples": warmups,
        "validated_path_p50_ms": _percentile(full_samples, 0.50),
        "a_star_without_edge_validator_p50_ms": _percentile(core_samples, 0.50),
        "edge_validator_inclusive_time_p50_ms": _percentile(edge_time_samples, 0.50),
        "estimated_edge_validator_share_p50_percent": _percentile(shares, 0.50),
        "validated_minus_core_p50_ms": _percentile(deltas, 0.50),
        "edge_validator_calls_per_query_p50": _percentile(
            [float(value) for value in edge_call_samples], 0.50,
        ),
        "edge_validator_calls_per_query_min": min(edge_call_samples),
        "edge_validator_calls_per_query_max": max(edge_call_samples),
        "validated_path_nodes": len(full_path),
        "no_validator_path_nodes": len(core_path),
        "paths_match": full_path == core_path,
        "interpretation": (
            "The no-validator path is a diagnostic counterfactual only. "
            "For obstacle maps it may cross an obstacle and differ from the "
            "validated route. Gameplay continues to require physical edge validation."
        ),
    }

def run_benchmark(route_lengths: list[int], topologies: list[str], iterations: int) -> dict:
    scenarios = []
    for topology in topologies:
        for route_cells in route_lengths:
            print(f"Benchmarking {topology} {route_cells}-cell player route ({iterations} samples)...", flush=True)
            baseline = _baseline_samples(route_cells, topology, iterations)
            controller = _controller_samples(route_cells, topology, iterations)
            cached = _cache_probe(route_cells, topology, iterations)
            edge_profile = _edge_validation_profile(route_cells, topology)
            scenarios.append({
                "topology": topology,
                "route_cells": route_cells,
                "route_nodes": baseline["path_nodes"],
                "iterations": iterations,
                "baseline": baseline,
                "controller_replanned_samples": controller,
                "cached_route": cached,
                "edge_validation_profile": edge_profile,
                "path_query_reduction_percent": round(
                    100.0 * (
                        1.0 - cached["path_queries"] / baseline["path_queries"]
                    ),
                    3,
                ),
                "target_arrival_time_ms": None,
            })
    return {
        "benchmark": "eldoria_player_click_to_move",
        "method": (
            "Real HexWorldRuntime A* and occupancy with immutable native "
            "physics snapshot; direct repeated path_to baseline compared "
            "with one active cached route."
        ),
        "iterations": iterations,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "route_lengths_cells": route_lengths,
        "topologies": topologies,
        "arrival_time_note": (
            "Not measured: MovementIntegrator has no target-aware braking "
            "or acceleration model; see phase 3.5 assessment."
        ),
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument(
        "--route-lengths",
        type=int,
        nargs="+",
        default=[1, 10, 100],
    )
    parser.add_argument(
        "--topologies",
        choices=["corridor", "broad_obstacle"],
        nargs="+",
        default=["corridor"],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("player-click-move-benchmark.json"),
    )
    args = parser.parse_args()
    if args.iterations < 2:
        parser.error("--iterations must be at least 2")
    if not args.route_lengths or any(length < 1 for length in args.route_lengths):
        parser.error("--route-lengths values must be positive")

    result = run_benchmark(args.route_lengths, args.topologies, args.iterations)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
