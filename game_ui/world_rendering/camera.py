"""Smooth player-follow and edge-scroll camera for the hex-world presentation."""
from __future__ import annotations

import math


class HexCamera:
    """Time-based camera that follows the rendered actor or edge-scrolls freely."""

    EDGE_MARGIN = 22.0
    EDGE_SPEED = 360.0
    FOLLOW_RATE = 8.0

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.initialized = False
        self.free_look = False

    @staticmethod
    def _clamp_axis(value, low, high, half_view):
        if high - low <= half_view * 2:
            return (low + high) / 2.0
        return max(low + half_view, min(high - half_view, value))

    def update(
        self, target, mouse_position, viewport_size, world_bounds, zoom,
        elapsed_seconds, *, projection="cartesian",
    ):
        """Advance camera state; bounds and position remain in world coordinates.

        For the 2:1 isometric projection, a rectangular screen viewport maps to
        a diamond in world space. Its conservative half extent is the screen
        half-height plus half the screen half-width on both world axes.
        """
        dt = max(0.0, min(float(elapsed_seconds), 0.1))
        if not self.initialized:
            self.x, self.y = map(float, target)
            self.initialized = True

        width, height = viewport_size
        min_x, min_y, max_x, max_y = world_bounds
        half_width = width / (2.0 * zoom)
        half_height = height / (2.0 * zoom)
        if projection == "isometric":
            half_view_x = half_height + half_width * 0.5
            half_view_y = half_height + half_width * 0.5
        elif projection == "cartesian":
            half_view_x, half_view_y = half_width, half_height
        else:
            raise ValueError("projection must be 'isometric' or 'cartesian'.")

        dx = dy = 0.0
        if mouse_position is not None:
            mx, my = mouse_position
            if mx <= self.EDGE_MARGIN:
                dx = -1.0
            elif mx >= width - self.EDGE_MARGIN:
                dx = 1.0
            if my <= self.EDGE_MARGIN:
                dy = -1.0
            elif my >= height - self.EDGE_MARGIN:
                dy = 1.0

        self.free_look = bool(dx or dy)
        if self.free_look and dt:
            if projection == "isometric":
                world_dx = dx * 0.5 + dy
                world_dy = dy - dx * 0.5
            else:
                world_dx, world_dy = dx, dy
            length = math.hypot(world_dx, world_dy) or 1.0
            self.x += (world_dx / length) * self.EDGE_SPEED * dt / zoom
            self.y += (world_dy / length) * self.EDGE_SPEED * dt / zoom
        elif dt:
            blend = 1.0 - math.exp(-self.FOLLOW_RATE * dt)
            self.x += (float(target[0]) - self.x) * blend
            self.y += (float(target[1]) - self.y) * blend

        self.x = self._clamp_axis(self.x, min_x, max_x, half_view_x)
        self.y = self._clamp_axis(self.y, min_y, max_y, half_view_y)
        return self.x, self.y
