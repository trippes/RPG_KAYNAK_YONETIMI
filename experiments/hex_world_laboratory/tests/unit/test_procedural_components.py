import pygame
import pytest

from hex_world_lab.rendering.procedural.canvas import ProceduralCanvas
from hex_world_lab.rendering.procedural.components import (
    draw_circle,
    draw_ellipse,
    draw_polygon,
    draw_polyline,
)
from hex_world_lab.rendering.procedural.geometry import Point2D


def test_drawing_components_render_into_canvas_surface():
    canvas = ProceduralCanvas((24, 20), supersampling=2)
    draw_ellipse(canvas, (20, 80, 40, 255), (1, 1, 8, 5))
    draw_polygon(
        canvas, (180, 90, 30, 255),
        (Point2D(10, 2), Point2D(18, 2), Point2D(14, 9)),
    )
    draw_polyline(
        canvas, (255, 255, 255, 255),
        (Point2D(2, 12), Point2D(8, 16), Point2D(14, 12)), width=1,
    )
    draw_circle(canvas, (40, 80, 200, 255), Point2D(19, 15), 3)
    assert pygame.mask.from_surface(canvas.surface).count() > 0


def test_components_reject_invalid_geometry_and_color():
    canvas = ProceduralCanvas((10, 10))
    with pytest.raises(ValueError):
        draw_polygon(canvas, (0, 0, 0), (Point2D(0, 0), Point2D(1, 1)))
    with pytest.raises(ValueError):
        draw_circle(canvas, (0, 0, 0), Point2D(2, 2), -1)
    with pytest.raises(ValueError):
        draw_ellipse(canvas, (256, 0, 0), (0, 0, 2, 2))
    with pytest.raises(ValueError):
        draw_polyline(canvas, (0, 0, 0), (Point2D(0, 0), Point2D(1, 1)), width=0)


def test_component_draw_calls_preserve_transparent_background():
    canvas = ProceduralCanvas((10, 10))
    draw_circle(canvas, (255, 0, 0, 255), Point2D(5, 5), 2)
    assert canvas.surface.get_at((0, 0)).a == 0
    assert canvas.surface.get_at((15, 15)).a == 255
