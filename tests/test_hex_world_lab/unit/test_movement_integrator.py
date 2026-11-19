import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.movement.integrator import MovementIntegrator


def make_integrator(speed=120.0):
    return MovementIntegrator(MovementConfig(max_speed=speed))


def test_integrator_moves_horizontally_by_speed_times_delta():
    state = MovementState(WorldPoint(1.0, 2.0))
    result = make_integrator().step(state, MovementIntent(Vector2(1.0, 0.0)), 1 / 60)
    assert result.position.x == pytest.approx(3.0)
    assert result.position.y == pytest.approx(2.0)
    assert result.velocity == Vector2(120.0, 0.0)


def test_integrator_moves_vertically_in_mathematical_coordinates():
    state = MovementState(WorldPoint(1.0, 2.0))
    result = make_integrator().step(state, MovementIntent(Vector2(0.0, 1.0)), 0.5)
    assert result.position == WorldPoint(1.0, 62.0)


def test_integrator_normalizes_diagonal_movement():
    integrator = make_integrator()
    horizontal = integrator.step(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementIntent(Vector2(1.0, 0.0)), 1.0,
    )
    diagonal = integrator.step(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementIntent(Vector2(1.0, 1.0)), 1.0,
    )
    assert diagonal.position.x == pytest.approx(horizontal.position.x / 2**0.5)
    assert diagonal.position.y == pytest.approx(horizontal.position.x / 2**0.5)
    assert diagonal.velocity.length == pytest.approx(horizontal.velocity.length)


def test_integrator_stops_and_clears_velocity_without_intent():
    state = MovementState(WorldPoint(4.0, 5.0), Vector2(20.0, 0.0))
    result = make_integrator().step(state, MovementIntent(), 1.0)
    assert result.position == state.position
    assert result.velocity == Vector2(0.0, 0.0)


def test_integrator_changes_direction_immediately():
    state = MovementState(WorldPoint(0.0, 0.0), Vector2(120.0, 0.0))
    result = make_integrator().step(state, MovementIntent(Vector2(0.0, -1.0)), 0.25)
    assert result.position == WorldPoint(0.0, -30.0)
    assert result.velocity == Vector2(0.0, -120.0)


def test_zero_max_speed_prevents_movement():
    state = MovementState(WorldPoint(2.0, 3.0))
    result = make_integrator(0.0).step(state, MovementIntent(Vector2(1.0, 0.0)), 1.0)
    assert result.position == state.position
    assert result.velocity == Vector2(0.0, 0.0)


def test_zero_delta_time_does_not_advance_position():
    state = MovementState(WorldPoint(2.0, 3.0))
    result = make_integrator().step(state, MovementIntent(Vector2(1.0, 0.0)), 0.0)
    assert result.position == state.position
    assert result.velocity == Vector2(120.0, 0.0)


@pytest.mark.parametrize("delta_time", [-1.0, -0.01])
def test_integrator_rejects_negative_delta_time(delta_time):
    with pytest.raises(ValueError):
        make_integrator().step(MovementState(WorldPoint(0.0, 0.0)), MovementIntent(), delta_time)


@pytest.mark.parametrize("delta_time", [float("nan"), float("inf"), float("-inf")])
def test_integrator_rejects_non_finite_delta_time(delta_time):
    with pytest.raises(ValueError):
        make_integrator().step(MovementState(WorldPoint(0.0, 0.0)), MovementIntent(), delta_time)


@pytest.mark.parametrize("delta_time", [True, "0.1", None])
def test_integrator_rejects_non_numeric_delta_time(delta_time):
    with pytest.raises(TypeError):
        make_integrator().step(MovementState(WorldPoint(0.0, 0.0)), MovementIntent(), delta_time)


def test_integrator_rejects_invalid_state_and_intent_types():
    integrator = make_integrator()
    with pytest.raises(TypeError):
        integrator.step(object(), MovementIntent(), 1.0)
    with pytest.raises(TypeError):
        integrator.step(MovementState(WorldPoint(0.0, 0.0)), object(), 1.0)


def test_integrator_does_not_mutate_input_state():
    state = MovementState(WorldPoint(1.25, -2.5), Vector2(3.0, 4.0))
    result = make_integrator().step(state, MovementIntent(Vector2(1.0, 0.0)), 0.5)
    assert state.position == WorldPoint(1.25, -2.5)
    assert state.velocity == Vector2(3.0, 4.0)
    assert result is not state


def test_integrator_accepts_large_delta_time_without_internal_clamping():
    result = make_integrator(2.0).step(
        MovementState(WorldPoint(0.0, 0.0)), MovementIntent(Vector2(1.0, 0.0)), 10.0
    )
    assert result.position == WorldPoint(20.0, 0.0)
