import pytest
from hex_world_lab.rendering.procedural.palette import (
    ColorRamp,
    interpolate_rgb,
    validate_rgb,
)


def test_rgb_validation_accepts_valid_immutable_triple():
    assert validate_rgb((0, 128, 255)) == (0, 128, 255)


@pytest.mark.parametrize("color", [(0, 1), (0, 1, 2, 3), [0, 1, 2]])
def test_rgb_validation_rejects_invalid_shape(color):
    with pytest.raises(TypeError):
        validate_rgb(color)


@pytest.mark.parametrize("color", [(0, True, 2), (0, 1, 256), (-1, 0, 0)])
def test_rgb_validation_rejects_invalid_channels(color):
    with pytest.raises((TypeError, ValueError)):
        validate_rgb(color)


def test_interpolate_rgb_is_deterministic_and_clamps_only_by_contract():
    assert interpolate_rgb((0, 10, 20), (100, 110, 120), 0) == (0, 10, 20)
    assert interpolate_rgb((0, 10, 20), (100, 110, 120), 0.5) == (50, 60, 70)
    assert interpolate_rgb((0, 10, 20), (100, 110, 120), 1) == (100, 110, 120)
    with pytest.raises(ValueError):
        interpolate_rgb((0, 0, 0), (255, 255, 255), 1.1)


def test_color_ramp_samples_multiple_stops():
    ramp = ColorRamp(((0, 0, 0), (100, 50, 0), (200, 100, 50)))
    assert ramp.sample(0) == (0, 0, 0)
    assert ramp.sample(0.5) == (100, 50, 0)
    assert ramp.sample(1) == (200, 100, 50)
    assert ramp.sample(0.25) == (50, 25, 0)


def test_color_ramp_rejects_invalid_stops_and_sample_values():
    with pytest.raises(ValueError):
        ColorRamp(((1, 2, 3),))
    with pytest.raises(ValueError):
        ColorRamp(((1, 2, 3), (4, 5, 256)))
    with pytest.raises(ValueError):
        ColorRamp(((1, 2, 3), (4, 5, 6))).sample(float("nan"))
