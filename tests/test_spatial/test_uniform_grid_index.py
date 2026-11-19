"""Tests for the native map-scoped continuous spatial index."""

import unittest

from core.domain.spatial import AABB, UniformGridIndex, WorldPoint


class UniformGridIndexTests(unittest.TestCase):
    def test_query_returns_only_intersecting_entries_in_stable_order(self):
        index = UniformGridIndex(cell_size=10)
        index.insert("b", "forest", AABB(1, 1, 2, 2))
        index.insert("a", "forest", AABB(3, 3, 4, 4))
        index.insert("other-map", "cave", AABB(1, 1, 2, 2))

        self.assertEqual(index.query("forest", AABB(0, 0, 5, 5)), ("a", "b"))
        self.assertEqual(index.query("cave", AABB(0, 0, 5, 5)), ("other-map",))
        self.assertEqual(index.query("forest", AABB(20, 20, 30, 30)), ())

    def test_update_moves_entry_between_buckets_and_maps(self):
        index = UniformGridIndex(cell_size=8)
        index.insert("hero", "forest", AABB.at_point(WorldPoint(1, 1)))
        index.update("hero", "cave", AABB.at_point(WorldPoint(40, 40)))

        self.assertEqual(index.query("forest", AABB(0, 0, 8, 8)), ())
        self.assertEqual(index.query("cave", AABB(39, 39, 41, 41)), ("hero",))

    def test_failed_update_keeps_previous_entry(self):
        index = UniformGridIndex(cell_size=8)
        index.insert("hero", "forest", AABB(1, 1, 2, 2))
        with self.assertRaises(ValueError):
            index.update("hero", "", AABB(3, 3, 4, 4))
        self.assertEqual(index.query("forest", AABB(0, 0, 5, 5)), ("hero",))

    def test_duplicate_and_missing_ids_are_rejected(self):
        index = UniformGridIndex()
        bounds = AABB(0, 0, 1, 1)
        index.insert("hero", "forest", bounds)
        with self.assertRaises(ValueError):
            index.insert("hero", "forest", bounds)
        with self.assertRaises(KeyError):
            index.remove("missing")
        with self.assertRaises(KeyError):
            index.update("missing", "forest", bounds)

    def test_aabb_rejects_invalid_bounds_and_inclusive_edge_intersection(self):
        with self.assertRaises(ValueError):
            AABB(2, 0, 1, 1)
        self.assertTrue(AABB(0, 0, 1, 1).intersects(AABB(1, 1, 2, 2)))


if __name__ == "__main__":
    unittest.main()
