"""Deterministic terrain drawing for the isometric axial world."""
from __future__ import annotations

import math


class HexTerrainRenderer:
    TERRAIN_COLORS = {
        "grass": (76, 124, 66), "forest_floor": (49, 103, 62),
        "clearing_floor": (137, 119, 76), "water": (47, 102, 150),
        "soil": (112, 88, 58), "sand": (190, 166, 112),
        "rock": (105, 105, 99), "snow": (218, 226, 229),
        "swamp": (75, 91, 65),
    }
    BLOCKED_COLOR = (45, 65, 91)
    SELECTED_COLOR = (132, 157, 83)

    def __init__(self):
        self._scaled_textures = {}
        self._frame_surface_size = None

    def begin_frame(self, renderer, terrain_ids=()):
        """Paint one continuous ground base before individual cell surfaces."""
        colors = [self.TERRAIN_COLORS.get(item) for item in terrain_ids]
        colors = [item for item in colors if item is not None]
        base = colors[0] if colors else (74, 111, 68)
        surface = renderer.surface
        fill = getattr(surface, "fill", None)
        if callable(fill):
            fill(base)
        elif hasattr(renderer, "_fill"):
            renderer._fill(base)
        self._frame_surface_size = (renderer.width, renderer.height)

    def _scaled_texture(self, pg, texture, size):
        key = (id(texture), size)
        if key not in self._scaled_textures:
            self._scaled_textures[key] = (
                texture if texture.get_size() == (size, size)
                else pg.transform.smoothscale(texture, (size, size))
            )
        return self._scaled_textures[key]

    @staticmethod
    def is_visible(center, radius, width, height):
        x, y = center
        return not (
            x + radius < 0 or y + radius < 0
            or x - radius > width or y - radius > height
        )

    @staticmethod
    def polygon_for(center, radius):
        """Project a pointy-top world hex into a 2:1 isometric screen hex."""
        if radius <= 0:
            raise ValueError("radius must be greater than zero.")
        cx, cy = center
        points = []
        for index in range(6):
            angle = math.radians(-90 + index * 60)
            world_x = math.cos(angle) * radius
            world_y = math.sin(angle) * radius
            screen_x = world_x - world_y
            screen_y = (world_x + world_y) * 0.5
            points.append((round(cx + screen_x), round(cy + screen_y)))
        return tuple(points)

    def color_for(self, cell_data, selected=False):
        if selected:
            return self.SELECTED_COLOR
        if cell_data.blocked:
            return self.BLOCKED_COLOR
        return self.TERRAIN_COLORS.get(cell_data.terrain_id, (91, 105, 79))

    def draw_cell(
        self, renderer, cell, cell_data, center, radius,
        selected=False, image=None, images=(),
    ):
        pg = renderer.pg
        polygon = self.polygon_for(center, radius)
        seed = (cell.q * 73856093) ^ (cell.r * 19349663)
        base = self.color_for(cell_data, selected=selected)
        if not selected and not cell_data.blocked:
            variation = ((seed >> 3) % 7) - 3
            base = tuple(max(0, min(255, channel + variation)) for channel in base)
        pg.draw.polygon(renderer.surface, base, polygon)
        outline = tuple(max(0, round(channel * 0.72)) for channel in base)
        pg.draw.polygon(renderer.surface, outline, polygon, 1)

        textures = tuple(images) + ((image,) if image is not None else ())
        size = max(1, round(radius * 2.08))
        for texture in textures:
            renderer.surface.blit(
                self._scaled_texture(pg, texture, size),
                (round(center[0] - size / 2), round(center[1] - size / 2)),
            )

        detail = (
            (103, 148, 76)
            if cell_data.terrain_id == "grass"
            else (39, 86, 54)
        )
        if not textures and cell_data.terrain_id in (
            "grass", "forest_floor", "clearing_floor",
        ):
            for index in range(9):
                dx = ((seed >> (index * 4)) % 13 - 6) * radius / 22
                dy = ((seed >> (index * 6 + 1)) % 13 - 6) * radius / 22
                point = (
                    round(center[0] + dx - dy),
                    round(center[1] + (dx + dy) * 0.5),
                )
                pg.draw.circle(
                    renderer.surface, detail, point,
                    max(1, round(radius * 0.045)),
                )
        elif image is None and cell_data.terrain_id == "water":
            pg.draw.line(
                renderer.surface, (91, 166, 199),
                (round(center[0] - radius * .25), round(center[1])),
                (round(center[0] + radius * .25), round(center[1] - radius * .08)),
                max(1, round(radius * .04)),
            )
