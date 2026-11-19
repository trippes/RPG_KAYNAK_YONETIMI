import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementMode, MovementState, Vector2


def test_state_preserves_fractional_world_position():
    position = WorldPoint(12.375, -4.625)
    state = MovementState(position=position)
    assert state.position is position
    assert state.position.x == 12.375
    assert state.position.y == -4.625


def test_state_defaults_to_zero_velocity_and_normal_mode():
    state = MovementState(WorldPoint(0.0, 0.0))
    assert state.velocity == Vector2(0.0, 0.0)
    assert state.mode is MovementMode.NORMAL


def test_state_accepts_velocity_vector_and_mode():
    velocity = Vector2(2.5, -1.25)
    state = MovementState(WorldPoint(1.0, 2.0), velocity, MovementMode.STEALTH)
    assert state.velocity is velocity
    assert state.mode is MovementMode.STEALTH


def test_state_requires_world_point():
    with pytest.raises(TypeError):
        MovementState(position=(1.0, 2.0))


def test_state_requires_vector_velocity():
    with pytest.raises(TypeError):
        MovementState(position=WorldPoint(0.0, 0.0), velocity=(0.0, 0.0))


def test_state_rejects_invalid_mode():
    with pytest.raises(TypeError, match="MovementMode"):
        MovementState(position=WorldPoint(0.0, 0.0), mode="stealth")


def test_state_is_immutable():
    state = MovementState(WorldPoint(0.0, 0.0))
    with pytest.raises((AttributeError, TypeError)):
        state.position = WorldPoint(1.0, 1.0)
