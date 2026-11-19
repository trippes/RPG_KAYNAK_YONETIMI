from types import SimpleNamespace

import pytest
import pygame

from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexMovableEntity
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile
from core.domain.spatial import HexDirection
from game_ui.input import InputState
from game_ui.world_rendering.hex_gameplay_view import HexGameplayView
from game_ui.screens.main_screen import MainScreen


class RecordingActorBinding:
    def __init__(self):
        self.moves = []
        self.transitions = []
        self.toward = []

    def move_toward(self, actor_id, goal):
        self.toward.append((actor_id, goal))
        return SimpleNamespace(
            success=True,
            position=EntityPosition("village", LocalHexPosition(1, 0)),
        )

    def move(self, actor_id, direction):
        self.moves.append((actor_id, direction))
        return SimpleNamespace(success=True)

    def transition(self, actor_id, transition_id):
        self.transitions.append((actor_id, transition_id))
        return SimpleNamespace(success=True)


class FakeRuntime:
    def __init__(self, transitions=()):
        self.transitions = transitions

    def entity(self, _actor_id):
        return SimpleNamespace(
            position=EntityPosition("village", LocalHexPosition(0, 0)),
        )

    def map_definition(self, _map_id):
        return SimpleNamespace(
            transitions=self.transitions,
            has_cell=lambda _cell: True,
        )


class FakeService:
    def __init__(self):
        self.hex_world_runtime = FakeRuntime()
        self.hex_actor_binding = RecordingActorBinding()
        self.player_actor_id = "hero"


def test_hex_gameplay_view_maps_six_keyboard_actions_to_axial_directions():
    service = FakeService()
    view = HexGameplayView(service)
    state = InputState(actions={
        "right", "left", "up", "down",
        "hex_north_west", "hex_south_west",
    })

    view.handle(state)

    assert service.hex_actor_binding.moves == [
        ("hero", HexDirection.EAST),
        ("hero", HexDirection.WEST),
        ("hero", HexDirection.NORTH_EAST),
        ("hero", HexDirection.SOUTH_EAST),
        ("hero", HexDirection.NORTH_WEST),
        ("hero", HexDirection.SOUTH_WEST),
    ]


def test_hex_gameplay_view_mouse_wheel_changes_only_presentation_zoom():
    service = FakeService()
    view = HexGameplayView(service)

    view.handle(InputState(mouse_wheel=2, mouse_pos=(100, 120)))

    assert view.zoom == pytest.approx(1.16)
    assert view.mouse_position == (100, 120)
    assert service.hex_actor_binding.moves == []


def test_hex_gameplay_view_zoom_is_clamped():
    service = FakeService()
    view = HexGameplayView(service)

    view.handle(InputState(mouse_wheel=100))
    assert view.zoom == view.MAX_ZOOM

    view.handle(InputState(mouse_wheel=-1000))
    assert view.zoom == view.MIN_ZOOM


def test_hex_gameplay_view_does_not_issue_moves_without_runtime():
    service = FakeService()
    service.hex_world_runtime = None
    view = HexGameplayView(service)

    view.handle(InputState(actions={"right"}))

    assert service.hex_actor_binding.moves == []

def test_hex_gameplay_view_renders_runtime_map_without_mutating_entity_position():
    map_definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "village",
        "name": "Village",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [0, 1]],
        "cell_overrides": [],
    })
    player = HexMovableEntity(
        "hero",
        "player",
        EntityPosition("village", LocalHexPosition(0, 0)),
        MovementProfile(),
    )

    class Runtime:
        def entity(self, _entity_id):
            return player

        def entities(self):
            return (player,)

        def map_definition(self, _map_id):
            return map_definition

    service = FakeService()
    service.hex_world_runtime = Runtime()
    view = HexGameplayView(service)
    surface = pygame.Surface((800, 600))
    renderer = SimpleNamespace(
        pg=pygame,
        surface=surface,
        width=800,
        height=600,
        text=lambda *_args, **_kwargs: None,
    )

    assert view.render(renderer) is True
    assert player.position == EntityPosition(
        "village", LocalHexPosition(0, 0),
    )

def test_hex_gameplay_view_click_selects_axial_destination():
    service = FakeService()
    view = HexGameplayView(service)
    view._panel = pygame.Rect(24, 96, 752, 480)
    view.transform.configure(
        camera_x=0,
        camera_y=0,
        viewport_center=(400, 336),
        zoom=1,
    )

    view.handle(InputState(mouse_clicked=True, mouse_pos=(455, 336)))

    assert service.hex_actor_binding.toward == [
        ("hero", LocalHexPosition(1, 0)),
    ]


def test_hex_gameplay_view_update_advances_click_to_move_goal():
    service = FakeService()
    view = HexGameplayView(service)
    view._move_goal = LocalHexPosition(2, 0)
    view._move_map_id = "village"

    view.update(HexGameplayView.MOVE_STEP_SECONDS)

    assert service.hex_actor_binding.toward == [
        ("hero", LocalHexPosition(2, 0)),
    ]


def test_hex_gameplay_view_uses_authored_map_transition_at_exit_cell():
    transition = SimpleNamespace(
        active=True,
        exit_direction=HexDirection.EAST,
        source_cells=(LocalHexPosition(0, 0),),
        transition_id="village_to_forest",
    )
    service = FakeService()
    service.hex_world_runtime = FakeRuntime((transition,))
    view = HexGameplayView(service)

    view.handle(InputState(actions={"right"}))

    assert service.hex_actor_binding.transitions == [
        ("hero", "village_to_forest"),
    ]
    assert service.hex_actor_binding.moves == []


def test_hex_gameplay_view_ignores_inactive_map_transitions():
    transition = SimpleNamespace(
        active=False,
        exit_direction=HexDirection.EAST,
        source_cells=(LocalHexPosition(0, 0),),
        transition_id="inactive_exit",
    )
    service = FakeService()
    service.hex_world_runtime = FakeRuntime((transition,))
    view = HexGameplayView(service)

    view.handle(InputState(actions={"right"}))

    assert service.hex_actor_binding.transitions == []
    assert service.hex_actor_binding.moves == [
        ("hero", HexDirection.EAST),
    ]




def _interaction_service():
    player = HexMovableEntity(
        "hero",
        "player",
        EntityPosition("village", LocalHexPosition(0, 0)),
        MovementProfile(),
    )
    npc = HexMovableEntity(
        "guard_eren",
        "npc",
        EntityPosition("village", LocalHexPosition(1, 0)),
        MovementProfile(),
    )

    class Runtime:
        def entity(self, entity_id):
            return {"hero": player, "guard_eren": npc}[entity_id]

        def entities(self):
            return (player, npc)

        def map_definition(self, _map_id):
            return SimpleNamespace(
                transitions=(),
                has_cell=lambda _cell: True,
            )

    service = FakeService()
    service.hex_world_runtime = Runtime()
    return service


def _configure_interaction_view(view):
    view._panel = pygame.Rect(24, 96, 752, 480)
    view.transform.configure(
        camera_x=0,
        camera_y=0,
        viewport_center=(400, 336),
        zoom=1,
    )


def test_left_clicking_npc_selects_it_and_requests_dialogue():
    service = _interaction_service()
    view = HexGameplayView(service)
    _configure_interaction_view(view)

    result = view.handle(InputState(mouse_clicked=True, mouse_pos=(455, 336)))

    assert result == "dialogue"
    assert view.selected_npc_id == "guard_eren"
    assert view._move_goal is None


def test_right_clicking_npc_opens_empty_context_menu_without_actions():
    service = _interaction_service()
    view = HexGameplayView(service)
    _configure_interaction_view(view)

    view.handle(InputState(mouse_right_clicked=True, mouse_pos=(455, 336)))

    assert view.context_menu_npc_id == "guard_eren"
    assert view.context_menu_position == (455, 336)
    assert service.hex_actor_binding.moves == []
    assert service.hex_actor_binding.toward == []


def test_right_clicking_empty_cell_closes_npc_context_menu():
    service = _interaction_service()
    view = HexGameplayView(service)
    _configure_interaction_view(view)
    view.context_menu_npc_id = "guard_eren"
    view.context_menu_position = (455, 336)

    view.handle(InputState(mouse_right_clicked=True, mouse_pos=(510, 336)))

    assert view.context_menu_npc_id is None
    assert view.context_menu_position is None



def test_main_screen_forwards_selected_npc_to_dialogue_navigation():
    service = FakeService()
    screen = MainScreen(service)
    screen._hex_view = SimpleNamespace(
        selected_npc_id="guard_eren",
        handle=lambda _state: "dialogue",
    )

    assert screen.handle(InputState()) == "dialogue"
    assert screen.selected_npc_id == "guard_eren"
