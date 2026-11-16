from __future__ import annotations

import pygame

from hex_world_lab.application.movement_demo import (
    MAP_ID,
    PLAYER_COLLIDER_RADIUS,
    MovementDemo,
)
from hex_world_lab.physics import CircleShape
from hex_world_lab.simulation import CollisionAwareMovementSystem


def _pressed_keys(*key_codes: int) -> list[bool]:
    keys = [False] * 512
    for key_code in key_codes:
        keys[key_code] = True
    return keys


def test_pygame_demo_uses_collision_aware_movement_and_map_geometry() -> None:
    demo = MovementDemo(key_state_provider=lambda: _pressed_keys())

    assert isinstance(demo.movement_system, CollisionAwareMovementSystem)
    assert demo.movement_system.map_id == MAP_ID
    assert isinstance(demo.body_definition.collider, CircleShape)
    assert demo.body_definition.collider.radius == PLAYER_COLLIDER_RADIUS
    assert demo.collision_geometry.boundary_edges
    assert any(item.obstacle_id.startswith("cell:") for item in demo.collision_geometry.obstacles)
    obstacle_ids = {item.obstacle_id for item in demo.collision_geometry.obstacles}
    assert obstacle_ids >= {
        "object:tree",
        "object:rock",
        "object:wall",
        "structure:starter-house:left",
        "structure:starter-house:right",
        "structure:starter-house:back",
        "structure:starter-house:front-left",
        "structure:starter-house:front-right",
    }


def test_pygame_demo_player_stops_at_adjacent_hex_obstacle_wall() -> None:
    keys = _pressed_keys(pygame.K_d)
    demo = MovementDemo(key_state_provider=lambda: keys)

    for tick in range(100):
        demo._advance_tick(tick)

    assert demo.state.position.x < 60.0
    assert demo.state.position.x > 45.0
    assert demo.last_collision_resolution is not None
    assert demo.last_collision_resolution.contacts


def test_pygame_demo_house_is_a_skeleton_with_a_doorway_gap() -> None:
    demo = MovementDemo(key_state_provider=lambda: _pressed_keys())

    house_walls = [
        item for item in demo.collision_geometry.obstacles
        if item.obstacle_id.startswith("structure:starter-house:")
    ]

    assert len(house_walls) == 5
    assert demo.house_center is not None


def test_pygame_demo_render_includes_collision_scene() -> None:
    pygame.init()
    try:
        demo = MovementDemo(key_state_provider=lambda: _pressed_keys())
        surface = pygame.Surface((960, 640))
        demo.render(surface, render_fps=60.0)
        assert surface.get_at((480, 328)) != (0, 0, 0, 255)
    finally:
        pygame.quit()
