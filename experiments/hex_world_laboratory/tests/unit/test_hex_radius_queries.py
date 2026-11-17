"""Differential tests for direct axial disk generation."""
import pytest

from hex_world_lab.geometry import AxialCoord, hex_distance, hex_radius_cells


@pytest.mark.parametrize("radius", range(7))
def test_axial_disk_matches_brute_force(radius):
    center = AxialCoord(-4, 9)
    actual = hex_radius_cells(center, radius)
    expected = tuple(sorted(
        (AxialCoord(q, r) for q in range(center.q-radius, center.q+radius+1)
         for r in range(center.r-radius, center.r+radius+1)
         if hex_distance(center, AxialCoord(q, r)) <= radius),
        key=lambda cell: (cell.q, cell.r),
    ))
    assert actual == expected
    assert len(actual) == 1 + 3 * radius * (radius + 1)


def test_radius_zero_and_invalid_radius():
    assert hex_radius_cells(AxialCoord(0, 0), 0) == (AxialCoord(0, 0),)
    with pytest.raises(ValueError):
        hex_radius_cells(AxialCoord(0, 0), -1)
