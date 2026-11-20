"""Tests for separated, map-scoped presentation placement data."""

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from application.content_loader import load_content_package
from game_ui.assets.asset_definition import AssetCatalog
from game_ui.assets.placement_catalog import (
    ScenePlacementCatalog,
    ScenePlacementCatalogError,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "content" / "demo_eldoria"


class TestScenePlacementCatalog(unittest.TestCase):
    def test_demo_package_has_assets_and_map_scoped_scene_placements(self):
        package = load_content_package(PACKAGE_ROOT)
        self.assertIsNotNone(package.asset_catalog_path)
        catalog = AssetCatalog.load(package.asset_catalog_path)
        self.assertEqual(len(catalog.assets), 7)
        self.assertEqual(len(package.scene_placements.placements), 15)

    def test_placement_catalog_exposes_an_immutable_snapshot(self):
        package = load_content_package(PACKAGE_ROOT)
        catalog = AssetCatalog.load(package.asset_catalog_path)
        placements = ScenePlacementCatalog.load_directory(
            package.map_placements_path, catalog
        )
        with self.assertRaises(FrozenInstanceError):
            placements.placements = ()


    def test_legacy_combined_presentation_file_remains_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy_path = Path(directory) / "presentation_assets.json"
            split_assets = json.loads(
                (PACKAGE_ROOT / "asset_catalog.json").read_text(encoding="utf-8")
            )
            split_placements = []
            for source in sorted((PACKAGE_ROOT / "placements").glob("*.json")):
                data = json.loads(source.read_text(encoding="utf-8"))
                split_placements.extend(
                    {**record, "map_id": data["map_id"]}
                    for record in data["objects"]
                )
            legacy_data = {**split_assets, "objects": split_placements}
            legacy_path.write_text(json.dumps(legacy_data), encoding="utf-8")

            legacy = AssetCatalog.load(legacy_path)

            self.assertEqual(len(legacy.assets), 7)
            self.assertEqual(len(legacy.objects), 15)
            self.assertEqual(legacy_data["assets"], split_assets["assets"])
            self.assertEqual(legacy_data["objects"], split_placements)

    def test_unknown_asset_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "asset_catalog.json"
            catalog_path.write_text(json.dumps({
                "schema_version": 1,
                "assets": [{
                    "asset_id": "flora.tree",
                    "path": "missing.png",
                    "width": 0,
                    "height": 0,
                }],
            }), encoding="utf-8")
            catalog = AssetCatalog.load(catalog_path)
            placements_dir = root / "placements"
            placements_dir.mkdir()
            (placements_dir / "forest.json").write_text(json.dumps({
                "schema_version": 1,
                "map_id": "forest",
                "objects": [{
                    "object_id": "tree-1",
                    "asset_id": "flora.missing",
                    "q": 0,
                    "r": 0,
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ScenePlacementCatalogError, "unknown asset"):
                ScenePlacementCatalog.load_directory(placements_dir, catalog)

    def test_unknown_map_id_is_rejected_when_package_map_ids_are_supplied(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "asset_catalog.json"
            catalog_path.write_text(json.dumps({
                "schema_version": 1,
                "assets": [{
                    "asset_id": "flora.tree",
                    "path": "missing.png",
                    "width": 0,
                    "height": 0,
                }],
            }), encoding="utf-8")
            catalog = AssetCatalog.load(catalog_path)
            placements_dir = root / "placements"
            placements_dir.mkdir()
            (placements_dir / "forest.json").write_text(json.dumps({
                "schema_version": 1,
                "map_id": "missing_map",
                "objects": [{
                    "object_id": "tree-1",
                    "asset_id": "flora.tree",
                    "q": 0,
                    "r": 0,
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(ScenePlacementCatalogError, "unknown map"):
                ScenePlacementCatalog.load_directory(
                    placements_dir, catalog, valid_map_ids={"forest"}
                )

    def test_duplicate_object_ids_are_rejected_across_map_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "asset_catalog.json"
            catalog_path.write_text(json.dumps({
                "schema_version": 1,
                "assets": [{
                    "asset_id": "flora.tree",
                    "path": "missing.png",
                    "width": 0,
                    "height": 0,
                }],
            }), encoding="utf-8")
            catalog = AssetCatalog.load(catalog_path)
            placements_dir = root / "placements"
            placements_dir.mkdir()
            for map_id in ("forest", "clearing"):
                (placements_dir / f"{map_id}.json").write_text(json.dumps({
                    "schema_version": 1,
                    "map_id": map_id,
                    "objects": [{
                        "object_id": "shared-id",
                        "asset_id": "flora.tree",
                        "q": 0,
                        "r": 0,
                    }],
                }), encoding="utf-8")
            with self.assertRaisesRegex(ScenePlacementCatalogError, "Duplicate"):
                ScenePlacementCatalog.load_directory(placements_dir, catalog)


if __name__ == "__main__":
    unittest.main()
