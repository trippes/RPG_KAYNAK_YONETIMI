"""Pygame renderer for immutable world-space visual snapshots."""

from __future__ import annotations
from dataclasses import dataclass
import math
from collections.abc import Mapping
import pygame

from hex_world_lab.camera import WorldScreenTransform
from hex_world_lab.geometry import HexLayout, axial_to_world, hex_polygon, WorldPoint
from .snapshot import CircleVisual, ColliderVisual, PolygonVisual, SpriteVisual, WorldRenderSnapshot

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
DEBUG_CENTER = (255, 224, 120)
DEBUG_COLLIDER = (235, 91, 204)


@dataclass(frozen=True, slots=True)
class SpriteAsset:
    """Pygame image and normalized foot-anchor coordinates."""
    surface: pygame.Surface
    foot_anchor_x: float = 0.5
    foot_anchor_y: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.surface, pygame.Surface):
            raise TypeError("surface must be a pygame.Surface")
        if not (math.isfinite(self.foot_anchor_x) and 0.0 <= self.foot_anchor_x <= 1.0):
            raise ValueError("foot_anchor_x must be between 0 and 1")
        if not (math.isfinite(self.foot_anchor_y) and 0.0 <= self.foot_anchor_y <= 1.0):
            raise ValueError("foot_anchor_y must be between 0 and 1")


class PygameWorldRenderer:
    """Draw a world snapshot through exactly one camera transform."""

    def __init__(self, sprite_assets: Mapping[str, SpriteAsset] | None = None) -> None:
        self._sprite_assets = dict(sprite_assets or {})
        self._font: pygame.font.Font | None = None

    def register_sprite_asset(self, asset_key: str, asset: SpriteAsset) -> None:
        if not isinstance(asset_key, str) or not asset_key.strip():
            raise ValueError("asset_key must be a non-empty string")
        if not isinstance(asset, SpriteAsset):
            raise TypeError("asset must be a SpriteAsset")
        self._sprite_assets[asset_key] = asset

    def render(self, surface: pygame.Surface, snapshot: WorldRenderSnapshot,
               layout: HexLayout, transform: WorldScreenTransform) -> None:
        if not isinstance(surface, pygame.Surface):
            raise TypeError("surface must be a pygame.Surface")
        if not isinstance(snapshot, WorldRenderSnapshot):
            raise TypeError("snapshot must be a WorldRenderSnapshot")
        if not isinstance(layout, HexLayout):
            raise TypeError("layout must be a HexLayout")
        if not isinstance(transform, WorldScreenTransform):
            raise TypeError("transform must be a WorldScreenTransform")

        surface.fill(BACKGROUND)
        options = snapshot.debug_options
        for cell in snapshot.cells:
            center_world = axial_to_world(cell.coord, layout)
            points = self._points(hex_polygon(cell.coord, layout), transform)
            fill = CELL_OBSTACLE_FILL if cell.has_obstacle else HEX_FILL
            pygame.draw.polygon(surface, fill, points)
            if options.show_hex_edges:
                edge = (
                    SELECTED_EDGE if snapshot.selected_cell == cell.coord
                    else ACTIVE_EDGE if cell.is_active
                    else (88, 215, 225) if options.show_culling_debug
                    else HEX_EDGE
                )
                pygame.draw.polygon(surface, edge, points, width=max(1, round(transform.zoom)))
            if options.show_cell_centers:
                pygame.draw.circle(surface, DEBUG_CENTER, self._point(center_world, transform), 3)
            if options.show_coordinate_labels:
                self._draw_cell_label(surface, cell.coord.q, cell.coord.r, center_world, transform)

        for line in snapshot.house_lines:
            color = (190, 151, 103) if line.kind == "frame" else (225, 190, 139)
            pygame.draw.line(surface, color, self._point(line.start, transform),
                             self._point(line.end, transform), max(1, round(line.width * transform.zoom)))
        for line in snapshot.boundaries:
            pygame.draw.line(surface, BOUNDARY_COLOR, self._point(line.start, transform),
                             self._point(line.end, transform), max(1, round(line.width * transform.zoom)))

        # Ground props, sprites and actor share one stable depth queue.
        draw_items = []
        for index, circle in enumerate(snapshot.circles):
            draw_items.append(((-circle.center.y, 20, f"circle:{index:08d}"), "circle", circle))
        for index, polygon in enumerate(snapshot.polygons):
            anchor_y = sum(point.y for point in polygon.vertices) / len(polygon.vertices)
            draw_items.append(((-anchor_y, 20, f"polygon:{index:08d}"), "polygon", polygon))
        for sprite in snapshot.sprites:
            draw_items.append(((-sprite.depth_anchor_y, sprite.layer_priority, sprite.visual_id), "sprite", sprite))
        draw_items.append(((-snapshot.actor_position.y, 30, "actor-anchor"), "actor", snapshot))

        for _, kind, item in sorted(draw_items, key=lambda entry: entry[0]):
            if kind == "circle":
                self._draw_circle(surface, item, transform)
            elif kind == "polygon":
                self._draw_polygon(surface, item, transform)
            elif kind == "sprite":
                self._draw_sprite(surface, item, transform)
            else:
                marker = self._point(snapshot.actor_position, transform)
                radius = max(2, round(min(snapshot.actor_radius, 4.0) * transform.zoom))
                pygame.draw.circle(surface, ACTOR_COLOR, marker, radius)

        if options.show_collider_debug:
            for collider in snapshot.colliders:
                self._draw_collider(surface, collider, transform)
        if options.show_culling_debug:
            # The conservative culling AABB includes a hex-radius safety margin
            # and lies just outside the viewport; highlight visible cells and
            # the actual viewport boundary so the active draw region is clear.
            pygame.draw.rect(
                surface, (88, 215, 225), surface.get_rect().inflate(-2, -2), 1
            )

    def _draw_circle(self, surface, circle: CircleVisual, transform: WorldScreenTransform) -> None:
        center = self._point(circle.center, transform)
        radius = max(1, round(circle.radius * transform.zoom))
        pygame.draw.circle(surface, OBJECT_CIRCLE_COLOR, center, radius)
        pygame.draw.circle(surface, (206, 224, 208), center, radius,
                           width=max(1, round(2 * transform.zoom)))

    def _draw_polygon(self, surface, polygon: PolygonVisual, transform: WorldScreenTransform) -> None:
        points = self._points(polygon.vertices, transform)
        fill = CELL_OBSTACLE_FILL if polygon.is_cell_obstacle else OBJECT_POLYGON_COLOR
        pygame.draw.polygon(surface, fill, points)
        pygame.draw.polygon(surface, (205, 211, 222), points,
                            width=max(1, round(2 * transform.zoom)))

    def _draw_sprite(self, surface, sprite: SpriteVisual, transform: WorldScreenTransform) -> None:
        asset = self._sprite_assets.get(sprite.asset_key)
        if asset is None and sprite.asset_key == "demo-player":
            asset = self._make_demo_actor_asset()
            self._sprite_assets[sprite.asset_key] = asset
        if asset is None:
            return
        source = asset.surface
        width = max(1, round(source.get_width() * transform.zoom))
        height = max(1, round(source.get_height() * transform.zoom))
        scaled = source if (width, height) == source.get_size() else pygame.transform.smoothscale(source, (width, height))
        anchor = transform.world_to_screen(sprite.ground_anchor)
        # Keep anchor/pivot arithmetic in float; quantize only the final blit origin.
        destination = (round(anchor.x - asset.foot_anchor_x * width),
                       round(anchor.y - asset.foot_anchor_y * height))
        surface.blit(scaled, destination)

    @staticmethod
    def _make_demo_actor_asset() -> SpriteAsset:
        image = pygame.Surface((24, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (36, 45, 61), (5, 25, 7, 10))
        pygame.draw.ellipse(image, (36, 45, 61), (12, 25, 7, 10))
        pygame.draw.polygon(image, (164, 75, 65), ((4, 15), (20, 15), (19, 29), (5, 29)))
        pygame.draw.circle(image, (224, 185, 145), (12, 9), 6)
        pygame.draw.rect(image, (105, 75, 48), (6, 2, 12, 4), border_radius=2)
        return SpriteAsset(image, 0.5, 1.0)

    def _draw_collider(self, surface, collider: ColliderVisual, transform: WorldScreenTransform) -> None:
        shape = collider.shape
        if isinstance(shape, CircleVisual):
            pygame.draw.circle(surface, DEBUG_COLLIDER, self._point(shape.center, transform),
                               max(1, round(shape.radius * transform.zoom)),
                               width=max(1, round(transform.zoom)))
        elif isinstance(shape, PolygonVisual):
            pygame.draw.polygon(surface, DEBUG_COLLIDER, self._points(shape.vertices, transform),
                                width=max(1, round(transform.zoom)))

    def _draw_cell_label(self, surface, q: int, r: int, center: WorldPoint,
                         transform: WorldScreenTransform) -> None:
        if self._font is None:
            self._font = pygame.font.Font(None, 16)
        label = self._font.render(f"{q},{r}", True, (198, 210, 225))
        point = transform.world_to_screen(center)
        surface.blit(label, (round(point.x - label.get_width() / 2),
                             round(point.y - label.get_height() / 2)))

    @staticmethod
    def _point(point, transform: WorldScreenTransform) -> tuple[int, int]:
        screen = transform.world_to_screen(point)
        return round(screen.x), round(screen.y)

    @classmethod
    def _points(cls, points, transform: WorldScreenTransform) -> list[tuple[int, int]]:
        return [cls._point(point, transform) for point in points]
