import math
import pytest
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world, hex_corners, hex_edges, hex_polygon

@pytest.mark.parametrize("orientation",list(HexOrientation))
def test_hex_has_six_vertices_and_equal_radii(orientation):
    layout=HexLayout(orientation=orientation,radius=2.0,origin=WorldPoint(3.0,-5.0))
    center=axial_to_world(AxialCoord(-2,4),layout)
    corners=hex_corners(center,layout)
    assert len(corners)==6
    for corner in corners:
        assert math.hypot(corner.x-center.x,corner.y-center.y)==pytest.approx(2.0)

@pytest.mark.parametrize("orientation",list(HexOrientation))
def test_hex_edges_have_equal_length(orientation):
    layout=HexLayout(orientation=orientation,radius=1.75)
    corners=hex_corners(WorldPoint(0.0,0.0),layout)
    lengths=[math.hypot(corners[(i+1)%6].x-corners[i].x,corners[(i+1)%6].y-corners[i].y) for i in range(6)]
    assert lengths==pytest.approx([layout.radius]*6)
    assert len(hex_edges(WorldPoint(0.0,0.0),layout))==6

def test_hex_polygon_uses_cell_center():
    layout=HexLayout(HexOrientation.POINTY_TOP,radius=1.0)
    assert hex_polygon(AxialCoord(0,0),layout)==hex_corners(WorldPoint(0,0),layout)
