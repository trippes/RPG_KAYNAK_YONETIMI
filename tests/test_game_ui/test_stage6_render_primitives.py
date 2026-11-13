import unittest
from types import SimpleNamespace

from game_ui.world_rendering.depth_sorter import DepthSorter
from game_ui.world_rendering.character_renderer import HexCharacterRenderer
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer


class FakeDraw:
    def polygon(self, *args, **kwargs):
        pass
    def circle(self, *args, **kwargs):
        self.calls.append(("circle", args, kwargs))
    def __init__(self):
        self.calls = []
    def line(self, *args, **kwargs):
        pass


class FakeImage:
    def get_size(self):
        return (64, 64)


class TestStage6RenderPrimitives(unittest.TestCase):
    def test_depth_sort_uses_ground_anchor_and_stable_secondary_key(self):
        items = [
            SimpleNamespace(name="late", depth=20, stable=2),
            SimpleNamespace(name="first", depth=10, stable=1),
            SimpleNamespace(name="second", depth=10, stable=2),
        ]
        result = DepthSorter.sort_by_depth(items, lambda item: item.depth, lambda item: item.stable)
        self.assertEqual([item.name for item in result], ["first", "second", "late"])

    def test_depth_sort_preserves_equal_key_input_order(self):
        items = ["a", "b", "c"]
        self.assertEqual(DepthSorter.sort_by_depth(items, lambda item: 1), ("a", "b", "c"))

    def test_sprite_draw_uses_normalized_foot_anchor(self):
        calls = []
        surface = SimpleNamespace(blit=lambda image, position: calls.append((image, position)))
        transform = SimpleNamespace(smoothscale=lambda image, size: FakeImage())
        renderer = SimpleNamespace(surface=surface, pg=SimpleNamespace(transform=transform))
        HexCharacterRenderer.draw_sprite(renderer, FakeImage(), (100, 100), 64, (0.5, 1.0))
        self.assertEqual(calls[0][1], (68, 36))

    def test_terrain_image_path_blits_without_hex_outline(self):
        calls = []
        draw = FakeDraw()
        surface = SimpleNamespace(blit=lambda image, position: calls.append(position))
        renderer = SimpleNamespace(pg=SimpleNamespace(draw=draw), surface=surface)
        cell = SimpleNamespace(terrain_id="grass", blocked=False)
        HexTerrainRenderer().draw_cell(renderer, SimpleNamespace(q=0, r=0), cell,
                                       (100, 100), 32, image=FakeImage())
        self.assertEqual(calls, [(67, 67)])
        self.assertTrue(any(call[0] == "circle" for call in draw.calls))


if __name__ == "__main__":
    unittest.main()
