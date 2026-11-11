"""High-DPI drawing adapters for logical-coordinate gameplay screens.

Screens keep their existing design-space geometry and hitboxes. Drawing calls
are translated to a target-resolution surface, while fonts are rasterized at
the target scale instead of enlarging a low-resolution screenshot.
"""

from __future__ import annotations

import math


def _round(value):
    return int(round(value))


def _scale_point(point, scale):
    return (_round(point[0] * scale), _round(point[1] * scale))


def _scale_rect(rect, scale, backend):
    return backend.Rect(
        _round(rect.x * scale),
        _round(rect.y * scale),
        max(0, _round(rect.width * scale)),
        max(0, _round(rect.height * scale)),
    )


class ScaledFont:
    """Keep layout measurements logical while rasterizing text at target DPI."""

    def __init__(self, backend, point_size, scale):
        self.scale = scale
        self.font = backend.font.Font(None, max(1, _round(point_size * scale)))

    def size(self, value):
        width, height = self.font.size(str(value))
        return (_round(width / self.scale), _round(height / self.scale))

    def render(self, *args, **kwargs):
        return self.font.render(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.font, name)


class ScaledSurface:
    """Surface facade accepting logical coordinates and drawing at target DPI."""

    def __init__(self, surface, scale, backend):
        self._surface = surface
        self._scale = scale
        self._backend = backend

    def blit(self, source, destination, area=None, special_flags=0):
        if hasattr(destination, "x"):
            destination = _scale_rect(destination, self._scale, self._backend)
        else:
            destination = _scale_point(destination, self._scale)
        if area is not None:
            area = _scale_rect(area, self._scale, self._backend)
        return self._surface.blit(source, destination, area, special_flags)

    def fill(self, color, rect=None, special_flags=0):
        if rect is not None:
            rect = _scale_rect(rect, self._scale, self._backend)
        return self._surface.fill(color, rect, special_flags)

    def set_clip(self, rect=None):
        if rect is not None:
            rect = _scale_rect(rect, self._scale, self._backend)
        return self._surface.set_clip(rect)

    def get_clip(self):
        rect = self._surface.get_clip()
        return self._backend.Rect(
            _round(rect.x / self._scale),
            _round(rect.y / self._scale),
            _round(rect.width / self._scale),
            _round(rect.height / self._scale),
        )

    def get_size(self):
        width, height = self._surface.get_size()
        return (_round(width / self._scale), _round(height / self._scale))

    def __getattr__(self, name):
        return getattr(self._surface, name)


class ScaledDraw:
    """Scale pygame draw primitive geometry without changing logical Rects."""

    _RECT_PRIMITIVES = {"rect", "ellipse", "arc"}
    _POINT_PRIMITIVES = {"line", "aaline"}
    _POINT_LIST_PRIMITIVES = {"polygon"}
    _LINE_LIST_PRIMITIVES = {"lines", "aalines"}

    def __init__(self, draw, scale, backend):
        self._draw = draw
        self._scale = scale
        self._backend = backend

    def __getattr__(self, name):
        primitive = getattr(self._draw, name)
        if name not in (
            self._RECT_PRIMITIVES
            | self._POINT_PRIMITIVES
            | self._POINT_LIST_PRIMITIVES
            | self._LINE_LIST_PRIMITIVES
            | {"circle"}
        ):
            return primitive

        def scaled(*args, **kwargs):
            values = list(args)
            if values and isinstance(values[0], ScaledSurface):
                values[0] = values[0]._surface

            if name in self._RECT_PRIMITIVES and len(values) >= 3:
                values[2] = _scale_rect(values[2], self._scale, self._backend)
            elif name in self._POINT_PRIMITIVES and len(values) >= 4:
                values[2] = _scale_point(values[2], self._scale)
                values[3] = _scale_point(values[3], self._scale)
            elif name in self._POINT_LIST_PRIMITIVES and len(values) >= 3:
                values[2] = [_scale_point(point, self._scale) for point in values[2]]
            elif name in self._LINE_LIST_PRIMITIVES and len(values) >= 4:
                values[3] = [_scale_point(point, self._scale) for point in values[3]]
            elif name == "circle" and len(values) >= 4:
                values[2] = _scale_point(values[2], self._scale)
                values[3] = max(1, _round(values[3] * self._scale))

            # Pygame's optional line width is the last positional argument for
            # these primitives; zero remains zero because it means filled.
            if name in {"rect", "ellipse", "arc", "line", "aaline", "lines", "aalines", "polygon", "circle"}:
                width_index = {
                    "rect": 3, "ellipse": 3, "arc": 6,
                    "line": 4, "aaline": None, "lines": 4,
                    "aalines": None, "polygon": 3, "circle": 4,
                }[name]
                if width_index is not None and len(values) > width_index:
                    width = values[width_index]
                    values[width_index] = 0 if width == 0 else max(1, _round(width * self._scale))
                elif "width" in kwargs:
                    width = kwargs["width"]
                    kwargs["width"] = 0 if width == 0 else max(1, _round(width * self._scale))

            if "border_radius" in kwargs:
                kwargs["border_radius"] = max(0, _round(kwargs["border_radius"] * self._scale))
            return primitive(*values, **kwargs)

        return scaled


class ScaledPygame:
    """Expose logical Rect construction and high-DPI drawing primitives."""

    def __init__(self, backend, scale):
        self._backend = backend
        self.draw = ScaledDraw(backend.draw, scale, backend)

    def __getattr__(self, name):
        return getattr(self._backend, name)
