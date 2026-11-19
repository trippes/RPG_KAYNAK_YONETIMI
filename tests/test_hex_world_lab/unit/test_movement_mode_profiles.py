import math

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import (
    MovementConfig,
    MovementIntent,
    MovementMode,
    MovementState,
    Vector2,
)
from hex_world_lab.movement.integrator import MovementIntegrator


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (MovementMode.NORMAL, 1.0),
        (MovementMode.RUNNING, 1.5),
        (MovementMode.STEALTH, 0.5),
    ],
)
def test_default_config_resolves_each_mode_multiplier(mode, expected):
    config = MovementConfig(max_speed=60.0)
    assert config.speed_multiplier_for(mode) == expected


def test_normal_speed_is_one_times_base_speed():
    config = MovementConfig(max_speed=60.0)
    assert config.max_speed * config.speed_multiplier_for(MovementMode.NORMAL) == 60.0


def test_custom_mode_multipliers_are_supported():
    config = MovementConfig(
        max_speed=80.0,
        running_speed_multiplier=2.0,
        stealth_speed_multiplier=0.25,
    )
    assert config.speed_multiplier_for(MovementMode.RUNNING) == 2.0
    assert config.speed_multiplier_for(MovementMode.STEALTH) == 0.25


@pytest.mark.parametrize("field", ["running_speed_multiplier", "stealth_speed_multiplier"])
@pytest.mark.parametrize("value", [-0.01, -1.0])
def test_config_rejects_negative_mode_multipliers(field, value):
    with pytest.raises(ValueError):
        MovementConfig(max_speed=60.0, **{field: value})


@pytest.mark.parametrize("field", ["running_speed_multiplier", "stealth_speed_multiplier"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_config_rejects_non_finite_mode_multipliers(field, value):
    with pytest.raises(ValueError):
        MovementConfig(max_speed=60.0, **{field: value})


@pytest.mark.parametrize("field", ["running_speed_multiplier", "stealth_speed_multiplier"])
@pytest.mark.parametrize("value", [True, "1.5", None])
def test_config_rejects_non_numeric_mode_multipliers(field, value):
    with pytest.raises(TypeError):
        MovementConfig(max_speed=60.0, **{field: value})


@pytest.mark.parametrize("mode", ["normal", "running", None])
def test_config_rejects_unknown_mode_type(mode):
    with pytest.raises(TypeError):
        MovementConfig(max_speed=60.0).speed_multiplier_for(mode)


@pytest.mark.parametrize(
    ("mode", "expected_speed"),
    [
        (MovementMode.NORMAL, 60.0),
        (MovementMode.RUNNING, 90.0),
        (MovementMode.STEALTH, 30.0),
    ],
)
def test_integrator_applies_expected_speed_profile(mode, expected_speed):
    integrator = MovementIntegrator(MovementConfig(max_speed=60.0))
    result = integrator.step(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementIntent(Vector2(1.0, 0.0), mode),
        1.0,
    )
    assert result.position.x == pytest.approx(expected_speed)
    assert result.velocity.length == pytest.approx(expected_speed)
    assert result.mode is mode


def test_mode_multipliers_scale_different_base_speeds_proportionally():
    for base_speed in (12.0, 60.0, 137.5):
        integrator = MovementIntegrator(MovementConfig(max_speed=base_speed))
        outputs = {}
        for mode in MovementMode:
            result = integrator.step(
                MovementState(WorldPoint(0.0, 0.0)),
                MovementIntent(Vector2(1.0, 0.0), mode),
                1.0,
            )
            outputs[mode] = result.velocity.length
        assert outputs[MovementMode.NORMAL] == pytest.approx(base_speed)
        assert outputs[MovementMode.RUNNING] == pytest.approx(base_speed * 1.5)
        assert outputs[MovementMode.STEALTH] == pytest.approx(base_speed * 0.5)


@pytest.mark.parametrize("mode", list(MovementMode))
def test_diagonal_movement_is_normalized_for_every_mode(mode):
    integrator = MovementIntegrator(MovementConfig(max_speed=60.0))
    result = integrator.step(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementIntent(Vector2(1.0, 1.0), mode),
        1.0,
    )
    expected = 60.0 * MovementConfig(60.0).speed_multiplier_for(mode)
    assert result.velocity.length == pytest.approx(expected)
    assert result.velocity.x == pytest.approx(expected / math.sqrt(2.0))
    assert result.velocity.y == pytest.approx(expected / math.sqrt(2.0))


@pytest.mark.parametrize("mode", list(MovementMode))
def test_zero_direction_keeps_mode_without_moving(mode):
    start = WorldPoint(2.25, -4.5)
    result = MovementIntegrator(MovementConfig(60.0)).step(
        MovementState(start),
        MovementIntent(mode=mode),
        1.0,
    )
    assert result.position == start
    assert result.velocity == Vector2(0.0, 0.0)
    assert result.mode is mode


def test_zero_multiplier_disables_only_its_selected_mode():
    config = MovementConfig(
        max_speed=60.0,
        running_speed_multiplier=0.0,
        stealth_speed_multiplier=0.0,
    )
    integrator = MovementIntegrator(config)
    for mode in (MovementMode.RUNNING, MovementMode.STEALTH):
        result = integrator.step(
            MovementState(WorldPoint(1.0, 2.0)),
            MovementIntent(Vector2(1.0, 0.0), mode),
            1.0,
        )
        assert result.position == WorldPoint(1.0, 2.0)
        assert result.velocity == Vector2(0.0, 0.0)
        assert result.mode is mode


def test_mode_change_takes_effect_on_the_current_step():
    integrator = MovementIntegrator(MovementConfig(max_speed=60.0))
    state = MovementState(WorldPoint(0.0, 0.0))
    running = integrator.step(
        state, MovementIntent(Vector2(1.0, 0.0), MovementMode.RUNNING), 1.0 / 60.0
    )
    stealth = integrator.step(
        running, MovementIntent(Vector2(1.0, 0.0), MovementMode.STEALTH), 1.0 / 60.0
    )
    assert running.position.x == pytest.approx(1.5)
    assert running.mode is MovementMode.RUNNING
    assert stealth.position.x - running.position.x == pytest.approx(0.5)
    assert stealth.mode is MovementMode.STEALTH
