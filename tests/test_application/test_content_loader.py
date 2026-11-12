import json
import tempfile
import unittest
from pathlib import Path

from core.domain.spatial import WorldHexPosition
from application.content_loader import (
    ContentPackageError,
    _load_hex_maps,
    load_content_package,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = PROJECT_ROOT / "content" / "demo_eldoria"


class TestContentPackageLoader(unittest.TestCase):
    def test_demo_package_loads_its_starter_definition(self):
        package = load_content_package(DEMO_PACKAGE)

        self.assertEqual(package.package_id, "demo_eldoria")
        self.assertEqual(package.package_version, "0.6.0")
        self.assertIn("starter", package.files)
        self.assertIn("npcs", package.files)
        self.assertIn("quests", package.files)
        self.assertIn("resources", package.files)
        self.assertIn("characters", package.files)
        self.assertIn("gameplay_rules", package.files)
        self.assertEqual(package.files["starter"]["schema_version"], 1)
        self.assertNotIn("locations", package.files["starter"])
        self.assertNotIn("connections", package.files["starter"])
        self.assertEqual(len(package.map_definitions), 9)
        self.assertEqual(len(package.files["npcs"]["npcs"]), 4)
        self.assertEqual(len(package.files["quests"]["quests"]), 2)
        self.assertEqual(len(package.files["resources"]["nodes"]), 22)
        self.assertEqual(len(package.files["characters"]["races"]), 3)
        self.assertEqual(len(package.files["characters"]["classes"]), 3)

    def test_demo_package_separates_hex_maps_from_square_maps(self):
        package = load_content_package(DEMO_PACKAGE)

        self.assertEqual(set(package.hex_map_definitions), {"hex_forest_demo"})
        self.assertIsNotNone(package.world_map_definition)
        self.assertEqual(package.world_map_definition.world_map_id, "eldoria_hex_world")
        self.assertEqual(
            package.world_map_definition.placements_by_map_id["hex_forest_demo"].position,
            WorldHexPosition(0, 0),
        )
        self.assertNotIn("hex_forest_demo", package.map_definitions)
        self.assertEqual(len(package.map_definitions), 9)
        self.assertTrue(
            set(package.map_definitions).isdisjoint(package.hex_map_definitions)
        )


    def test_hex_transition_ids_are_unique_across_local_maps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for map_id in ("first", "second"):
                definition = {
                    "schema_version": 2,
                    "map_id": map_id,
                    "name": map_id,
                    "description": "",
                    "geometry": {
                        "type": "hex_axial",
                        "orientation": "pointy_top",
                        "coordinate_system": "axial",
                    },
                    "terrain_ids": ["grass"],
                    "default_terrain": "grass",
                    "valid_cells": [[0, 0]],
                    "transitions": [{
                        "id": "shared_exit",
                        "source_cells": [[0, 0]],
                        "exit_direction": "east",
                        "target_map_id": "future",
                        "target_entry_direction": "west",
                        "target_cells": [],
                        "active": False,
                        "traversal_mode": "one_way",
                    }],
                }
                (root / f"{map_id}.json").write_text(
                    json.dumps(definition), encoding="utf-8"
                )
            with self.assertRaisesRegex(ContentPackageError, "Duplicate transition ID"):
                _load_hex_maps(root, {})

    def test_package_rejects_unsupported_manifest_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps({
                    "schema_version": 99,
                    "package_id": "invalid",
                    "package_version": "1.0.0",
                    "files": {"starter": "starter.json"},
                }),
                encoding="utf-8",
            )
            (root / "starter.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ContentPackageError, "Unsupported"):
                load_content_package(root)

    def test_package_rejects_paths_outside_package_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "package"
            root.mkdir()
            (root.parent / "outside.json").write_text("{}", encoding="utf-8")
            (root / "manifest.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "package_id": "invalid",
                    "package_version": "1.0.0",
                    "files": {"outside": "../outside.json"},
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ContentPackageError, "outside"):
                load_content_package(root)

    def test_package_rejects_missing_data_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "package_id": "invalid",
                    "package_version": "1.0.0",
                    "files": {"missing": "missing.json"},
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ContentPackageError, "could not be loaded"):
                load_content_package(root)

    def test_demo_package_discovers_all_map_json_files(self):
        package = load_content_package(DEMO_PACKAGE)

        self.assertEqual(
            set(package.map_definitions),
            {
                "village", "forest", "south_forest", "west_forest",
                "east_forest", "north_mine", "south_mine", "west_mine",
                "east_mine",
            },
        )

    def test_package_rejects_missing_declared_maps_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "package_id": "invalid",
                    "package_version": "1.0.0",
                    "files": {"starter": "starter.json"},
                    "maps": "maps",
                }),
                encoding="utf-8",
            )
            (root / "starter.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ContentPackageError, "maps directory"):
                load_content_package(root)


if __name__ == "__main__":
    unittest.main()
