import unittest

from core.domain.spatial import HexCoord, HexDirection, LocalHexPosition, WorldHexPosition


class TestWorldHexPosition(unittest.TestCase):
    def test_world_coordinate_is_immutable_hashable_and_distinct(self):
        position = WorldHexPosition(2, -3)
        self.assertEqual(position, WorldHexPosition(2, -3))
        self.assertEqual(len({position, WorldHexPosition(2, -3)}), 1)
        self.assertEqual(position.to_hex_coord(), HexCoord(2, -3))
        self.assertNotEqual(position, LocalHexPosition(2, -3))
        with self.assertRaises((AttributeError, TypeError)):
            position.q = 5

    def test_world_coordinate_rejects_bool_and_non_integer_components(self):
        for q, r in ((True, 0), (0, False), (1.5, 0), (0, "1")):
            with self.subTest(q=q, r=r), self.assertRaises(TypeError):
                WorldHexPosition(q, r)

    def test_six_neighbors_reuse_canonical_hex_direction_offsets(self):
        origin = WorldHexPosition(0, 0)
        expected = {
            HexDirection.EAST: WorldHexPosition(1, 0),
            HexDirection.NORTH_EAST: WorldHexPosition(1, -1),
            HexDirection.NORTH_WEST: WorldHexPosition(0, -1),
            HexDirection.WEST: WorldHexPosition(-1, 0),
            HexDirection.SOUTH_WEST: WorldHexPosition(-1, 1),
            HexDirection.SOUTH_EAST: WorldHexPosition(0, 1),
        }
        for direction, neighbor in expected.items():
            with self.subTest(direction=direction):
                self.assertEqual(origin.neighbor(direction), neighbor)
                self.assertEqual(neighbor.neighbor(direction.opposite), origin)

    def test_world_distance_uses_shared_hex_geometry(self):
        self.assertEqual(WorldHexPosition(0, 0).distance_to(WorldHexPosition(2, -1)), 2)
        with self.assertRaises(TypeError):
            WorldHexPosition(0, 0).distance_to(LocalHexPosition(1, 0))


if __name__ == "__main__":
    unittest.main()
