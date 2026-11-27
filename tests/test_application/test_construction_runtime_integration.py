import unittest

from application.construction_placement import (
    ConstructionPlacementRequest,
    ConstructionPlacementValidator,
    PlacementFailureReason,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    ConstructionPosition,
    EntityPosition,
    HexCoord,
    LocalHexPosition,
    WorldPoint,
    axial_to_world_point,
)


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "forest",
        "name": "Forest",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [
            [0, 0], [1, 0], [0, 1], [-1, 1], [-1, 0], [0, -1], [1, -1],
        ],
    })


class TestConstructionRuntimeIntegration(unittest.TestCase):
    def setUp(self):
        self.runtime = HexWorldRuntime({"forest": make_map()})
        self.runtime.register_entity(
            "player",
            "player",
            EntityPosition("forest", LocalHexPosition(0, 0)),
        )
        self.target = ConstructionPosition(
            "forest",
            axial_to_world_point(HexCoord(1, 0), self.runtime.HEX_SIZE),
        )
        self.request = ConstructionPlacementRequest(
            "stone_wall",
            self.target,
            (WorldPoint(0.0, 0.0),),
            "player",
        )
        self.support = frozenset(
            position.to_hex_coord()
            for position in self.runtime.map_definition("forest").valid_cells
        )

    def preview(self):
        snapshot = self.runtime.construction_snapshot(
            "forest", supported_cells=self.support
        )
        return snapshot, ConstructionPlacementValidator.validate(
            self.request, snapshot
        )

    def test_runtime_snapshot_combines_actor_and_structure_occupancy(self):
        snapshot, result = self.preview()

        self.assertIn(HexCoord(0, 0), snapshot.occupied_cells)
        self.assertEqual(snapshot.occupied_cells[HexCoord(0, 0)], "player")
        self.assertTrue(result.valid)

        self.assertTrue(
            self.runtime.commit_if_revision(
                snapshot.state_revision, self.request, result
            )
        )
        updated = self.runtime.construction_snapshot(
            "forest", supported_cells=self.support
        )
        self.assertIn(HexCoord(1, 0), updated.occupied_cells)
        self.assertEqual(
            len(self.runtime.structure_placements("forest")), 1
        )

    def test_actor_movement_invalidates_previous_placement_revision(self):
        snapshot, result = self.preview()
        self.assertTrue(result.valid)

        moved = self.runtime.move("player", __import__(
            "core.domain.spatial", fromlist=["HexDirection"]
        ).HexDirection.EAST)
        self.assertTrue(moved.success)
        self.assertGreater(self.runtime.state_revision, snapshot.state_revision)

        self.assertFalse(
            self.runtime.commit_if_revision(
                snapshot.state_revision, self.request, result
            )
        )
        self.assertEqual(self.runtime.structure_placements(), ())

    def test_second_structure_cannot_reuse_an_existing_footprint(self):
        snapshot, result = self.preview()
        self.assertTrue(
            self.runtime.commit_if_revision(
                snapshot.state_revision, self.request, result
            )
        )

        second_snapshot = self.runtime.construction_snapshot(
            "forest", supported_cells=self.support
        )
        second_result = ConstructionPlacementValidator.validate(
            self.request, second_snapshot
        )
        self.assertFalse(second_result.valid)
        self.assertIn(PlacementFailureReason.OVERLAP, second_result.reasons)
        self.assertEqual(len(self.runtime.structure_placements()), 1)

    def test_runtime_rejects_placement_by_unregistered_actor(self):
        snapshot = self.runtime.construction_snapshot(
            "forest", supported_cells=self.support
        )
        request = ConstructionPlacementRequest(
            "stone_wall",
            self.target,
            (WorldPoint(0.0, 0.0),),
            "missing_actor",
        )
        result = ConstructionPlacementValidator.validate(request, snapshot)
        self.assertTrue(result.valid)
        self.assertFalse(
            self.runtime.commit_if_revision(
                snapshot.state_revision, request, result
            )
        )
        self.assertEqual(self.runtime.structure_placements(), ())


if __name__ == "__main__":
    unittest.main()
