import math
import pytest
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world, world_to_axial, world_to_fractional_axial

@pytest.mark.parametrize("orientation",list(HexOrientation))
@pytest.mark.parametrize("radius",[0.25,1.0,3.5])
@pytest.mark.parametrize("origin",[WorldPoint(0.0,0.0),WorldPoint(12.5,-7.25)])
def test_cell_centers_round_trip(orientation,radius,origin):
    layout=HexLayout(orientation=orientation,radius=radius,origin=origin)
    for q in range(-12,13):
        for r in range(-12,13):
            cell=AxialCoord(q,r)
            assert world_to_axial(axial_to_world(cell,layout),layout)==cell

@pytest.mark.parametrize("orientation",list(HexOrientation))
def test_fractional_axial_transform_inverts_world_transform(orientation):
    layout=HexLayout(orientation=orientation,radius=2.75,origin=WorldPoint(-4.0,8.0))
    for q,r in [(-3.25,7.5),(0.0,0.0),(2.125,-4.75),(100.5,-20.25)]:
        if orientation is HexOrientation.FLAT_TOP:
            point=WorldPoint(layout.origin.x+layout.radius*1.5*q,
                layout.origin.y+layout.radius*math.sqrt(3)*(r+q/2))
        else:
            point=WorldPoint(layout.origin.x+layout.radius*math.sqrt(3)*(q+r/2),
                layout.origin.y+layout.radius*1.5*r)
        actual=world_to_fractional_axial(point,layout)
        assert actual[0]==pytest.approx(q)
        assert actual[1]==pytest.approx(r)

def test_layout_rejects_invalid_radius():
    with pytest.raises(ValueError): HexLayout(HexOrientation.FLAT_TOP,radius=0)
