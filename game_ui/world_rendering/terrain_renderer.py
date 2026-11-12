"""Deterministic terrain-cell drawing for the axial world view."""
from __future__ import annotations
import math

class HexTerrainRenderer:
    TERRAIN_COLORS = {"grass": (83, 132, 73), "forest_floor": (49, 103, 62), "clearing_floor": (137, 119, 76), "water": (47, 102, 150)}
    BLOCKED_COLOR = (45, 65, 91)
    SELECTED_COLOR = (132, 157, 83)

    @staticmethod
    def polygon_for(center, radius):
        if radius <= 0:
            raise ValueError("radius must be greater than zero.")
        cx, cy = center
        return tuple((round(cx + math.cos(math.radians(-90 + i * 60)) * radius), round(cy + math.sin(math.radians(-90 + i * 60)) * radius)) for i in range(6))

    def color_for(self, cell_data, selected=False):
        if selected:
            return self.SELECTED_COLOR
        if cell_data.blocked:
            return self.BLOCKED_COLOR
        return self.TERRAIN_COLORS.get(cell_data.terrain_id, (91, 105, 79))

    def draw_cell(self, renderer, cell, cell_data, center, radius, selected=False):
        pg = renderer.pg
        polygon = self.polygon_for(center, radius)
        base = self.color_for(cell_data, selected)
        shadow = tuple((x, y + max(2, round(radius * 0.08))) for x, y in polygon)
        pg.draw.polygon(renderer.surface, (24, 34, 29), shadow)
        pg.draw.polygon(renderer.surface, base, polygon)
        seed = (cell.q * 73856093) ^ (cell.r * 19349663)
        detail = (111, 157, 83) if cell_data.terrain_id == "grass" else (39, 86, 54)
        if cell_data.terrain_id in ("grass", "forest_floor", "clearing_floor"):
            for index in range(3):
                dx = ((seed >> (index * 4)) % 13 - 6) * radius / 22
                dy = ((seed >> (index * 6 + 1)) % 13 - 6) * radius / 22
                pg.draw.circle(renderer.surface, detail, (round(center[0] + dx), round(center[1] + dy)), max(1, round(radius * 0.045)))
        elif cell_data.terrain_id == "water":
            pg.draw.line(renderer.surface, (91, 166, 199), (round(center[0] - radius * .25), round(center[1])), (round(center[0] + radius * .25), round(center[1] - radius * .08)), max(1, round(radius * .04)))
        pg.draw.polygon(renderer.surface, (35, 48, 38), polygon, max(1, round(radius * .055)))
