import json
import tempfile
import unittest
from pathlib import Path

from application.content_loader import (
    ContentPackageError,
    load_content_package,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = PROJECT_ROOT / "content" / "demo_eldoria"


class TestContentPackageLoader(unittest.TestCase):
    def test_demo_package_loads_its_starter_definition(self):
        package = load_content_package(DEMO_PACKAGE)

        self.assertEqual(package.package_id, "demo_eldoria")
        self.assertEqual(package.package_version, "0.1.0")
        self.assertIn("starter", package.files)
        self.assertEqual(package.files["starter"]["schema_version"], 1)
        self.assertIn("locations", package.files["starter"])

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


if __name__ == "__main__":
    unittest.main()
