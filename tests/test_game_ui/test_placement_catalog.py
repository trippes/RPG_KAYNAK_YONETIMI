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
    def test_demo_package_loads_assets_and_placements_from_separate_sources(self):
        package = load_content_package(PACKAGE_ROOT)
        self.assertIsNotNone(package.asset_catalog_path)
        self.assertIsNotNone(package.map_placements_path)
        catalog = AssetCatalog.load(package.asset_catalog_path)
        placements = ScenePlacementCatalog.load_directory(
            package.map_placements_path, catalog
        )

        self.assertEqual(len(catalog.assets), 6)
        self.assertEqual(len(placements.placements), 14)
        self.assertEqual(
            placements.map_ids, ("hex_clearing_demo", "hex_forest_demo")
        )
        self.assertEqual(len(placements.objects_for_map("hex_forest_demo")), 12)
        self.assertEqual(len(placements.objects_for_map("hex_clearing_demo")), 2)
        self.assertEqual(catalog.objects, ())

    def test_placement_catalog_exposes_an_immutable_snapshot(self):
        package = load_content_package(PACKAGE_ROOT)
        catalog = AssetCatalog.load(package.asset_catalog_path)
        placements = ScenePlacementCatalog.load_directory(
            package.map_placements_path, catalog
        )
        with self.assertRaises(FrozenInstanceError):
            placements.placements = ()

    def test_same_asset_can_be_reused_across_maps_and_instances(self):
        package = load_content_package(PACKAGE_ROOT)
        catalog = AssetCatalog.load(package.asset_catalog_path)
        placements = ScenePlacementCatalog.load_directory(
            package.map_placements_path, catalog
        )
        forest = placements.objects_for_map("hex_forest_demo")
        clearing = placements.objects_for_map("hex_clearing_demo")

        self.assertTrue(any(item.asset_id == "flora.tree.young" for item in forest))
        self.assertTrue(any(item.asset_id == "flora.tree.young" for item in clearing))
        first_tree = next(item for item in forest if item.object_id == "tree-oak-01")
        another_tree = next(item for item in forest if item.object_id == "tree-oak-04")
        self.assertEqual(first_tree.asset_id, another_tree.asset_id)
        self.assertNotEqual(first_tree.offset_x, another_tree.offset_x)
        self.assertIsNotNone(first_tree.collision_box)

    def test_legacy_combined_presentation_file_remains_readable(self):
        legacy_path = PACKAGE_ROOT / "presentation_assets.json"
        legacy = AssetCatalog.load(legacy_path)
        self.assertEqual(len(legacy.assets), 6)
        self.assertEqual(len(legacy.objects_for_map("hex_forest_demo")), 12)
        self.assertEqual(len(legacy.objects_for_map("hex_clearing_demo")), 2)

        legacy_data = json.loads(legacy_path.read_text(encoding="utf-8"))
        split_assets = json.loads(
            (PACKAGE_ROOT / "asset_catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(legacy_data["assets"], split_assets["assets"])
        split_placements = []
        for source in sorted((PACKAGE_ROOT / "placements").glob("*.json")):
            data = json.loads(source.read_text(encoding="utf-8"))
            split_placements.extend(
                {**record, "map_id": data["map_id"]}
                for record in data["objects"]
            )
        self.assertEqual(
            sorted(legacy_data["objects"], key=lambda item: item["object_id"]),
            sorted(split_placements, key=lambda item: item["object_id"]),
        )

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
