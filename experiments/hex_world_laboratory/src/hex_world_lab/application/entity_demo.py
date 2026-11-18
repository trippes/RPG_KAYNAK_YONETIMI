"""Multi-entity acceptance scene composed around the existing player movement demo."""
from __future__ import annotations
import pygame
from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.camera import ScreenPoint
from hex_world_lab.application.entity_world_coordinator import EntityWorldCoordinator
from hex_world_lab.entities import EntityId, EntityKind, EntityLocation, EntityRecord, EntityTransform
from hex_world_lab.interaction import InteractionProfile, TargetQuery
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.geometry import AxialCoord, WorldPoint, axial_to_world
from hex_world_lab.physics import BodyDefinition, CircleShape, ActorBodyTransform
from hex_world_lab.rendering import (
    WorldRenderSnapshot, SpriteVisual, ColliderVisual, CircleVisual, PolygonVisual, RenderDebugOptions,
)
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset


class EntityDemo:
    """Player movement remains authoritative in MovementDemo; other entities are stationary."""
    def __init__(self, movement_demo: MovementDemo | None = None) -> None:
        self.movement = movement_demo or MovementDemo()
        self.world, self.map_id = self.movement.world, self.movement.map_id
        self.coordinator = EntityWorldCoordinator(self.world)
        self.coordinator.spatial_index.activate_map(self.map_id)
        self.player_id = EntityId("entity-demo-player")
        self.npc_ids = (EntityId("npc-guard"), EntityId("npc-trader"))
        self.resource_ids = (EntityId("resource-herb"), EntityId("resource-ore"))
        player_profile = InteractionProfile(True, 36.0, frozenset({"inspect"}), 10)
        self.coordinator.register_entity(EntityRecord(
            self.player_id, EntityKind.PLAYER,
            EntityTransform(EntityLocation(self.world.world_id, self.map_id, self.movement.state.position)),
            self.movement.body_definition, player_profile))
        npc_points = (WorldPoint(92.0, 38.0), WorldPoint(128.0, -42.0))
        for index, (entity_id, point) in enumerate(zip(self.npc_ids, npc_points)):
            body = BodyDefinition(entity_id.value, CircleShape(7.0), body_height=1.7)
            profile = InteractionProfile(True, 22.0, frozenset({"talk", "inspect"}), 8 - index)
            self.coordinator.register_entity(EntityRecord(
                entity_id, EntityKind.NPC,
                EntityTransform(EntityLocation(self.world.world_id, self.map_id, point)), body, profile))
        resource_points = (
            axial_to_world(AxialCoord(2, -1), self.movement._layout),
            axial_to_world(AxialCoord(-1, 1), self.movement._layout),
        )
        for entity_id, point in zip(self.resource_ids, resource_points):
            profile = InteractionProfile(True, 18.0, frozenset({"gather", "inspect"}), 2)
            self.coordinator.register_entity(EntityRecord(
                entity_id, EntityKind.RESOURCE,
                EntityTransform(EntityLocation(self.world.world_id, self.map_id, point)), None, profile))
        self.target_query = TargetQuery(self.coordinator.registry, self.coordinator.spatial_index)
        self.selected_target_id: EntityId | None = None
        self.action_menu_target_id: EntityId | None = None
        self.action_menu_position: tuple[int, int] | None = None
        self._action_menu_items: list[tuple[pygame.Rect, str, str]] = []
        self._register_placeholder_assets()
        self.movement.tick_coordinator.bind_entity_sync_callback(self._sync_player_position)

    def _register_placeholder_assets(self) -> None:
        colors = {"npc-guard": (92, 145, 196), "npc-trader": (191, 151, 83),
                  "resource-herb": (83, 169, 103), "resource-ore": (143, 151, 165)}
        for key, color in colors.items():
            size = (24, 34) if key.startswith("npc-") else (24, 24)
            surface = pygame.Surface(size, pygame.SRCALPHA)
            if key.startswith("npc-"):
                pygame.draw.ellipse(surface, (36, 43, 54), (4, 23, 7, 10))
                pygame.draw.ellipse(surface, (36, 43, 54), (13, 23, 7, 10))
                pygame.draw.polygon(surface, color, ((4, 13), (20, 13), (19, 27), (5, 27)))
                pygame.draw.circle(surface, (225, 190, 154), (12, 8), 6)
            elif key == "resource-herb":
                pygame.draw.circle(surface, color, (12, 12), 9)
                pygame.draw.line(surface, (214, 231, 190), (12, 20), (12, 5), 2)
                pygame.draw.ellipse(surface, (126, 194, 121), (4, 7, 9, 5))
                pygame.draw.ellipse(surface, (126, 194, 121), (12, 4, 9, 5))
            else:
                pygame.draw.polygon(surface, color, ((12, 1), (22, 8), (18, 21), (6, 22), (2, 10)))
                pygame.draw.polygon(surface, (210, 216, 226), ((12, 1), (22, 8), (18, 21), (6, 22), (2, 10)), 2)
            self.movement.renderer.register_sprite_asset(key, SpriteAsset(surface, 0.5, 1.0))

    def _sync_player_position(self, position: WorldPoint) -> None:
        if not isinstance(position, WorldPoint):
            raise TypeError("position must be a WorldPoint")
        entity = self.coordinator.registry.require(self.player_id)
        if entity.transform.location.position == position:
            return
        transform = EntityTransform(
            EntityLocation(self.world.world_id, self.map_id, position), entity.transform.rotation_radians)
        self.coordinator.update_transform(self.player_id, transform)

    def recruit_guard(self):
        return self.coordinator.companions.recruit(self.player_id, self.npc_ids[0])

    def issue_guard_command(self, command: CompanionCommand):
        return self.coordinator.companions.issue_command(self.npc_ids[0], command)

    def select_world_point(self, point: WorldPoint) -> EntityId | None:
        self.selected_target_id = self.target_query.select_target(point, self.map_id)
        return self.selected_target_id

    def select_screen_point(self, point: ScreenPoint) -> EntityId | None:
        if not isinstance(point, ScreenPoint):
            raise TypeError("point must be a ScreenPoint")
        return self.select_world_point(self.movement.camera.transform.screen_to_world(point))

    def _action_items(self) -> tuple[tuple[str, str], ...]:
        target = self.action_menu_target_id
        if target is None:
            return ()
        relationship = self.coordinator.companions.get_relationship(target)
        if relationship is None:
            return (("Yoldaş olarak al", "recruit"),)
        return (("Takip et (FOLLOW)", "follow"), ("Bekle (WAIT)", "wait"),
                ("Geri dön (RETURN)", "return"), ("Yoldaşlıktan çıkar", "dismiss"))

    def _run_action(self, action: str) -> None:
        target = self.action_menu_target_id
        if target is None:
            return
        if action == "recruit":
            self.coordinator.companions.recruit(self.player_id, target)
        elif action == "follow":
            self.coordinator.companions.issue_command(target, CompanionCommand.FOLLOW)
        elif action == "wait":
            self.coordinator.companions.issue_command(target, CompanionCommand.WAIT)
        elif action == "return":
            self.coordinator.companions.issue_command(target, CompanionCommand.RETURN)
        elif action == "dismiss":
            self.coordinator.companions.dismiss(target)
        self.action_menu_target_id = None
        self.action_menu_position = None
        self._action_menu_items = []

    def handle_event(self, event: pygame.event.Event) -> EntityId | None:
        self.movement.handle_event(event)
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        if event.button == 3:
            world_point = self.movement.camera.transform.screen_to_world(ScreenPoint(*event.pos))
            target_id = self.target_query.select_target(world_point, self.map_id, frozenset({"talk"}))
            target = self.coordinator.registry.get(target_id) if target_id is not None else None
            if target is not None and target.kind is EntityKind.NPC:
                self.action_menu_target_id, self.action_menu_position = target_id, event.pos
            else:
                self.action_menu_target_id = self.action_menu_position = None
                self._action_menu_items = []
            return target_id
        if event.button == 1:
            for rect, _, action in self._action_menu_items:
                if rect.collidepoint(event.pos):
                    self._run_action(action)
                    return self.selected_target_id
            if self.action_menu_target_id is not None:
                self.action_menu_target_id = self.action_menu_position = None
                self._action_menu_items = []
            return self.select_screen_point(ScreenPoint(*event.pos))
        return None

    def build_render_snapshot(self, debug_options: RenderDebugOptions | None = None) -> WorldRenderSnapshot:
        base = self.movement.build_render_snapshot(debug_options=debug_options)
        sprites, colliders = list(base.sprites), list(base.colliders)
        for entity in self.coordinator.registry.entities_for_map(self.world.world_id, self.map_id):
            if entity.entity_id == self.player_id:
                continue
            point = entity.transform.location.position
            if entity.kind is EntityKind.NPC:
                sprites.append(SpriteVisual(entity.entity_id.value, entity.entity_id.value, point, point.y, 12))
            else:
                sprites.append(SpriteVisual(entity.entity_id.value, entity.entity_id.value, point, point.y, 18))
                radius = entity.interaction_profile.interaction_radius
                colliders.append(ColliderVisual(entity.entity_id.value, CircleVisual(point, radius), "interaction"))
            if entity.body is not None:
                shape = ActorBodyTransform(point, entity.transform.rotation_radians).transform_shape(entity.body)
                visual = (
                    CircleVisual(WorldPoint(shape.center.x, shape.center.y), shape.radius)
                    if isinstance(shape, CircleShape)
                    else PolygonVisual(tuple(WorldPoint(v.x, v.y) for v in shape.vertices))
                )
                colliders.append(ColliderVisual(entity.entity_id.value, visual, "entity"))
        return WorldRenderSnapshot(
            cells=base.cells, circles=base.circles, polygons=base.polygons,
            boundaries=base.boundaries, house_lines=base.house_lines,
            actor_position=base.actor_position, actor_radius=base.actor_radius,
            selected_cell=base.selected_cell, sprites=tuple(sprites), colliders=tuple(colliders),
            debug_options=base.debug_options, visible_region=base.visible_region,
            environment_debug=base.environment_debug,
        )

    def render(self, surface: pygame.Surface, render_fps: float = 0.0,
               debug_options: RenderDebugOptions | None = None) -> None:
        snapshot = self.build_render_snapshot(debug_options)
        self.movement.renderer.render(surface, snapshot, self.movement._layout, self.movement.camera.transform)
        if self.movement._font is None:
            self.movement._font = pygame.font.Font(None, 23)
            self.movement._small_font = pygame.font.Font(None, 19)
        self.movement._draw_diagnostics(surface, render_fps)
        relationships = self.coordinator.companions.all_relationships()
        companion_text = "none" if not relationships else ", ".join(
            f"{r.companion_id.value}:{r.command.value}#{r.command_revision}" for r in relationships)
        selected = "none" if self.selected_target_id is None else self.selected_target_id.value
        entities = self.coordinator.registry.all_entities()
        counts = {kind: sum(e.kind.value == kind for e in entities) for kind in ("player", "npc", "resource")}
        lines = (f"Entities: P{counts['player']} / NPC{counts['npc']} / R{counts['resource']}",
                 f"Selected target: {selected}", f"Companions: {companion_text}")
        font = pygame.font.Font(None, 19)
        width = max(font.size(line)[0] for line in lines) + 20
        panel = pygame.Surface((width, 68), pygame.SRCALPHA)
        panel.fill((9, 13, 20, 218))
        x, y = max(12, surface.get_width() - width - 12), max(12, surface.get_height() - 80)
        surface.blit(panel, (x, y))
        for index, line in enumerate(lines):
            surface.blit(font.render(line, True, (210, 220, 233)), (x + 10, y + 8 + index * 19))
        self._draw_action_menu(surface)

    def _draw_action_menu(self, surface: pygame.Surface) -> None:
        if self.action_menu_target_id is None or self.action_menu_position is None:
            self._action_menu_items = []
            return
        target = self.coordinator.registry.get(self.action_menu_target_id)
        if target is None or target.kind is not EntityKind.NPC:
            self.action_menu_target_id = self.action_menu_position = None
            self._action_menu_items = []
            return
        font, title_font = pygame.font.Font(None, 22), pygame.font.Font(None, 20)
        items = self._action_items()
        width = max(190, max((font.size(label)[0] for label, _ in items), default=0) + 24)
        row_height, height = 30, 30 + len(items) * 30 + 8
        x, y = self.action_menu_position
        x = max(8, min(x, surface.get_width() - width - 8))
        y = max(8, min(y, surface.get_height() - height - 8))
        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (17, 23, 33), panel, border_radius=6)
        pygame.draw.rect(surface, (112, 133, 158), panel, 1, border_radius=6)
        surface.blit(title_font.render("NPC Eylemleri", True, (225, 233, 244)), (x + 12, y + 8))
        self._action_menu_items = []
        for index, (label, action) in enumerate(items):
            rect = pygame.Rect(x + 5, y + 32 + index * row_height, width - 10, row_height)
            pygame.draw.rect(surface, (49, 66, 86), rect, border_radius=4)
            surface.blit(font.render(label, True, (235, 240, 247)), (rect.x + 8, rect.y + 6))
            self._action_menu_items.append((rect, label, action))
