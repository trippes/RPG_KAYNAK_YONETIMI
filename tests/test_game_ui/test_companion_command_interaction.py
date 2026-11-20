"""End-to-end UI routing tests for companion follow/wait commands."""

from types import SimpleNamespace

import pygame

from core.domain.spatial import EntityPosition, LocalHexPosition
from game_ui.input import InputState
from game_ui.screens.main_screen import MainScreen
from game_ui.world_rendering.hex_gameplay_view import HexGameplayView


class FakeRuntime:
    def entity(self, entity_id):
        if entity_id != "hero":
            raise KeyError(entity_id)
        return SimpleNamespace(
            position=EntityPosition("village", LocalHexPosition(0, 0)),
        )


class FakeCompanionRegistry:
    def __init__(self, enlisted=True):
        self.enlisted = enlisted

    def get(self, npc_id):
        return object() if npc_id == "guard" and self.enlisted else None


class FakeService:
    player_actor_id = "hero"
    hex_world_runtime = FakeRuntime()

    def __init__(self, *, enlisted=True):
        self.companion_command_service = SimpleNamespace(
            registry=FakeCompanionRegistry(enlisted),
        )
        self.commands = []

    def npc_at_world_point(self, _map_id, _point):
        return "guard"

    def command_companion(self, npc_id, command):
        self.commands.append((npc_id, command))


def make_screen(*, enlisted=True):
    service = FakeService(enlisted=enlisted)
    screen = MainScreen(service)
    view = HexGameplayView(service)
    view._panel = pygame.Rect(24, 96, 752, 480)
    view.transform.configure(
        camera_x=0,
        camera_y=0,
        viewport_center=(400, 336),
        zoom=1,
    )
    screen._hex_view = view
    return screen, service, view


def open_companion_menu(screen, view):
    position = view.transform.axial_to_screen(
        LocalHexPosition(1, 0).to_hex_coord(),
    )
    result = screen.handle(InputState(
        mouse_right_clicked=True,
        mouse_pos=position,
    ))
    assert result == "companion_menu"
    return view.context_menu_position


def test_enlisted_companion_context_menu_routes_follow_command():
    screen, service, view = make_screen()
    x, y = open_companion_menu(screen, view)

    result = screen.handle(InputState(
        mouse_clicked=True,
        mouse_pos=(x + 12, y + 8),
    ))

    assert result == "companion_command"
    assert service.commands == [("guard", "follow")]
    assert screen.notice == "Yoldaş komutu uygulandı."


def test_enlisted_companion_context_menu_routes_wait_command():
    screen, service, view = make_screen()
    x, y = open_companion_menu(screen, view)

    result = screen.handle(InputState(
        mouse_clicked=True,
        mouse_pos=(x + 12, y + 36),
    ))

    assert result == "companion_command"
    assert service.commands == [("guard", "wait")]


def test_non_companion_npc_does_not_receive_companion_command_menu():
    screen, service, view = make_screen(enlisted=False)
    position = view.transform.axial_to_screen(
        LocalHexPosition(1, 0).to_hex_coord(),
    )

    result = screen.handle(InputState(
        mouse_right_clicked=True,
        mouse_pos=position,
    ))

    assert result == "npc_menu"
    assert view.context_menu_is_companion is False
    assert service.commands == []
