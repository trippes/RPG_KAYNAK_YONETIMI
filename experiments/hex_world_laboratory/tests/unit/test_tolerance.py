from hex_world_lab.geometry.tolerance import GEOMETRY_ABS_TOLERANCE, GEOMETRY_REL_TOLERANCE

def test_geometry_tolerances_are_centralized_and_positive():
    assert GEOMETRY_ABS_TOLERANCE>0
    assert GEOMETRY_REL_TOLERANCE>0
