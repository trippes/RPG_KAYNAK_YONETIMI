import unittest

from application.hex_map_definition import parse_hex_map
from application.square_grid_cache import (
    SquareGridChunkCache,
    SquareGridChunkCoord,
    square_grid_geometry_fingerprint,
)
from application.square_grid_coverage import build_square_grid_coverage
from core.domain.spatial import WorldPoint


def _make_map(*, blocked=False):
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "cache_test_map",
        "name": "Cache test map",
        "description": "",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass", "water"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [-1, 0], [0, 1]],
        "cell_overrides": (
            [{"q": 0, "r": 0, "terrain": "water", "blocked": True}]
            if blocked else []
        ),
    })


class TestSquareGridChunkCache(unittest.TestCase):
    def test_chunks_reconstruct_full_coverage_exactly(self):
        definition = _make_map()
        full = build_square_grid_coverage(definition, 8)
        cache = SquareGridChunkCache(chunk_size=8, max_chunks=64)
        reconstructed = {}
        for chunk_coord in cache.chunk_coords(definition, cell_size=8):
            chunk = cache.get_chunk(
                definition, chunk_coord, cell_size=8,
            )
            for coord, cell in chunk.cells.items():
                self.assertNotIn(coord, reconstructed)
                reconstructed[coord] = cell
        self.assertEqual(reconstructed, dict(full.cells))


    def test_get_coverage_map_reconstructs_full_map_through_chunk_cache(self):
        definition = _make_map()
        expected = build_square_grid_coverage(definition, 8)
        cache = SquareGridChunkCache(chunk_size=8, max_chunks=64)

        actual = cache.get_coverage_map(definition, cell_size=8)

        self.assertEqual(actual, expected)
        self.assertEqual(dict(actual.cells), dict(expected.cells))
        self.assertGreater(cache.stats.misses, 0)

    def test_get_coverage_map_preserves_non_default_geometry_origins(self):
        definition = _make_map()
        grid_origin = WorldPoint(12.0, -7.0)
        hex_origin = WorldPoint(100.0, 45.0)
        cache = SquareGridChunkCache(chunk_size=8, max_chunks=64)

        actual = cache.get_coverage_map(
            definition,
            cell_size=8,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )
        expected = build_square_grid_coverage(
            definition,
            8,
            grid_origin=grid_origin,
            hex_origin=hex_origin,
        )

        self.assertEqual(actual, expected)
        self.assertEqual(actual.grid_origin, grid_origin)
        self.assertEqual(actual.hex_origin, hex_origin)

    def test_repeated_chunk_request_is_a_cache_hit_and_returns_same_value(self):
        definition = _make_map()
        cache = SquareGridChunkCache(chunk_size=8, max_chunks=8)
        coord = cache.chunk_coords(definition, cell_size=8)[0]
        first = cache.get_chunk(definition, coord, cell_size=8)
        second = cache.get_chunk(definition, coord, cell_size=8)
        self.assertIs(first, second)
        self.assertEqual(cache.stats.hits, 1)
        self.assertEqual(cache.stats.misses, 1)
        self.assertEqual(cache.stats.entries, 1)

    def test_geometry_change_invalidates_by_content_fingerprint(self):
        original = _make_map()
        changed = _make_map(blocked=True)
        original_fingerprint = square_grid_geometry_fingerprint(
            original, cell_size=8,
        )
        changed_fingerprint = square_grid_geometry_fingerprint(
            changed, cell_size=8,
        )
        self.assertNotEqual(original_fingerprint, changed_fingerprint)

        cache = SquareGridChunkCache(chunk_size=8, max_chunks=8)
        coord = cache.chunk_coords(original, cell_size=8)[0]
        first = cache.get_chunk(original, coord, cell_size=8)
        second = cache.get_chunk(changed, coord, cell_size=8)
        self.assertIsNot(first, second)
        self.assertEqual(cache.stats.misses, 2)
        self.assertEqual(cache.stats.entries, 2)

    def test_fingerprint_is_independent_of_set_iteration_order(self):
        first = _make_map()
        second = _make_map()
        self.assertEqual(
            square_grid_geometry_fingerprint(first, cell_size=16),
            square_grid_geometry_fingerprint(second, cell_size=16),
        )

    def test_lru_evicts_oldest_chunk_at_capacity(self):
        definition = _make_map()
        cache = SquareGridChunkCache(chunk_size=4, max_chunks=1)
        coords = cache.chunk_coords(definition, cell_size=8)
        self.assertGreaterEqual(len(coords), 2)
        cache.get_chunk(definition, coords[0], cell_size=8)
        cache.get_chunk(definition, coords[1], cell_size=8)
        self.assertEqual(cache.stats.entries, 1)
        self.assertEqual(cache.stats.evictions, 1)
        cache.get_chunk(definition, coords[0], cell_size=8)
        self.assertEqual(cache.stats.misses, 3)

    def test_negative_grid_coordinates_use_floor_division_chunking(self):
        definition = _make_map()
        cache = SquareGridChunkCache(chunk_size=8, max_chunks=32)
        coords = cache.chunk_coords(definition, cell_size=8)
        self.assertTrue(any(coord.x < 0 for coord in coords))
        negative_chunk = next(coord for coord in coords if coord.x < 0)
        chunk = cache.get_chunk(definition, negative_chunk, cell_size=8)
        self.assertTrue(all(cell_coord.x < 0 for cell_coord in chunk.cells))

    def test_invalid_chunk_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            SquareGridChunkCache(chunk_size=0)
        with self.assertRaises(ValueError):
            SquareGridChunkCache(max_chunks=0)
        with self.assertRaises(TypeError):
            SquareGridChunkCoord(True, 0)


if __name__ == "__main__":
    unittest.main()
