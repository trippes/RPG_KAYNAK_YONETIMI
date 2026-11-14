"""Safe save and migration contracts for presentation content packages."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from application.presentation_content_store import (
    ContentMigrationError,
    ContentWriteError,
    PresentationContentStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = PROJECT_ROOT / "content" / "demo_eldoria"


class TestPresentationContentStore(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "demo_eldoria"
        shutil.copytree(DEMO_PACKAGE, self.root)
        self.store = PresentationContentStore(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def read_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_asset_catalog_save_is_deterministic_and_keeps_previous_backup(self):
        target = self.root / "asset_catalog.json"
        previous = target.read_bytes()
        payload = self.read_json(target)
        payload["assets"][0]["category"] = "flora"

        first = self.store.save_asset_catalog(payload)
        first_bytes = target.read_bytes()
        second = self.store.save_asset_catalog(payload)

        self.assertEqual(target.read_bytes(), first_bytes)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), payload)
        self.assertEqual((self.root / "asset_catalog.json.bak").read_bytes(), first_bytes)
        self.assertEqual(first.backup_paths, ((self.root / "asset_catalog.json.bak").resolve(),))
        self.assertEqual(second.written_paths, (target.resolve(),))
        self.assertNotEqual(previous, first_bytes)

    def test_invalid_asset_catalog_is_rejected_without_replacing_source(self):
        target = self.root / "asset_catalog.json"
        original = target.read_bytes()
        payload = self.read_json(target)
        payload["assets"][1]["asset_id"] = payload["assets"][0]["asset_id"]

        with self.assertRaisesRegex(ContentWriteError, "Duplicate asset id"):
            self.store.save_asset_catalog(payload)

        self.assertEqual(target.read_bytes(), original)
        self.assertFalse((self.root / "asset_catalog.json.bak").exists())

    def test_future_asset_schema_is_rejected_without_replacing_source(self):
        target = self.root / "asset_catalog.json"
        original = target.read_bytes()
        payload = self.read_json(target)
        payload["schema_version"] = 99

        with self.assertRaises(ContentWriteError):
            self.store.save_asset_catalog(payload)

        self.assertEqual(target.read_bytes(), original)

    def test_non_finite_values_are_rejected_before_staging(self):
        target = self.root / "asset_catalog.json"
        original = target.read_bytes()
        payload = self.read_json(target)
        payload["assets"][0]["scale"] = float("nan")

        with self.assertRaisesRegex(ContentWriteError, "Non-finite"):
            self.store.save_asset_catalog(payload)

        self.assertEqual(target.read_bytes(), original)

    def test_invalid_placement_is_rejected_without_replacing_source(self):
        target = self.root / "placements" / "hex_forest_demo.json"
        original = target.read_bytes()
        payload = self.read_json(target)
        payload["objects"][0]["q"] = 9999
        payload["objects"][0]["r"] = 9999

        with self.assertRaises(ContentWriteError):
            self.store.save_map_placements("hex_forest_demo", payload)

        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(target.with_name(target.name + ".bak").exists())

    def test_valid_placement_save_is_reloadable_and_keeps_previous_backup(self):
        target = self.root / "placements" / "hex_forest_demo.json"
        original = target.read_bytes()
        payload = self.read_json(target)
        payload["objects"][0]["offset_x"] = -12.5

        result = self.store.save_map_placements("hex_forest_demo", payload)

        self.assertEqual(self.read_json(target)["objects"][0]["offset_x"], -12.5)
        self.assertEqual(target.with_name(target.name + ".bak").read_bytes(), original)
        self.assertEqual(result.written_paths, (target.resolve(),))
        from application.content_loader import load_content_package
        package = load_content_package(self.root)
        placement = next(
            item for item in package.scene_placements.placements
            if item.object_id == "tree-oak-01"
        )
        self.assertEqual(placement.offset_x, -12.5)

    def test_placement_payload_must_match_requested_map_id(self):
        payload = self.read_json(self.root / "placements" / "hex_forest_demo.json")
        with self.assertRaisesRegex(ContentWriteError, "must match"):
            self.store.save_map_placements("hex_clearing_demo", payload)

    def test_manifest_path_escape_is_rejected(self):
        manifest_path = self.root / "manifest.json"
        manifest = self.read_json(manifest_path)
        manifest["asset_catalog"] = "../outside.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        payload = self.read_json(self.root / "asset_catalog.json")

        with self.assertRaisesRegex(ContentWriteError, "Unsafe content path"):
            self.store.save_asset_catalog(payload)

        self.assertEqual(manifest_path.read_text(encoding="utf-8"), json.dumps(manifest))

    def _make_legacy_package(self):
        manifest_path = self.root / "manifest.json"
        manifest = self.read_json(manifest_path)
        manifest.pop("asset_catalog")
        manifest.pop("map_placements")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (self.root / "asset_catalog.json").unlink()
        shutil.rmtree(self.root / "placements")
        return manifest_path

    def test_legacy_combined_migration_splits_sources_and_is_idempotent(self):
        manifest_path = self._make_legacy_package()
        legacy_path = self.root / "presentation_assets.json"
        legacy_bytes = legacy_path.read_bytes()

        first = self.store.migrate_legacy_combined_presentation()
        second = self.store.migrate_legacy_combined_presentation()

        self.assertTrue(first.migrated)
        self.assertFalse(second.migrated)
        self.assertTrue((self.root / "asset_catalog.json").is_file())
        self.assertEqual(
            {path.name for path in (self.root / "placements").glob("*.json")},
            {"hex_forest_demo.json", "hex_clearing_demo.json"},
        )
        self.assertEqual(legacy_path.read_bytes(), legacy_bytes)
        manifest = self.read_json(manifest_path)
        self.assertEqual(manifest["asset_catalog"], "asset_catalog.json")
        self.assertEqual(manifest["map_placements"], "placements")
        from application.content_loader import load_content_package
        package = load_content_package(self.root)
        self.assertEqual(len(package.presentation_catalog.assets), 6)
        self.assertEqual(len(package.scene_placements.placements), 14)

    def test_migration_reuses_matching_orphaned_files_after_interrupted_attempt(self):
        self._make_legacy_package()
        legacy = self.read_json(self.root / "presentation_assets.json")
        (self.root / "asset_catalog.json").write_text(
            PresentationContentStore._encode_json({
                "schema_version": 1,
                "assets": legacy["assets"],
            }),
            encoding="utf-8",
        )
        placements = self.root / "placements"
        placements.mkdir()
        forest_records = [
            {key: value for key, value in record.items() if key != "map_id"}
            for record in legacy["objects"]
            if record["map_id"] == "hex_forest_demo"
        ]
        (placements / "hex_forest_demo.json").write_text(
            PresentationContentStore._encode_json({
                "schema_version": 1,
                "map_id": "hex_forest_demo",
                "objects": forest_records,
            }),
            encoding="utf-8",
        )

        result = self.store.migrate_legacy_combined_presentation()

        self.assertTrue(result.migrated)
        self.assertTrue((placements / "hex_clearing_demo.json").is_file())
        from application.content_loader import load_content_package
        package = load_content_package(self.root)
        self.assertEqual(len(package.scene_placements.placements), 14)

    def test_migration_rejects_existing_unmanaged_split_sources(self):
        self._make_legacy_package()
        (self.root / "asset_catalog.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ContentMigrationError, "conflicts"):
            self.store.migrate_legacy_combined_presentation()

    def test_migration_failure_preserves_legacy_file_and_manifest(self):
        manifest_path = self._make_legacy_package()
        legacy_path = self.root / "presentation_assets.json"
        legacy = self.read_json(legacy_path)
        legacy["objects"][1]["object_id"] = legacy["objects"][0]["object_id"]
        legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
        original_legacy = legacy_path.read_bytes()
        original_manifest = manifest_path.read_bytes()

        with self.assertRaises(ContentMigrationError):
            self.store.migrate_legacy_combined_presentation()

        self.assertEqual(legacy_path.read_bytes(), original_legacy)
        self.assertEqual(manifest_path.read_bytes(), original_manifest)
        self.assertFalse((self.root / "asset_catalog.json").exists())
        self.assertFalse((self.root / "placements").exists())

    def test_multi_file_migration_rolls_back_if_a_later_replace_fails(self):
        manifest_path = self._make_legacy_package()
        original_manifest = manifest_path.read_bytes()
        replace = self.store._replace_target
        calls = 0

        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected replace failure")
            replace(source, target)

        with patch.object(self.store, "_replace_target", side_effect=fail_second):
            with self.assertRaisesRegex(ContentWriteError, "rolled back"):
                self.store.migrate_legacy_combined_presentation()

        self.assertEqual(manifest_path.read_bytes(), original_manifest)
        self.assertFalse((self.root / "asset_catalog.json").exists())
        self.assertFalse((self.root / "placements").exists())
        self.assertEqual(
            list(self.root.glob(".*.tmp")) + list((self.root / "placements").glob(".*.tmp"))
            if (self.root / "placements").exists() else list(self.root.glob(".*.tmp")),
            [],
        )


if __name__ == "__main__":
    unittest.main()
