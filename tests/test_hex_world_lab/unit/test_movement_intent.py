import pytest

from hex_world_lab.movement import MovementIntent, MovementMode, Vector2


def test_default_intent_means_no_movement_in_normal_mode():
    intent = MovementIntent()
    assert intent.direction == Vector2(0.0, 0.0)
    assert intent.mode is MovementMode.NORMAL
    assert not intent.is_moving


def test_non_zero_direction_means_movement():
    assert MovementIntent(Vector2(1.0, 0.0)).is_moving


def test_intent_preserves_requested_direction_and_mode():
    direction = Vector2(-1.0, 1.0)
    intent = MovementIntent(direction, MovementMode.RUNNING)
    assert intent.direction is direction
    assert intent.mode is MovementMode.RUNNING


def test_intent_accepts_mode_as_keyword_without_changing_direction_default():
    intent = MovementIntent(mode=MovementMode.STEALTH)
    assert intent.direction == Vector2(0.0, 0.0)
    assert intent.mode is MovementMode.STEALTH
    assert not intent.is_moving


def test_intent_requires_vector():
    with pytest.raises(TypeError):
        MovementIntent((1.0, 0.0))


def test_intent_rejects_invalid_mode():
    with pytest.raises(TypeError, match="MovementMode"):
        MovementIntent(mode="running")


def test_intent_is_immutable():
    intent = MovementIntent(Vector2(1.0, 0.0))
    with pytest.raises((AttributeError, TypeError)):
        intent.direction = Vector2(0.0, 1.0)
