import pytest

from hex_world_lab.movement import MovementConfig


def test_config_accepts_positive_speed():
    assert MovementConfig(max_speed=4.5).max_speed == 4.5


def test_config_accepts_zero_speed():
    assert MovementConfig(max_speed=0.0).max_speed == 0.0


def test_config_rejects_negative_speed():
    with pytest.raises(ValueError):
        MovementConfig(max_speed=-1.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_config_rejects_non_finite_speed(value):
    with pytest.raises(ValueError):
        MovementConfig(max_speed=value)


def test_config_rejects_boolean_speed():
    with pytest.raises(TypeError):
        MovementConfig(max_speed=True)


def test_config_is_immutable():
    config = MovementConfig(max_speed=3.0)
    with pytest.raises((AttributeError, TypeError)):
        config.max_speed = 5.0
