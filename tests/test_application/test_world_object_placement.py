import unittest
from application import WorldObjectPlacement, WorldObjectPlacementError, WorldObjectPlacementRegistry
from world import LocalMapDefinition

class TestWorldObjectPlacementRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = WorldObjectPlacementRegistry()
        self.registry.register_local_map(LocalMapDefinition("world_a", "village", 8, 6))
        self.registry.register_local_map(LocalMapDefinition("world_a", "forest", 5, 5))
        self.registry.register_local_map(LocalMapDefinition("world_b", "village", 8, 6))

    def placement(self, object_id="chest", **kwargs):
        values = dict(object_id=object_id, world_id="world_a", location_id="village", x=1, y=1)
        values.update(kwargs)
        return WorldObjectPlacement(**values)

    def test_places_and_queries_object_by_location_and_tile(self):
        item = self.registry.place(self.placement())
        self.assertEqual(self.registry.get("chest"), item)
        self.assertEqual(self.registry.for_location("world_a", "village"), (item,))
        self.assertEqual(self.registry.at("world_a", "village", 1, 1), (item,))

    def test_duplicate_object_placement_is_rejected(self):
        self.registry.place(self.placement())
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.place(self.placement(x=3))

    def test_blocking_footprints_cannot_overlap(self):
        self.registry.place(self.placement(width=2, height=2))
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.place(self.placement("barrel", x=2, y=2))

    def test_non_blocking_objects_may_share_tiles(self):
        self.registry.place(self.placement())
        self.registry.place(self.placement("decoration", blocks_movement=False))
        self.assertEqual(len(self.registry.at("world_a", "village", 1, 1)), 2)
        self.assertEqual(self.registry.blocked_tiles("world_a", "village"), frozenset({(1, 1)}))

    def test_footprint_must_fit_inside_registered_local_map(self):
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.place(self.placement(x=7, width=2))
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.place(self.placement(y=6))

    def test_move_is_atomic_when_destination_is_blocked(self):
        self.registry.place(self.placement("chest"))
        self.registry.place(self.placement("barrel", x=4, y=4))
        before = self.registry.get("chest")
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.move("chest", 4, 4)
        self.assertEqual(self.registry.get("chest"), before)

    def test_move_updates_blocked_tiles(self):
        self.registry.place(self.placement())
        self.registry.move("chest", 3, 2)
        self.assertNotIn((1, 1), self.registry.blocked_tiles("world_a", "village"))
        self.assertIn((3, 2), self.registry.blocked_tiles("world_a", "village"))

    def test_transfer_between_local_maps_is_atomic(self):
        self.registry.place(self.placement())
        moved = self.registry.transfer("chest", "forest", 2, 2)
        self.assertEqual(moved.location_id, "forest")
        with self.assertRaises(WorldObjectPlacementError):
            self.registry.transfer("chest", "missing", 0, 0)
        self.assertEqual(self.registry.get("chest"), moved)

    def test_same_coordinates_in_different_worlds_do_not_conflict(self):
        self.registry.place(self.placement())
        self.registry.place(self.placement("other", world_id="world_b"))
        self.assertEqual(len(self.registry.placements()), 2)

    def test_remove_clears_spatial_occupancy(self):
        self.registry.place(self.placement())
        self.assertEqual(self.registry.remove("chest").object_id, "chest")
        self.assertEqual(self.registry.blocked_tiles("world_a", "village"), frozenset())

    def test_registry_validation_checks_existing_placements(self):
        self.registry.place(self.placement())
        self.registry.validate()
    def test_local_map_dimensions_are_required(self):
        with self.assertRaises(TypeError):
            LocalMapDefinition("world_a", "village")


if __name__ == "__main__":
    unittest.main()
