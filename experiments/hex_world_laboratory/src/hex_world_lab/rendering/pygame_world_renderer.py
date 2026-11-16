"""Pygame renderer for immutable world-space visual snapshots."""

from __future__ import annotations

import pygame

from hex_world_lab.camera import WorldScreenTransform
from hex_world_lab.geometry import HexLayout, hex_polygon

from .snapshot import WorldRenderSnapshot

BACKGROUND = (21, 25, 34)
HEX_FILL = (42, 51, 65)
HEX_EDGE = (104, 121, 143)
ACTIVE_EDGE = (235, 190, 92)
SELECTED_EDGE = (116, 174, 235)
ACTOR_COLOR = (231, 93, 83)
CELL_OBSTACLE_FILL = (91, 66, 55)
OBJECT_CIRCLE_COLOR = (72, 122, 86)
OBJECT_POLYGON_COLOR = (112, 119, 132)
BOUNDARY_COLOR = (201, 160, 91)


class PygameWorldRenderer:
    """Draw a world snapshot through exactly one camera transform."""

    def render(
        self,
        surface: pygame.Surface,
        snapshot: WorldRenderSnapshot,
        layout: HexLayout,
        transform: WorldScreenTransform,
    ) -> None:
        if not isinstance(surface, pygame.Surface):
            raise TypeError("surface must be a pygame.Surface")
        if not isinstance(snapshot, WorldRenderSnapshot):
            raise TypeError("snapshot must be a WorldRenderSnapshot")
        if not isinstance(layout, HexLayout):
            raise TypeError("layout must be a HexLayout")
        if not isinstance(transform, WorldScreenTransform):
            raise TypeError("transform must be a WorldScreenTransform")

        surface.fill(BACKGROUND)

        for cell in snapshot.cells:
            points = self._points(hex_polygon(cell.coord, layout), transform)
            fill = CELL_OBSTACLE_FILL if cell.has_obstacle else HEX_FILL
            pygame.draw.polygon(surface, fill, points)
            if snapshot.selected_cell == cell.coord:
                edge = SELECTED_EDGE
            elif cell.is_active:
                edge = ACTIVE_EDGE
            else:
                edge = HEX_EDGE
            pygame.draw.polygon(surface, edge, points, width=max(1, round(transform.zoom)))

        for circle in snapshot.circles:
            center = self._point(circle.center, transform)
            radius = max(1, round(circle.radius * transform.zoom))
            outline = max(1, round(2 * transform.zoom))
            pygame.draw.circle(surface, OBJECT_CIRCLE_COLOR, center, radius)
            pygame.draw.circle(surface, (206, 224, 208), center, radius, width=outline)

        for polygon in snapshot.polygons:
            points = self._points(polygon.vertices, transform)
            fill = CELL_OBSTACLE_FILL if polygon.is_cell_obstacle else OBJECT_POLYGON_COLOR
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.polygon(
                surface, (205, 211, 222), points,
                width=max(1, round(2 * transform.zoom)),
            )

        for line in snapshot.house_lines:
            color = (190, 151, 103) if line.kind == "frame" else (225, 190, 139)
            pygame.draw.line(
                surface,
                color,
                self._point(line.start, transform),
                self._point(line.end, transform),
                max(1, round(line.width * transform.zoom)),
            )

        for line in snapshot.boundaries:
            pygame.draw.line(
                surface,
                BOUNDARY_COLOR,
                self._point(line.start, transform),
                self._point(line.end, transform),
                max(1, round(line.width * transform.zoom)),
            )

        actor = self._point(snapshot.actor_position, transform)
        radius = max(1, round(snapshot.actor_radius * transform.zoom))
        pygame.draw.circle(surface, ACTOR_COLOR, actor, radius)
        pygame.draw.circle(
            surface, (255, 235, 225), actor, radius,
            width=max(1, round(2 * transform.zoom)),
        )

    @staticmethod
    def _point(point, transform: WorldScreenTransform) -> tuple[int, int]:
        screen = transform.world_to_screen(point)
        return round(screen.x), round(screen.y)

    @classmethod
    def _points(cls, points, transform: WorldScreenTransform) -> list[tuple[int, int]]:
        return [cls._point(point, transform) for point in points]
