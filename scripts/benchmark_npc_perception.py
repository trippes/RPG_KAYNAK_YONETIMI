"""Benchmark actual NPC patrol, flee and companion perception workloads.

Run from the repository root:
    python scripts/benchmark_npc_perception.py --counts 1 10 25 50 100 --repeats 5
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from time import perf_counter

from application.companion_commands import CompanionCommandService
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from application.npc_avoidance import NPCAvoidanceSystem
from application.npc_behavior_system import NPCBehaviorSystem
from application.npc_simulation_metrics import NPCSimulationMetrics
from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId
from npc import (
    BehaviorController,
    BehaviorState,
    CompanionCommand,
    CompanionRegistry,
    NPC,
    NPCRegistry,
)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, int((percentile / 100.0) * len(ordered) + 0.999999))
    return ordered[rank - 1]


def _build_scenario(npc_count: int):
    size = 36
    cells = [[q, r] for q in range(size) for r in range(size)]
    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "npc_perception_benchmark",
        "name": "NPC Perception Benchmark",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": cells,
        "cell_overrides": [],
        "transitions": [],
    })
    world_id = WorldId("npc-perception-benchmark")
    metrics = NPCSimulationMetrics()
    runtime = HexWorldRuntime(
        {definition.map_id: definition},
        world_id=world_id,
        metrics=metrics,
    )
    center = size // 2
    runtime.register_entity(
        "hero",
        "player",
        EntityPosition(definition.map_id, LocalHexPosition(center, center)),
        MovementProfile(),
        local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    flee_cells = [
        (center + dq, center + dr)
        for dq in range(-3, 4)
        for dr in range(-3, 4)
        if max(abs(dq), abs(dr), abs(dq + dr)) <= 3 and (dq, dr) != (0, 0)
    ]
    npcs = []
    companion_ids = []
    body_bounds = AABB(-4, -4, 4, 4)
    for index in range(npc_count):
        npc_id = f"benchmark_npc_{index:03d}"
        body = PhysicsBodyDefinition(f"body_{index:03d}", CircleShape(4.0))
        role = index % 3
        if role == 0:
            row = index // 3
            q, r = 2 + row % 10, 2 + row // 10
            behavior = BehaviorState.PATROL
            route = (LocalHexPosition(q, r), LocalHexPosition(q + 1, r))
        elif role == 1:
            flee_index = (index // 3) % len(flee_cells)
            q, r = flee_cells[flee_index]
            behavior = BehaviorState.FLEE
            route = ()
        else:
            row = index // 3
            q, r = 31 - row % 5, 2 + row // 5
            behavior = BehaviorState.IDLE
            route = ()
            companion_ids.append(npc_id)
        npc = NPC(
            npc_id,
            f"Benchmark NPC {index}",
            behavior=BehaviorController(behavior),
            patrol_route=route,
            patrol_interval_seconds=0.25,
            physics_body=body,
        )
        npcs.append(npc)
        runtime.register_entity(
            npc_id,
            "npc",
            EntityPosition(definition.map_id, LocalHexPosition(q, r)),
            MovementProfile(),
            local_spatial_bounds=body_bounds,
        )
    registry = NPCRegistry(npcs)
    snapshot = build_hex_physics_snapshot(world_id, definition, 32.0)
    avoidance = NPCAvoidanceSystem(registry, runtime, snapshot, "hero")
    patrol = NPCBehaviorSystem(registry, runtime, snapshot)
    companion_registry = CompanionRegistry()
    companions = CompanionCommandService(
        runtime, registry, companion_registry, "hero",
        physics_snapshot=snapshot,
    )
    for npc_id in companion_ids:
        companions.enlist(npc_id)
        companions.command(npc_id, CompanionCommand.FOLLOW)
    metrics.reset()
    return metrics, patrol, avoidance, companions


def run_scenario(npc_count: int, steps: int = 30) -> dict:
    if npc_count < 1 or steps < 1:
        raise ValueError("npc_count and steps must be positive")
    metrics, patrol, avoidance, companions = _build_scenario(npc_count)
    step_latencies = []
    for _ in range(steps):
        started = perf_counter()
        patrol.step(1.0 / 60.0)
        avoidance.step(1.0 / 60.0)
        companions.tick(1.0 / 60.0)
        elapsed = perf_counter() - started
        step_latencies.append(elapsed)
        metrics.record_duration("npc_simulation_total", elapsed)
    return {
        "npc_count": npc_count,
        "steps": steps,
        "step_latency_seconds": {
            "p50": _percentile(step_latencies, 50),
            "p95": _percentile(step_latencies, 95),
            "p99": _percentile(step_latencies, 99),
            "max": max(step_latencies),
            "mean": statistics.mean(step_latencies),
        },
        "metrics": metrics.snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", nargs="+", type=int, default=[1, 10, 25, 50, 100])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--output")
    args = parser.parse_args()
    if any(count < 1 for count in args.counts):
        parser.error("all NPC counts must be positive")
    if args.repeats < 1 or args.steps < 1:
        parser.error("--repeats and --steps must be positive")
    report = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "measurement_note": (
            "Measures real patrol, flee and companion systems with opt-in counters. "
            "Compare revisions on the same machine and Python build; timings are "
            "observations, not hardware-independent guarantees."
        ),
        "scenarios": [],
    }
    for count in args.counts:
        samples = [run_scenario(count, args.steps) for _ in range(args.repeats)]
        report["scenarios"].append({
            "npc_count": count,
            "repetitions": args.repeats,
            "step_latency_seconds": {
                key: statistics.median(
                    sample["step_latency_seconds"][key] for sample in samples
                )
                for key in ("p50", "p95", "p99", "max", "mean")
            },
            "metrics": samples[-1]["metrics"],
            "samples": samples,
        })
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            output.write(rendered + "\n")
        print(f"NPC perception benchmark written to: {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
