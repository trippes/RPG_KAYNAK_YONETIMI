import pytest

from hex_world_lab.environment import (
    EnvironmentalObjectDefinition, EnvironmentalObjectPlacement, EnvironmentalObjectScene,
)
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.world import MapId, WorldId


def _definition(key="tree"):
    return EnvironmentalObjectDefinition(key, key, (0.5, 1), (0.5, 0.8))


def _placement(instance, definition="tree", map_id=None):
    return EnvironmentalObjectPlacement(instance, definition, WorldId("world"), map_id or MapId("map"), WorldPoint(0, 0))


def test_scene_sorts_definitions_and_instances_deterministically():
    scene = EnvironmentalObjectScene(WorldId("world"), MapId("map"), (_definition("z"), _definition("tree")), (_placement("z", "tree"), _placement("a", "z")))
    assert [item.definition_id for item in scene.definitions] == ["tree", "z"]
    assert [item.instance_id for item in scene.placements] == ["a", "z"]


def test_scene_rejects_duplicate_ids_unknown_definitions_and_wrong_map():
    with pytest.raises(ValueError):
        EnvironmentalObjectScene(WorldId("world"), MapId("map"), (_definition(), _definition()), ())
    with pytest.raises(ValueError):
        EnvironmentalObjectScene(WorldId("world"), MapId("map"), (_definition(),), (_placement("a", "missing"),))
    with pytest.raises(ValueError):
        EnvironmentalObjectScene(WorldId("world"), MapId("map"), (_definition(),), (_placement("a", map_id=MapId("elsewhere")),))
