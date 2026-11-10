import math
from dataclasses import FrozenInstanceError

import pytest

from core.domain.spatial import Position


def test_position_defaults_to_origin():
    assert Position() == Position(x=0, y=0)


@pytest.mark.parametrize(
    ("x", "y"),
    [(3, 4), (-2, 7), (1.5, -0.25)],
)
def test_position_stores_numeric_coordinates(x, y):
    position = Position(x=x, y=y)

    assert (position.x, position.y) == (x, y)


@pytest.mark.parametrize("value", [True, False, "1", None, object()])
def test_position_rejects_non_numeric_coordinates(value):
    with pytest.raises(TypeError):
        Position(x=value, y=0)

    with pytest.raises(TypeError):
        Position(x=0, y=value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_position_rejects_non_finite_coordinates(value):
    with pytest.raises(ValueError):
        Position(x=value, y=0)

    with pytest.raises(ValueError):
        Position(x=0, y=value)


def test_position_is_immutable():
    position = Position(2, 5)

    with pytest.raises(FrozenInstanceError):
        position.x = 10


def test_position_supports_ordering():
    assert sorted([Position(2, 0), Position(1, 5), Position(1, 2)]) == [
        Position(1, 2),
        Position(1, 5),
        Position(2, 0),
    ]


def test_translated_returns_a_new_position_without_mutating_original():
    original = Position(2, 3)

    translated = original.translated(dx=-1, dy=4)

    assert translated == Position(1, 7)
    assert original == Position(2, 3)
    assert translated is not original


@pytest.mark.parametrize("value", [True, "1", None, math.nan, math.inf])
def test_translated_rejects_invalid_offsets(value):
    position = Position(1, 2)

    with pytest.raises((TypeError, ValueError)):
        position.translated(dx=value)

    with pytest.raises((TypeError, ValueError)):
        position.translated(dy=value)


def test_distance_to_returns_euclidean_distance():
    assert Position(0, 0).distance_to(Position(3, 4)) == 5.0


def test_distance_to_rejects_non_position_values():
    with pytest.raises(TypeError, match="other must be a Position"):
        Position().distance_to((0, 0))


def test_to_dict_and_to_persistence_return_coordinate_data():
    position = Position(2.5, -4)

    assert position.to_dict() == {"x": 2.5, "y": -4}
    assert position.to_persistence() == {"x": 2.5, "y": -4}


def test_from_dict_and_from_persistence_restore_position():
    data = {"x": 2.5, "y": -4}

    assert Position.from_dict(data) == Position(2.5, -4)
    assert Position.from_persistence(data) == Position(2.5, -4)


def test_from_dict_rejects_non_dictionary_data():
    with pytest.raises(TypeError, match="Position data must be a dictionary"):
        Position.from_dict([1, 2])


@pytest.mark.parametrize("data", [{"x": 1}, {"y": 2}, {}])
def test_from_dict_rejects_missing_coordinate_fields(data):
    with pytest.raises(ValueError, match="Missing position field"):
        Position.from_dict(data)
