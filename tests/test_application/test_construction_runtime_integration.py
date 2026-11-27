import unittest

from application.construction_placement import (
    ConstructionPlacementRequest,
    ConstructionPlacementService,
    ConstructionPlacementValidator,
    PlacementFailureReason,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime, HexWorldRuntimeOwner
from core.domain.spatial import (
    ConstructionPosition,
    EntityPosition,
    HexCoord,
    HexDirection,
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
        "terrain_ids": ["grass", "water"],
        "default_terrain": "grass",
        "foundation_supporting_terrain_ids": ["grass"],
        "cell_overrides": [
            {"q": 0, "r": 1, "terrain": "water", "blocked": True},
        ],
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
            requires_support=True,
        )

    def preview(self):
        snapshot = self.runtime.construction_snapshot("forest")
        return snapshot, ConstructionPlacementValidator.validate(
            self.request, snapshot
        )

    def test_placement_service_uses_hex_runtime_as_snapshot_and_commit_owner(self):
        service = ConstructionPlacementService(
            lambda: self.runtime.construction_snapshot("forest"),
            self.runtime,
        )

        result = service.try_commit(self.request)

        self.assertTrue(result.valid)
        self.assertEqual(len(self.runtime.structure_placements("forest")), 1)
        self.assertEqual(
            self.runtime.structure_placements("forest")[0].created_by_actor_id,
            "player",
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
        updated = self.runtime.construction_snapshot("forest")
        self.assertIn(HexCoord(1, 0), updated.occupied_cells)
        self.assertEqual(
            len(self.runtime.structure_placements("forest")), 1
        )


    def test_runtime_derives_foundation_support_from_terrain_capabilities(self):
        snapshot = self.runtime.construction_snapshot("forest")

        self.assertIn(HexCoord(0, 0), snapshot.supported_cells)
        self.assertNotIn(HexCoord(0, 1), snapshot.supported_cells)

    def test_runtime_fails_closed_when_map_has_no_foundation_support_metadata(self):
        unsupported_map = parse_hex_map({
            "schema_version": 2,
            "map_id": "unsupported",
            "name": "Unsupported",
            "geometry": {
                "type": "hex_axial",
                "orientation": "pointy_top",
                "coordinate_system": "axial",
            },
            "terrain_ids": ["grass"],
            "default_terrain": "grass",
            "valid_cells": [[0, 0], [1, 0]],
        })
        runtime = HexWorldRuntime({"unsupported": unsupported_map})
        runtime.register_entity(
            "player", "player", EntityPosition("unsupported", LocalHexPosition(0, 0))
        )
        target = ConstructionPosition(
            "unsupported",
            axial_to_world_point(HexCoord(1, 0), runtime.HEX_SIZE),
        )
        request = ConstructionPlacementRequest(
            "stone_wall", target, (WorldPoint(0.0, 0.0),), "player",
            requires_support=True,
        )

        result = ConstructionPlacementValidator.validate(
            request, runtime.construction_snapshot("unsupported")
        )

        self.assertFalse(result.valid)
        self.assertIn(PlacementFailureReason.UNSUPPORTED, result.reasons)

    def test_actor_movement_invalidates_previous_placement_revision(self):
        snapshot, result = self.preview()
        self.assertTrue(result.valid)

        moved = self.runtime.move("player", HexDirection.EAST)
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

        second_snapshot = self.runtime.construction_snapshot("forest")
        second_result = ConstructionPlacementValidator.validate(
            self.request, second_snapshot
        )
        self.assertFalse(second_result.valid)
        self.assertIn(PlacementFailureReason.OVERLAP, second_result.reasons)
        self.assertEqual(len(self.runtime.structure_placements()), 1)

    def test_runtime_owner_cannot_discard_a_world_that_still_has_structures(self):
        snapshot, result = self.preview()
        self.assertTrue(
            self.runtime.commit_if_revision(
                snapshot.state_revision, self.request, result
            )
        )
        owner = HexWorldRuntimeOwner(self.runtime)
        self.runtime.remove_entity("player")

        with self.assertRaisesRegex(RuntimeError, "entities or structures"):
            owner.discard_if_empty(self.runtime)
        self.assertIs(owner.runtime, self.runtime)

    def test_runtime_rejects_placement_by_unregistered_actor(self):
        snapshot = self.runtime.construction_snapshot("forest")
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
