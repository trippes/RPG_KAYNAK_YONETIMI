import json
import shutil
import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_loader import load_content_package
from application.content_pack import (
    populate_gameplay_resources,
    populate_opening_content,
)
from game_ui.screens.main_screen import MainScreen


ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = ROOT / "content" / "demo_eldoria"


class TestIndependentMapContentPackage(unittest.TestCase):
    def test_new_non_32x32_map_is_discovered_playable_and_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "independent_world"
            shutil.copytree(DEMO_PACKAGE, package)

            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["package_id"] = "independent_world"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            source_path = package / "maps" / "north_mine.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["transitions"].append({
                "id": "north_mine_to_test_valley",
                "from_tiles": [[16, 31]],
                "target_map_id": "test_valley",
                "target_tiles": [[8, 0]],
                "direction": "south",
                "bidirectional": True,
            })
            source_path.write_text(
                json.dumps(source, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            new_map = {
                "schema_version": 1,
                "map_id": "test_valley",
                "name": "Bağımsız Test Vadisi",
                "description": "Yalnızca içerik dosyalarıyla eklenen test haritası.",
                "size": {"width": 16, "height": 24},
                "terrain": {"default_tile": "grass"},
                "world_position": [620, 50],
                "activities": ["travel"],
                "metadata": {"location_type": "valley"},
                "transitions": [{
                    "id": "test_valley_to_north_mine",
                    "from_tiles": [[8, 0]],
                    "target_map_id": "north_mine",
                    "target_tiles": [[16, 31]],
                    "direction": "north",
                    "bidirectional": True,
                }],
            }
            (package / "maps" / "test_valley.json").write_text(
                json.dumps(new_map, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            application = GameApplication.create_default()
            service, _ids = populate_opening_content(
                application, content_package_path=package,
            )
            populate_gameplay_resources(
                service, content_package_path=package,
            )

            world_map = application.holder.current.movement.map_for("demo_valley")
            self.assertIsNotNone(world_map.get("test_valley"))
            self.assertIn(
                "test_valley",
                tuple(item.location_id for item in world_map.neighbors("north_mine")),
            )
            self.assertTrue(
                application.holder.current.world_objects.has_local_map(
                    "demo_valley", "test_valley",
                )
            )

            actor = service.actor("hero")
            service.place_actor(actor.actor_id, "north_mine")
            service.set_actor_tile_position(actor.actor_id, 16, 31)
            actor = service.actor("hero")
            screen = MainScreen(service)
            self.assertEqual(screen._location().location_id, "north_mine")
            source_definition = screen._map_definition()
            self.assertEqual(source_definition.map_id, "north_mine")
            self.assertTrue(any(
                item.transition_id == "north_mine_to_test_valley"
                for item in source_definition.transitions
            ))
            self.assertEqual(screen._position(actor.position), (16, 31))
            self.assertTrue(screen._cross_boundary(actor, 0, 1), screen.message)
            self.assertEqual(service.actor("hero").location_id, "test_valley")
            self.assertEqual(
                (service.actor("hero").position.x, service.actor("hero").position.y),
                (8, 0),
            )
            self.assertEqual(screen._map_width(), 16)
            self.assertEqual(screen._map_height(), 24)

            save_path = package / "independent-world-save.json"
            application.save(save_path)
            application.load(save_path)

            restored_actor = application.holder.current.actors.get(actor.actor_id)
            self.assertEqual(restored_actor.location_id, "test_valley")
            self.assertEqual(
                (restored_actor.position.x, restored_actor.position.y),
                (8, 0),
            )

        # The temporary package is gone; the original package remains usable.
        self.assertEqual(len(load_content_package(DEMO_PACKAGE).map_definitions), 9)


if __name__ == "__main__":
    unittest.main()
