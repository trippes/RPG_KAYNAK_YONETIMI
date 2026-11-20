"""Main Pygame presentation adapter for the authoritative HexWorldRuntime."""

from __future__ import annotations

import math

from core.domain.spatial import HexDirection, WorldPoint, world_point_to_hex
from game_ui.world_transform import WorldTransform

from .camera import HexCamera
from .character_renderer import HexCharacterRenderer
from .depth_sorter import DepthSorter
from .terrain_renderer import HexTerrainRenderer
from .scene_object_pipeline import SceneObjectPipeline
from .character_sprite_factory import ProceduralCharacterSpriteFactory


class HexGameplayView:
    """Render and control one map without owning gameplay position or identity."""

    HEX_SIZE = 32.0
    MIN_ZOOM = 0.55
    MAX_ZOOM = 1.8
    ZOOM_STEP = 0.08
    MOVE_STEP_SECONDS = 0.18
    MOVE_ANIMATION_SECONDS = 0.18

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
        self._scene_pipeline = None
        self._character_sprite_factory = None
        self._player_animator = None
        self._npc_animators = {}
        self._npc_visual_states = {}
        self._player_facing = "south"
        self._character_sprite_cache = {}
        self._last_render_stats = {}
        self.zoom = 1.0
        self.elapsed_seconds = 0.0
        self.mouse_position = None
        self._camera_map_id = None
        self._panel = None
        self._move_goal = None
        self._move_map_id = None
        self._movement_accumulator = 0.0
        self._visual_map_id = None
        self._visual_cell = None
        self._visual_position = None
        self._visual_start = None
        self._visual_target = None
        self._visual_elapsed = 0.0
        self._visual_moving = False
        self._continuous_motion_active = False
        self._runtime_motion_elapsed = 0.0
        self._last_runtime_position = None
        self.context_menu_npc_id = None
        self.context_menu_position = None
        self.context_menu_is_companion = False
        self.context_menu_target_id = None
        self.context_menu_target_kind = None
        self.selected_interaction_target_id = None
        self.selected_npc_id = None
        self.selected_scene_object_id = None

    @property
    def render_stats(self):
        """Return the latest deterministic renderer counters."""
        return dict(self._last_render_stats)

    def _npc_at_screen_position(self, runtime, position, map_id):
        if position is None or self._panel is None or not self._panel.collidepoint(position):
            return None
        world_point = self.transform.screen_to_world_point(*position)
        return self.service.npc_at_world_point(map_id, world_point)

    def _cell_world_position(self, cell):
        return self.transform.axial_to_world(cell.to_hex_coord())

    def _ensure_visual_position(self, map_id, cell, continuous_position=None):
        position = (
            (continuous_position.x, continuous_position.y)
            if continuous_position is not None
            else self._cell_world_position(cell)
        )
        if self._visual_map_id != map_id or (
            self._visual_cell != cell and not self._visual_moving
        ):
            self._visual_map_id = map_id
            self._visual_cell = cell
            self._visual_position = position
            self._visual_start = position
            self._visual_target = position
            self._visual_elapsed = 0.0
            self._visual_moving = False
        elif self._visual_position is None:
            self._visual_map_id = map_id
            self._visual_cell = cell
            self._visual_position = position
            self._visual_start = position
            self._visual_target = position
        elif not self._visual_moving and continuous_position is not None:
            self._visual_cell = cell
            self._visual_position = position
            self._visual_start = position
            self._visual_target = position

    def _begin_visual_move(self, map_id, source_cell, target_cell):
        if source_cell == target_cell:
            return
        if self._visual_map_id != map_id:
            self._ensure_visual_position(map_id, source_cell)
        if self._visual_position is None:
            self._visual_position = self._cell_world_position(source_cell)
        target = self._cell_world_position(target_cell)
        self._visual_start = self._visual_position
        self._visual_target = target
        self._continuous_motion_active = False
        self._set_player_facing_from_world_delta(
            target[0] - self._visual_position[0],
            target[1] - self._visual_position[1],
        )
        self._visual_elapsed = 0.0
        self._visual_cell = target_cell
        self._visual_map_id = map_id
        self._visual_moving = self._visual_start != target

    def _advance_visual_position(self, elapsed_seconds):
        if not self._visual_moving or self._continuous_motion_active:
            return
        self._visual_elapsed = min(
            self.MOVE_ANIMATION_SECONDS,
            self._visual_elapsed + max(0.0, elapsed_seconds),
        )
        progress = min(1.0, self._visual_elapsed / self.MOVE_ANIMATION_SECONDS)
        start_x, start_y = self._visual_start
        target_x, target_y = self._visual_target
        self._visual_position = (
            start_x + (target_x - start_x) * progress,
            start_y + (target_y - start_y) * progress,
        )
        if progress >= 1.0:
            self._visual_position = self._visual_target
            self._visual_moving = False

    def _record_move_result(self, map_id, source_cell, result):
        if result is not None and result.success:
            self._begin_visual_move(map_id, source_cell, result.position.cell)

    def _advance_npc_visuals(self, delta_seconds):
        runtime = getattr(self.service, "hex_world_runtime", None)
        entities_method = getattr(runtime, "entities", None)
        if not callable(entities_method):
            return
        active_ids = set()
        for entity in entities_method():
            if entity.kind != "npc":
                continue
            active_ids.add(entity.entity_id)
            try:
                point = runtime.continuous_position(entity.entity_id).point
                target = (point.x, point.y)
            except KeyError:
                continue
            state = self._npc_visual_states.get(entity.entity_id)
            if state is None:
                state = {
                    "start": target, "target": target, "current": target,
                    "elapsed": 0.18, "moving": False, "direction": "south",
                }
                self._npc_visual_states[entity.entity_id] = state
            elif target != state["target"]:
                current = state["current"]
                state["start"] = current
                state["target"] = target
                state["elapsed"] = 0.0
                state["moving"] = True
                state["direction"] = self._direction_from_world_delta(
                    target[0] - current[0], target[1] - current[1],
                )
            if state["elapsed"] < 0.18:
                state["elapsed"] = min(0.18, state["elapsed"] + delta_seconds)
            progress = min(1.0, state["elapsed"] / 0.18)
            eased = progress * progress * (3.0 - 2.0 * progress)
            state["current"] = (
                state["start"][0] + (state["target"][0] - state["start"][0]) * eased,
                state["start"][1] + (state["target"][1] - state["start"][1]) * eased,
            )
            state["moving"] = progress < 1.0
        for stale_id in set(self._npc_visual_states) - active_ids:
            self._npc_visual_states.pop(stale_id, None)

    def update(self, elapsed_seconds: float = 0.0) -> None:
        self.elapsed_seconds = max(0.0, float(elapsed_seconds))
        self._sync_continuous_visual()
        self._advance_visual_position(self.elapsed_seconds)
        self._advance_npc_visuals(self.elapsed_seconds)
        if self._player_animator is not None:
            state = self._player_animation_state(self._visual_moving)
            self._player_animator.select(
                direction=self._player_facing, state=state,
            )
            self._player_animator.update(self.elapsed_seconds)
        for npc_id, animator in self._npc_animators.items():
            visual = self._npc_visual_states.get(npc_id)
            animator.select(
                direction=visual["direction"] if visual else animator.direction,
                state="walk" if visual and visual["moving"] else "idle",
            )
            animator.update(self.elapsed_seconds)
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
        source_cell = entity.position.cell
        result = self.service.hex_actor_binding.move_toward(
            self.service.player_actor_id,
            self._move_goal,
        )
        self._record_move_result(entity.position.map_id, source_cell, result)
        if not result.success or result.position.cell == self._move_goal:
            self._clear_move_goal()

    def _sync_continuous_visual(self):
        """Track fixed-step keyboard motion for facing and walk animation."""
        if self._move_goal is not None:
            return
        if self._visual_moving and self._visual_target != self._visual_start:
            return
        runtime = getattr(self.service, "hex_world_runtime", None)
        if runtime is None:
            return
        try:
            entity = runtime.entity(self.service.player_actor_id)
            continuous = runtime.continuous_position(self.service.player_actor_id)
        except KeyError:
            return
        if continuous is None:
            return
        current = continuous.point
        if self._last_runtime_position is not None:
            dx = current.x - self._last_runtime_position.x
            dy = current.y - self._last_runtime_position.y
            if abs(dx) + abs(dy) > 1e-7:
                self._set_player_facing_from_world_delta(dx, dy)
                self._visual_moving = True
                self._continuous_motion_active = True
                self._runtime_motion_elapsed = 0.0
            elif self._continuous_motion_active:
                self._runtime_motion_elapsed += self.elapsed_seconds
                if self._runtime_motion_elapsed >= 0.10:
                    self._visual_moving = False
                    self._continuous_motion_active = False
        self._last_runtime_position = current
        self._visual_map_id = entity.position.map_id
        self._visual_cell = entity.position.cell
        self._visual_position = (current.x, current.y)
        self._visual_start = self._visual_position
        self._visual_target = self._visual_position

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
            self.context_menu_npc_id = None
            self.context_menu_position = None
            self.context_menu_is_companion = False
            self.context_menu_target_id = None
            self.context_menu_target_kind = None
            if state.mouse_pos is None:
                return
            player = runtime.entity(self.service.player_actor_id)
            npc_id = self._npc_at_screen_position(
                runtime, state.mouse_pos, player.position.map_id,
            )
            if npc_id is not None:
                companion_service = getattr(
                    self.service, "companion_command_service", None,
                )
                companion_registry = getattr(companion_service, "registry", None)
                self.context_menu_is_companion = (
                    companion_registry is not None
                    and companion_registry.get(npc_id) is not None
                )
                self.context_menu_npc_id = npc_id
                menu_x, menu_y = state.mouse_pos
                if self._panel is not None:
                    menu_x = min(
                        max(self._panel.left, menu_x),
                        max(self._panel.left, self._panel.right - 176),
                    )
                    menu_y = min(
                        max(self._panel.top, menu_y),
                        max(self._panel.top, self._panel.bottom - 56),
                    )
                self.context_menu_position = (menu_x, menu_y)
                return (
                    "companion_menu" if self.context_menu_is_companion
                    else "npc_menu"
                )

            if (
                self._panel is None
                or not self._panel.collidepoint(state.mouse_pos)
            ):
                return
            world_point = self.transform.screen_to_world_point(*state.mouse_pos)
            scene_object = (
                self._scene_pipeline.object_at_world_point(
                    player.position.map_id, world_point,
                )
                if self._scene_pipeline is not None else None
            )
            if scene_object is not None and scene_object.kind == "structure":
                structure_cell = LocalHexPosition.from_hex_coord(
                    world_point_to_hex(
                        WorldPoint(scene_object.world_x, scene_object.world_y),
                        runtime.HEX_SIZE,
                    )
                )
                actor_cell = player.position.cell
                distance = (
                    abs(actor_cell.q - structure_cell.q)
                    + abs(actor_cell.r - structure_cell.r)
                    + abs(
                        actor_cell.q + actor_cell.r
                        - structure_cell.q - structure_cell.r
                    )
                ) // 2
                if distance <= 1:
                    self.context_menu_target_kind = "structure"
                    self.context_menu_target_id = scene_object.object_id
                else:
                    self.selected_scene_object_id = scene_object.object_id
                    return "inspect"
            elif scene_object is not None:
                self.selected_scene_object_id = scene_object.object_id
                return "inspect"
            else:
                target = self.service.world_target_at_world_point(
                    player.position.map_id, world_point,
                )
                if target is not None:
                    self.context_menu_target_kind, self.context_menu_target_id = target
                else:
                    transition_id = self.service.transition_at_world_point(
                        player.position.map_id, world_point,
                    )
                    if transition_id is not None:
                        self.context_menu_target_kind = "door"
                        self.context_menu_target_id = transition_id
            if self.context_menu_target_id is not None:
                menu_x, menu_y = state.mouse_pos
                menu_x = min(
                    max(self._panel.left, menu_x),
                    max(self._panel.left, self._panel.right - 176),
                )
                menu_y = min(
                    max(self._panel.top, menu_y),
                    max(self._panel.top, self._panel.bottom - 56),
                )
                self.context_menu_position = (menu_x, menu_y)
                return "world_target_menu"
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
                    result = self.service.hex_actor_binding.transition(
                        actor_id,
                        transition.transition_id,
                    )
                    if result.success:
                        self._visual_map_id = None
                        self._visual_cell = None
                        self._visual_position = None
                        self._visual_moving = False
                else:
                    result = self.service.hex_actor_binding.move(actor_id, direction)
                    self._record_move_result(
                        entity.position.map_id, entity.position.cell, result,
                    )
        if manual_move:
            self._clear_move_goal()
        elif state.mouse_clicked and state.mouse_pos is not None:
            if (
                self.context_menu_target_kind is not None
                and self.context_menu_target_id is not None
                and self.context_menu_position is not None
            ):
                menu_x, menu_y = self.context_menu_position
                mouse_x, mouse_y = state.mouse_pos
                target_kind = self.context_menu_target_kind
                target_id = self.context_menu_target_id
                if menu_x <= mouse_x <= menu_x + 176 and menu_y <= mouse_y <= menu_y + 56:
                    first_option = mouse_y < menu_y + 28
                    self.context_menu_target_kind = None
                    self.context_menu_target_id = None
                    self.context_menu_position = None
                    if not first_option:
                        self.selected_interaction_target_id = target_id
                        return "inspect_target"
                    if target_kind == "resource_node":
                        self.selected_interaction_target_id = target_id
                        return "gather"
                    if target_kind == "container":
                        return f"container:{target_id}"
                    if target_kind == "door":
                        return f"door:{target_id}"
                    if target_kind == "structure":
                        return f"structure:{target_id}"
                self.context_menu_target_kind = None
                self.context_menu_target_id = None
                self.context_menu_position = None
            if self.context_menu_npc_id is not None and self.context_menu_position is not None:
                menu_x, menu_y = self.context_menu_position
                mouse_x, mouse_y = state.mouse_pos
                if menu_x <= mouse_x <= menu_x + 176 and menu_y <= mouse_y <= menu_y + 56:
                    first_option = mouse_y < menu_y + 28
                    npc_id = self.context_menu_npc_id
                    is_companion = self.context_menu_is_companion
                    self.context_menu_npc_id = None
                    self.context_menu_position = None
                    self.context_menu_is_companion = False
                    if is_companion:
                        self.service.command_companion(
                            npc_id, "follow" if first_option else "wait",
                        )
                        return "companion_command"
                    self.selected_npc_id = npc_id
                    return "dialogue" if first_option else "inspect_npc"
                self.context_menu_npc_id = None
                self.context_menu_position = None
                self.context_menu_is_companion = False
            player = runtime.entity(self.service.player_actor_id)
            npc_id = self._npc_at_screen_position(
                runtime, state.mouse_pos, player.position.map_id,
            )
            self.context_menu_npc_id = None
            self.context_menu_position = None
            if npc_id is not None:
                self._clear_move_goal()
                self.selected_npc_id = npc_id
                self.selected_scene_object_id = None
                self.context_menu_npc_id = None
                self.context_menu_position = None
                return "dialogue"
            if self._panel is None or not self._panel.collidepoint(state.mouse_pos):
                return None
            actor_id = self.service.player_actor_id
            entity = runtime.entity(actor_id)
            if self._scene_pipeline is not None:
                world_point = self.transform.screen_to_world_point(*state.mouse_pos)
                scene_object = self._scene_pipeline.object_at_world_point(
                    entity.position.map_id, world_point, self.transform,
                )
                if scene_object is not None:
                    self._clear_move_goal()
                    self.selected_scene_object_id = scene_object.object_id
                    return "inspect"
            self.selected_scene_object_id = None
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
                self._record_move_result(
                    entity.position.map_id, entity.position.cell, result,
                )
                if not result.success or result.position.cell == goal:
                    self._clear_move_goal()

    def _ensure_character_animators(self, renderer):
        """Create directional sprite sets lazily after Pygame is initialized."""
        if self._character_sprite_factory is not None:
            return
        if not callable(getattr(renderer.pg, "Surface", None)) or not hasattr(renderer.pg, "SRCALPHA"):
            return
        self._character_sprite_factory = ProceduralCharacterSpriteFactory()
        self._player_animator = self._character_sprite_factory.create_animator(
            renderer.pg, palette="player",
        )

    def _animator_for_actor(self, renderer, actor_id, *, player=False):
        self._ensure_character_animators(renderer)
        if player:
            return self._player_animator
        animator = self._npc_animators.get(actor_id)
        if animator is None:
            animator = self._character_sprite_factory.create_animator(
                renderer.pg, palette="npc",
            )
            self._npc_animators[actor_id] = animator
        return animator

    def _player_animation_state(self, moving):
        if not moving:
            return "idle"
        mode = getattr(self.service, "_player_movement_mode", None)
        return "run" if getattr(mode, "value", None) == "running" else "walk"

    def _direction_from_world_delta(self, dx, dy):
        screen_dx, screen_dy = self.transform.project_vector(dx, dy)
        if abs(screen_dx) + abs(screen_dy) < 1e-8:
            return "south"
        angle = math.degrees(math.atan2(screen_dy, screen_dx))
        directions = (
            "east", "south_east", "south", "south_west",
            "west", "north_west", "north", "north_east",
        )
        return directions[int(round(angle / 45.0)) % 8]

    def _set_player_facing_from_world_delta(self, dx, dy):
        direction = self._direction_from_world_delta(dx, dy)
        if direction:
            self._player_facing = direction

    def _ensure_scene_pipeline(self, renderer):
        """Load validated map-authored presentation props once per gameplay view."""
        if self._scene_pipeline is not None:
            return
        package_path = getattr(self.service, "_content_package_path", None)
        if package_path is None:
            return
        self._scene_pipeline = SceneObjectPipeline(
            package_path, renderer.pg, self.HEX_SIZE,
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
            self._panel = panel

            world_centers = tuple(
                self.transform.axial_to_world(position.to_hex_coord())
                for position in map_definition.valid_cells
            )
            min_x = min(point[0] for point in world_centers) - self.HEX_SIZE
            min_y = min(point[1] for point in world_centers) - self.HEX_SIZE
            max_x = max(point[0] for point in world_centers) + self.HEX_SIZE
            max_y = max(point[1] for point in world_centers) + self.HEX_SIZE
            self._ensure_visual_position(
                player.position.map_id,
                player.position.cell,
                player.continuous_position.point if player.continuous_position is not None else None,
            )
            target = self._visual_position
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
                projection=self.transform.projection,
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

            visible_cell_count = 0
            visible_scene_count = 0
            culled_scene_count = 0
            drawn_scene_count = 0
            drawn_actor_count = 0
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
                    visible_cell_count += 1
                    self.terrain.draw_cell(
                        renderer,
                        position,
                        cell,
                        center,
                        radius,
                    )

            self._ensure_scene_pipeline(renderer)
            self._ensure_character_animators(renderer)
            draw_items = []
            entities = tuple(
                entity for entity in runtime.entities()
                if entity.position.map_id == player.position.map_id
            )
            for entity in entities:
                if entity.kind == "player":
                    foot = self.transform.world_to_screen(*self._visual_position)
                    moving = self._visual_moving
                elif entity.continuous_position is not None:
                    visual = self._npc_visual_states.get(entity.entity_id)
                    world_position = (
                        visual["current"] if visual else (
                            entity.continuous_position.point.x,
                            entity.continuous_position.point.y,
                        )
                    )
                    foot = self.transform.world_to_screen(*world_position)
                    moving = bool(visual and visual["moving"])
                else:
                    foot = self.transform.axial_to_screen(
                        entity.position.cell.to_hex_coord()
                    )
                    moving = False
                draw_items.append((
                    1,
                    foot[1],
                    f"actor:{entity.entity_id}",
                    "actor",
                    entity,
                    foot,
                    moving,
                ))

            if self._scene_pipeline is not None:
                for scene_object in self._scene_pipeline.objects_for_map(
                    player.position.map_id
                ):
                    foot = self.transform.world_to_screen(
                        scene_object.world_x, scene_object.world_y
                    )
                    if not self._scene_pipeline.is_visible(
                        scene_object, foot, panel, self.zoom
                    ):
                        culled_scene_count += 1
                        continue
                    visible_scene_count += 1
                    layer_group = (
                        0 if scene_object.layer == "underlay"
                        else 2 if scene_object.layer == "overlay"
                        else 1
                    )
                    draw_items.append((
                        layer_group,
                        foot[1] + scene_object.depth_offset * self.zoom,
                        f"scene:{scene_object.object_id}",
                        "scene",
                        scene_object,
                        foot,
                        False,
                    ))

            ordered_items = DepthSorter.sort_by_depth(
                draw_items,
                lambda item: (item[0], item[1]),
                lambda item: item[2],
            )
            for _, _, _, item_type, item, foot, moving in ordered_items:
                if item_type == "scene":
                    if not self._scene_pipeline.draw(
                        renderer, item, foot, self.zoom
                    ):
                        self._scene_pipeline.draw_fallback(
                            renderer, item, foot, self.zoom,
                        )
                    drawn_scene_count += 1
                    continue
                if item.kind in {"player", "npc"}:
                    animator = self._animator_for_actor(
                        renderer,
                        item.entity_id,
                        player=item.kind == "player",
                    )
                    if animator is None:
                        self.characters.draw(
                            renderer, foot, max(18.0, radius * 1.25),
                            self.elapsed_seconds, moving=moving,
                        )
                        continue
                    npc_visual = (
                        self._npc_visual_states.get(item.entity_id)
                        if item.kind == "npc" else None
                    )
                    animator.select(
                        direction=(
                            self._player_facing if item.kind == "player"
                            else npc_visual["direction"] if npc_visual
                            else animator.direction
                        ),
                        state=(
                            self._player_animation_state(moving)
                            if item.kind == "player"
                            else "walk" if moving else "idle"
                        ),
                    )
                    self.characters.draw_sprite(
                        renderer, animator.current_frame, foot,
                        64.0 * self.zoom, (0.5, 1.0),
                        self._character_sprite_cache,
                    )
                    drawn_actor_count += 1
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
