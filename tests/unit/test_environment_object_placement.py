import pytest

from hex_world_lab.environment import EnvironmentalObjectPlacement
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.world import MapId, WorldId


def test_placement_is_immutable_and_world_scoped():
    value = EnvironmentalObjectPlacement("tree-1", "tree", WorldId("world"), MapId("map"), WorldPoint(2, 3))
    assert value.ground_position == WorldPoint(2, 3)
    with pytest.raises((AttributeError, TypeError)):
        value.instance_id = "other"


def test_placement_rejects_invalid_scope_and_point():
    with pytest.raises(TypeError):
        EnvironmentalObjectPlacement("tree-1", "tree", "world", MapId("map"), WorldPoint(0, 0))
