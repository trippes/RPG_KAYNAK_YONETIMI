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

    def test_load_preserves_validated_rig_layer_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(directory)
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["rig_layers"] = [{
                "component_id": "branch.left",
                "order": 1,
                "anchor": [0.5, 0.6],
                "pivot": [0.5, 1.0],
                "size": [0.3, 0.4],
                "motion": {"kind": "branch", "index": 0},
            }]
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            atlas = TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)
        self.assertEqual(len(atlas.rig_layers), 1)
        self.assertEqual(atlas.rig_layers[0]["component_id"], "branch.left")

    def test_rejects_rig_layer_referencing_missing_component(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(directory)
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["rig_layers"] = [{
                "component_id": "missing",
                "order": 0,
                "anchor": [0.5, 0.5],
                "pivot": [0.5, 0.5],
                "size": [0.2, 0.2],
            }]
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(TreeAtlasError):
                TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)

    def test_rejects_invalid_rig_motion_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas_path, manifest_path = self._write_files(directory)
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["rig_layers"] = [{
                "component_id": "branch.left",
                "order": 0,
                "anchor": [0.5, 0.5],
                "pivot": [0.5, 0.5],
                "size": [0.2, 0.2],
                "motion": {"kind": "branch", "index": -1},
            }]
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(TreeAtlasError):
                TreePartsAtlas.load(FakePygame, atlas_path, manifest_path)

    def test_demo_rig_manifest_uses_existing_components_and_skeleton_indices(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads(
            (root / "content" / "demo_eldoria" / "assets" / "tree_parts_atlas.json")
            .read_text(encoding="utf-8")
        )
        component_ids = {item["id"] for item in manifest["components"]}
        self.assertTrue(manifest["rig_layers"])
        for layer in manifest["rig_layers"]:
            self.assertIn(layer["component_id"], component_ids)
            motion = layer.get("motion", {})
            if motion.get("kind") == "branch":
                self.assertIn(motion["index"], range(4))
            elif motion.get("kind") == "leaf":
                self.assertIn(motion["index"], range(5))

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
