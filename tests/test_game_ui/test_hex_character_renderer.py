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


class TestHexCharacterRenderer(unittest.TestCase):
    def test_placeholder_draws_humanoid_parts_and_animates_stride(self):
        draw = FakeDraw()
        renderer = SimpleNamespace(pg=SimpleNamespace(draw=draw), surface=object())
        HexCharacterRenderer.draw(renderer, (100, 120), 32, 0.25, moving=True)
        self.assertGreaterEqual(len(draw.calls), 8)
        self.assertTrue(any(call[0] == "polygon" for call in draw.calls))
        self.assertTrue(any(call[0] == "line" for call in draw.calls))


if __name__ == "__main__":
    unittest.main()
