import unittest
from types import SimpleNamespace

from game_ui.assets.asset_manager import AssetManager
from game_ui.assets.animation import Animation
from game_ui.assets.sprite_sheet import SpriteSheet


class FakeFrame:
    def __init__(self, rect=None): self.rect = rect
    def copy(self): return FakeFrame(self.rect)


class FakeSurface:
    def __init__(self, width, height): self.width, self.height = width, height
    def get_width(self): return self.width
    def get_height(self): return self.height
    def subsurface(self, rect): return FakeFrame(rect)


class TestPresentationAssets(unittest.TestCase):
    def test_asset_manager_caches_loaded_image(self):
        calls = []
        image = SimpleNamespace(convert_alpha=lambda: "converted")
        pygame = SimpleNamespace(image=SimpleNamespace(load=lambda path: calls.append(path) or image))
        assets = AssetManager(pygame)
        self.assertEqual(assets.load_image("hero", "hero.png"), "converted")
        self.assertEqual(assets.load_image("hero", "different.png"), "converted")
        self.assertEqual(calls, ["hero.png"])
        self.assertEqual(assets.image_count, 1)

    def test_sprite_sheet_slices_frames_in_row_major_order(self):
        sheet = SpriteSheet(FakeSurface(64, 32), 16, 16)
        self.assertEqual(sheet.frame_count, 8)
        self.assertEqual(sheet.frame(5).rect, (16, 16, 16, 16))

    def test_sprite_sheet_rejects_invalid_frame_index(self):
        sheet = SpriteSheet(FakeSurface(32, 16), 16, 16)
        with self.assertRaises(IndexError): sheet.frame(2)

    def test_animation_advances_and_loops(self):
        animation = Animation(("a", "b", "c"), 0.1)
        animation.update(0.25)
        self.assertEqual(animation.current_frame, "c")
        animation.update(0.1)
        self.assertEqual(animation.current_frame, "a")

    def test_non_looping_animation_finishes_on_last_frame(self):
        animation = Animation(("a", "b"), 0.1, loop=False)
        animation.update(1.0)
        self.assertEqual(animation.current_frame, "b")
        self.assertTrue(animation.finished)


if __name__ == "__main__":
    unittest.main()
