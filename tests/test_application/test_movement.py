import unittest

from application import GameplayService
from core.domain.spatial import Position
from main import oyun_olustur
from world import Location, WorldMap


class TestMovement(unittest.TestCase):
    def setUp(self):
        self.game = oyun_olustur("Movement")
        self.service = GameplayService(self.game)
        world = self.game.aktif_dunya()
        self.map = WorldMap(world.world_id)
        self.map.add_location(Location("town", "Town", Position(0, 0)))
        self.map.add_location(Location("road", "Road", Position(1, 0)))
        self.map.add_location(Location("mine", "Mine", Position(2, 0)))
        self.map.connect("town", "road")
        self.map.connect("road", "mine")
        self.service.register_world_map(self.map)
        self.service.register_actor("hero", "player")
        self.service.place_actor("hero", "town")

    def test_actor_position_and_neighbor_route(self):
        movement = self.service.move_actor("hero", "mine")
        self.assertEqual(movement.path, ("town", "road", "mine"))
        self.assertEqual(self.service.actor("hero").location_id, "town")
        self.assertEqual(self.service.actor("hero").position, Position(0, 0))

        self.service.advance_by(1)
        self.assertEqual(self.service.actor("hero").location_id, "town")
        self.service.advance_by(1)
        actor = self.service.actor("hero")
        self.assertEqual(actor.location_id, "mine")
        self.assertEqual(actor.position, Position(2, 0))
        self.assertEqual(self.service.movement(movement.action_id).state, "completed")

    def test_unreachable_location_is_rejected(self):
        self.map.add_location(Location("island", "Island"))
        with self.assertRaises(ValueError):
            self.service.move_actor("hero", "island")


if __name__ == "__main__":
    unittest.main()
