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
    MOVE_STEP_SECONDS = 0.18

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
        self._panel = None
        self._move_goal = None
        self._move_map_id = None
        self._movement_accumulator = 0.0
        self.context_menu_npc_id = None
        self.context_menu_position = None
        self.selected_npc_id = None

    def _npc_at_screen_position(self, runtime, position, map_id):
        if position is None or self._panel is None or not self._panel.collidepoint(position):
            return None
        entities = getattr(runtime, "entities", None)
        if not callable(entities):
            return None
        cell = LocalHexPosition.from_hex_coord(
            self.transform.screen_to_axial(*position)
        )
        for entity in entities():
            if (
                entity.kind == "npc"
                and entity.position.map_id == map_id
                and entity.position.cell == cell
            ):
                return entity.entity_id
        return None

    def update(self, elapsed_seconds: float = 0.0) -> None:
        self.elapsed_seconds = max(0.0, float(elapsed_seconds))
        if self._move_goal is None:
            return
        runtime = self.service.hex_world_runtime
        if runtime is None:
            self._clear_move_goal()
            return
        try:
            entity = runtime.entity(self.service.player_actor_id)
        except KeyError:
            self._clear_move_goal()
            return
        if entity.position.map_id != self._move_map_id:
            self._clear_move_goal()
            return
        if entity.position.cell == self._move_goal:
            self._clear_move_goal()
            return

        self._movement_accumulator += self.elapsed_seconds
        if self._movement_accumulator < self.MOVE_STEP_SECONDS:
            return
        self._movement_accumulator %= self.MOVE_STEP_SECONDS
        result = self.service.hex_actor_binding.move_toward(
            self.service.player_actor_id,
            self._move_goal,
        )
        if not result.success or result.position.cell == self._move_goal:
            self._clear_move_goal()

    def _clear_move_goal(self) -> None:
        self._move_goal = None
        self._move_map_id = None
        self._movement_accumulator = 0.0

    def handle(self, state) -> str | None:
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

        if state.mouse_right_clicked:
            self._clear_move_goal()
            player = runtime.entity(self.service.player_actor_id)
            npc_id = self._npc_at_screen_position(
                runtime, state.mouse_pos, player.position.map_id,
            )
            self.context_menu_npc_id = npc_id
            self.context_menu_position = state.mouse_pos if npc_id is not None else None
            return

        manual_move = False
        for action, direction in self.DIRECTIONS:
            if state.pressed(action):
                manual_move = True
                actor_id = self.service.player_actor_id
                entity = runtime.entity(actor_id)
                map_definition = runtime.map_definition(entity.position.map_id)
                transition = next(
                    (
                        candidate
                        for candidate in map_definition.transitions
                        if (
                            candidate.active
                            and candidate.exit_direction == direction
                            and entity.position.cell in candidate.source_cells
                        )
                    ),
                    None,
                )
                if transition is not None:
                    self.service.hex_actor_binding.transition(
                        actor_id,
                        transition.transition_id,
                    )
                else:
                    self.service.hex_actor_binding.move(actor_id, direction)
        if manual_move:
            self._clear_move_goal()
        elif state.mouse_clicked and state.mouse_pos is not None:
            player = runtime.entity(self.service.player_actor_id)
            npc_id = self._npc_at_screen_position(
                runtime, state.mouse_pos, player.position.map_id,
            )
            self.context_menu_npc_id = None
            self.context_menu_position = None
            if npc_id is not None:
                self._clear_move_goal()
                self.selected_npc_id = npc_id
                return "dialogue"
            if self._panel is None or not self._panel.collidepoint(state.mouse_pos):
                return None
            actor_id = self.service.player_actor_id
            entity = runtime.entity(actor_id)
            map_definition = runtime.map_definition(entity.position.map_id)
            q = self.transform.screen_to_axial(*state.mouse_pos)
            goal = LocalHexPosition.from_hex_coord(q)
            if map_definition.has_cell(goal):
                self._clear_move_goal()
                self._move_goal = goal
                self._move_map_id = entity.position.map_id
                result = self.service.hex_actor_binding.move_toward(
                    actor_id,
                    goal,
                )
                if not result.success or result.position.cell == goal:
                    self._clear_move_goal()

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
            self._panel = panel

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

            if self._move_goal is not None and self._move_map_id == player.position.map_id:
                goal_screen = self.transform.axial_to_screen(
                    self._move_goal.to_hex_coord()
                )
                renderer.pg.draw.circle(
                    surface,
                    (244, 207, 124),
                    (round(goal_screen[0]), round(goal_screen[1])),
                    max(8, round(radius * 0.38)),
                    2,
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
            if self.context_menu_npc_id is not None and self.context_menu_position is not None:
                menu_width, menu_height = 220, 76
                menu_x = min(
                    max(panel.x, self.context_menu_position[0]),
                    max(panel.x, panel.right - menu_width),
                )
                menu_y = min(
                    max(panel.y, self.context_menu_position[1]),
                    max(panel.y, panel.bottom - menu_height),
                )
                menu_rect = renderer.pg.Rect(menu_x, menu_y, menu_width, menu_height)
                renderer.panel(menu_rect, (23, 29, 43), (145, 118, 70))
                renderer.text("Eylemler", menu_x + 12, menu_y + 9)
                renderer.text(
                    self.context_menu_npc_id,
                    menu_x + 12,
                    menu_y + 39,
                    max_width=menu_width - 24,
                )
            return True
        finally:
            if callable(set_clip):
                set_clip(previous_clip)


__all__ = ["HexGameplayView"]
