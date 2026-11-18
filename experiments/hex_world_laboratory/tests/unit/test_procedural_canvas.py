import pygame
import pytest
from hex_world_lab.rendering.procedural.canvas import ProceduralCanvas
from hex_world_lab.rendering.procedural.geometry import Point2D


def test_canvas_creates_supersampled_alpha_surface_without_display():
    display_was_initialized = pygame.display.get_init()
    canvas = ProceduralCanvas((20, 12))
    assert pygame.display.get_init() is display_was_initialized
    assert canvas.pixel_size == (60, 36)
    assert canvas.surface.get_flags() & pygame.SRCALPHA
    assert canvas.surface.get_bitsize() == 32


def test_canvas_maps_logical_points_and_rectangles_to_pixel_coordinates():
    canvas = ProceduralCanvas((20, 12), supersampling=3)
    assert canvas.point(Point2D(1.5, 2)) == (4, 6)
    assert canvas.rect((1, 2, 3, 4)) == pygame.Rect(3, 6, 9, 12)


def test_canvas_finish_returns_logical_size_and_preserves_alpha():
    canvas = ProceduralCanvas((8, 6), supersampling=3)
    pygame.draw.circle(canvas.surface, (220, 80, 40, 255), (12, 9), 6)
    result = canvas.finish()
    assert result.get_size() == (8, 6)
    assert result.get_flags() & pygame.SRCALPHA
    assert result.get_at((0, 0)).a == 0
    assert result.get_at((4, 3)).a > 0


def test_canvas_can_finalize_to_explicit_output_size():
    canvas = ProceduralCanvas((8, 6), supersampling=2)
    assert canvas.finish((16, 12)).get_size() == (16, 12)


@pytest.mark.parametrize("size", [(0, 1), (1, -1), (1.5, 2), (True, 2)])
def test_canvas_rejects_invalid_logical_size(size):
    with pytest.raises((TypeError, ValueError)):
        ProceduralCanvas(size)


@pytest.mark.parametrize("scale", [0, -1, True, 1.5])
def test_canvas_rejects_invalid_supersampling(scale):
    with pytest.raises((TypeError, ValueError)):
        ProceduralCanvas((2, 2), supersampling=scale)


def test_canvas_rejects_invalid_rectangle():
    canvas = ProceduralCanvas((4, 4))
    with pytest.raises(ValueError):
        canvas.rect((0, 0, -1, 2))
