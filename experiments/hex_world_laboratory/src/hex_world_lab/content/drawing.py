"""Versioned, immutable vector drawing documents; deliberately Pygame-free."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TypeAlias
from .values import finite_number, non_empty_id, freeze_json

@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float
    def __post_init__(self):
        object.__setattr__(self, "x", finite_number(self.x, "point.x"))
        object.__setattr__(self, "y", finite_number(self.y, "point.y"))

@dataclass(frozen=True, slots=True)
class DrawingStyle:
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float = 1.0
    def __post_init__(self):
        if self.fill is None and self.stroke is None:
            raise ValueError("a drawing style requires fill or stroke")
        for name in ("fill", "stroke"):
            value = getattr(self, name)
            if value is not None:
                non_empty_id(value, f"style.{name}")
        width = finite_number(self.stroke_width, "style.stroke_width")
        if width < 0:
            raise ValueError("stroke_width must not be negative")
        object.__setattr__(self, "stroke_width", width)

@dataclass(frozen=True, slots=True)
class PolygonElement:
    element_id: str
    points: tuple[Point, ...]
    style: DrawingStyle
    def __post_init__(self):
        non_empty_id(self.element_id, "element_id")
        points = tuple(self.points)
        if len(points) < 3 or any(not isinstance(p, Point) for p in points):
            raise ValueError("polygon requires at least three Point values")
        object.__setattr__(self, "points", points)
        if not isinstance(self.style, DrawingStyle):
            raise TypeError("style must be DrawingStyle")

@dataclass(frozen=True, slots=True)
class EllipseElement:
    element_id: str
    x: float
    y: float
    width: float
    height: float
    style: DrawingStyle
    def __post_init__(self):
        non_empty_id(self.element_id, "element_id")
        for name in ("x", "y", "width", "height"):
            value = finite_number(getattr(self, name), name)
            if name in ("width", "height") and value <= 0:
                raise ValueError(f"{name} must be positive")
            object.__setattr__(self, name, value)
        if not isinstance(self.style, DrawingStyle):
            raise TypeError("style must be DrawingStyle")

@dataclass(frozen=True, slots=True)
class CircleElement:
    element_id: str
    center: Point
    radius: float
    style: DrawingStyle
    def __post_init__(self):
        non_empty_id(self.element_id, "element_id")
        if not isinstance(self.center, Point):
            raise TypeError("center must be Point")
        radius = finite_number(self.radius, "radius")
        if radius <= 0:
            raise ValueError("radius must be positive")
        object.__setattr__(self, "radius", radius)
        if not isinstance(self.style, DrawingStyle):
            raise TypeError("style must be DrawingStyle")

@dataclass(frozen=True, slots=True)
class PolylineElement:
    element_id: str
    points: tuple[Point, ...]
    style: DrawingStyle
    closed: bool = False
    def __post_init__(self):
        non_empty_id(self.element_id, "element_id")
        points = tuple(self.points)
        if len(points) < 2 or any(not isinstance(p, Point) for p in points):
            raise ValueError("polyline requires at least two Point values")
        if not isinstance(self.closed, bool):
            raise TypeError("closed must be bool")
        object.__setattr__(self, "points", points)
        if not isinstance(self.style, DrawingStyle):
            raise TypeError("style must be DrawingStyle")

DrawingElement: TypeAlias = PolygonElement | EllipseElement | CircleElement | PolylineElement

@dataclass(frozen=True, slots=True)
class Layer:
    layer_id: str
    order: int
    elements: tuple[DrawingElement, ...]
    def __post_init__(self):
        non_empty_id(self.layer_id, "layer_id")
        if isinstance(self.order, bool) or not isinstance(self.order, int):
            raise TypeError("layer order must be an integer")
        elements = tuple(self.elements)
        if any(not isinstance(item, (PolygonElement, EllipseElement, CircleElement, PolylineElement)) for item in elements):
            raise TypeError("layer contains an unsupported drawing element")
        ids = [item.element_id for item in elements]
        if len(ids) != len(set(ids)):
            raise ValueError("element IDs must be unique within a layer")
        object.__setattr__(self, "elements", elements)

@dataclass(frozen=True, slots=True)
class VisualDocument:
    logical_size: tuple[float, float]
    ground_anchor: tuple[float, float]
    depth_anchor: tuple[float, float]
    palette: object
    layers: tuple[Layer, ...]
    document_version: int = 1
    generator: object | None = None
    def __post_init__(self):
        if isinstance(self.document_version, bool) or self.document_version != 1:
            raise ValueError("only VisualDocument version 1 is supported")
        if len(self.logical_size) != 2:
            raise ValueError("logical_size requires width and height")
        size = tuple(finite_number(v, "logical_size") for v in self.logical_size)
        if any(v <= 0 for v in size):
            raise ValueError("logical_size values must be positive")
        object.__setattr__(self, "logical_size", size)
        for name in ("ground_anchor", "depth_anchor"):
            pair = tuple(finite_number(v, name) for v in getattr(self, name))
            if len(pair) != 2 or any(not 0 <= v <= 1 for v in pair):
                raise ValueError(f"{name} must be a normalized pair")
            object.__setattr__(self, name, pair)
        palette = dict(self.palette)
        if not palette:
            raise ValueError("palette must not be empty")
        for token, color in palette.items():
            non_empty_id(token, "palette token")
            if not isinstance(color, (tuple, list)) or len(color) not in (3, 4):
                raise ValueError(f"palette[{token}] must be RGB or RGBA")
            if any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 255 for c in color):
                raise ValueError(f"palette[{token}] channels must be integers from 0 to 255")
            palette[token] = tuple(color)
        object.__setattr__(self, "palette", freeze_json(palette))
        layers = tuple(self.layers)
        if any(not isinstance(layer, Layer) for layer in layers):
            raise TypeError("layers must contain Layer values")
        layer_ids = [layer.layer_id for layer in layers]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("layer IDs must be unique")
        element_ids = [element.element_id for layer in layers for element in layer.elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("element IDs must be unique across the document")
        for layer in layers:
            for element in layer.elements:
                for token in (element.style.fill, element.style.stroke):
                    if token is not None and token not in palette:
                        raise ValueError(f"unknown palette token: {token}")
        object.__setattr__(self, "layers", tuple(sorted(layers, key=lambda item: item.order)))
        if self.generator is not None:
            object.__setattr__(self, "generator", freeze_json(self.generator))
