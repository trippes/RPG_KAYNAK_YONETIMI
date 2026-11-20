"""Smoke tests for reproducible NPC spatial benchmark statistics."""

import unittest

from scripts.benchmark_npc_spatial_index import (
    _percentile,
    _summarize_repetitions,
    run_scenario,
)


class TestNPCSpatialBenchmark(unittest.TestCase):
    def test_small_collider_scenario_runs_and_reports_measurements(self):
        result = run_scenario(
            12,
            (0, 50, 100),
            collider_bounds=True,
            query_limit=6,
        )

        self.assertEqual(result["npc_count"], 12)
        self.assertEqual(result["broadphase_mode"], "collider_aabb")
        self.assertEqual(result["query_count"], 6)
        self.assertEqual(result["movement_updates"][-1]["updated_npcs"], 12)
        self.assertGreaterEqual(result["registration_seconds"], 0.0)
        self.assertGreater(result["retained_memory_bytes_after_registration"], 0)
        self.assertEqual(set(result["query_latency_seconds"]), {"p50", "p95", "p99"})

    def test_nearest_rank_percentile_is_deterministic(self):
        self.assertEqual(_percentile([4.0, 1.0, 3.0, 2.0], 50), 2.0)
        self.assertEqual(_percentile([4.0, 1.0, 3.0, 2.0], 95), 4.0)
        self.assertEqual(_percentile([], 95), 0.0)

    def test_repetition_summary_reports_median_and_tail(self):
        summary = _summarize_repetitions([
            {
                "registration_seconds": 1.0,
                "query_seconds": 0.1,
                "retained_memory_bytes_after_registration": 100,
            },
            {
                "registration_seconds": 3.0,
                "query_seconds": 0.3,
                "retained_memory_bytes_after_registration": 300,
            },
            {
                "registration_seconds": 2.0,
                "query_seconds": 0.2,
                "retained_memory_bytes_after_registration": 200,
            },
        ])
        self.assertEqual(summary["repetitions"], 3)
        self.assertEqual(summary["registration_seconds"]["median"], 2.0)
        self.assertEqual(summary["query_seconds"]["median"], 0.2)
        self.assertEqual(summary["retained_memory_bytes"]["median"], 200)


if __name__ == "__main__":
    unittest.main()
