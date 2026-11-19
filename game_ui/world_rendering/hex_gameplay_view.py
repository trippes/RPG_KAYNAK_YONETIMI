"""Main Pygame presentation adapter for the authoritative HexWorldRuntime."""

from __future__ import annotations

from core.domain.spatial import HexDirection, LocalHexPosition
from game_ui.world_transform import WorldTransform

from .camera import HexCamera
from .character_renderer import HexCharacterRenderer
from .depth_sorter import DepthSorter
from .terrain_renderer import HexTerrainRenderer


class HexGameplayView:
    """Render and control one map without owning gameplay position or identity."""

    HEX_SIZE = 32.0
    MIN_ZOOM = 0.55
    MAX_ZOOM = 1.8
    ZOOM_STEP = 0.08

    DIRECTIONS = (
        ("right", HexDirection.EAST),
        ("left", HexDirection.WEST),
        ("up", HexDirection.NORTH_EAST),
        ("down", HexDirection.SOUTH_EAST),
        ("hex_north_west", HexDirection.NORTH_WEST),
        ("hex_south_west", HexDirection.SOUTH_WEST),
    )

    def __init__(self, service) -> None:
        self.service = service
        self.camera = HexCamera()
        self.transform = WorldTransform(hex_size=self.HEX_SIZE)
        self.terrain = HexTerrainRenderer()
        self.characters = HexCharacterRenderer()
        self.zoom = 1.0
        self.elapsed_seconds = 0.0
        self.mouse_position = None
        self._camera_map_id = None

    def update(self, elapsed_seconds: float = 0.0) -> None:
        self.elapsed_seconds = max(0.0, float(elapsed_seconds))

    def handle(self, state) -> None:
        runtime = self.service.hex_world_runtime
        if runtime is None:
            return
        try:
            runtime.entity(self.service.player_actor_id)
        except KeyError:
            return
        if state.mouse_wheel:
            self.zoom = max(
                self.MIN_ZOOM,
                min(self.MAX_ZOOM, self.zoom + state.mouse_wheel * self.ZOOM_STEP),
            )
        self.mouse_position = state.mouse_pos

        for action, direction in self.DIRECTIONS:
            if state.pressed(action):
                self.service.hex_actor_binding.move(
                    self.service.player_actor_id,
                    direction,
                )

    def render(self, renderer) -> bool:
        runtime = self.service.hex_world_runtime
        if runtime is None:
            return False
        try:
            player = runtime.entity(self.service.player_actor_id)
        except (KeyError, RuntimeError):
            return False

        map_definition = runtime.map_definition(player.position.map_id)
        panel = renderer.pg.Rect(
            24,
            96,
            max(1, renderer.width - 48),
            max(1, renderer.height - 120),
        )
        surface = renderer.surface
        get_clip = getattr(surface, "get_clip", None)
        set_clip = getattr(surface, "set_clip", None)
        previous_clip = get_clip() if callable(get_clip) else None

        try:
            if callable(set_clip):
                set_clip(panel)
            renderer.pg.draw.rect(surface, (31, 49, 43), panel)
            renderer.pg.draw.rect(surface, (80, 103, 83), panel, 2)

            world_centers = tuple(
                self.transform.axial_to_world(position.to_hex_coord())
                for position in map_definition.valid_cells
            )
            min_x = min(point[0] for point in world_centers) - self.HEX_SIZE
            min_y = min(point[1] for point in world_centers) - self.HEX_SIZE
            max_x = max(point[0] for point in world_centers) + self.HEX_SIZE
            max_y = max(point[1] for point in world_centers) + self.HEX_SIZE
            target = self.transform.axial_to_world(
                player.position.cell.to_hex_coord()
            )
            local_mouse = None
            if self.mouse_position is not None:
                mx, my = self.mouse_position
                if panel.collidepoint((mx, my)):
                    local_mouse = (mx - panel.x, my - panel.y)

            camera_x, camera_y = self.camera.update(
                target,
                local_mouse,
                (panel.width, panel.height),
                (min_x, min_y, max_x, max_y),
                self.zoom,
                self.elapsed_seconds,
            )
            if self._camera_map_id != player.position.map_id:
                self.camera.x, self.camera.y = target
                self._camera_map_id = player.position.map_id
                camera_x, camera_y = target
            self.transform.configure(
                camera_x=camera_x,
                camera_y=camera_y,
                viewport_center=(panel.centerx, panel.centery),
                zoom=self.zoom,
            )

            cells = sorted(
                map_definition.valid_cells,
                key=lambda position: (position.r, position.q),
            )
            radius = self.HEX_SIZE * self.zoom
            for position in cells:
                cell = map_definition.get_cell(position)
                center = self.transform.axial_to_screen(
                    position.to_hex_coord()
                )
                if self.terrain.is_visible(
                    center, radius * 1.35, renderer.width, renderer.height,
                ):
                    self.terrain.draw_cell(
                        renderer,
                        position,
                        cell,
                        center,
                        radius,
                    )

            entities = tuple(
                entity for entity in runtime.entities()
                if entity.position.map_id == player.position.map_id
            )
            for entity in DepthSorter.sort(
                entities, lambda item: item.position.cell,
            ):
                foot = self.transform.axial_to_screen(
                    entity.position.cell.to_hex_coord()
                )
                if entity.kind in {"player", "npc"}:
                    self.characters.draw(
                        renderer,
                        foot,
                        max(18.0, radius * 1.25),
                        self.elapsed_seconds,
                        moving=False,
                    )
                else:
                    renderer.pg.draw.circle(
                        surface,
                        (174, 147, 92),
                        (round(foot[0]), round(foot[1])),
                        max(5, round(radius * 0.22)),
                    )

            renderer.text(
                f"{map_definition.name}  ·  {player.position.cell.q}, {player.position.cell.r}",
                panel.x + 16,
                panel.y + 12,
            )
            renderer.text(
                "Hareket: yön tuşları + Z/X   Yakınlaştırma: fare tekerleği",
                panel.x + 16,
                panel.bottom - 28,
            )
            return True
        finally:
            if callable(set_clip):
                set_clip(previous_clip)


__all__ = ["HexGameplayView"]
