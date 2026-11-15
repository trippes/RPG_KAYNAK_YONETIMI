import pytest
from hex_world_lab.geometry import AxialCoord, hex_distance

@pytest.mark.parametrize("first,second,expected",[
    (AxialCoord(0,0),AxialCoord(0,0),0),
    (AxialCoord(0,0),AxialCoord(1,0),1),
    (AxialCoord(0,0),AxialCoord(1,-1),1),
    (AxialCoord(-4,8),AxialCoord(5,-2),10),
    (AxialCoord(1000,-2000),AxialCoord(-1000,2000),4000),
])
def test_hex_distance(first,second,expected):
    assert hex_distance(first,second)==expected

def test_distance_is_symmetric_and_non_negative():
    a,b=AxialCoord(-9,4),AxialCoord(12,-20)
    assert hex_distance(a,b)==hex_distance(b,a)
    assert hex_distance(a,b)>=0
