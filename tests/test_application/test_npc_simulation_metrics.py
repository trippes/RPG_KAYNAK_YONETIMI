"""Tests for opt-in NPC simulation metrics."""
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from application.npc_simulation_metrics import NPCSimulationMetrics
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile


def test_metrics_snapshot_reports_counts_and_nearest_rank_percentiles():
    metrics = NPCSimulationMetrics()
    metrics.increment("path_queries", 2)
    metrics.record_duration("npc_patrol", 0.01)
    metrics.record_duration("npc_patrol", 0.03)

    snapshot = metrics.snapshot()

    assert snapshot["counts"] == {"path_queries": 2}
    assert snapshot["durations_seconds"]["npc_patrol"]["samples"] == 2
    assert snapshot["durations_seconds"]["npc_patrol"]["p50"] == 0.01
    assert snapshot["durations_seconds"]["npc_patrol"]["p95"] == 0.03


def test_metrics_reset_clears_counters_and_duration_samples():
    metrics = NPCSimulationMetrics()
    metrics.increment("spatial_queries")
    metrics.record_duration("npc_avoidance", 0.02)

    metrics.reset()

    assert metrics.snapshot() == {"counts": {}, "durations_seconds": {}}


def test_runtime_records_validation_path_and_spatial_query_counts():
    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "metrics_field",
        "name": "Metrics Field",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0]],
        "cell_overrides": [],
        "transitions": [],
    })
    metrics = NPCSimulationMetrics()
    runtime = HexWorldRuntime({"metrics_field": definition}, metrics=metrics)
    runtime.register_entity(
        "guard",
        "npc",
        EntityPosition("metrics_field", LocalHexPosition(0, 0)),
        MovementProfile(),
        local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    metrics.reset()

    runtime.entity("guard")
    runtime.path_to("guard", LocalHexPosition(1, 0))
    candidates = runtime.query_spatial_candidates(
        "metrics_field", AABB(-8, -8, 8, 8),
    )

    counts = metrics.snapshot()["counts"]
    assert candidates == ("guard",)
    assert counts["runtime_entity_validation_queries"] == 2
    assert counts["runtime_path_queries"] == 1
    assert counts["runtime_spatial_queries"] == 1
    assert counts["runtime_spatial_candidates"] == 1
