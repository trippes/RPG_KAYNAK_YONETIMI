"""Pygame adapter that renders immutable VisualDocument values to alpha Surfaces."""
from __future__ import annotations
import hashlib
import pygame
from hex_world_lab.content.definition import ContentDefinition
from .cache import ProceduralSurfaceCache
from hex_world_lab.content.drawing import (
    CircleElement, EllipseElement, PolygonElement, PolylineElement, VisualDocument,
)
from .canvas import ProceduralCanvas
from .components import draw_circle, draw_ellipse, draw_polygon, draw_polyline
from .geometry import Point2D

def _color(document, token):
    return None if token is None else tuple(document.palette[token])

def render_visual_document(document: VisualDocument, *, supersampling: int = 3) -> pygame.Surface:
    if not isinstance(document, VisualDocument):
        raise TypeError("document must be a VisualDocument")
    canvas = ProceduralCanvas(tuple(round(v) for v in document.logical_size), supersampling)
    for layer in document.layers:
        for element in layer.elements:
            style = element.style
            fill, stroke = _color(document, style.fill), _color(document, style.stroke)
            if isinstance(element, PolygonElement):
                points = tuple(Point2D(p.x, p.y) for p in element.points)
                if fill is not None:
                    draw_polygon(canvas, fill, points)
                if stroke is not None and style.stroke_width > 0:
                    draw_polygon(canvas, stroke, points, max(1, round(style.stroke_width)))
            elif isinstance(element, EllipseElement):
                rect = (element.x, element.y, element.width, element.height)
                if fill is not None:
                    draw_ellipse(canvas, fill, rect)
                if stroke is not None and style.stroke_width > 0:
                    draw_ellipse(canvas, stroke, rect, max(1, round(style.stroke_width)))
            elif isinstance(element, CircleElement):
                center = Point2D(element.center.x, element.center.y)
                if fill is not None:
                    draw_circle(canvas, fill, center, element.radius)
                if stroke is not None and style.stroke_width > 0:
                    draw_circle(canvas, stroke, center, element.radius, max(1, round(style.stroke_width)))
            elif isinstance(element, PolylineElement):
                if stroke is None:
                    raise ValueError("polyline elements require a stroke palette token")
                draw_polyline(canvas, stroke, tuple(Point2D(p.x, p.y) for p in element.points),
                              max(1, round(style.stroke_width)), element.closed)
            else:
                raise TypeError(f"unsupported drawing element: {type(element).__name__}")
    return canvas.finish()

def render_content_definition(definition: ContentDefinition, *, cache: ProceduralSurfaceCache | None = None, supersampling: int = 3) -> pygame.Surface:
    """Render one reusable content definition, caching by canonical document identity."""
    if not isinstance(definition, ContentDefinition):
        raise TypeError("definition must be a ContentDefinition")
    if cache is not None and not isinstance(cache, ProceduralSurfaceCache):
        raise TypeError("cache must be a ProceduralSurfaceCache or None")
    digest = hashlib.sha256(repr(definition.visual_document).encode("utf-8")).hexdigest()
    def factory() -> pygame.Surface:
        return render_visual_document(definition.visual_document, supersampling=supersampling)

    key = ("visual-document-v1", digest, supersampling)
    return factory() if cache is None else cache.get_or_create(key, factory)
