"""Regression tests for the unified eight-way WASD movement contract."""

from types import SimpleNamespace

from game_ui.input import InputMapper
from game_ui.world_transform import WorldTransform


class FakeBackend:
    KEYDOWN = 1

    def __init__(self):
        self.mouse = SimpleNamespace(get_pos=lambda: (0, 0))


def test_wasd_and_legacy_hex_keys_do_not_trigger_global_actions():
    mapper = InputMapper(FakeBackend())
    events = [
        SimpleNamespace(type=1, key=key, unicode=key)
        for key in ("w", "a", "s", "d", "z", "x")
    ]

    state = mapper.collect(events)

    assert state.pressed("world")
    assert state.pressed("dialogue_history")
    assert state.actions.isdisjoint({
        "hex_north_west", "hex_south_west",
    })


def test_dialogue_history_shortcut_remains_d_outside_wasd_movement():
    mapper = InputMapper(FakeBackend())
    state = mapper.collect([
        SimpleNamespace(type=1, key="d", unicode="d"),
    ])

    assert state.pressed("dialogue_history")


def test_world_shortcut_is_still_mapped_to_w_for_non_gameplay_screens():
    mapper = InputMapper(FakeBackend())
    state = mapper.collect([
        SimpleNamespace(type=1, key="w", unicode="w"),
    ])

    assert state.pressed("world")


def test_all_eight_screen_directions_round_trip_through_world_transform():
    transform = WorldTransform(projection="isometric")
    directions = (
        (0.0, -1.0), (1.0, -1.0), (1.0, 0.0), (1.0, 1.0),
        (0.0, 1.0), (-1.0, 1.0), (-1.0, 0.0), (-1.0, -1.0),
    )

    for screen_x, screen_y in directions:
        world_x, world_y = transform.unproject_vector(screen_x, screen_y)
        projected_x, projected_y = transform.project_vector(world_x, world_y)
        assert projected_x == pytest.approx(screen_x)
        assert projected_y == pytest.approx(screen_y)


import pytest
