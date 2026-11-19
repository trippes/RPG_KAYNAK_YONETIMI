from types import SimpleNamespace

import pytest
import pygame

from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexMovableEntity
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile
from core.domain.spatial import HexDirection
from game_ui.input import InputState
from game_ui.world_rendering.hex_gameplay_view import HexGameplayView


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
        return SimpleNamespace(transitions=self.transitions)


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

