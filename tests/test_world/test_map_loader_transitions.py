import json
import tempfile
import unittest
from pathlib import Path

from world.map_loader import load_map_definitions
from world.map_definition import MapDefinitionError


def record(map_id, width=4, height=3, transitions=()):
    return {
        "schema_version": 1, "map_id": map_id, "name": map_id, "description": "",
        "size": {"width": width, "height": height},
        "terrain": {"default_tile": "grass"}, "transitions": list(transitions),
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


if __name__ == "__main__":
    unittest.main()
