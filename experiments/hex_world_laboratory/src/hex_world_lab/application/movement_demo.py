"""Single-actor, single-map continuous-movement acceptance prototype."""

from __future__ import annotations

import math
from typing import Callable

import pygame

from hex_world_lab.application.demo_tick_pump import DemoTickPump, TickPumpDiagnostics
from hex_world_lab.camera import (
    CameraBoundsPolicy,
    CameraController,
    ScreenPoint,
    Viewport,
    bounds_from_hex_cells,
)
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
    world_to_axial,
)
from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.environment import (
    EnvironmentalObjectDefinition, EnvironmentalObjectPlacement, EnvironmentalObjectScene,
    environment_debug_visuals, environment_obstacles, environment_sprite_visuals,
)
from hex_world_lab.rendering.pygame_world_renderer import PygameWorldRenderer
from hex_world_lab.rendering.environment_assets import register_environment_assets
from hex_world_lab.rendering.visibility import VisibleAreaCuller, should_use_culling
from hex_world_lab.rendering.snapshot import (
    CellVisual,
    CircleVisual,
    ColliderVisual,
    LineVisual,
    PolygonVisual,
    RenderDebugOptions,
    SpriteVisual,
    WorldRenderSnapshot,
)
from hex_world_lab.movement import MovementConfig, MovementState, Vector2
from hex_world_lab.physics import (
    BoundaryPolicy,
    ActorBodyTransform,
    BodyDefinition,
    CircleShape,
    ContinuousCollisionResolution,
    ConvexPolygonShape,
    ObstacleDefinition,
    build_hex_map_collision_geometry,
)
from hex_world_lab.simulation import (
    CollisionAwareMovementSystem,
    MovementCellTracker,
    SimulationTickCoordinator,
)
from hex_world_lab.world import (
    HexCellData,
    HexMapDefinition,
    HexWorld,
    MapId,
    MovementWorldContext,
    WorldId,
)

WORLD_ID = WorldId("movement-demo-world")
MAP_ID = MapId("movement-demo-map")
MAP_NAME = "Movement Demo Map"
HEX_RADIUS = 32.0
MAP_DISK_RADIUS = 4
TEXT_COLOR = (225, 231, 240)
MUTED_TEXT = (157, 170, 188)
PLAYER_COLLIDER_RADIUS = 8.0
HOUSE_ID = "structure:starter-house"
HOUSE_HALF_WIDTH = 17.0
HOUSE_DOORWAY_HALF_WIDTH = 10.0


def _box_shape(half_width: float, half_height: float) -> ConvexPolygonShape:
    """Build a local-axis-aligned convex wall segment for the demo house."""
    return ConvexPolygonShape((
        Vector2(-half_width, -half_height),
        Vector2(half_width, -half_height),
        Vector2(half_width, half_height),
        Vector2(-half_width, half_height),
    ))


def build_demo_world() -> tuple[HexWorld, MapId]:
    """Create and load the deterministic 61-cell acceptance map."""
    world = HexWorld(WORLD_ID)
    world.register_map(MAP_ID, MAP_NAME)
    layout = HexLayout(
        orientation=HexOrientation.FLAT_TOP,
        radius=HEX_RADIUS,
        origin=WorldPoint(0.0, 0.0),
    )
    blocked_cells = {
        AxialCoord(2, r) for r in range(0, 3)
    } | {AxialCoord(-2, 0)}
    cells = {
        AxialCoord(q, r): HexCellData(
            "grass", True, AxialCoord(q, r) in blocked_cells
        )
        for q in range(-MAP_DISK_RADIUS, MAP_DISK_RADIUS + 1)
        for r in range(-MAP_DISK_RADIUS, MAP_DISK_RADIUS + 1)
        if max(abs(q), abs(r), abs(q + r)) <= MAP_DISK_RADIUS
    }
    definition = HexMapDefinition(WORLD_ID, MAP_ID, MAP_NAME, layout, cells)
    world.load_map(definition)
    return world, MAP_ID


class MovementDemo:
    """Orchestrate movement, cell tracking, input, tick pump and read-only drawing."""

    __slots__ = (
        "world",
        "map_id",
        "keyboard",
        "movement_system",
        "body_definition",
        "collision_geometry",
        "cell_tracker",
        "tick_pump",
        "tick_coordinator",
        "_layout",
        "_movement_config",
        "house_center",
        "_font",
        "_small_font",
        "_last_diagnostics",
        "camera",
        "renderer",
        "selected_cell",
        "_visibility_culler",
        "environment_scene",
        "environment_asset_sizes",
        "environment_obstacle_ids",
    )

    def __init__(
        self,
        *,
        movement_speed: float = 60.0,
        viewport: Viewport | None = None,
        key_state_provider: Callable[[], object] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.world, self.map_id = build_demo_world()
        definition = self.world.get_map(self.map_id)
        assert definition is not None
        self._layout = definition.layout
        start_position = axial_to_world(AxialCoord(0, 0), self._layout)
        map_bounds = bounds_from_hex_cells(definition.cells, self._layout)
        self.camera = CameraController(
            viewport or Viewport(960, 640),
            start_position,
            bounds=map_bounds,
            bounds_policy=CameraBoundsPolicy.UNBOUNDED,
        )
        self.camera.set_target(start_position)
        self.renderer = PygameWorldRenderer()
        self.environment_asset_sizes = register_environment_assets(self.renderer)
        self._visibility_culler = VisibleAreaCuller()
        self.selected_cell: AxialCoord | None = None
        self._movement_config = MovementConfig(max_speed=movement_speed)
        tree_center = axial_to_world(AxialCoord(0, 2), self._layout)
        rock_center = axial_to_world(AxialCoord(-2, 2), self._layout)
        bush_center = axial_to_world(AxialCoord(3, -2), self._layout)
        grass_center = axial_to_world(AxialCoord(-4, 0), self._layout)
        flower_center = axial_to_world(AxialCoord(3, 1), self._layout)
        wall_center = axial_to_world(AxialCoord(0, -2), self._layout)
        self.house_center = axial_to_world(AxialCoord(-3, 0), self._layout)
        environment_definitions = (
            EnvironmentalObjectDefinition(
                "tree", "tree", (0.5, 0.94), (0.5, 0.82),
                (0.04, 0.02, 0.92, 0.68),
                # Coordinates are relative to the sprite's ground anchor.
                # The visible trunk/root base occupies roughly x=-35..28, y=-1..13.
                # Keep the canopy passable; block only the trunk/root contact footprint.
                ConvexPolygonShape((
                    Vector2(-31.0, 0.0), Vector2(-16.0, 13.0),
                    Vector2(14.0, 13.0), Vector2(29.0, 0.0),
                )),
            ),
            EnvironmentalObjectDefinition(
                "rock", "rock", (0.5, 0.92), (0.5, 0.84), None,
                # The 66x48 surface uses a (0.5, 0.92) anchor: convert its
                # visible silhouette pixels into ground-anchor-relative world units.
                # This keeps collision on the rock instead of displaced below it.
                ConvexPolygonShape((
                    Vector2(-28.0, 13.2), Vector2(-24.0, 26.2),
                    Vector2(-13.0, 36.2), Vector2(1.0, 39.2),
                    Vector2(14.0, 32.2), Vector2(28.0, 19.2),
                    Vector2(24.0, 7.2), Vector2(10.0, 2.2),
                    Vector2(-16.0, 4.2),
                )),
            ),
            EnvironmentalObjectDefinition(
                "bush", "bush", (0.5, 0.92), (0.5, 0.84),
                (0.05, 0.08, 0.9, 0.78), None,
            ),
            EnvironmentalObjectDefinition(
                "grass", "grass", (0.5, 0.94), (0.5, 0.84), None, None,
            ),
            EnvironmentalObjectDefinition(
                "flower", "flower", (0.5, 0.94), (0.5, 0.84), None, None,
            ),
        )
        environment_placements = (
            EnvironmentalObjectPlacement("tree", "tree", WORLD_ID, self.map_id, tree_center),
            EnvironmentalObjectPlacement("rock", "rock", WORLD_ID, self.map_id, rock_center),
            EnvironmentalObjectPlacement("bush", "bush", WORLD_ID, self.map_id, bush_center),
            EnvironmentalObjectPlacement("grass", "grass", WORLD_ID, self.map_id, grass_center),
            EnvironmentalObjectPlacement("flower", "flower", WORLD_ID, self.map_id, flower_center),
        )
        self.environment_scene = EnvironmentalObjectScene(
            WORLD_ID, self.map_id, environment_definitions, environment_placements
        )
        object_obstacles = environment_obstacles(self.environment_scene)
        self.environment_obstacle_ids = frozenset(item.obstacle_id for item in object_obstacles)
        wall_obstacle = ObstacleDefinition(
            "object:wall", self.map_id,
            ConvexPolygonShape((
                Vector2(-15.0, -4.0), Vector2(15.0, -4.0),
                Vector2(15.0, 4.0), Vector2(-15.0, 4.0),
            )),
            wall_center,
        )
        object_obstacles = (*object_obstacles, wall_obstacle)
        # Placeholder structure only: independent convex walls leave a doorway.
        house_wall_specs = (
            ("left", -15.0, 0.0, 2.0, 15.0),
            ("right", 15.0, 0.0, 2.0, 15.0),
            ("back", 0.0, 13.0, 13.0, 2.0),
            ("front-left", -(HOUSE_HALF_WIDTH + HOUSE_DOORWAY_HALF_WIDTH) / 2, -13.0, (HOUSE_HALF_WIDTH - HOUSE_DOORWAY_HALF_WIDTH) / 2, 2.0),
            ("front-right", (HOUSE_HALF_WIDTH + HOUSE_DOORWAY_HALF_WIDTH) / 2, -13.0, (HOUSE_HALF_WIDTH - HOUSE_DOORWAY_HALF_WIDTH) / 2, 2.0),
        )
        house_obstacles = tuple(
            ObstacleDefinition(
                f"{HOUSE_ID}:{wall_name}",
                self.map_id,
                _box_shape(half_width, half_height),
                WorldPoint(
                    self.house_center.x + offset_x,
                    self.house_center.y + offset_y,
                ),
            )
            for wall_name, offset_x, offset_y, half_width, half_height
            in house_wall_specs
        )
        object_obstacles = (*object_obstacles, *house_obstacles)
        self.collision_geometry = build_hex_map_collision_geometry(
            self.world.view,
            self.world.runtime,
            self.map_id,
            boundary_policy=BoundaryPolicy.OPEN,
            object_obstacles=object_obstacles,
        )
        self.body_definition = BodyDefinition(
            "demo-player",
            CircleShape(PLAYER_COLLIDER_RADIUS),
            body_height=1.8,
        )
        self.movement_system = CollisionAwareMovementSystem(
            MovementState(position=start_position),
            self._movement_config,
            self.body_definition,
            self.collision_geometry,
        )
        context = MovementWorldContext(self.world, self.map_id)
        self.cell_tracker = MovementCellTracker(context)
        self.cell_tracker.update(start_position)
        self.keyboard = (
            PygameKeyboardAdapter()
            if key_state_provider is None
            else PygameKeyboardAdapter(key_state_provider)
        )
        self.tick_coordinator = SimulationTickCoordinator(
            self.movement_system,
            self.keyboard.read_intent,
            self.cell_tracker,
        )
        callback = self._advance_tick
        pump_options = {"first_tick_number": self.tick_coordinator.next_tick_number}
        self.tick_pump = (
            DemoTickPump(callback, **pump_options)
            if clock is None
            else DemoTickPump(callback, clock=clock, **pump_options)
        )
        self._last_diagnostics: TickPumpDiagnostics | None = None
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None

    @property
    def state(self) -> MovementState:
        return self.movement_system.state

    @property
    def last_collision_resolution(self) -> ContinuousCollisionResolution | None:
        """Return the most recent read-only collision resolution snapshot."""
        return self.movement_system.last_resolution

    @property
    def diagnostics(self) -> TickPumpDiagnostics:
        return self.tick_pump.diagnostics

    @property
    def current_resolution(self):
        return self.cell_tracker.current_resolution

    def start(self) -> None:
        """Start the demo's sole real-time tick source."""
        self.tick_pump.start()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.keyboard.handle_event(event)
        if event.type == pygame.MOUSEWHEEL:
            self.camera.zoom_by_steps(event.y)
        elif event.type == pygame.VIDEORESIZE:
            self.camera.set_viewport(Viewport(*event.size))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.select_screen_point(ScreenPoint(*event.pos))

    def update_camera(self, delta_seconds: float):
        """Update presentation-only follow using elapsed render time."""
        self.camera.set_target(self.state.position)
        return self.camera.update(delta_seconds)

    def select_screen_point(self, point: ScreenPoint) -> AxialCoord | None:
        """Resolve a viewport pixel to an existing map cell, or None."""
        if not isinstance(point, ScreenPoint):
            raise TypeError("point must be a ScreenPoint")
        world_point = self.camera.transform.screen_to_world(point)
        candidate = world_to_axial(world_point, self._layout, self.selected_cell)
        definition = self.world.get_map(self.map_id)
        assert definition is not None
        self.selected_cell = candidate if candidate in definition.cells else None
        return self.selected_cell

    def build_render_snapshot(
        self, *, cull_to_viewport: bool = True,
        debug_options: RenderDebugOptions | None = None,
    ) -> WorldRenderSnapshot:
        """Create immutable world-space render data without changing simulation.

        Visible-area culling happens before DTO allocation, avoiding per-frame
        snapshot objects for cells outside the viewport.
        """
        definition = self.world.get_map(self.map_id)
        assert definition is not None
        active = self.current_resolution
        active_coord = None if active is None else active.coord
        culling_active = cull_to_viewport and should_use_culling(len(definition.cells))
        visible_region = (
            self._visibility_culler.visible_region(self.camera.transform, self._layout)
            if culling_active else None
        )
        visible_coords = (
            self._visibility_culler.visible_cells(
                definition.cells, self._layout, self.camera.transform
            )
            if culling_active
            else tuple(sorted(definition.cells, key=lambda item: (item.q, item.r)))
        )
        cells = tuple(
            CellVisual(coord, definition.cells[coord].has_obstacle, coord == active_coord)
            for coord in visible_coords
        )
        circles = []
        polygons = []
        colliders = []
        for obstacle in self.collision_geometry.obstacles:
            shape = obstacle.world_shape()
            if isinstance(shape, CircleShape):
                if visible_region is not None and not visible_region.intersects_aabb(
                    shape.center.x - shape.radius, shape.center.y - shape.radius,
                    shape.center.x + shape.radius, shape.center.y + shape.radius,
                ):
                    continue
                circle_visual = CircleVisual(
                    WorldPoint(shape.center.x, shape.center.y), shape.radius
                )
                if obstacle.obstacle_id not in self.environment_obstacle_ids:
                    circles.append(circle_visual)
                colliders.append(ColliderVisual(obstacle.obstacle_id, circle_visual, "obstacle"))
            else:
                if visible_region is not None:
                    min_x = min(vertex.x for vertex in shape.vertices)
                    min_y = min(vertex.y for vertex in shape.vertices)
                    max_x = max(vertex.x for vertex in shape.vertices)
                    max_y = max(vertex.y for vertex in shape.vertices)
                    if not visible_region.intersects_aabb(min_x, min_y, max_x, max_y):
                        continue
                polygon_visual = PolygonVisual(
                    tuple(WorldPoint(vertex.x, vertex.y) for vertex in shape.vertices),
                    obstacle.obstacle_id.startswith("cell:"),
                )
                if obstacle.obstacle_id not in self.environment_obstacle_ids:
                    polygons.append(polygon_visual)
                colliders.append(ColliderVisual(obstacle.obstacle_id, polygon_visual, "obstacle"))

        actor_shape = ActorBodyTransform(self.state.position).transform_shape(self.body_definition)
        if isinstance(actor_shape, CircleShape):
            actor_visual = CircleVisual(
                WorldPoint(actor_shape.center.x, actor_shape.center.y), actor_shape.radius
            )
        else:
            actor_visual = PolygonVisual(
                tuple(WorldPoint(vertex.x, vertex.y) for vertex in actor_shape.vertices)
            )
        colliders.append(ColliderVisual(self.body_definition.body_id, actor_visual, "actor"))

        boundaries = tuple(
            LineVisual(edge.start, edge.end, "boundary", 2)
            for edge in self.collision_geometry.boundary_edges
        )

        def house_point(offset_x: float, offset_y: float) -> WorldPoint:
            return WorldPoint(
                self.house_center.x + offset_x,
                self.house_center.y + offset_y,
            )

        frame_segments = (
            ((-17, 17), (17, 17)),
            ((-17, 17), (-17, -17)),
            ((17, 17), (17, -17)),
            ((-HOUSE_HALF_WIDTH, -HOUSE_HALF_WIDTH), (-HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH)),
            ((HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (HOUSE_HALF_WIDTH, -HOUSE_HALF_WIDTH)),
            ((-HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (-HOUSE_DOORWAY_HALF_WIDTH, -8)),
            ((HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (HOUSE_DOORWAY_HALF_WIDTH, -8)),
        )
        detail_segments = (
            ((-12, 0), (12, 0)),
            ((-12, 0), (-17, 17)),
            ((12, 0), (17, 17)),
            ((-5, -8), (5, -8)),
        )
        house_lines = tuple(
            LineVisual(house_point(*start), house_point(*end), "frame", 3)
            for start, end in frame_segments
        ) + tuple(
            LineVisual(house_point(*start), house_point(*end), "detail", 2)
            for start, end in detail_segments
        )
        return WorldRenderSnapshot(
            cells=cells,
            circles=tuple(circles),
            polygons=tuple(polygons),
            boundaries=boundaries,
            house_lines=house_lines,
            actor_position=self.state.position,
            actor_radius=PLAYER_COLLIDER_RADIUS,
            selected_cell=self.selected_cell,
            colliders=tuple(colliders),
            sprites=(SpriteVisual(
                visual_id="demo-player", asset_key="demo-player",
                ground_anchor=self.state.position,
                depth_anchor_y=self.state.position.y,
                layer_priority=10,
            ), *environment_sprite_visuals(self.environment_scene, self.environment_asset_sizes)),
            debug_options=debug_options or RenderDebugOptions(),
            visible_region=visible_region,
            environment_debug=environment_debug_visuals(self.environment_scene, self.environment_asset_sizes),
        )

    def pump(self) -> TickPumpDiagnostics:
        self._last_diagnostics = self.tick_pump.pump()
        return self._last_diagnostics

    def _advance_tick(self, tick_number: int) -> MovementState:
        """Delegate one fixed tick to the authoritative simulation coordinator."""
        return self.tick_coordinator.advance_tick(tick_number)

    def render(
        self, surface: pygame.Surface, render_fps: float = 0.0,
        debug_options: RenderDebugOptions | None = None,
    ) -> None:
        """Draw the current snapshot without mutating simulation state."""
        if not isinstance(surface, pygame.Surface):
            raise TypeError("surface must be a pygame.Surface")
        if self._font is None:
            self._font = pygame.font.Font(None, 23)
            self._small_font = pygame.font.Font(None, 19)

        self.renderer.render(
            surface,
            self.build_render_snapshot(debug_options=debug_options),
            self._layout,
            self.camera.transform,
        )

        self._draw_diagnostics(surface, render_fps)

    def _draw_diagnostics(self, surface: pygame.Surface, render_fps: float) -> None:
        assert self._font is not None and self._small_font is not None
        resolution = self.current_resolution
        diagnostics = self._last_diagnostics or self.tick_pump.diagnostics
        velocity = self.state.velocity
        speed = math.hypot(velocity.x, velocity.y)
        mode = self.state.mode
        multiplier = self._movement_config.speed_multiplier_for(mode)
        mode_speed = self._movement_config.max_speed * multiplier
        cell = "—" if resolution is None else f"q={resolution.coord.q}, r={resolution.coord.r}"
        cell_data = (
            "unknown"
            if resolution is None
            else ("present" if resolution.cell_data is not None else "absent")
        )
        completed_tick = diagnostics.next_tick_number - 1
        collision = self.last_collision_resolution
        contact_count = 0 if collision is None else len(collision.contacts)
        impact_count = 0 if collision is None else len(collision.impacts)
        lines = (
            f"World: {self.world.world_id.value}",
            f"Map: {self.map_id.value}",
            f"Position: x={self.state.position.x:.3f}, y={self.state.position.y:.3f}",
            f"Velocity: x={velocity.x:.2f}, y={velocity.y:.2f}, speed={speed:.2f}",
            f"Mode: {mode.name}",
            f"Multiplier: {multiplier:.2f}x | Mode speed: {mode_speed:.1f} units/s",
            f"Cell: {cell} | data: {cell_data}",
            (
                f"Collider: circle r={PLAYER_COLLIDER_RADIUS:.1f} | "
                f"contacts: {contact_count} | impacts: {impact_count}"
            ),
            f"Last tick: {completed_tick if completed_tick >= 0 else '—'}",
            f"Render FPS: {render_fps:.1f}",
            f"Ticks this frame: {diagnostics.last_frame_tick_count}",
            f"Pending ticks: {diagnostics.pending_full_ticks} | debt: {diagnostics.time_debt_seconds:.4f}s",
        )
        panel_width = min(
            max(440, max(self._small_font.size(line)[0] for line in lines) + 20),
            max(300, surface.get_width() - 24),
        )
        panel_height = 18 + len(lines) * 23
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((9, 13, 20, 218))
        surface.blit(panel, (12, 12))
        for index, line in enumerate(lines):
            font = self._font if index < 2 else self._small_font
            color = TEXT_COLOR if index < 2 else MUTED_TEXT
            rendered = font.render(line, True, color)
            surface.blit(rendered, (22, 20 + index * 23))
