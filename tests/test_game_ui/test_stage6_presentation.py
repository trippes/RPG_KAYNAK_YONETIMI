import json
import tempfile
import unittest
from pathlib import Path
from game_ui.assets.asset_definition import AssetCatalog, AssetCatalogError
from game_ui.assets.animation import Animation
from game_ui.world_rendering.character_animation import CharacterAnimator
from game_ui.world_rendering.scene_object import SceneObject, SceneObjectRenderer

class TestStage6Presentation(unittest.TestCase):
    def test_catalog_resolves_metadata_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tree.png").write_bytes(b"placeholder")
            source = root / "assets.json"
            source.write_text(json.dumps({"schema_version": 1, "assets": [{
                "asset_id": "tree.oak", "path": "tree.png", "width": 64, "height": 96,
                "anchor": [0.5, 0.95], "collision": [20, 50, 24, 30],
                "terrain_types": ["grass"], "placement": "canopy", "interaction": "inspect"
            }]}), encoding="utf-8")
            catalog = AssetCatalog.load(source)
            self.assertTrue(catalog.available("tree.oak"))
            self.assertEqual(catalog.get("tree.oak").anchor, (0.5, 0.95))
            self.assertTrue(catalog.resolve_path("tree.oak").samefile(root / "tree.png"))
    def test_catalog_rejects_path_traversal_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "assets.json"
            record = {"asset_id": "tree", "path": "../outside.png", "width": 32, "height": 32}
            source.write_text(json.dumps({"schema_version": 1, "assets": [record]}), encoding="utf-8")
            with self.assertRaises(AssetCatalogError):
                AssetCatalog.load(source)
            record["path"] = "tree.png"
            source.write_text(json.dumps({"schema_version": 1, "assets": [record, record]}), encoding="utf-8")
            with self.assertRaises(AssetCatalogError):
                AssetCatalog.load(source)
    def test_scene_object_separates_visual_and_collision_geometry(self):
        obj = SceneObject("oak-1", "tree.oak", 100, 120, 80, 110, footprint=(2, 2), collision_box=(88, 90, 24, 30))
        self.assertEqual(obj.visual_bounds, (60.0, 10.0, 140.0, 120.0))
        self.assertEqual(obj.footprint, (2, 2))
        self.assertEqual(obj.collision_box, (88, 90, 24, 30))
    def test_culling_uses_complete_visual_bounds(self):
        obj = SceneObject("oak-1", "tree.oak", 100, 100, 80, 120)
        self.assertTrue(SceneObjectRenderer.is_visible(obj, (0, 0, 100, 30)))
        self.assertFalse(SceneObjectRenderer.is_visible(obj, (200, 200, 50, 50)))
    def test_character_animator_selects_direction_and_state(self):
        animation = Animation(("idle-0", "idle-1"), 0.1)
        animator = CharacterAnimator({"south": {"idle": animation}})
        animator.update(0.1)
        self.assertEqual(animator.current_frame, "idle-1")
        animator.select(direction="south", state="walk")
        self.assertIsNone(animator.current_frame)
        with self.assertRaises(ValueError):
            animator.select(direction="up")
    def test_missing_asset_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "assets.json"
            source.write_text(json.dumps({"schema_version": 1, "assets": [
                {"asset_id": "missing", "path": "missing.png", "width": 8, "height": 8}
            ]}), encoding="utf-8")
            self.assertFalse(AssetCatalog.load(source).available("missing"))

if __name__ == "__main__":
    unittest.main()
