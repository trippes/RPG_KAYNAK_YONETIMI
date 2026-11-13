"""Regression tests for the existing lazy Pygame asset cache."""

import unittest

from game_ui.assets.asset_manager import AssetManager


class FakeImage:
    def __init__(self, name):
        self.name = name
        self.converted = 0

    def convert_alpha(self):
        self.converted += 1
        return self


class FakeImageLoader:
    def __init__(self):
        self.calls = []
        self.fail = False

    def load(self, path):
        self.calls.append(path)
        if self.fail:
            raise OSError("broken image")
        return FakeImage(path)


class FakePygame:
    def __init__(self):
        self.image = FakeImageLoader()


class TestAssetManagerCacheContract(unittest.TestCase):
    def test_same_asset_key_reuses_cached_surface(self):
        pygame = FakePygame()
        manager = AssetManager(pygame)
        first = manager.load_image("flora.tree", "tree.png")
        second = manager.load_image("flora.tree", "tree.png")
        self.assertIs(first, second)
        self.assertEqual(pygame.image.calls, ["tree.png"])
        self.assertEqual(manager.image_count, 1)

    def test_clear_allows_asset_to_be_loaded_again(self):
        pygame = FakePygame()
        manager = AssetManager(pygame)
        manager.load_image("flora.tree", "tree.png")
        manager.clear()
        manager.load_image("flora.tree", "tree.png")
        self.assertEqual(pygame.image.calls, ["tree.png", "tree.png"])
        self.assertEqual(manager.image_count, 1)

    def test_failed_load_is_not_cached(self):
        pygame = FakePygame()
        pygame.image.fail = True
        manager = AssetManager(pygame)
        with self.assertRaises(OSError):
            manager.load_image("flora.tree", "tree.png")
        self.assertEqual(manager.image_count, 0)


if __name__ == "__main__":
    unittest.main()
