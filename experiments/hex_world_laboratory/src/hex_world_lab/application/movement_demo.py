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
from hex_world_lab.movement import MovementConfig, MovementState
from hex_world_lab.simulation import MovementCellTracker, MovementSystem
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
TEXT_COLOR = (225, 231, 240)
MUTED_TEXT = (157, 170, 188)


def build_demo_world() -> tuple[HexWorld, MapId]:
    """Create and load the deterministic 61-cell acceptance map."""
    world = HexWorld(WORLD_ID)
    world.register_map(MAP_ID, MAP_NAME)
    layout = HexLayout(
        orientation=HexOrientation.FLAT_TOP,
        radius=HEX_RADIUS,
        origin=WorldPoint(0.0, 0.0),
    )
    cells = {
        AxialCoord(q, r): HexCellData("grass", True, False)
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
        "cell_tracker",
        "tick_pump",
        "_layout",
        "_movement_config",
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
        self.movement_system = MovementSystem(
            MovementState(position=start_position),
            self._movement_config,
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

        for coord in definition.cells:
            corners = [
                self._screen_point(point, center)
                for point in hex_polygon(coord, self._layout)
            ]
            pygame.draw.polygon(surface, HEX_FILL, corners)
            edge_color = (
                ACTIVE_EDGE
                if self.current_resolution is not None
                and self.current_resolution.coord == coord
                else HEX_EDGE
            )
            pygame.draw.polygon(surface, edge_color, corners, width=1)

        actor = self._screen_point(self.state.position, center)
        pygame.draw.circle(surface, ACTOR_COLOR, actor, 9)
        pygame.draw.circle(surface, (255, 235, 225), actor, 9, width=2)

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
        lines = (
            f"World: {self.world.world_id.value}",
            f"Map: {self.map_id.value}",
            f"Position: x={self.state.position.x:.3f}, y={self.state.position.y:.3f}",
            f"Velocity: x={velocity.x:.2f}, y={velocity.y:.2f}, speed={speed:.2f}",
            f"Mode: {mode.name}",
            f"Multiplier: {multiplier:.2f}x | Mode speed: {mode_speed:.1f} units/s",
            f"Cell: {cell} | data: {cell_data}",
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
