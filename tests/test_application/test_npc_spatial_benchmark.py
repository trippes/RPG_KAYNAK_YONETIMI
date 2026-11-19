"""Smoke tests for the reproducible NPC spatial benchmark."""

import unittest

from scripts.benchmark_npc_spatial_index import run_scenario


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


if __name__ == "__main__":
    unittest.main()
