"""Contract tests for the Pygame-independent asset catalog."""

import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from game_ui.assets.asset_definition import AssetCatalog, AssetCatalogError


def write_png(path, width=2, height=3):
    """Write a tiny structurally valid RGBA PNG without external dependencies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + b"\x00\x00\x00\xff" * width for _ in range(height))

    def chunk(kind, data):
        checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


class TestAssetCatalogContract(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.catalog_path = self.root / "presentation_assets.json"
        write_png(self.root / "assets" / "tree.png")
        self.write_catalog(
            [
                {
                    "asset_id": "flora.tree",
                    "path": "assets/tree.png",
                    "width": 0,
                    "height": 0,
                    "scale": 1.0,
                    "category": "flora",
                }
            ]
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_catalog(self, assets, objects=None):
        self.catalog_path.write_text(
            json.dumps(
                {"schema_version": 1, "assets": assets, "objects": objects or []}
            ),
            encoding="utf-8",
        )

    def load(self):
        return AssetCatalog.load(self.catalog_path)

    def test_asset_ids_are_unique_and_lookup_is_explicit(self):
        catalog = self.load()
        self.assertEqual(catalog.asset_ids, ("flora.tree",))
        self.assertEqual(catalog.require("flora.tree").asset_id, "flora.tree")
        with self.assertRaisesRegex(AssetCatalogError, "Unknown asset id"):
            catalog.require("flora.missing")

    def test_duplicate_asset_id_is_rejected(self):
        asset = {
            "asset_id": "flora.tree",
            "path": "assets/tree.png",
            "width": 0,
            "height": 0,
        }
        self.write_catalog([asset, dict(asset)])
        with self.assertRaisesRegex(AssetCatalogError, "Duplicate asset id"):
            self.load()

    def test_unsafe_paths_are_rejected(self):
        for unsafe_path in ("../outside.png", "/tmp/outside.png", "C:\\outside.png", "assets\\tree.png"):
            with self.subTest(path=unsafe_path):
                self.write_catalog(
                    [{"asset_id": "flora.tree", "path": unsafe_path, "width": 0, "height": 0}]
                )
                with self.assertRaises(AssetCatalogError):
                    self.load()

    def test_symlink_escape_is_rejected_when_supported(self):
        outside = self.root.parent / (self.root.name + "-outside.png")
        write_png(outside)
        link = self.root / "assets" / "outside.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation is not available on this platform.")
        try:
            self.write_catalog(
                [{"asset_id": "flora.tree", "path": "assets/outside.png", "width": 0, "height": 0}]
            )
            with self.assertRaisesRegex(AssetCatalogError, "escapes catalog root"):
                self.load()
        finally:
            outside.unlink(missing_ok=True)

    def test_source_dimensions_are_read_once_and_zero_sentinel_is_preserved(self):
        catalog = self.load()
        self.assertEqual((catalog.require("flora.tree").width, catalog.require("flora.tree").height), (0, 0))
        self.assertEqual(catalog.source_size("flora.tree"), (2, 3))
        self.assertTrue(catalog.available("flora.tree"))
        self.assertEqual(catalog.validate_assets(), ())

    def test_metadata_dimension_mismatch_is_reported_not_fatal(self):
        self.write_catalog(
            [{"asset_id": "flora.tree", "path": "assets/tree.png", "width": 8, "height": 9}]
        )
        catalog = self.load()
        self.assertEqual(catalog.validate_assets()[0].code, "dimension_mismatch")
        self.assertTrue(catalog.available("flora.tree"))
        self.assertFalse(catalog.is_valid("flora.tree"))

    def test_missing_and_corrupt_pngs_are_reported_without_rejecting_catalog(self):
        self.write_catalog(
            [
                {"asset_id": "missing", "path": "assets/missing.png", "width": 0, "height": 0},
                {"asset_id": "corrupt", "path": "assets/tree.png", "width": 0, "height": 0},
            ]
        )
        (self.root / "assets" / "tree.png").write_bytes(b"not a png")
        catalog = self.load()
        self.assertEqual(
            {issue.code for issue in catalog.validate_assets()},
            {"missing_file", "invalid_png"},
        )
        self.assertFalse(catalog.available("missing"))
        self.assertTrue(catalog.available("corrupt"))
        self.assertFalse(catalog.is_valid("missing"))
        self.assertFalse(catalog.is_valid("corrupt"))

    def test_categories_are_queryable_without_ui_dependencies(self):
        catalog = self.load()
        self.assertEqual(catalog.categories, ("flora",))
        self.assertEqual([asset.asset_id for asset in catalog.list_assets("flora")], ["flora.tree"])
        self.assertEqual(len(catalog.list_assets("prop")), 0)

    def test_catalog_asset_mapping_is_read_only(self):
        catalog = self.load()
        with self.assertRaises(TypeError):
            catalog.assets["other"] = catalog.require("flora.tree")


if __name__ == "__main__":
    unittest.main()
