import unittest

from application.hex_map_definition import parse_hex_map
from application.hex_occupancy import HexOccupant, HexOccupancyRegistry
from application.hex_pathfinding import HexPathfinder
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition, MovementFailureReason, MovementProfile, WorldHexPosition
from application.world_map_definition import WorldMapDefinition, WorldMapPlacement


def make_world_map():
    return WorldMapDefinition(
        1, "test_world", "Test World",
        (
            WorldMapPlacement("a", WorldHexPosition(0, 0)),
            WorldMapPlacement("b", WorldHexPosition(1, 0)),
        ),
        {},
    )


def make_map(map_id="forest", cells=None, overrides=None, transitions=None):
    return parse_hex_map({
        "schema_version": 2,
        "map_id": map_id,
        "name": map_id,
        "geometry": {"type": "hex_axial", "orientation": "pointy_top", "coordinate_system": "axial"},
        "terrain_ids": ["grass", "water"],
        "default_terrain": "grass",
        "valid_cells": cells or [[0, 0], [1, 0], [1, -1], [2, -1], [0, -1], [-1, 0], [-1, 1], [0, 1], [2, 0]],
        "cell_overrides": overrides or [],
        "transitions": transitions or [],
    })


class TestHexPathfinding(unittest.TestCase):
    def test_finds_shortest_path_around_blocked_cell(self):
        definition = make_map(overrides=[{"q": 1, "r": 0, "blocked": True}])
        path = HexPathfinder.find_path(definition, LocalHexPosition(0, 0), LocalHexPosition(2, 0))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], LocalHexPosition(0, 0))
        self.assertEqual(path[-1], LocalHexPosition(2, 0))
        self.assertNotIn(LocalHexPosition(1, 0), path)
        self.assertEqual(len(path) - 1, 3)

    def test_respects_mask_and_profile(self):
        definition = make_map(cells=[[0, 0], [1, 0], [2, 0]], overrides=[{"q": 1, "r": 0, "terrain": "water"}])
        self.assertIsNone(HexPathfinder.find_path(definition, LocalHexPosition(0, 0), LocalHexPosition(2, 0), MovementProfile(allowed_terrain_ids={"grass"})))

    def test_occupied_cells_are_excluded(self):
        definition = make_map(cells=[[0, 0], [1, 0], [1, -1], [2, -1], [0, -1], [2, 0]])
        path = HexPathfinder.find_path(definition, LocalHexPosition(0, 0), LocalHexPosition(2, 0), blocked_cells={LocalHexPosition(1, 0)})
        self.assertNotIn(LocalHexPosition(1, 0), path)

    def test_invalid_endpoints_return_no_path(self):
        definition = make_map(cells=[[0, 0], [1, 0]])
        self.assertIsNone(HexPathfinder.find_path(definition, LocalHexPosition(0, 0), LocalHexPosition(8, 8)))


class TestHexOccupancy(unittest.TestCase):
    def test_distinguishes_movement_blocking_from_occupancy_blocking(self):
        registry = HexOccupancyRegistry()
        position = EntityPosition("forest", LocalHexPosition(0, 0))
        registry.add(HexOccupant("soft", position, blocks_movement=False, blocks_occupancy=True))
        self.assertFalse(registry.is_movement_blocked(position))
        self.assertTrue(registry.is_occupied(position))
        registry.remove("soft")
        registry.add(HexOccupant("wall", position, blocks_movement=True, blocks_occupancy=False))
        self.assertTrue(registry.is_movement_blocked(position))
        self.assertFalse(registry.is_occupied(position))

    def test_rejects_duplicate_occupancy_and_keeps_failed_move_atomic(self):
        registry = HexOccupancyRegistry()
        first = EntityPosition("forest", LocalHexPosition(0, 0))
        second = EntityPosition("forest", LocalHexPosition(1, 0))
        registry.add(HexOccupant("a", first))
        registry.add(HexOccupant("b", second))
        with self.assertRaises(ValueError):
            registry.move("a", second)
        self.assertEqual(registry.get("a").position, first)


class TestHexWorldRuntime(unittest.TestCase):
    def setUp(self):
        self.map = make_map()
        self.runtime = HexWorldRuntime({"forest": self.map})
        self.runtime.register_entity("player", "player", EntityPosition("forest", LocalHexPosition(0, 0)))
        self.runtime.register_entity("npc", "npc", EntityPosition("forest", LocalHexPosition(0, 1)))

    def test_player_moves_in_all_six_axial_directions(self):
        for direction in HexDirection:
            runtime = HexWorldRuntime({"forest": self.map})
            runtime.register_entity("player", "player", EntityPosition("forest", LocalHexPosition(0, 0)))
            self.assertTrue(runtime.move("player", direction).success, direction.name)

    def test_player_movement_rejects_invalid_and_blocked_cells(self):
        blocked = make_map(overrides=[{"q": 0, "r": -1, "blocked": True}])
        runtime = HexWorldRuntime({"forest": blocked})
        runtime.register_entity("player", "player", EntityPosition("forest", LocalHexPosition(0, 0)))
        result = runtime.move("player", HexDirection.NORTH_WEST)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.BLOCKED_CELL)

    def test_collision_failure_does_not_change_either_entity(self):
        before = self.runtime.entity("player").position
        result = self.runtime.move("player", HexDirection.SOUTH_EAST)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.OCCUPIED_CELL)
        self.assertEqual(self.runtime.entity("player").position, before)

    def test_inactive_entity_cannot_move(self):
        self.runtime.set_active("player", False)
        result = self.runtime.move("player", HexDirection.EAST)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.MOVEMENT_NOT_ALLOWED)

    def test_path_movement_uses_next_step_and_stays_in_mask(self):
        path = self.runtime.path_to("player", LocalHexPosition(2, 0))
        self.assertIsNotNone(path)
        result = self.runtime.move_toward("player", LocalHexPosition(2, 0))
        self.assertTrue(result.success)
        self.assertEqual(self.runtime.entity("player").position.cell, path[1])

    def test_npc_can_approach_avoid_and_patrol(self):
        self.runtime.move_toward("npc", LocalHexPosition(2, 0))
        self.assertNotEqual(self.runtime.entity("npc").position.cell, LocalHexPosition(0, 1))
        away = self.runtime.move_away("npc", LocalHexPosition(2, 0))
        self.assertTrue(away.success)
        patrol = self.runtime.patrol("npc", [LocalHexPosition(0, 1), LocalHexPosition(1, 0)])
        self.assertTrue(patrol.success)

    def test_movable_object_requires_explicit_movement_profile(self):
        runtime = HexWorldRuntime({"forest": self.map})
        runtime.register_entity("crate", "object", EntityPosition("forest", LocalHexPosition(0, 0)))
        self.assertFalse(runtime.move("crate", HexDirection.EAST).success)
        movable = HexWorldRuntime({"forest": self.map})
        movable.register_entity("crate", "object", EntityPosition("forest", LocalHexPosition(0, 0)), MovementProfile())
        self.assertTrue(movable.move("crate", HexDirection.EAST).success)

    def test_ignores_occupancy_profile_can_overlap_and_path_through_occupants(self):
        runtime = HexWorldRuntime({"forest": self.map})
        runtime.register_entity("guard", "npc", EntityPosition("forest", LocalHexPosition(1, 0)))
        runtime.register_entity(
            "wraith", "npc", EntityPosition("forest", LocalHexPosition(0, 0)),
            MovementProfile(ignores_occupancy=True),
        )
        path = runtime.path_to("wraith", LocalHexPosition(1, 0))
        self.assertEqual(path, (LocalHexPosition(0, 0), LocalHexPosition(1, 0)))
        self.assertTrue(runtime.move("wraith", HexDirection.EAST).success)
        self.assertEqual(runtime.entity("wraith").position.cell, LocalHexPosition(1, 0))

    def test_transition_preserves_position_when_inactive_or_unavailable(self):
        map_a = make_map("a", transitions=[{
            "id": "closed", "source_cells": [[0, 0]], "exit_direction": "east",
            "target_map_id": "b", "target_entry_direction": "west",
            "target_cells": [[0, 0]], "active": False, "traversal_mode": "one_way",
        }])
        runtime = HexWorldRuntime({"a": map_a})
        runtime.register_entity("player", "player", EntityPosition("a", LocalHexPosition(0, 0)))
        result = runtime.transition("player", "closed")
        self.assertFalse(result.success)
        self.assertEqual(runtime.entity("player").position, EntityPosition("a", LocalHexPosition(0, 0)))

    def test_transition_failure_keeps_source_position_when_all_entries_are_blocked(self):
        map_a = make_map("a", transitions=[{
            "id": "blocked-exit", "source_cells": [[0, 0]], "exit_direction": "east",
            "target_map_id": "b", "target_entry_direction": "west",
            "target_cells": [[0, 0]], "active": True, "traversal_mode": "one_way",
        }])
        map_b = make_map("b")
        runtime = HexWorldRuntime({"a": map_a, "b": map_b}, world_map_definition=make_world_map())
        source = EntityPosition("a", LocalHexPosition(0, 0))
        runtime.register_entity("player", "player", source)
        runtime.register_entity("blocker", "npc", EntityPosition("b", LocalHexPosition(0, 0)))
        result = runtime.transition("player", "blocked-exit")
        self.assertFalse(result.success)
        self.assertEqual(runtime.entity("player").position, source)

    def test_transition_moves_entity_to_first_available_target_cell(self):
        map_a = make_map("a", transitions=[{
            "id": "open", "source_cells": [[0, 0]], "exit_direction": "east",
            "target_map_id": "b", "target_entry_direction": "west",
            "target_cells": [[0, 0], [1, 0]], "active": True, "traversal_mode": "one_way",
        }])
        map_b = make_map("b")
        runtime = HexWorldRuntime({"a": map_a, "b": map_b}, world_map_definition=make_world_map())
        runtime.register_entity("player", "player", EntityPosition("a", LocalHexPosition(0, 0)))
        runtime.register_entity("guard", "npc", EntityPosition("b", LocalHexPosition(0, 0)))
        result = runtime.transition("player", "open")
        self.assertTrue(result.success)
        self.assertEqual(result.position, EntityPosition("b", LocalHexPosition(1, 0)))


if __name__ == "__main__":
    unittest.main()
