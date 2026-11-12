import json
import tempfile
import unittest
from pathlib import Path

from world.map_loader import (
    load_map_definitions, build_world_map, build_local_map_definitions,
)
from world.map_definition import MapDefinitionError


def record(map_id, width=4, height=3, transitions=()):
    return {
        "schema_version": 1, "map_id": map_id, "name": map_id, "description": "",
        "size": {"width": width, "height": height},
        "terrain": {"default_tile": "grass"}, "world_position": [0, 0], "transitions": list(transitions),
    }


def transition(identifier, target, source=(3, 1), destination=(0, 1), direction="east"):
    return {
        "id": identifier, "from_tiles": [list(source)], "target_map_id": target,
        "target_tiles": [list(destination)], "direction": direction,
    }


class TestMapPackageTransitions(unittest.TestCase):
    def _load(self, records):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for map_id, data in records.items():
            (root / f"{map_id}.json").write_text(json.dumps(data), encoding="utf-8")
        return load_map_definitions(root)

    def test_loads_transition_between_different_sized_maps(self):
        maps = self._load({
            "source": record("source", transitions=[transition("out", "target", destination=(5, 6))]),
            "target": record("target", 8, 7),
        })
        self.assertEqual(maps["source"].transitions[0].target_tiles, ((5, 6),))

    def test_rejects_missing_target_map(self):
        with self.assertRaises(MapDefinitionError):
            self._load({"source": record("source", transitions=[transition("out", "missing")])})

    def test_rejects_target_coordinate_outside_target_bounds(self):
        with self.assertRaises(MapDefinitionError):
            self._load({
                "source": record("source", transitions=[transition("out", "target", destination=(8, 1))]),
                "target": record("target", 8, 7),
            })

    def test_rejects_duplicate_transition_ids_across_maps(self):
        with self.assertRaises(MapDefinitionError):
            self._load({
                "source": record("source", transitions=[transition("shared", "target")]),
                "target": record("target", transitions=[transition("shared", "source")]),
            })

    def test_maps_without_transitions_are_valid(self):
        self.assertEqual(self._load({"isolated": record("isolated")})["isolated"].transitions, ())

    def test_world_graph_is_built_from_one_way_map_exits(self):
        maps = self._load({
            "source": record("source", transitions=[
                {**transition("out", "target"), "bidirectional": False}
            ]),
            "target": record("target", 8, 7),
        })
        world = build_world_map(maps, "world")
        self.assertEqual(
            tuple(item.location_id for item in world.neighbors("source")),
            ("target",),
        )
        self.assertEqual(world.neighbors("target"), ())

    def test_local_map_dimensions_are_built_from_map_catalog(self):
        maps = self._load({
            "small": record("small", 16, 24),
            "large": record("large", 40, 18),
        })
        local_maps = {
            item.location_id: (item.width, item.height)
            for item in build_local_map_definitions(maps, "world")
        }
        self.assertEqual(local_maps, {"large": (40, 18), "small": (16, 24)})

    def test_bidirectional_exit_requires_exact_reciprocal_tile_sets(self):
        with self.assertRaisesRegex(MapDefinitionError, "reciprocal"):
            self._load({
                "source": record("source", transitions=[
                    {**transition("out", "target", source=(3, 0), destination=(0, 1)),
                     "bidirectional": True}
                ]),
                "target": record("target", 8, 7, transitions=[
                    {**transition("back", "source", source=(0, 1), destination=(3, 1), direction="west"),
                     "bidirectional": True}
                ]),
            })


if __name__ == "__main__":
    unittest.main()
