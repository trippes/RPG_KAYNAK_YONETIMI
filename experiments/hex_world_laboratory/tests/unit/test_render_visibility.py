"""Conservative viewport culling tests for both hex orientations."""

import pytest

from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering.visibility import VisibleAreaCuller


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_culler_returns_existing_cells_deterministically_and_reduces_candidates(orientation):
    layout = HexLayout(orientation, radius=20.0)
    transform = WorldScreenTransform(Viewport(160, 120), WorldPoint(0.0, 0.0), 1.0)
    cells = {AxialCoord(q, r): object() for q in range(-20, 21) for r in range(-20, 21)}

    result = VisibleAreaCuller().visible_cells(cells, layout, transform)

    assert result == tuple(sorted(result, key=lambda coord: (coord.q, coord.r)))
    assert result
    assert set(result) <= set(cells)
    assert len(result) < len(cells)


def test_culler_keeps_cells_that_can_intersect_viewport_even_when_center_is_outside():
    layout = HexLayout(HexOrientation.FLAT_TOP, radius=20.0)
    transform = WorldScreenTransform(Viewport(100, 100), WorldPoint(0.0, 0.0), 1.0)
    cells = {AxialCoord(q, r): None for q in range(-4, 5) for r in range(-4, 5)}

    result = set(VisibleAreaCuller().visible_cells(cells, layout, transform))

    assert AxialCoord(2, 0) in result


@pytest.mark.parametrize("zoom", [0.5, 1.0, 2.5, 3.0])
def test_culler_tracks_camera_zoom_and_pan(zoom):
    layout = HexLayout(HexOrientation.POINTY_TOP, radius=16.0)
    transform = WorldScreenTransform(Viewport(200, 140), WorldPoint(120.0, -75.0), zoom)
    cells = {AxialCoord(q, r): None for q in range(-100, 101) for r in range(-100, 101)}

    result = VisibleAreaCuller().visible_cells(cells, layout, transform)

    assert result
    assert len(result) < len(cells)
