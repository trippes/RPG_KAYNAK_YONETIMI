import json
import math
import unittest
from pathlib import Path

from application.hex_map_definition import parse_hex_map
from application.square_grid_coverage import (
    SquareGridCellStatus,
    build_square_grid_coverage,
)
from core.domain.spatial import LocalHexPosition, SquareGridCoord


def _make_hex_map(valid_cells, *, blocked_cells=()):
    blocked = set(blocked_cells)
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "square_grid_test",
        "name": "Square grid test map",
        "description": "",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass", "water"],
        "default_terrain": "grass",
        "valid_cells": [list(position) for position in valid_cells],
        "cell_overrides": [
            {
                "q": q,
                "r": r,
                "terrain": "water",
                "blocked": True,
            }
            for q, r in sorted(blocked)
        ],
    })


class TestSquareGridHexCoverage(unittest.TestCase):
    def test_one_hex_area_is_conserved_across_square_cells(self):
        definition = _make_hex_map([(0, 0)])
        coverage = build_square_grid_coverage(definition, 8)
        measured_area = sum(cell.covered_area for cell in coverage.cells.values())
        expected_area = 3.0 * math.sqrt(3.0) * 32.0 * 32.0 / 2.0
        self.assertAlmostEqual(measured_area, expected_area, places=7)

    def test_central_square_is_fully_covered_and_walkable(self):
        coverage = build_square_grid_coverage(_make_hex_map([(0, 0)]), 8)
        cell = coverage.cells[SquareGridCoord(0, 0)]
        self.assertEqual(cell.status, SquareGridCellStatus.WALKABLE)
        self.assertTrue(cell.fully_covered)
        self.assertTrue(cell.walkable)
        self.assertAlmostEqual(cell.coverage_ratio, 1.0)

    def test_blocked_hex_overlap_prevents_square_cell_walkability(self):
        definition = _make_hex_map([(0, 0)], blocked_cells={(0, 0)})
        coverage = build_square_grid_coverage(definition, 8)
        cell = coverage.cells[SquareGridCoord(0, 0)]
        self.assertEqual(cell.status, SquareGridCellStatus.BLOCKED)
        self.assertTrue(cell.blocked)
        self.assertFalse(cell.walkable)

    def test_partial_and_outside_cells_are_not_walkable(self):
        coverage = build_square_grid_coverage(_make_hex_map([(0, 0)]), 8)
        partial = coverage.cells[SquareGridCoord(0, -4)]
        outside = coverage.cells[SquareGridCoord(-3, -4)]
        self.assertEqual(partial.status, SquareGridCellStatus.PARTIAL)
        self.assertGreater(partial.coverage_ratio, 0.0)
        self.assertLess(partial.coverage_ratio, 1.0)
        self.assertEqual(outside.status, SquareGridCellStatus.OUTSIDE)
        self.assertFalse(partial.walkable)
        self.assertFalse(outside.walkable)

    def test_one_square_can_be_covered_by_multiple_hexes(self):
        definition = _make_hex_map([(0, 0), (1, 0)])
        coverage = build_square_grid_coverage(definition, 8)
        shared = coverage.cells[SquareGridCoord(3, 0)]
        self.assertEqual(
            {item.position for item in shared.hex_cells},
            {LocalHexPosition(0, 0), LocalHexPosition(1, 0)},
        )
        self.assertTrue(shared.fully_covered)
        self.assertTrue(shared.walkable)

    def test_starting_valley_resolution_comparison_conserves_map_area(self):
        map_path = (
            Path(__file__).resolve().parents[2]
            / "content"
            / "demo_eldoria"
            / "hex_maps"
            / "starting_valley.json"
        )
        with map_path.open("r", encoding="utf-8") as stream:
            definition = parse_hex_map(json.load(stream))

        coarse = build_square_grid_coverage(definition, 16)
        fine = build_square_grid_coverage(definition, 8)
        expected_area = (
            len(definition.valid_cells)
            * 3.0
            * math.sqrt(3.0)
            * 32.0
            * 32.0
            / 2.0
        )
        for coverage in (coarse, fine):
            measured_area = sum(cell.covered_area for cell in coverage.cells.values())
            self.assertAlmostEqual(measured_area, expected_area, places=6)
            self.assertGreater(coverage.partial_count, 0)
            self.assertGreater(coverage.blocked_count, 0)
            self.assertGreater(coverage.outside_count, 0)
        self.assertGreater(len(fine.cells), len(coarse.cells))
        self.assertGreater(fine.walkable_count, coarse.walkable_count)


if __name__ == "__main__":
    unittest.main()
