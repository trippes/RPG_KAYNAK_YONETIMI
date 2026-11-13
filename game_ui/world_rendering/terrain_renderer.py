"""Deterministic, image-capable terrain drawing for the axial world view."""
from __future__ import annotations
import math

class HexTerrainRenderer:
    TERRAIN_COLORS = {
        "grass": (83, 132, 73), "forest_floor": (49, 103, 62),
        "clearing_floor": (137, 119, 76), "water": (47, 102, 150),
        "soil": (112, 88, 58), "sand": (190, 166, 112),
        "rock": (105, 105, 99), "snow": (218, 226, 229),
        "swamp": (75, 91, 65),
    }
    BLOCKED_COLOR = (45, 65, 91)
    SELECTED_COLOR = (132, 157, 83)

    @staticmethod
    def is_visible(center, radius, width, height):
        x, y = center
        return not (x + radius < 0 or y + radius < 0 or x - radius > width or y - radius > height)

    @staticmethod
    def polygon_for(center, radius):
        if radius <= 0:
            raise ValueError("radius must be greater than zero.")
        cx, cy = center
        return tuple((round(cx + math.cos(math.radians(-90 + i * 60)) * radius),
                      round(cy + math.sin(math.radians(-90 + i * 60)) * radius))
                     for i in range(6))

    def color_for(self, cell_data, selected=False):
        if selected:
            return self.SELECTED_COLOR
        if cell_data.blocked:
            return self.BLOCKED_COLOR
        return self.TERRAIN_COLORS.get(cell_data.terrain_id, (91, 105, 79))

    def draw_cell(self, renderer, cell, cell_data, center, radius, selected=False, image=None, images=()):
        pg = renderer.pg
        polygon = self.polygon_for(center, radius)
        base = self.color_for(cell_data, selected)
        shadow = tuple((x, y + max(2, round(radius * 0.08))) for x, y in polygon)
        pg.draw.polygon(renderer.surface, (24, 34, 29), shadow)
        pg.draw.polygon(renderer.surface, base, polygon)
        textures = tuple(images) + ((image,) if image is not None else ())
        size = max(1, round(radius * 2))
        for texture in textures:
            current = texture
            if current.get_size() != (size, size):
                current = pg.transform.smoothscale(current, (size, size))
            renderer.surface.blit(current, (round(center[0] - radius), round(center[1] - radius)))
        seed = (cell.q * 73856093) ^ (cell.r * 19349663)
        detail = (111, 157, 83) if cell_data.terrain_id == "grass" else (39, 86, 54)
        if not textures and cell_data.terrain_id in ("grass", "forest_floor", "clearing_floor"):
            for index in range(3):
                dx = ((seed >> (index * 4)) % 13 - 6) * radius / 22
                dy = ((seed >> (index * 6 + 1)) % 13 - 6) * radius / 22
                pg.draw.circle(renderer.surface, detail,
                               (round(center[0] + dx), round(center[1] + dy)),
                               max(1, round(radius * 0.045)))
        elif image is None and cell_data.terrain_id == "water":
            pg.draw.line(renderer.surface, (91, 166, 199),
                         (round(center[0] - radius * .25), round(center[1])),
                         (round(center[0] + radius * .25), round(center[1] - radius * .08)),
                         max(1, round(radius * .04)))
        # Deliberately omit a high-contrast hex outline: cell edges are data,
        # not a visual grid the player should perceive.
