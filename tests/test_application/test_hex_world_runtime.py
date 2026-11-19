import unittest
from application.hex_map_definition import parse_hex_map
from application.hex_occupancy import HexOccupant, HexOccupancyRegistry
from application.hex_pathfinding import HexPathfinder
from application.hex_world_runtime import HexWorldRuntime, HexWorldRuntimeOwner
from core.domain.spatial import (
    AABB,
    ContinuousEntityPosition,
    EntityPosition,
    HexCoord,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    WorldHexPosition,
    WorldPoint,
    axial_to_world_point,
)
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
        self.assertIn(LocalHexPosition(0, 0), registry.blocked_cells("forest"))
        registry.remove("soft")
        registry.add(HexOccupant("wall", position, blocks_movement=True, blocks_occupancy=False))
        self.assertTrue(registry.is_movement_blocked(position))
        self.assertFalse(registry.is_occupied(position))

    def test_non_blocking_occupants_can_overlap_blocking_entities_in_either_order(self):
        position = EntityPosition("forest", LocalHexPosition(0, 0))
        for first, second in (
            (
                HexOccupant("resource", position, False, False, "object"),
                HexOccupant("hero", position),
            ),
            (
                HexOccupant("hero", position),
                HexOccupant("resource", position, False, False, "object"),
            ),
        ):
            registry = HexOccupancyRegistry()
            registry.add(first)
            registry.add(second)
            self.assertEqual(len(registry.at(position)), 2)
            self.assertTrue(registry.is_occupied(position))
            self.assertTrue(registry.is_movement_blocked(position))

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

    def test_runtime_spatial_index_tracks_continuous_actor_positions(self):
        initial = self.runtime.continuous_position("player").point
        self.assertEqual(
            self.runtime.query_spatial_candidates(
                "forest", AABB.around_point(initial, 2.0)
            ),
            ("player",),
        )

        updated = WorldPoint(4.0, 5.0)
        self.runtime.set_continuous_position("player", updated)
        self.assertEqual(
            self.runtime.query_spatial_candidates(
                "forest", AABB.around_point(updated, 1.0)
            ),
            ("player",),
        )
        self.assertEqual(
            self.runtime.query_spatial_candidates(
                "other-map", AABB.around_point(updated, 1.0)
            ),
            (),
        )

    def test_runtime_keeps_local_collider_bounds_through_position_updates(self):
        self.runtime.register_entity(
            "bounded_npc", "npc", EntityPosition("forest", LocalHexPosition(2, 0)),
            local_spatial_bounds=AABB(-4.0, -4.0, 4.0, 4.0),
        )
        initial = self.runtime.continuous_position("bounded_npc").point
        inside = AABB.around_point(WorldPoint(initial.x + 3.5, initial.y), 0.1)
        outside = AABB.around_point(WorldPoint(initial.x + 4.5, initial.y), 0.1)
        self.assertIn("bounded_npc", self.runtime.query_spatial_candidates("forest", inside))
        self.assertNotIn("bounded_npc", self.runtime.query_spatial_candidates("forest", outside))
        moved = WorldPoint(initial.x + 1.0, initial.y + 1.0)
        self.assertTrue(self.runtime.set_continuous_position("bounded_npc", moved).success)
        moved_inside = AABB.around_point(WorldPoint(moved.x + 3.5, moved.y), 0.1)
        moved_outside = AABB.around_point(WorldPoint(moved.x + 4.5, moved.y), 0.1)
        self.assertIn("bounded_npc", self.runtime.query_spatial_candidates("forest", moved_inside))
        self.assertNotIn("bounded_npc", self.runtime.query_spatial_candidates("forest", moved_outside))

    def test_runtime_registers_continuous_position_at_cell_center(self):
        position = self.runtime.continuous_position("player")
        expected = axial_to_world_point(HexCoord(0, 0), self.runtime.HEX_SIZE)
        self.assertEqual(position, ContinuousEntityPosition("forest", expected))
        self.assertEqual(self.runtime.entity("player").continuous_position, position)

    def test_continuous_motion_updates_subcell_position_and_derived_occupancy(self):
        within_cell = self.runtime.set_continuous_position("player", WorldPoint(4.0, 5.0))
        self.assertTrue(within_cell.success)
        self.assertEqual(self.runtime.entity("player").position.cell, LocalHexPosition(0, 0))
        self.assertEqual(self.runtime.continuous_position("player").point, WorldPoint(4.0, 5.0))

        next_center = axial_to_world_point(HexCoord(1, 0), self.runtime.HEX_SIZE)
        across_cell = self.runtime.set_continuous_position("player", next_center)
        self.assertTrue(across_cell.success)
        self.assertEqual(self.runtime.entity("player").position.cell, LocalHexPosition(1, 0))
        self.assertEqual(
            self.runtime.occupancy.get("player").position,
            self.runtime.entity("player").position,
        )
        self.assertEqual(self.runtime.continuous_position("player").point, next_center)

    def test_continuous_motion_rejects_occupied_cell_without_partial_update(self):
        before = self.runtime.continuous_position("player")
        target = axial_to_world_point(HexCoord(0, 1), self.runtime.HEX_SIZE)
        result = self.runtime.set_continuous_position("player", target)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.OCCUPIED_CELL)
        self.assertEqual(self.runtime.continuous_position("player"), before)
        self.assertEqual(self.runtime.entity("player").position.cell, LocalHexPosition(0, 0))

    def test_continuous_motion_rejects_out_of_mask_position(self):
        before = self.runtime.continuous_position("player")
        result = self.runtime.set_continuous_position("player", WorldPoint(10000.0, 10000.0))
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.INVALID_TARGET)
        self.assertEqual(self.runtime.continuous_position("player"), before)

    def test_entity_position_is_derived_only_from_occupancy(self):
        stored_state = self.runtime._entities["player"]
        self.assertFalse(hasattr(stored_state, "position"))

        before = self.runtime.entity("player")
        self.assertEqual(
            before.position,
            self.runtime.occupancy.get("player").position,
        )

        result = self.runtime.move("player", HexDirection.EAST)
        self.assertTrue(result.success)
        current = self.runtime.entity("player")
        occupant = self.runtime.occupancy.get("player")
        self.assertEqual(current.position, occupant.position)
        self.assertEqual(current.position, result.position)

    def test_invalid_entity_registration_does_not_leave_occupancy(self):
        position = EntityPosition("forest", LocalHexPosition(2, 0))

        with self.assertRaises(ValueError):
            self.runtime.register_entity("invalid-kind", "merchant", position)
        self.assertIsNone(self.runtime.occupancy.get("invalid-kind"))

        with self.assertRaises(TypeError):
            self.runtime.register_entity(
                "invalid-active", "npc", position, active=1
            )
        self.assertIsNone(self.runtime.occupancy.get("invalid-active"))

    def test_entity_view_detects_missing_authoritative_occupancy(self):
        self.runtime.occupancy.remove("player")
        with self.assertRaisesRegex(
            RuntimeError, "authoritative occupancy record"
        ):
            self.runtime.entity("player")

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

    def test_path_movement_preserves_movement_not_allowed_failure(self):
        self.runtime.set_active("player", False)
        before = self.runtime.entity("player").position
        result = self.runtime.move_toward("player", LocalHexPosition(2, 0))
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.MOVEMENT_NOT_ALLOWED)
        self.assertEqual(self.runtime.entity("player").position, before)

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

    def test_reciprocal_runtime_map_transitions_use_isolated_definitions(self):
        map_a = make_map("a", cells=[[8, 0], [-8, 0]], transitions=[{
            "id": "a_to_b", "source_cells": [[8, 0]], "exit_direction": "east",
            "target_map_id": "b", "target_entry_direction": "west",
            "target_cells": [[-8, 0]], "active": True, "traversal_mode": "bidirectional",
        }])
        map_b = make_map("b", cells=[[-8, 0], [8, 0]], transitions=[{
            "id": "b_to_a", "source_cells": [[-8, 0]], "exit_direction": "west",
            "target_map_id": "a", "target_entry_direction": "east",
            "target_cells": [[8, 0]], "active": True, "traversal_mode": "bidirectional",
        }])
        runtime = HexWorldRuntime({"a": map_a, "b": map_b}, world_map_definition=make_world_map())
        runtime.register_entity("hero", "player", EntityPosition("a", LocalHexPosition(8, 0)))
        outbound = runtime.transition("hero", "a_to_b")
        self.assertTrue(outbound.success)
        self.assertEqual(outbound.position, EntityPosition("b", LocalHexPosition(-8, 0)))
        self.assertEqual(runtime.occupancy.get("hero").position, outbound.position)
        inbound = runtime.transition("hero", "b_to_a")
        self.assertTrue(inbound.success)
        self.assertEqual(inbound.position, EntityPosition("a", LocalHexPosition(8, 0)))
        self.assertEqual(runtime.occupancy.get("hero").position, inbound.position)

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

    def test_transition_rejects_wrong_source_cell_and_missing_target_map(self):
        map_a = make_map("a", transitions=[{
            "id": "exit", "source_cells": [[0, 0]], "exit_direction": "east",
            "target_map_id": "missing_map", "target_entry_direction": "west",
            "target_cells": [[0, 0]], "active": True, "traversal_mode": "one_way",
        }])
        wrong_source_runtime = HexWorldRuntime({"a": map_a})
        wrong_source = EntityPosition("a", LocalHexPosition(1, 0))
        wrong_source_runtime.register_entity("hero", "player", wrong_source)
        wrong_source_result = wrong_source_runtime.transition("hero", "exit")
        self.assertFalse(wrong_source_result.success)
        self.assertEqual(wrong_source_result.reason, MovementFailureReason.INVALID_TRANSITION)
        self.assertEqual(wrong_source_runtime.entity("hero").position, wrong_source)

        missing_target_runtime = HexWorldRuntime({"a": map_a})
        source = EntityPosition("a", LocalHexPosition(0, 0))
        missing_target_runtime.register_entity("hero", "player", source)
        missing_target_result = missing_target_runtime.transition("hero", "exit")
        self.assertFalse(missing_target_result.success)
        self.assertEqual(missing_target_result.reason, MovementFailureReason.INVALID_TRANSITION)
        self.assertEqual(missing_target_runtime.entity("hero").position, source)

    def test_patrol_route_cannot_leave_the_local_map_mask(self):
        with self.assertRaises(ValueError):
            self.runtime.patrol("npc", [LocalHexPosition(99, 99)])

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


class TestHexWorldRuntimeOwner(unittest.TestCase):
    def test_discard_if_empty_releases_only_the_owned_runtime(self):
        owner = HexWorldRuntimeOwner()
        runtime = owner.get_or_create(
            lambda: HexWorldRuntime({"forest": make_map("forest")})
        )

        self.assertTrue(owner.discard_if_empty(runtime))
        self.assertIsNone(owner.runtime)

    def test_discard_if_empty_rejects_runtime_with_spatial_entities(self):
        owner = HexWorldRuntimeOwner()
        runtime = owner.get_or_create(
            lambda: HexWorldRuntime({"forest": make_map("forest")})
        )
        runtime.register_entity(
            "hero",
            "player",
            EntityPosition("forest", LocalHexPosition(0, 0)),
        )

        with self.assertRaisesRegex(RuntimeError, "still has entities"):
            owner.discard_if_empty(runtime)
        self.assertIs(owner.runtime, runtime)



if __name__ == "__main__":
    unittest.main()
