import math
import pytest

from hex_world_lab.environment import EnvironmentalObjectDefinition
from hex_world_lab.physics import CircleShape


def test_definition_normalizes_immutable_anchor_values():
    value = EnvironmentalObjectDefinition("tree", "tree", [0.5, 0.95], (0.5, 0.8), (0.1, 0.0, 0.8, 0.7), CircleShape(5))
    assert value.ground_anchor == (0.5, 0.95)
    assert value.canopy_bounds == (0.1, 0.0, 0.8, 0.7)
    with pytest.raises((AttributeError, TypeError)):
        value.asset_key = "other"


@pytest.mark.parametrize("anchor", [(float("nan"), 0.5), (0.5, float("inf")), (-0.1, 0.5), (0.5, 1.1)])
def test_definition_rejects_invalid_anchors(anchor):
    with pytest.raises(ValueError):
        EnvironmentalObjectDefinition("tree", "tree", anchor, (0.5, 0.8))


@pytest.mark.parametrize("bounds", [(0, 0, 0, 1), (0.8, 0, 0.3, 1), (0, 0, 1, float("nan"))])
def test_definition_rejects_invalid_canopy_bounds(bounds):
    with pytest.raises(ValueError):
        EnvironmentalObjectDefinition("tree", "tree", (0.5, 1), (0.5, 0.8), bounds)


def test_definition_rejects_blank_identity_and_unsupported_collider():
    with pytest.raises(ValueError):
        EnvironmentalObjectDefinition(" ", "tree", (0.5, 1), (0.5, 0.8))
    with pytest.raises(TypeError):
        EnvironmentalObjectDefinition("tree", "tree", (0.5, 1), (0.5, 0.8), collider=object())
