"""Tests for runtime extraction of individual sprites from the tree atlas."""
import json
import tempfile
import unittest
from pathlib import Path

from game_ui.world_rendering.tree_atlas import TreeAtlasError, TreePartsAtlas


class FakeSurface:
    def __init__(self, size, origin=(0, 0)):
        self._size = size
        self.origin = origin

    def convert_alpha(self):
        return self

    def get_size(self):
        return self._size

    def get_width(self):
        return self._size[0]

    def get_height(self):
        return self._size[1]

    def subsurface(self, rect):
        x, y, width, height = rect
        return FakeSurface((width, height), (self.origin[0] + x, self.origin[1] + y))

    def copy(self):
        return FakeSurface(self._size, self.origin)


class FakeImage:
    @staticmethod
    def load(_path):
        return FakeSurface((100, 80))


class FakePygame:
    image = FakeImage()


class TestTreePartsAtlas(unittest.TestCase):
    def _write_files(self, directory, rect=(10, 12, 20, 18)):
        atlas = Path(directory) / "atlas.png"
        atlas.write_bytes(b"fake")
        manifest = Path(directory) / "atlas.json"
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "source_size": [100, 80],
            "components": [{"id": "branch.left", "type": "branch", "rect": list(rect)}],
        }), encoding="utf-8")
        return atlas, manifest

    def test_load_extracts_independent_surface_for_each_component(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(directory)
            atlas = TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)
        self.assertEqual(len(atlas), 1)
        self.assertEqual(atlas.get("branch.left").get_size(), (20, 18))
        self.assertEqual(atlas.component("branch.left")["rect"], (10, 12, 20, 18))
        self.assertEqual(tuple(atlas.by_type("branch")), ("branch.left",))
        self.assertIsNone(atlas.get("missing"))

    def test_rejects_component_outside_atlas_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(
                directory, rect=(90, 70, 20, 18)
            )
            with self.assertRaises(TreeAtlasError):
                TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)

    def test_rejects_unsupported_manifest_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(directory)
            manifest_path.write_text(json.dumps({
                "schema_version": 99, "components": []
            }), encoding="utf-8")
            with self.assertRaises(TreeAtlasError):
                TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)


if __name__ == "__main__":
    unittest.main()
