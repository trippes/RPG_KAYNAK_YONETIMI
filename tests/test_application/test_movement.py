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

    def test_tile_position_uses_registered_local_map_dimensions(self):
        from application import GameApplication
        from application.actor_system import WorldActor
        from world import LocalMapDefinition, Location, WorldMap

        application = GameApplication.create_default()
        bundle = application.holder.current
        bundle.session.worlds.create("Dynamic", world_id="dynamic_world")
        world_map = WorldMap("dynamic_world")
        world_map.add_location(Location(
            "small_map", "Small Map", (0, 0), "", "test", (), (),
        ))
        bundle.movement.register_map(world_map)
        bundle.world_objects.register_local_map(
            LocalMapDefinition("dynamic_world", "small_map", 16, 24)
        )
        bundle.actors.add(WorldActor(
            "dynamic_hero", "dynamic_world", "player", True,
            location_id="small_map",
        ))

        bundle.movement.set_tile_position("dynamic_hero", 15, 23)
        self.assertEqual(
            (bundle.actors.get("dynamic_hero").position.x,
             bundle.actors.get("dynamic_hero").position.y),
            (15, 23),
        )
        with self.assertRaisesRegex(ValueError, "16x24"):
            bundle.movement.set_tile_position("dynamic_hero", 16, 23)


if __name__ == "__main__":
    unittest.main()
