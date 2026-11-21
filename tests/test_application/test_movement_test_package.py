import unittest
from pathlib import Path

from application import GameApplication
from application.content_loader import load_content_package
from application.content_pack import (
    load_movement_configs,
    populate_gameplay_resources,
    populate_opening_content,
)
from application.hex_world_initializer import initialize_hex_world
from core.domain.spatial import LocalHexPosition


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "movement_test"


class TestMovementTestPackage(unittest.TestCase):
    def test_package_loads_its_map_profiles_and_placements(self):
        package = load_content_package(PACKAGE)

        self.assertEqual(package.package_id, "movement_test")
        self.assertEqual(tuple(package.hex_map_definitions), ("movement_test_arena",))
        self.assertIsNotNone(package.gameplay_placements)
        self.assertEqual(len(package.gameplay_placements.placements), 4)
        self.assertTrue(
            package.hex_map_definitions["movement_test_arena"].is_blocked(
                LocalHexPosition(0, -3)
            )
        )

        profiles = load_movement_configs(package_path=PACKAGE)
        self.assertEqual(profiles["hero"].max_speed, 96)
        self.assertEqual(profiles["test_guard"].max_speed, 96)
        self.assertEqual(profiles["test_target"].max_speed, 96)
        self.assertEqual(profiles["hero"].running_speed_multiplier, 1.5)
        self.assertEqual(profiles["hero"].stealth_speed_multiplier, 0.5)

    def test_gameplay_content_registers_actors_resources_and_spatial_placements(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(
            application, content_package_path=PACKAGE,
        )
        self.assertEqual(ids.hero_id, "hero")
        populate_gameplay_resources(service, content_package_path=PACKAGE)

        runtime = initialize_hex_world(service, content_package_path=PACKAGE)

        self.assertEqual(runtime.map_ids, ("movement_test_arena",))
        self.assertEqual(runtime.entity("hero").position.cell, LocalHexPosition(0, 0))
        self.assertEqual(runtime.entity("test_guard").kind, "npc")
        self.assertEqual(runtime.entity("test_target").kind, "npc")
        self.assertEqual(runtime.entity("test_wood_node").kind, "object")
        self.assertEqual(runtime.entity("test_iron_node").kind, "object")
        self.assertIsNotNone(service.npc_hex_binding.npc("test_guard"))
        self.assertIsNotNone(application.holder.current.resource_nodes.get("test_wood_node"))


if __name__ == "__main__":
    unittest.main()
