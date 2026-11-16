"""Single-actor, single-map continuous-movement acceptance prototype."""

from __future__ import annotations

import math
from typing import Callable

import pygame

from hex_world_lab.application.demo_tick_pump import DemoTickPump, TickPumpDiagnostics
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
    hex_polygon,
)
from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.movement import MovementConfig, MovementState, Vector2
from hex_world_lab.physics import (
    BoundaryPolicy,
    BodyDefinition,
    CircleShape,
    ContinuousCollisionResolution,
    ConvexPolygonShape,
    ObstacleDefinition,
    build_hex_map_collision_geometry,
)
from hex_world_lab.simulation import CollisionAwareMovementSystem, MovementCellTracker
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
BACKGROUND = (21, 25, 34)
HEX_FILL = (42, 51, 65)
HEX_EDGE = (104, 121, 143)
ACTIVE_EDGE = (235, 190, 92)
ACTOR_COLOR = (231, 93, 83)
CELL_OBSTACLE_FILL = (91, 66, 55)
OBJECT_CIRCLE_COLOR = (72, 122, 86)
OBJECT_POLYGON_COLOR = (112, 119, 132)
BOUNDARY_COLOR = (201, 160, 91)
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
        AxialCoord(2, r) for r in range(-3, 2)
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
        "_layout",
        "_movement_config",
        "house_center",
        "_font",
        "_small_font",
        "_last_diagnostics",
    )

    def __init__(
        self,
        *,
        movement_speed: float = 60.0,
        key_state_provider: Callable[[], object] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.world, self.map_id = build_demo_world()
        definition = self.world.get_map(self.map_id)
        assert definition is not None
        self._layout = definition.layout
        start_position = axial_to_world(AxialCoord(0, 0), self._layout)
        self._movement_config = MovementConfig(max_speed=movement_speed)
        tree_center = axial_to_world(AxialCoord(0, 2), self._layout)
        rock_center = axial_to_world(AxialCoord(-2, 2), self._layout)
        wall_center = axial_to_world(AxialCoord(0, -2), self._layout)
        self.house_center = axial_to_world(AxialCoord(1, 1), self._layout)
        object_obstacles = (
            ObstacleDefinition(
                "object:tree",
                self.map_id,
                CircleShape(8.5),
                tree_center,
            ),
            ObstacleDefinition(
                "object:rock",
                self.map_id,
                ConvexPolygonShape((
                    Vector2(-9.0, -7.0),
                    Vector2(7.0, -9.0),
                    Vector2(10.0, 3.0),
                    Vector2(-3.0, 10.0),
                )),
                rock_center,
            ),
            ObstacleDefinition(
                "object:wall",
                self.map_id,
                ConvexPolygonShape((
                    Vector2(-15.0, -4.0),
                    Vector2(15.0, -4.0),
                    Vector2(15.0, 4.0),
                    Vector2(-15.0, 4.0),
                )),
                wall_center,
            ),
        )
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
            boundary_policy=BoundaryPolicy.BLOCKED,
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
        callback = self._advance_tick
        self.tick_pump = (
            DemoTickPump(callback)
            if clock is None
            else DemoTickPump(callback, clock=clock)
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

    def pump(self) -> TickPumpDiagnostics:
        self._last_diagnostics = self.tick_pump.pump()
        return self._last_diagnostics

    def _advance_tick(self, tick_number: int) -> None:
        next_state = self.movement_system.step(
            tick_number,
            self.keyboard.read_intent(),
        )
        self.cell_tracker.update(next_state.position)

    @staticmethod
    def _screen_point(point: WorldPoint, center: tuple[int, int]) -> tuple[int, int]:
        return (
            round(center[0] + point.x),
            round(center[1] - point.y),
        )

    def render(self, surface: pygame.Surface, render_fps: float = 0.0) -> None:
        """Draw the current snapshot without mutating simulation state."""
        if not isinstance(surface, pygame.Surface):
            raise TypeError("surface must be a pygame.Surface")
        if self._font is None:
            self._font = pygame.font.Font(None, 23)
            self._small_font = pygame.font.Font(None, 19)

        surface.fill(BACKGROUND)
        width, height = surface.get_size()
        center = (width // 2, height // 2 + 8)
        definition = self.world.get_map(self.map_id)
        assert definition is not None

        for coord, cell in definition.cells.items():
            corners = [
                self._screen_point(point, center)
                for point in hex_polygon(coord, self._layout)
            ]
            fill = CELL_OBSTACLE_FILL if cell.has_obstacle else HEX_FILL
            pygame.draw.polygon(surface, fill, corners)
            edge_color = (
                ACTIVE_EDGE
                if self.current_resolution is not None
                and self.current_resolution.coord == coord
                else HEX_EDGE
            )
            pygame.draw.polygon(surface, edge_color, corners, width=1)

        for obstacle in self.collision_geometry.obstacles:
            shape = obstacle.world_shape()
            if isinstance(shape, CircleShape):
                point = self._screen_point(
                    WorldPoint(shape.center.x, shape.center.y), center
                )
                pygame.draw.circle(
                    surface, OBJECT_CIRCLE_COLOR, point, round(shape.radius)
                )
                pygame.draw.circle(
                    surface, (206, 224, 208), point, round(shape.radius), width=2
                )
            else:
                points = [
                    self._screen_point(WorldPoint(vertex.x, vertex.y), center)
                    for vertex in shape.vertices
                ]
                color = (
                    CELL_OBSTACLE_FILL
                    if obstacle.obstacle_id.startswith("cell:")
                    else OBJECT_POLYGON_COLOR
                )
                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, (205, 211, 222), points, width=2)

        self._draw_house_skeleton(surface, center)

        for edge in self.collision_geometry.boundary_edges:
            pygame.draw.line(
                surface,
                BOUNDARY_COLOR,
                self._screen_point(edge.start, center),
                self._screen_point(edge.end, center),
                2,
            )

        actor = self._screen_point(self.state.position, center)
        pygame.draw.circle(
            surface, ACTOR_COLOR, actor, round(PLAYER_COLLIDER_RADIUS)
        )
        pygame.draw.circle(
            surface, (255, 235, 225), actor,
            round(PLAYER_COLLIDER_RADIUS), width=2
        )

        self._draw_diagnostics(surface, render_fps)

    def _draw_house_skeleton(
        self,
        surface: pygame.Surface,
        screen_center: tuple[int, int],
    ) -> None:
        """Draw a placeholder house frame; this is not final art or build UI."""
        def point(offset_x: float, offset_y: float) -> tuple[int, int]:
            return self._screen_point(
                WorldPoint(
                    self.house_center.x + offset_x,
                    self.house_center.y + offset_y,
                ),
                screen_center,
            )

        frame_color = (190, 151, 103)
        detail_color = (225, 190, 139)
        segments = (
            ((-17, 17), (17, 17)),
            ((-17, 17), (-17, -17)),
            ((17, 17), (17, -17)),
            ((-HOUSE_HALF_WIDTH, -HOUSE_HALF_WIDTH), (-HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH)),
            ((HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (HOUSE_HALF_WIDTH, -HOUSE_HALF_WIDTH)),
            ((-HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (-HOUSE_DOORWAY_HALF_WIDTH, -8)),
            ((HOUSE_DOORWAY_HALF_WIDTH, -HOUSE_HALF_WIDTH), (HOUSE_DOORWAY_HALF_WIDTH, -8)),
        )
        for start, end in segments:
            pygame.draw.line(surface, frame_color, point(*start), point(*end), 3)

        # Roof ridge and rafters are visual guides, not colliders.
        pygame.draw.line(surface, detail_color, point(-12, 0), point(12, 0), 2)
        pygame.draw.line(surface, detail_color, point(-12, 0), point(-17, 17), 2)
        pygame.draw.line(surface, detail_color, point(12, 0), point(17, 17), 2)
        pygame.draw.line(surface, detail_color, point(-5, -8), point(5, -8), 2)

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
