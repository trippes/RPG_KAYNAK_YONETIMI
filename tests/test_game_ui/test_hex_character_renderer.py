import unittest
from types import SimpleNamespace

from game_ui.world_rendering.character_renderer import HexCharacterRenderer


class FakeDraw:
    def __init__(self):
        self.calls = []
    def circle(self, *args, **kwargs):
        self.calls.append(("circle", args, kwargs))
    def line(self, *args, **kwargs):
        self.calls.append(("line", args, kwargs))
    def polygon(self, *args, **kwargs):
        self.calls.append(("polygon", args, kwargs))
    def rect(self, *args, **kwargs):
        self.calls.append(("rect", args, kwargs))


class TestHexCharacterRenderer(unittest.TestCase):
    def test_placeholder_draws_humanoid_parts_and_animates_stride(self):
        draw = FakeDraw()
        renderer = SimpleNamespace(pg=SimpleNamespace(draw=draw), surface=object())
        HexCharacterRenderer.draw(renderer, (100, 120), 32, 0.25, moving=True)
        self.assertGreaterEqual(len(draw.calls), 8)
        self.assertTrue(any(call[0] == "polygon" for call in draw.calls))
        self.assertTrue(any(call[0] == "line" for call in draw.calls))

    def test_debug_skeleton_draws_bounds_bones_joints_and_ground_anchor(self):
        draw = FakeDraw()
        pg = SimpleNamespace(draw=draw, Rect=lambda *args: args)
        renderer = SimpleNamespace(pg=pg, surface=object())
        HexCharacterRenderer.draw_debug_skeleton(renderer, (100, 120), 32)
        self.assertTrue(any(call[0] == "rect" for call in draw.calls))
        self.assertGreaterEqual(sum(call[0] == "line" for call in draw.calls), 8)
        self.assertGreaterEqual(sum(call[0] == "circle" for call in draw.calls), 8)


if __name__ == "__main__":
    unittest.main()
