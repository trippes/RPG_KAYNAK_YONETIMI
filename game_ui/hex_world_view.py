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
from game_ui.world_rendering.camera import HexCamera
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer
from game_ui.world_rendering.depth_sorter import DepthSorter
from application.content_loader import load_content_package


class HexWorldView:
    """Render and control the active player's axial-hex world session."""

    START_MAP_ID = "hex_forest_demo"
    PLAYER_KIND = "player"
    HEX_RADIUS = 32

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
        self._movement_path = ()
        self._movement_elapsed = 0.0
        self._movement_step_seconds = 0.18
        self._camera = HexCamera()
        self._mouse_position = None
        self._viewport_size = (960, 640)
        self._frame_elapsed = 0.0

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
            self._movement_path = ()
            self._movement_elapsed = 0.0
            self._camera = HexCamera()
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
        self._movement_path = ()
        self._camera = HexCamera()
        self.message = "Kare dünyaya geri dönüldü."

    def _entity(self):
        return self.runtime.entity(self.entity_id)

    def _map(self):
        return self.runtime.map_definition(self._entity().position.map_id)

    def _move(self, direction):
        entity = self._entity()
        previous_map_id = entity.position.map_id
        previous_cell = entity.position.cell
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
            if result.position.map_id == previous_map_id:
                self._start_visual_movement((previous_cell, result.position.cell))
            else:
                self._movement_path = ()
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
        self._start_visual_movement(path)
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

    def _start_visual_movement(self, path):
        self._movement_path = tuple(path) if len(path) > 1 else ()
        self._movement_elapsed = 0.0

    def update(self, elapsed_seconds):
        self._frame_elapsed = max(0.0, float(elapsed_seconds))
        if not self._movement_path or elapsed_seconds <= 0:
            return
        self._movement_elapsed += float(elapsed_seconds)
        duration = (len(self._movement_path) - 1) * self._movement_step_seconds
        if self._movement_elapsed >= duration:
            self._movement_path = ()
            self._movement_elapsed = 0.0

    def handle(self, state):
        if not self.active:
            return None
        self._mouse_position = state.mouse_pos
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

    def _visual_player_world_position(self):
        entity = self._entity()
        cell = entity.position.cell
        if not self._movement_path:
            return axial_to_pixel(HexCoord(cell.q, cell.r), self._hex_size)
        duration = (len(self._movement_path) - 1) * self._movement_step_seconds
        elapsed = min(self._movement_elapsed, duration)
        segment = min(int(elapsed / self._movement_step_seconds), len(self._movement_path) - 2)
        progress = min(1.0, (elapsed - segment * self._movement_step_seconds) / self._movement_step_seconds)
        start = self._movement_path[segment]
        end = self._movement_path[segment + 1]
        start_x, start_y = axial_to_pixel(HexCoord(start.q, start.r), self._hex_size)
        end_x, end_y = axial_to_pixel(HexCoord(end.q, end.r), self._hex_size)
        return (
            start_x + (end_x - start_x) * progress,
            start_y + (end_y - start_y) * progress,
        )

    def _layout(self, definition, renderer):
        # Keep a stable world scale; the camera reveals a viewport-sized part
        # of the map instead of shrinking the entire region into a small panel.
        size = float(self.HEX_RADIUS)
        self._hex_size = size
        self._center = (renderer.width / 2.0, renderer.height / 2.0)
        world_centers = {
            cell: axial_to_pixel(HexCoord(cell.q, cell.r), size)
            for cell in definition.valid_cells
        }
        xs = [point[0] for point in world_centers.values()]
        ys = [point[1] for point in world_centers.values()]
        radius_x = math.sqrt(3) * size
        radius_y = 2.0 * size
        bounds = (
            min(xs) - radius_x, min(ys) - radius_y,
            max(xs) + radius_x, max(ys) + radius_y,
        )
        target = self._visual_player_world_position()
        self._camera.update(
            target, self._mouse_position, (renderer.width, renderer.height),
            bounds, self._zoom, self._frame_elapsed,
        )
        self._frame_elapsed = 0.0
        self._viewport_size = (renderer.width, renderer.height)
        self._world_transform.configure(
            hex_size=size, camera_x=self._camera.x, camera_y=self._camera.y,
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
        render_radius = self._hex_size * self._zoom

        for cell in sorted(definition.valid_cells, key=lambda item: (item.r, item.q)):
            if not self._terrain_renderer.is_visible(centers[cell], render_radius, renderer.width, renderer.height):
                continue
            self._terrain_renderer.draw_cell(
                renderer, cell, definition.get_cell(cell), centers[cell],
                render_radius, selected=(cell == self.selected),
            )

        for feature in definition.features:
            for cell in feature.cells:
                center = centers[cell]
                if not self._terrain_renderer.is_visible(center, render_radius, renderer.width, renderer.height):
                    continue
                if feature.feature_type == "river":
                    renderer.pg.draw.circle(
                        renderer.surface, (75, 157, 201),
                        (round(center[0]), round(center[1])),
                        max(4, round(render_radius * 0.32)),
                    )

        for transition in definition.transitions:
            if not transition.active:
                continue
            for cell in transition.source_cells:
                center = centers[cell]
                if not self._terrain_renderer.is_visible(center, render_radius, renderer.width, renderer.height):
                    continue
                renderer.pg.draw.circle(
                    renderer.surface, (102, 219, 230),
                    (round(center[0]), round(center[1])),
                    max(7, round(render_radius * 0.48)), 2,
                )

        drawables = [(item.position, "landmark", item) for item in definition.landmarks if self._terrain_renderer.is_visible(centers[item.position], render_radius, renderer.width, renderer.height)]
        drawables.append((entity.position.cell, "player", entity))
        for position, drawable_type, drawable in DepthSorter.sort(
            drawables, lambda item: item[0],
        ):
            center = centers[position]
            if drawable_type == "landmark":
                renderer.pg.draw.circle(
                    renderer.surface, (180, 145, 83),
                    (round(center[0]), round(center[1])),
                    max(5, round(render_radius * 0.22)),
                )
                renderer.text(
                    drawable.name,
                    round(center[0] - render_radius),
                    round(center[1] + render_radius * 0.28),
                    (245, 225, 180),
                    max_width=round(render_radius * 2),
                )
            else:
                player_center = center
                if self._movement_path:
                    elapsed = min(self._movement_elapsed, (len(self._movement_path) - 1) * self._movement_step_seconds)
                    segment = min(int(elapsed / self._movement_step_seconds), len(self._movement_path) - 2)
                    progress = min(1.0, (elapsed - segment * self._movement_step_seconds) / self._movement_step_seconds)
                    move_start = centers.get(self._movement_path[segment])
                    move_end = centers.get(self._movement_path[segment + 1])
                    if move_start is not None and move_end is not None:
                        player_center = (
                            move_start[0] + (move_end[0] - move_start[0]) * progress,
                            move_start[1] + (move_end[1] - move_start[1]) * progress,
                        )
                renderer.pg.draw.circle(
                    renderer.surface, (118, 238, 166),
                    (round(player_center[0]), round(player_center[1])),
                    max(6, round(render_radius * 0.24)),
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
