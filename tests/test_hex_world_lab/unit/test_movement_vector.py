import math

import pytest

from hex_world_lab.movement import Vector2


def test_vector_length_and_squared_length():
    vector = Vector2(3.0, 4.0)
    assert vector.length == 5.0
    assert vector.length_squared == 25.0


def test_vector_normalization_returns_unit_vector():
    normalized = Vector2(3.0, 4.0).normalized()
    assert normalized.x == pytest.approx(0.6)
    assert normalized.y == pytest.approx(0.8)
    assert normalized.length == pytest.approx(1.0)


def test_zero_vector_normalizes_to_zero():
    assert Vector2(0.0, 0.0).normalized() == Vector2(0.0, 0.0)


def test_vector_supports_basic_arithmetic():
    assert Vector2(1.0, 2.0) + Vector2(3.0, 4.0) == Vector2(4.0, 6.0)
    assert Vector2(3.0, 4.0) - Vector2(1.0, 2.0) == Vector2(2.0, 2.0)
    assert 2.0 * Vector2(1.0, -3.0) == Vector2(2.0, -6.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_vector_rejects_non_finite_components(value):
    with pytest.raises(ValueError):
        Vector2(value, 0.0)


def test_vector_rejects_boolean_component():
    with pytest.raises(TypeError):
        Vector2(True, 0.0)


def test_vector_is_immutable():
    vector = Vector2(1.0, 2.0)
    with pytest.raises((AttributeError, TypeError)):
        vector.x = 5.0
