"""Pygame presentation adapter for the axial hex-world runtime.

The legacy square-map actor remains untouched while this view is active. The
H-key bridge is a temporary development entrance/exit; final portal placement
is deliberately left to authored world content.
"""
from __future__ import annotations

import math
from pathlib import Path

from game_ui.assets.asset_definition import AssetCatalog, AssetCatalogError
from game_ui.assets.asset_manager import AssetManager
from game_ui.assets.animation import Animation
from game_ui.assets.sprite_sheet import SpriteSheet
from game_ui.world_rendering.character_animation import CharacterAnimator
from game_ui.world_rendering.scene_object import SceneObject, SceneObjectRenderer
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    EntityPosition, HexCoord, HexDirection, LocalHexPosition, MovementProfile,
)
from core.domain.spatial.hex_geometry import axial_to_pixel
from game_ui.world_transform import WorldTransform
from game_ui.world_rendering.camera import HexCamera
from game_ui.world_rendering.character_renderer import HexCharacterRenderer
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
        self._presentation_catalog = None
        self._presentation_assets_loaded = False
        self._asset_manager = None
        self._scene_object_renderer = None
        self._character_visual_loaded = False
        self._character_animator = None
        self._character_asset = None
        self._character_scaled_frames = {}
        self._terrain_texture_cache = {}
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

    def _load_presentation_assets(self, pygame_module):
        """Load optional image metadata once; missing art keeps procedural fallbacks."""
        if self._presentation_assets_loaded:
            return
        self._presentation_assets_loaded = True
        package_root = getattr(self.service, "_content_package_path", None)
        if package_root is None:
            return
        catalog_path = getattr(self._package, "presentation_assets_path", None)
        if catalog_path is None:
            catalog_path = Path(package_root) / "presentation_assets.json"
        if not catalog_path.is_file():
            return
        try:
            self._presentation_catalog = AssetCatalog.load(catalog_path)
            self._asset_manager = AssetManager(pygame_module)
            self._scene_object_renderer = SceneObjectRenderer(self._asset_manager)
        except (AssetCatalogError, OSError, ValueError):
            self._presentation_catalog = None
            self._asset_manager = None

    def _terrain_images(self, cell, terrain_id, definition):
        """Resolve deterministic base/detail/transition textures for one cell."""
        if self._presentation_catalog is None or self._asset_manager is None:
            return ()
        adjacent = {terrain_id}
        for direction in HexDirection:
            neighbor = LocalHexPosition.from_hex_coord(
                cell.to_hex_coord().neighbor(direction)
            )
            if definition.has_cell(neighbor):
                adjacent.add(definition.get_cell(neighbor).terrain_id)
        layers = {"underlay": 0, "ground": 1, "overlay": 2}
        selected = []
        for asset in self._presentation_catalog.assets.values():
            required = set(asset.terrain_types)
            if asset.placement not in layers or not required or not required.issubset(adjacent):
                continue
            if asset.asset_id not in self._terrain_texture_cache:
                path = self._presentation_catalog.resolve_path(asset.asset_id)
                image = None
                if path is not None and path.is_file():
                    try:
                        image = self._asset_manager.load_image(asset.asset_id, path, alpha=True)
                    except Exception:
                        image = None
                self._terrain_texture_cache[asset.asset_id] = image
            image = self._terrain_texture_cache[asset.asset_id]
            if image is None:
                continue
            selected.append((layers[asset.placement], asset.asset_id, image))
        selected.sort(key=lambda item: (item[0], item[1]))
        return tuple(item[2] for item in selected)

    def _load_character_visual(self):
        """Build directional sprite animations from optional content metadata."""
        if self._character_visual_loaded:
            return
        self._character_visual_loaded = True
        if self._presentation_catalog is None or self._asset_manager is None:
            return
        asset = (
            self._presentation_catalog.get("player")
            or self._presentation_catalog.get("character.player")
        )
        if asset is None:
            return
        path = self._presentation_catalog.resolve_path(asset.asset_id)
        if path is None or not path.is_file():
            return
        try:
            surface = self._asset_manager.load_image(asset.asset_id, path, alpha=True)
            sheet_data = asset.sheet or {}
            if sheet_data:
                sheet = SpriteSheet(
                    surface, int(sheet_data["frame_width"]),
                    int(sheet_data["frame_height"]),
                )
                frame_getter = sheet.frame
            else:
                frame_getter = lambda index: surface if index == 0 else None
            definitions = asset.animations or {
                "south": {"idle": {"frames": [0], "frame_duration": 0.5}}
            }
            animations = {}
            for direction, states in definitions.items():
                animations[direction] = {}
                for state, definition in states.items():
                    indices = definition.get("frames", [0])
                    frames = tuple(frame_getter(int(index)) for index in indices)
                    if not frames or any(frame is None for frame in frames):
                        raise ValueError("Character animation references an invalid frame.")
                    animations[direction][state] = Animation(
                        frames, float(definition.get("frame_duration", 0.12)),
                        loop=bool(definition.get("loop", True)),
                    )
            self._character_animator = CharacterAnimator(animations)
            self._character_asset = asset
        except Exception:
            self._character_animator = None
            self._character_asset = None

    def _player_facing(self):
        if not self._movement_path or len(self._movement_path) < 2:
            return None
        elapsed = min(
            self._movement_elapsed,
            (len(self._movement_path) - 1) * self._movement_step_seconds,
        )
        segment = min(
            int(elapsed / self._movement_step_seconds),
            len(self._movement_path) - 2,
        )
        start, end = self._movement_path[segment:segment + 2]
        delta = (end.q - start.q, end.r - start.r)
        return {
            (1, -1): "north_east", (1, 0): "east",
            (0, 1): "south_east", (-1, 1): "south_west",
            (-1, 0): "west", (0, -1): "north_west",
        }.get(delta)

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
        if self._character_animator is not None:
            self._character_animator.update(self._frame_elapsed)
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

    def _draw_placed_scene_object(self, renderer, placement, center):
        """Draw a map-authored prop/NPC/resource visual without owning its logic."""
        if self._presentation_catalog is None or self._asset_manager is None:
            return
        asset = self._presentation_catalog.get(placement.asset_id)
        if asset is None:
            return
        anchor = (
            center[0] + placement.offset_x * self._zoom,
            center[1] + placement.offset_y * self._zoom,
        )
        path = self._presentation_catalog.resolve_path(asset.asset_id)
        image = None
        if path is not None and path.is_file():
            try:
                image = self._asset_manager.load_image(asset.asset_id, path, alpha=True)
            except Exception:
                image = None
        if image is not None:
            source_width, source_height = image.get_size()
            visual_width = (asset.width or source_width) * asset.scale
            visual_height = (asset.height or source_height) * asset.scale
            obj = SceneObject(
                object_id=placement.object_id, asset_id=placement.asset_id,
                world_x=anchor[0], world_y=anchor[1],
                visual_width=visual_width, visual_height=visual_height,
                anchor_x=asset.anchor[0], anchor_y=asset.anchor[1],
                footprint=placement.footprint,
                collision_box=placement.collision_box,
                depth_offset=asset.depth_offset + placement.depth_offset,
                layer=placement.layer,
            )
            if not SceneObjectRenderer.is_visible(
                obj, (0, 0, renderer.width, renderer.height), self._zoom
            ):
                return
            self._scene_object_renderer.draw(renderer, obj, anchor, self._zoom)
            return
        # Missing artwork uses deterministic procedural silhouettes. This keeps
        # authored content readable without turning every missing asset into a dot.
        pg = renderer.pg
        x, y = round(anchor[0]), round(anchor[1])
        pulse = math.sin(self._frame_elapsed * 3.0 + placement.q * 0.7 + placement.r) * self._zoom
        kind = placement.kind.lower()
        asset_id = placement.asset_id.lower()
        if "tree" in asset_id or kind == "flora" and "shrub" not in asset_id:
            trunk_h = max(7, round(16 * self._zoom))
            canopy = max(8, round(13 * self._zoom))
            pg.draw.rect(renderer.surface, (91, 66, 40), (x - max(2, canopy // 5), y - trunk_h, max(4, canopy * 2 // 5), trunk_h))
            for dx, dy, scale in ((0, -trunk_h, 1.0), (-canopy * 0.55, -trunk_h * 0.65, 0.72), (canopy * 0.55, -trunk_h * 0.7, 0.76)):
                pg.draw.circle(renderer.surface, (48, 112, 61), (round(x + dx + pulse), round(y + dy)), max(4, round(canopy * scale)))
        elif "rock" in asset_id or kind == "rock":
            radius = max(5, round(10 * self._zoom))
            pg.draw.polygon(renderer.surface, (105, 106, 102), ((x - radius, y), (x - radius // 2, y - radius), (x + radius // 2, y - radius + 2), (x + radius, y), (x + radius // 2, y + radius // 2), (x - radius // 2, y + radius // 2)))
        elif "plant" in asset_id or "flower" in asset_id:
            radius = max(3, round(5 * self._zoom))
            pg.draw.line(renderer.surface, (57, 118, 61), (x, y), (x + round(pulse), y - radius * 2), max(1, round(self._zoom)))
            pg.draw.circle(renderer.surface, (180, 145, 92), (x + round(pulse), y - radius * 2), radius)
        else:
            radius = max(4, round(9 * self._zoom))
            pg.draw.circle(renderer.surface, (63, 124, 70), (x - radius // 2, y - radius // 3), radius)
            pg.draw.circle(renderer.surface, (54, 111, 62), (x + radius // 2, y - radius // 4), radius)
            pg.draw.circle(renderer.surface, (49, 101, 56), (x, y - radius), radius)

    def _draw_landmark(self, renderer, landmark, center, render_radius):
        """Draw an authored sprite when available, otherwise retain the marker fallback."""
        if self._presentation_catalog is not None and self._asset_manager is not None:
            asset = (
                self._presentation_catalog.get(landmark.visual_type)
                or self._presentation_catalog.get(f"landmark.{landmark.visual_type}")
            )
            if asset is not None:
                path = self._presentation_catalog.resolve_path(asset.asset_id)
                if path is not None and path.is_file():
                    try:
                        image = self._asset_manager.load_image(asset.asset_id, path, alpha=True)
                        obj = SceneObject(
                            object_id=landmark.landmark_id,
                            asset_id=asset.asset_id,
                            world_x=center[0], world_y=center[1],
                            visual_width=(asset.width or image.get_width()) * asset.scale,
                            visual_height=(asset.height or image.get_height()) * asset.scale,
                            anchor_x=asset.anchor[0], anchor_y=asset.anchor[1],
                            depth_offset=asset.depth_offset,
                            layer=asset.placement,
                        )
                        if SceneObjectRenderer.is_visible(
                            obj, (0, 0, renderer.width, renderer.height), self._zoom
                        ):
                            self._scene_object_renderer.draw(
                                renderer, obj, center, self._zoom
                            )
                        return
                    except Exception:
                        pass
        if not self._terrain_renderer.is_visible(
            center, render_radius, renderer.width, renderer.height
        ):
            return
        renderer.pg.draw.circle(
            renderer.surface, (180, 145, 83),
            (round(center[0]), round(center[1])),
            max(5, round(render_radius * 0.22)),
        )
        renderer.text(
            landmark.name,
            round(center[0] - render_radius),
            round(center[1] + render_radius * 0.28),
            (245, 225, 180),
            max_width=round(render_radius * 2),
        )

    def render(self, renderer):
        if not self.active:
            return
        definition = self._map()
        entity = self._entity()
        centers = self._layout(definition, renderer)
        renderer.frame(definition.name, 0)
        render_radius = self._hex_size * self._zoom
        self._load_presentation_assets(renderer.pg)
        self._load_character_visual()

        self._terrain_renderer.begin_frame(
            renderer,
            [definition.get_cell(cell).terrain_id for cell in definition.valid_cells],
        )

        for cell in sorted(definition.valid_cells, key=lambda item: (item.r, item.q)):
            if not self._terrain_renderer.is_visible(centers[cell], render_radius, renderer.width, renderer.height):
                continue
            self._terrain_renderer.draw_cell(
                renderer, cell, definition.get_cell(cell), centers[cell],
                render_radius, selected=(cell == self.selected),
                images=self._terrain_images(cell, definition.get_cell(cell).terrain_id, definition),
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

        # Map links remain simulation-only; normal play does not reveal hex exits.\n\n        drawables = [(item.position, "landmark", item) for item in definition.landmarks]
        if self._presentation_catalog is not None:
            for placement in self._presentation_catalog.objects_for_map(definition.map_id):
                position = LocalHexPosition(placement.q, placement.r)
                if definition.has_cell(position):
                    drawables.append((position, "scene_object", placement))
        drawables.append((entity.position.cell, "player", entity))

        def drawable_depth(item):
            position, kind, value = item
            layer = getattr(value, "layer", "ground")
            layer_order = {"underlay": 0, "ground": 1, "canopy": 2, "overlay": 3}.get(layer, 1)
            offset = value.offset_y * self._zoom + value.depth_offset * self._zoom if kind == "scene_object" else 0
            return layer_order, centers[position][1] + offset

        for position, drawable_type, drawable in DepthSorter.sort_by_depth(
            drawables,
            drawable_depth,
            lambda item: (item[0].q, item[0].r, item[1], getattr(item[2], "object_id", getattr(item[2], "landmark_id", ""))),
        ):
            center = centers[position]
            if drawable_type == "landmark":
                self._draw_landmark(renderer, drawable, center, render_radius)
            elif drawable_type == "scene_object":
                self._draw_placed_scene_object(renderer, drawable, center)
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
                if self._character_animator is not None and self._character_asset is not None:
                    facing = self._player_facing()
                    self._character_animator.select(
                        direction=facing or "south",
                        state="walk" if self._movement_path else "idle",
                    )
                frame = (
                    self._character_animator.current_frame
                    if self._character_animator is not None else None
                )
                if frame is not None:
                    HexCharacterRenderer.draw_sprite(
                        renderer, frame,
                        (player_center[0], player_center[1] + render_radius * 0.28),
                        render_radius * self._character_asset.scale,
                        anchor=self._character_asset.anchor,
                        cache=self._character_scaled_frames,
                    )
                else:
                    HexCharacterRenderer.draw(
                        renderer, player_center, render_radius,
                        self._movement_elapsed, moving=bool(self._movement_path),
                    )

        # A small natural target ring gives mouse feedback without exposing a
        # hex cell outline or movement grid.
        if self._mouse_position is not None:
            target = self._world_transform.screen_to_axial(*self._mouse_position)
            target_cell = LocalHexPosition(target.q, target.r)
            if definition.has_cell(target_cell):
                target_center = centers[target_cell]
                renderer.pg.draw.circle(
                    renderer.surface, (214, 190, 112),
                    (round(target_center[0]), round(target_center[1])),
                    max(4, round(render_radius * 0.12)), 1,
                )
        renderer.text(
            f"Harita: {definition.name}",
            28, 76, (225, 215, 185), max_width=renderer.width - 56,
        )
        renderer.text(
            self.message, 28, renderer.height - 76, (230, 197, 126),
            max_width=renderer.width - 56,
        )
        renderer.footer(
            "Oklar: NE / E / SE / W   Z: NW   X: SW   Sınırdan geç: bağlı harita   H: kare dünyaya dön   Esc: Menü"
        )
