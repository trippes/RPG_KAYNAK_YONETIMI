import pytest

from hex_world_lab.movement import MovementIntent, Vector2


def test_default_intent_means_no_movement():
    intent = MovementIntent()
    assert intent.direction == Vector2(0.0, 0.0)
    assert not intent.is_moving


def test_non_zero_direction_means_movement():
    assert MovementIntent(Vector2(1.0, 0.0)).is_moving


def test_intent_preserves_requested_direction():
    direction = Vector2(-1.0, 1.0)
    assert MovementIntent(direction).direction is direction


def test_intent_requires_vector():
    with pytest.raises(TypeError):
        MovementIntent((1.0, 0.0))


def test_intent_is_immutable():
    intent = MovementIntent(Vector2(1.0, 0.0))
    with pytest.raises((AttributeError, TypeError)):
        intent.direction = Vector2(0.0, 1.0)
