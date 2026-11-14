"""UI-independent presentation-content service contracts."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from application.presentation_content_service import (
    PresentationContentService,
    PresentationContentServiceError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = PROJECT_ROOT / "content" / "demo_eldoria"


class TestPresentationContentService(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "demo_eldoria"
        shutil.copytree(DEMO_PACKAGE, self.root)
        self.service = PresentationContentService(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def read_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_lists_and_resolves_assets_without_exposing_ui_types(self):
        assets = self.service.list_assets()
        self.assertEqual(len(assets), 6)
        asset = self.service.get_asset("flora.tree.oak")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.asset_id, "flora.tree.oak")
        self.assertIsNone(self.service.get_asset("missing.asset"))
        self.assertEqual(self.service.list_assets("not-a-category"), ())

    def test_loads_placements_for_known_map(self):
        placements = self.service.load_map_placements("hex_forest_demo")
        self.assertTrue(placements)
        self.assertTrue(all(item.map_id == "hex_forest_demo" for item in placements))

    def test_unknown_map_is_rejected(self):
        with self.assertRaisesRegex(PresentationContentServiceError, "Unknown hex map"):
            self.service.load_map_placements("not-a-map")

    def test_package_validation_reports_missing_images_as_warnings(self):
        result = self.service.validate_content_package()
        self.assertTrue(result.valid)
        self.assertTrue(all(issue.severity == "warning" for issue in result.issues))
        self.assertTrue(any(issue.code == "missing_file" for issue in result.issues))

    def test_valid_asset_draft_passes_without_changing_live_source(self):
        path = self.root / "asset_catalog.json"
        original = path.read_bytes()
        draft = self.read_json(path)
        draft["assets"][0]["category"] = "flora"

        result = self.service.validate_asset_catalog(draft)

        self.assertTrue(result.valid)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(path.with_name(path.name + ".bak").exists())

    def test_invalid_asset_draft_is_structured_and_does_not_change_source(self):
        path = self.root / "asset_catalog.json"
        original = path.read_bytes()
        draft = self.read_json(path)
        draft["assets"][1]["asset_id"] = draft["assets"][0]["asset_id"]

        result = self.service.validate_asset_catalog(draft)

        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].code, "invalid_draft")
        self.assertIn("Duplicate asset id", result.issues[0].message)
        self.assertEqual(path.read_bytes(), original)

    def test_valid_placement_draft_passes_without_changing_live_source(self):
        path = self.root / "placements" / "hex_forest_demo.json"
        original = path.read_bytes()
        draft = self.read_json(path)
        draft["objects"][0]["offset_x"] = -4.25

        result = self.service.validate_map_placements("hex_forest_demo", draft)

        self.assertTrue(result.valid)
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_placement_draft_is_rejected_without_live_write(self):
        path = self.root / "placements" / "hex_forest_demo.json"
        original = path.read_bytes()
        draft = self.read_json(path)
        draft["objects"][0]["q"] = 9999

        result = self.service.validate_map_placements("hex_forest_demo", draft)

        self.assertFalse(result.valid)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(path.with_name(path.name + ".bak").exists())

    def test_asset_save_uses_safe_store_and_refreshes_read_results(self):
        path = self.root / "asset_catalog.json"
        draft = self.read_json(path)
        draft["assets"][0]["category"] = "service-test"

        result = self.service.save_asset_catalog(draft)

        self.assertEqual(result.written_paths, (path.resolve(),))
        self.assertEqual(self.service.get_asset(draft["assets"][0]["asset_id"]).category, "service-test")
        self.assertTrue((self.root / "asset_catalog.json.bak").is_file())

    def test_migration_status_is_read_only_for_split_package(self):
        before = (self.root / "manifest.json").read_bytes()

        status = self.service.migration_status()

        self.assertEqual(status.source_format, "split")
        self.assertFalse(status.migration_available)
        self.assertEqual((self.root / "manifest.json").read_bytes(), before)

    def test_legacy_migration_is_explicit_and_updates_status(self):
        manifest_path = self.root / "manifest.json"
        manifest = self.read_json(manifest_path)
        manifest.pop("asset_catalog")
        manifest.pop("map_placements")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (self.root / "asset_catalog.json").unlink()
        shutil.rmtree(self.root / "placements")

        before = self.service.migration_status()
        self.assertEqual(before.source_format, "legacy_combined")
        self.assertTrue(before.migration_available)

        result = self.service.migrate_legacy_content()

        self.assertTrue(result.migrated)
        self.assertEqual(self.service.migration_status().source_format, "split")
        self.assertTrue(self.service.validate_content_package().valid)

    def test_invalid_package_returns_structured_failure(self):
        (self.root / "asset_catalog.json").write_text("{broken", encoding="utf-8")

        result = self.service.validate_content_package()

        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].code, "invalid_package")


if __name__ == "__main__":
    unittest.main()
