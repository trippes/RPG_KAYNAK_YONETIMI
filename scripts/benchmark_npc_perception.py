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
        (center + 1, center),
        (center - 1, center),
        (center, center + 1),
        (center, center - 1),
        (center + 1, center - 1),
        (center - 1, center + 1),
    ]
    managed_npc_count = min(npc_count, 18)
    npcs = []
    companion_ids = []
    body_bounds = AABB(-4, -4, 4, 4)
    for index in range(npc_count):
        npc_id = f"benchmark_npc_{index:03d}"
        role = index % 3 if index < managed_npc_count else 3
        body = PhysicsBodyDefinition(
            npc_id, CircleShape(4.0), enabled=(role == 1),
        )
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
        elif role == 2:
            row = index // 3
            q, r = 31 - row % 5, 2 + row // 5
            behavior = BehaviorState.IDLE
            route = ()
            companion_ids.append(npc_id)
        else:
            idle_index = index - managed_npc_count
            q, r = idle_index % 18, 28 + idle_index // 18
            behavior = BehaviorState.IDLE
            route = ()
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
    # Patrol and companion movement use the runtime's logical path step here.
    # Only fleeing actors keep enabled physics bodies, isolating perception
    # work from the separate all-body overlap resolver cost.
    patrol = NPCBehaviorSystem(registry, runtime, None)
    companion_registry = CompanionRegistry()
    companions = CompanionCommandService(
        runtime, registry, companion_registry, "hero",
        physics_snapshot=None,
    )
    for npc_id in companion_ids:
        companions.enlist(npc_id)
        companions.command(npc_id, CompanionCommand.FOLLOW)
    metrics.reset()
    return metrics, patrol, avoidance, companions


def run_scenario(npc_count: int, steps: int = 4, warmup_steps: int = 2) -> dict:
    if npc_count < 1 or steps < 1 or warmup_steps < 0:
        raise ValueError("npc_count and steps must be positive; warmup_steps cannot be negative")
    if warmup_steps:
        _, warmup_patrol, warmup_avoidance, warmup_companions = _build_scenario(npc_count)
        for _ in range(warmup_steps):
            warmup_patrol.step(1.0 / 60.0)
            warmup_avoidance.step(1.0 / 60.0)
            warmup_companions.tick(1.0 / 60.0)
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
        "warmup_steps": warmup_steps,
        "step_latency_samples_seconds": step_latencies,
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
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--warmup-steps", type=int, default=2)
    parser.add_argument("--output")
    args = parser.parse_args()
    if any(count < 1 for count in args.counts):
        parser.error("all NPC counts must be positive")
    if args.repeats < 1 or args.steps < 1 or args.warmup_steps < 0:
        parser.error("--repeats and --steps must be positive; --warmup-steps cannot be negative")
    report = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "warmup_steps": args.warmup_steps,
        "measurement_note": (
            "Measures real patrol, flee and companion perception systems with opt-in counters. "
            "Each repetition uses a separate warmup world followed by a fresh measured world. "
            "For 25/50/100 NPC scenarios, the first 18 NPCs retain a fixed patrol/flee/"
            "companion mix and remaining NPCs are idle, isolating registry scan growth "
            "from changing active behavior density. Patrol/companion physics bodies are "
            "disabled and those systems use logical path movement so the separate overlap "
            "resolver does not dominate this perception benchmark. Compare revisions on "
            "the same machine and Python "
            "build; timings are observations, not hardware-independent guarantees."
        ),
        "scenarios": [],
    }
    for count in args.counts:
        samples = [
            run_scenario(count, args.steps, args.warmup_steps)
            for _ in range(args.repeats)
        ]
        latency_samples = [
            value
            for sample in samples
            for value in sample["step_latency_samples_seconds"]
        ]
        aggregate_metrics = NPCSimulationMetrics()
        for sample in samples:
            for name, amount in sample["metrics"]["counts"].items():
                aggregate_metrics.increment(name, amount)
            for name, duration in sample["metrics"]["durations_seconds"].items():
                for value in duration["samples_seconds"]:
                    aggregate_metrics.record_duration(name, value)
        report["scenarios"].append({
            "npc_count": count,
            "managed_npc_count": min(count, 18),
            "idle_npc_count": max(0, count - 18),
            "repetitions": args.repeats,
            "steps_per_repetition": args.steps,
            "warmup_steps_per_repetition": args.warmup_steps,
            "simulation_step_latency_seconds": {
                "p50": _percentile(latency_samples, 50),
                "p95": _percentile(latency_samples, 95),
                "p99": _percentile(latency_samples, 99),
                "max": max(latency_samples),
                "mean": statistics.mean(latency_samples),
            },
            "simulation_step_spikes_over_16_67ms": sum(
                value > (1.0 / 60.0) for value in latency_samples
            ),
            "metrics": aggregate_metrics.snapshot(),
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
