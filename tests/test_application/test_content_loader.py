import json
import shutil
import tempfile
import unittest
from pathlib import Path

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
        self.assertEqual(package.asset_catalog_path.name, "asset_catalog.json")
        self.assertEqual(package.map_placements_path.name, "placements")
        self.assertIsNone(package.presentation_assets_path)
        self.assertIn("starter", package.files)
        self.assertIn("npcs", package.files)
        self.assertIn("quests", package.files)
        self.assertIn("resources", package.files)
        self.assertIn("characters", package.files)
        self.assertIn("gameplay_rules", package.files)
        self.assertEqual(package.files["starter"]["schema_version"], 1)
        self.assertNotIn("locations", package.files["starter"])
        self.assertNotIn("connections", package.files["starter"])
        self.assertEqual(len(package.hex_map_definitions), 0)
        self.assertEqual(package.files["npcs"]["npcs"], [])
        self.assertEqual(package.files["quests"]["quests"], [])
        self.assertEqual(package.files["resources"]["nodes"], [])
        self.assertEqual(len(package.files["characters"]["races"]), 3)
        self.assertEqual(len(package.files["characters"]["classes"]), 3)

    def _copy_demo_package(self, parent):
        target = Path(parent) / "demo_eldoria"
        shutil.copytree(DEMO_PACKAGE, target)
        return target

    def test_package_exposes_one_prevalidated_presentation_snapshot(self):
        package = load_content_package(DEMO_PACKAGE)

        self.assertIsNotNone(package.presentation_catalog)
        self.assertIsNotNone(package.scene_placements)
        self.assertEqual(len(package.presentation_catalog.assets), 6)
        self.assertEqual(len(package.scene_placements.placements), 0)
        validation_issues = package.presentation_catalog.validate_assets()
        self.assertEqual(
            tuple((issue.asset_id, issue.code) for issue in validation_issues),
            (
                ("prop.rock.large", "missing_file"),
                ("flora.shrub.green", "missing_file"),
                ("flora.plant.wildflower", "missing_file"),
            ),
        )

    def test_package_rejects_duplicate_asset_ids_before_exposing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_demo_package(directory)
            catalog_path = root / "asset_catalog.json"
            payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            payload["assets"][1]["asset_id"] = payload["assets"][0]["asset_id"]
            catalog_path.write_text(json.dumps(payload), encoding="utf-8")
            invalid_bytes = catalog_path.read_bytes()

            with self.assertRaisesRegex(ContentPackageError, "Duplicate asset id"):
                load_content_package(root)

            self.assertEqual(catalog_path.read_bytes(), invalid_bytes)

    def test_boolean_asset_schema_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_demo_package(directory)
            catalog_path = root / "asset_catalog.json"
            payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            payload["schema_version"] = True
            catalog_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ContentPackageError, "Unsupported"):
                load_content_package(root)

    def test_legacy_combined_catalog_is_prevalidated_when_split_sources_are_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_demo_package(directory)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("asset_catalog")
            manifest.pop("map_placements")
            manifest["presentation_assets"] = "presentation_assets.json"
            legacy = json.loads((root / "asset_catalog.json").read_text(encoding="utf-8"))
            legacy["objects"] = []
            (root / "presentation_assets.json").write_text(
                json.dumps(legacy), encoding="utf-8"
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            package = load_content_package(root)

            self.assertIsNotNone(package.presentation_catalog)
            self.assertIsNone(package.scene_placements)
            self.assertEqual(len(package.presentation_catalog.objects), 0)

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
                _load_hex_maps(root)

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

    def test_demo_package_contains_no_legacy_square_or_demo_hex_maps(self):
        package = load_content_package(DEMO_PACKAGE)
        self.assertEqual(package.hex_map_definitions, {})
        self.assertIsNone(package.world_map_definition)

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
