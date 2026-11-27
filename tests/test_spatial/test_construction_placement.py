"""Tests for deterministic construction placement validation."""
import unittest

from application.hex_map_definition import parse_hex_map
from core.domain.spatial import ConstructionPosition, HexCoord, WorldPoint
from core.domain.structures import StructureGeometryDefinition, StructurePartDefinition
from application.construction_placement import (
    ConstructionPlacementRequest,
    ConstructionPlacementSnapshot,
    ConstructionPlacementValidator,
    ConstructionPlacementService,
    PlacementFailureReason,
    check_placement_revision,
)


def make_map(valid_cells=((0, 0), (1, 0), (0, 1), (-1, 0)) , blocked=()):
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "village",
        "name": "Village",
        "geometry": {"type": "hex_axial", "orientation": "pointy_top", "coordinate_system": "axial"},
        "terrain_ids": ["grass", "rock"],
        "default_terrain": "grass",
        "valid_cells": [list(p) for p in valid_cells],
        "cell_overrides": [{"q": q, "r": r, "terrain": "rock", "blocked": True}
                           for q, r in blocked],
    })


def request(point=WorldPoint(0, 0), *, footprint=(WorldPoint(0, 0),),
            rotation=0, support=False, permission=True, map_id="village"):
    return ConstructionPlacementRequest(
        "wall.basic",
        ConstructionPosition(map_id, point, rotation_degrees=rotation),
        footprint,
        "player",
        support,
        permission,
    )


def snapshot(*, cells=((0, 0), (1, 0), (0, 1), (-1, 0)),
             blocked=(), occupied=None, supported=(), revision=4):
    return ConstructionPlacementSnapshot(
        make_map(cells, blocked),
        32,
        WorldPoint(0, 0),
        occupied or {},
        frozenset(HexCoord(*p) for p in supported),
        revision,
    )


class ConstructionPlacementTests(unittest.TestCase):
    def test_valid_preview_returns_sorted_footprint_and_snapshot_revision(self):
        result = ConstructionPlacementValidator.validate(
            request(footprint=(WorldPoint(0, 0), WorldPoint(55.4256258, 0))),
            snapshot(),
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.footprint_cells, (HexCoord(0, 0), HexCoord(1, 0)))
        self.assertEqual(result.snapshot_revision, 4)
        self.assertEqual(result.reasons, ())

    def test_request_uses_explicit_part_geometry_footprint(self):
        part = StructurePartDefinition(
            "wall.basic",
            "wall",
            StructureGeometryDefinition(
                "custom", 2.0, 0.25, 3.0,
                footprint_local_points=(WorldPoint(-40, 0), WorldPoint(40, 0)),
            ),
        )
        placement = ConstructionPlacementRequest.from_part_definition(
            part, ConstructionPosition("village", WorldPoint(0, 0)), "player",
            requires_support=False,
        )
        result = ConstructionPlacementValidator.validate(placement, snapshot())
        self.assertTrue(result.valid)
        self.assertEqual(result.footprint_cells, (HexCoord(-1, 0), HexCoord(1, 0)))

    def test_ground_part_requires_foundation_support_by_default(self):
        part = StructurePartDefinition(
            "wall.basic",
            "wall",
            StructureGeometryDefinition(
                "box", 2.0, 0.25, 3.0,
                footprint_local_points=(WorldPoint(0, 0),),
            ),
        )
        placement = ConstructionPlacementRequest.from_part_definition(
            part, ConstructionPosition("village", WorldPoint(0, 0)), "player",
        )
        self.assertTrue(placement.requires_support)

    def test_request_rejects_part_without_explicit_footprint(self):
        part = StructurePartDefinition(
            "wall.basic", "wall",
            StructureGeometryDefinition("box", 2.0, 0.25, 3.0),
        )
        with self.assertRaisesRegex(ValueError, "footprint_local_points"):
            ConstructionPlacementRequest.from_part_definition(
                part, ConstructionPosition("village", WorldPoint(0, 0)), "player",
            )

    def test_wrong_map_is_rejected(self):
        result = ConstructionPlacementValidator.validate(
            request(map_id="forest"), snapshot()
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.reasons, (PlacementFailureReason.WRONG_MAP,))

    def test_outside_world_and_blocked_terrain_are_distinct(self):
        outside = ConstructionPlacementValidator.validate(
            request(point=WorldPoint(500, 500)), snapshot()
        )
        self.assertIn(PlacementFailureReason.OUTSIDE_WORLD, outside.reasons)
        blocked = ConstructionPlacementValidator.validate(
            request(point=WorldPoint(55.42562584220407, 0)), snapshot(blocked=((1, 0),))
        )
        self.assertIn(PlacementFailureReason.BLOCKED_TERRAIN, blocked.reasons)

    def test_overlap_and_support_are_independent_reasons(self):
        result = ConstructionPlacementValidator.validate(
            request(support=True),
            snapshot(occupied={HexCoord(0, 0): "existing"}),
        )
        self.assertIn(PlacementFailureReason.OVERLAP, result.reasons)
        self.assertIn(PlacementFailureReason.UNSUPPORTED, result.reasons)

    def test_permission_denial_does_not_skip_other_validation(self):
        result = ConstructionPlacementValidator.validate(
            request(permission=False, point=WorldPoint(500, 500)), snapshot()
        )
        self.assertIn(PlacementFailureReason.PERMISSION_DENIED, result.reasons)
        self.assertIn(PlacementFailureReason.OUTSIDE_WORLD, result.reasons)

    def test_rotation_changes_footprint_deterministically(self):
        req = request(
            footprint=(WorldPoint(55.4256258, 0),),
            rotation=90,
        )
        first = ConstructionPlacementValidator.validate(req, snapshot())
        second = ConstructionPlacementValidator.validate(req, snapshot())
        self.assertEqual(first, second)


    def test_commit_revalidates_and_uses_atomic_revision_guard(self):
        class AtomicPort:
            def __init__(self, current_revision):
                self.current_revision = current_revision
                self.committed = False

            def commit_if_revision(self, expected_revision, placement_request, result):
                if self.current_revision != expected_revision:
                    return False
                self.committed = True
                self.current_revision += 1
                return True

        current = snapshot(revision=8)
        port = AtomicPort(8)
        service = ConstructionPlacementService(lambda: current, port)
        preview = service.preview(request())
        self.assertTrue(preview.valid)
        committed = service.try_commit(request())
        self.assertTrue(committed.valid)
        self.assertTrue(port.committed)

    def test_commit_port_rejects_stale_revision_without_mutation(self):
        class StalePort:
            def __init__(self):
                self.committed = False

            def commit_if_revision(self, expected_revision, placement_request, result):
                return False

        port = StalePort()
        service = ConstructionPlacementService(lambda: snapshot(revision=8), port)
        result = service.try_commit(request())
        self.assertFalse(result.valid)
        self.assertIn(PlacementFailureReason.STALE_STATE, result.reasons)
        self.assertFalse(port.committed)

    def test_stale_preview_is_rejected_and_current_revision_is_preserved(self):
        result = ConstructionPlacementValidator.validate(request(), snapshot())
        self.assertTrue(check_placement_revision(result, 4).valid)
        stale = check_placement_revision(result, 5)
        self.assertFalse(stale.valid)
        self.assertIn(PlacementFailureReason.STALE_STATE, stale.reasons)
        self.assertEqual(stale.snapshot_revision, 4)


if __name__ == "__main__":
    unittest.main()
