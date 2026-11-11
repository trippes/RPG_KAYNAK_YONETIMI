"""Tests for target-resolution UI drawing adapters."""

import unittest

from game_ui.scaled_renderer import ScaledDraw, ScaledFont, ScaledSurface


class FakeRect:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height


class FakeFont:
    def __init__(self, _font_file, size):
        self.point_size = size

    def size(self, value):
        return (len(str(value)) * self.point_size, self.point_size)

    def render(self, value, antialias, color):
        return ("text", value, self.point_size, antialias, color)


class FakeDraw:
    def __init__(self):
        self.calls = []

    def rect(self, surface, color, rect, width=0, **kwargs):
        self.calls.append(("rect", surface, color, rect, width, kwargs))

    def circle(self, surface, color, center, radius, width=0):
        self.calls.append(("circle", surface, color, center, radius, width))

    def line(self, surface, color, start, end, width=1):
        self.calls.append(("line", surface, color, start, end, width))


class FakeSurface:
    def __init__(self, size=(400, 300)):
        self.size = size
        self.clip = FakeRect(0, 0, *size)
        self.calls = []

    def blit(self, source, destination, area=None, special_flags=0):
        self.calls.append(("blit", source, destination, area, special_flags))

    def fill(self, color, rect=None, special_flags=0):
        self.calls.append(("fill", color, rect, special_flags))

    def set_clip(self, rect=None):
        self.clip = rect or FakeRect(0, 0, *self.size)

    def get_clip(self):
        return self.clip

    def get_size(self):
        return self.size


class FakeBackend:
    Rect = FakeRect

    def __init__(self):
        self.draw = FakeDraw()
        self.font = type("FontModule", (), {"Font": FakeFont})


class ScaledRendererTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.surface = FakeSurface()

    def test_font_is_rasterized_at_target_scale_but_measured_logically(self):
        font = ScaledFont(self.backend, 24, 2.0)

        self.assertEqual(font.font.point_size, 48)
        self.assertEqual(font.size("AB"), (48, 24))
        self.assertEqual(font.render("AB", True, (255, 255, 255))[2], 48)

    def test_draw_primitives_scale_geometry_strokes_and_corner_radius(self):
        surface = ScaledSurface(self.surface, 2.0, self.backend)
        draw = ScaledDraw(self.backend.draw, 2.0, self.backend)

        draw.rect(surface, (1, 2, 3), FakeRect(10, 12, 30, 40), 2, border_radius=5)
        draw.circle(surface, (1, 2, 3), (20, 30), 7, 1)
        draw.line(surface, (1, 2, 3), (1, 2), (3, 4), 2)

        rect_call, circle_call, line_call = self.backend.draw.calls
        self.assertEqual(
            (rect_call[3].x, rect_call[3].y, rect_call[3].width, rect_call[3].height),
            (20, 24, 60, 80),
        )
        self.assertEqual(rect_call[4], 4)
        self.assertEqual(rect_call[5]["border_radius"], 10)
        self.assertEqual((circle_call[3], circle_call[4], circle_call[5]), ((40, 60), 14, 2))
        self.assertEqual((line_call[3], line_call[4], line_call[5]), ((2, 4), (6, 8), 4))

    def test_surface_blit_and_clip_use_the_same_scale(self):
        surface = ScaledSurface(self.surface, 1.5, self.backend)

        surface.blit("icon", (10, 20))
        surface.set_clip(FakeRect(4, 6, 20, 30))

        self.assertEqual(self.surface.calls[0][2], (15, 30))
        self.assertEqual(
            (self.surface.clip.x, self.surface.clip.y,
             self.surface.clip.width, self.surface.clip.height),
            (6, 9, 30, 45),
        )
        logical_clip = surface.get_clip()
        self.assertEqual(
            (logical_clip.x, logical_clip.y, logical_clip.width, logical_clip.height),
            (4, 6, 20, 30),
        )


if __name__ == "__main__":
    unittest.main()
