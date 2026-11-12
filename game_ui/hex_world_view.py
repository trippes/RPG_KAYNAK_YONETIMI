"""Pygame presentation adapter for the axial hex-world runtime.

The legacy square-map actor remains untouched while this view is active. The
H-key bridge is a temporary development entrance/exit; final portal placement
is deliberately left to authored world content.
"""
from __future__ import annotations

import math

from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    EntityPosition, HexCoord, HexDirection, LocalHexPosition, MovementProfile,
)
from core.domain.spatial.hex_geometry import axial_to_pixel
from game_ui.world_transform import WorldTransform
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer
from application.content_loader import load_content_package


class HexWorldView:
    """Render and control the active player's axial-hex world session."""

    START_MAP_ID = "hex_forest_demo"
    PLAYER_KIND = "player"
    HEX_RADIUS = 32
    TERRAIN_COLORS = {
        "grass": (83, 132, 73),
        "forest_floor": (49, 103, 62),
        "clearing_floor": (137, 119, 76),
        "water": (47, 102, 150),
    }

    def __init__(self, service):
        self.service = service
        self.runtime = None
        self.active = False
        self.entity_id = None
        self.selected = None
        self.message = "Altıgen dünyaya giriş için H tuşunu kullan."
        self._package = None
        self._hex_size = self.HEX_RADIUS
        self._center = (0, 0)
        self._world_transform = WorldTransform(hex_size=self.HEX_RADIUS)
        self._terrain_renderer = HexTerrainRenderer()
        self._zoom = 1.0

    def _load_package(self):
        if self._package is None:
            root = getattr(self.service, "_content_package_path", None)
            if root is None:
                raise RuntimeError("Aktif içerik paketi yolu bulunamadı.")
            self._package = load_content_package(root)
        if not self._package.hex_map_definitions or self._package.world_map_definition is None:
            raise RuntimeError("İçerik paketinde doğrulanmış altıgen dünya bulunamadı.")
        return self._package

    def enter(self):
        if self.active:
            return True
        actors = self.service.state().actors
        if not actors:
            self.message = "Altıgen dünyaya geçmek için aktif karakter bulunamadı."
            return False
        try:
            package = self._load_package()
            map_id = (
                self.START_MAP_ID
                if self.START_MAP_ID in package.hex_map_definitions
                else package.world_map_definition.placements[0].map_id
            )
            definition = package.hex_map_definitions[map_id]
            start = LocalHexPosition(0, 0)
            if not definition.has_cell(start) or definition.is_blocked(start):
                start = min(definition.valid_cells, key=lambda cell: (cell.q, cell.r))
            actor = actors[0]
            self.runtime = HexWorldRuntime(
                package.hex_map_definitions,
                world_map_definition=package.world_map_definition,
            )
            self.entity_id = actor.actor_id
            self.runtime.register_entity(
                self.entity_id,
                self.PLAYER_KIND,
                EntityPosition(map_id, start),
                MovementProfile(),
            )
            self.selected = start
            self.active = True
            self.message = "Altıgen dünyaya geçildi. Bağlı haritalara sınırdan geçebilirsin. H: kare dünyaya dön."
            return True
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            self.runtime = None
            self.active = False
            self.message = f"Altıgen dünya yüklenemedi: {error}"
            return False

    def leave(self):
        """Return to the untouched legacy square-world actor state."""
        self.runtime = None
        self.entity_id = None
        self.selected = None
        self.active = False
        self.message = "Kare dünyaya geri dönüldü."

    def _entity(self):
        return self.runtime.entity(self.entity_id)

    def _map(self):
        return self.runtime.map_definition(self._entity().position.map_id)

    def _move(self, direction):
        entity = self._entity()
        definition = self._map()
        target = LocalHexPosition.from_hex_coord(
            entity.position.cell.to_hex_coord().neighbor(direction)
        )

        # Leaving the local valid-cell mask can activate an authored world link.
        if not definition.has_cell(target):
            transition = next(
                (
                    item for item in definition.transitions
                    if item.active
                    and item.exit_direction == direction
                    and entity.position.cell in item.source_cells
                ),
                None,
            )
            if transition is None:
                self.message = "Bu yönde harita sınırı var; bağlantılı bir bölge bulunmuyor."
                return False
            result = self.runtime.transition(self.entity_id, transition.transition_id)
        else:
            result = self.runtime.move(self.entity_id, direction)

        if result.success:
            self.selected = result.position.cell
            destination = self.runtime.map_definition(result.position.map_id)
            self.message = f"{destination.name} — q={self.selected.q}, r={self.selected.r}"
        else:
            self.message = result.detail or "Bu altıgen hücreye hareket edilemiyor."
        return result.success

    def _move_to(self, target):
        path = self.runtime.path_to(self.entity_id, target)
        if not path:
            self.message = "Bu hücreye güvenli bir yol bulunamadı."
            return False
        moved = False
        for cell in path[1:]:
            result = self.runtime.move_to(self.entity_id, cell)
            if not result.success:
                self.message = result.detail or "Hareket yolu üzerinde engel var."
                return moved
            moved = True
        self.selected = target
        self.message = f"Hedef hücreye ulaşıldı: q={target.q}, r={target.r}"
        return True

    def handle(self, state):
        if not self.active:
            return None
        if state.mouse_wheel:
            self._zoom = max(0.75, min(1.8, self._zoom + state.mouse_wheel * 0.1))
            self.message = f"Yakınlaştırma: {self._zoom:.1f}x"
        directions = (
            ("up", HexDirection.NORTH_EAST),
            ("right", HexDirection.EAST),
            ("down", HexDirection.SOUTH_EAST),
            ("left", HexDirection.WEST),
            ("hex_north_west", HexDirection.NORTH_WEST),
            ("hex_south_west", HexDirection.SOUTH_WEST),
        )
        for action, direction in directions:
            if state.pressed(action):
                self._move(direction)
                return None

        if state.mouse_clicked and state.mouse_pos is not None:
            size = self._hex_size
            target_coord = self._world_transform.screen_to_axial(*state.mouse_pos)
            q, r = target_coord.q, target_coord.r
            target = LocalHexPosition(q, r)
            if self._map().has_cell(target):
                self._move_to(target)
            else:
                self.message = "Bu noktada geçerli bir altıgen hücre yok."
            return None

        # Enter does not change maps; travel is triggered by crossing a linked boundary.
        return None

    def _layout(self, definition, renderer):
        unit_centers = {
            cell: axial_to_pixel(HexCoord(cell.q, cell.r), 1)
            for cell in definition.valid_cells
        }
        min_x = min(point[0] for point in unit_centers.values())
        max_x = max(point[0] for point in unit_centers.values())
        min_y = min(point[1] for point in unit_centers.values())
        max_y = max(point[1] for point in unit_centers.values())
        span_x = max(1.0, max_x - min_x + math.sqrt(3))
        span_y = max(1.0, max_y - min_y + 2.0)
        size = min(
            float(self.HEX_RADIUS),
            max(12.0, (renderer.width - 100) / span_x),
            max(12.0, (renderer.height - 190) / span_y),
        )
        self._hex_size = size
        self._center = (renderer.width // 2, renderer.height // 2 + 4)
        camera_x = camera_y = 0.0
        if self._zoom > 1.0:
            player_cell = self._entity().position.cell
            camera_x, camera_y = axial_to_pixel(HexCoord(player_cell.q, player_cell.r), size)
        self._world_transform.configure(
            hex_size=size, camera_x=camera_x, camera_y=camera_y,
            viewport_center=self._center, zoom=self._zoom,
        )
        return {
            cell: self._world_transform.axial_to_screen(HexCoord(cell.q, cell.r))
            for cell in definition.valid_cells
        }

    def render(self, renderer):
        if not self.active:
            return
        definition = self._map()
        entity = self._entity()
        centers = self._layout(definition, renderer)
        renderer.frame(definition.name, 0)

        for cell in sorted(definition.valid_cells, key=lambda item: (item.r, item.q)):
            self._terrain_renderer.draw_cell(
                renderer, cell, definition.get_cell(cell), centers[cell],
                self._hex_size, selected=(cell == self.selected),
            )

        for feature in definition.features:
            for cell in feature.cells:
                center = centers[cell]
                if feature.feature_type == "river":
                    renderer.pg.draw.circle(
                        renderer.surface, (75, 157, 201),
                        (round(center[0]), round(center[1])),
                        max(4, round(self._hex_size * 0.32)),
                    )

        for landmark in definition.landmarks:
            center = centers[landmark.position]
            renderer.pg.draw.circle(
                renderer.surface, (180, 145, 83),
                (round(center[0]), round(center[1])),
                max(5, round(self._hex_size * 0.22)),
            )
            renderer.text(
                landmark.name,
                round(center[0] - self._hex_size),
                round(center[1] + self._hex_size * 0.28),
                (245, 225, 180),
                max_width=round(self._hex_size * 2),
            )

        for transition in definition.transitions:
            if not transition.active:
                continue
            for cell in transition.source_cells:
                center = centers[cell]
                renderer.pg.draw.circle(
                    renderer.surface, (102, 219, 230),
                    (round(center[0]), round(center[1])),
                    max(7, round(self._hex_size * 0.48)), 2,
                )

        player_center = centers[entity.position.cell]
        renderer.pg.draw.circle(
            renderer.surface, (118, 238, 166),
            (round(player_center[0]), round(player_center[1])),
            max(6, round(self._hex_size * 0.24)),
        )
        renderer.text(
            f"Harita: {definition.name}   Axial: q={entity.position.cell.q}, r={entity.position.cell.r}",
            28, 76, (225, 215, 185), max_width=renderer.width - 56,
        )
        renderer.text(
            self.message, 28, renderer.height - 76, (230, 197, 126),
            max_width=renderer.width - 56,
        )
        renderer.footer(
            "Oklar: NE / E / SE / W   Z: NW   X: SW   Sınırdan geç: bağlı harita   H: kare dünyaya dön   Esc: Menü"
        )
