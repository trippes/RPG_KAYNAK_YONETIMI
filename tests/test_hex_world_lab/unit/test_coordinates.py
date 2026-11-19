import pytest
from hex_world_lab.geometry import AxialCoord, CubeCoord, WorldPoint, axial_to_cube, cube_to_axial, cube_round

@pytest.mark.parametrize("q,r", [(0,0),(1,-1),(-8,3),(1000,-2000)])
def test_axial_cube_round_trip(q,r):
    axial=AxialCoord(q,r); cube=axial_to_cube(axial)
    assert cube.q+cube.r+cube.s==0
    assert cube_to_axial(cube)==axial

def test_cube_rejects_invalid_sum():
    with pytest.raises(ValueError): CubeCoord(1,2,3)

def test_axial_rejects_non_integer_values():
    with pytest.raises(TypeError): AxialCoord(1.5,0)

def test_world_point_rejects_non_finite_values():
    with pytest.raises(ValueError): WorldPoint(float("nan"),0.0)

def test_cube_rounding_rejects_invalid_fractional_sum():
    with pytest.raises(ValueError): cube_round(0.2,0.2,0.2)

def test_cube_rounding_rejects_non_finite_values():
    with pytest.raises(ValueError): cube_round(float("inf"),0.0,float("-inf"))
