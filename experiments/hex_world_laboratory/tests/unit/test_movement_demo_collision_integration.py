from __future__ import annotations

import pygame

from hex_world_lab.application.movement_demo import (
    HOUSE_DOORWAY_HALF_WIDTH,
    MAP_ID,
    PLAYER_COLLIDER_RADIUS,
    MovementDemo,
)
from hex_world_lab.physics import CircleShape
from hex_world_lab.simulation import CollisionAwareMovementSystem


class _PressedKeys:
    def __init__(self, active: set[int]) -> None:
        self.active = active

    def __getitem__(self, key_code: int) -> bool:
        return key_code in self.active


def _pressed_keys(*key_codes: int) -> _PressedKeys:
    return _PressedKeys(set(key_codes))


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
    # Approach the q=2, r=0 blocked hex diagonally; the horizontal
    # y=0 lane remains clear for the legacy continuous-movement scenarios.
    keys = _pressed_keys(pygame.K_d, pygame.K_w)
    demo = MovementDemo(key_state_provider=lambda: keys)

    for tick in range(100):
        demo._advance_tick(tick)

    assert 50.0 < demo.state.position.x < 60.0
    assert 50.0 < demo.state.position.y < 60.0
    assert demo.last_collision_resolution is not None
    assert demo.last_collision_resolution.contacts


def test_pygame_demo_house_is_a_skeleton_with_a_doorway_gap() -> None:
    demo = MovementDemo(key_state_provider=lambda: _pressed_keys())

    house_walls = [
        item for item in demo.collision_geometry.obstacles
        if item.obstacle_id.startswith("structure:starter-house:")
    ]

    assert len(house_walls) == 5
    assert HOUSE_DOORWAY_HALF_WIDTH > PLAYER_COLLIDER_RADIUS
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
