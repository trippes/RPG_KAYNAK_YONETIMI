import os
from pathlib import Path
import subprocess
import sys
import pytest
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world, hex_corners, hex_distance, hex_neighbors, world_to_axial

@pytest.mark.parametrize("orientation",list(HexOrientation))
def test_geometry_stack_is_consistent(orientation):
    layout=HexLayout(orientation=orientation,radius=1.25,origin=WorldPoint(-10,6))
    for q in range(-10,11):
        for r in range(-10,11):
            cell=AxialCoord(q,r); center=axial_to_world(cell,layout)
            assert world_to_axial(center,layout)==cell
            assert len(hex_corners(center,layout))==6
            assert all(hex_distance(cell,n)==1 for n in hex_neighbors(cell))

def test_geometry_import_does_not_load_pygame():
    source_root=Path(__file__).resolve().parents[2]/"src"
    environment=os.environ.copy(); environment["PYTHONPATH"]=str(source_root)
    result=subprocess.run([sys.executable,"-c","import sys; import hex_world_lab.geometry; assert 'pygame' not in sys.modules"],
        env=environment,capture_output=True,text=True,check=False)
    assert result.returncode==0,result.stderr
