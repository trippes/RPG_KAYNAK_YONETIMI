import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from application.hex_world_initializer import (
    HexWorldInitializationError,
    initialize_hex_world,
)
from application.hex_world_runtime import HexWorldRuntimeOwner
from core.domain.spatial import EntityPosition, LocalHexPosition


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"


class FakeBundle:
    def validate(self):
        return None


class FakeApplication:
    def __init__(self):
        self.holder = SimpleNamespace(current=FakeBundle())
        self._world = SimpleNamespace(world_id="eldoria_world")

    def aktif_dunya(self):
        return self._world


class FakeActorBinding:
    def __init__(self, service, fail=False):
        self.service = service
        self.fail = fail

    def register_spatial(self, actor_id, kind, position, profile, **flags):
        if self.fail:
            raise RuntimeError("actor binding rejected placement")
        return self.service.hex_world_runtime.register_entity(
            actor_id,
            kind,
            position,
            profile,
            blocks_movement=flags["blocks_movement"],
            blocks_occupancy=flags["blocks_occupancy"],
        )


class FakeService:
    def __init__(self, package_path, *, fail_registration=False):
        self._content_package_path = package_path
        self.application = FakeApplication()
        self.hex_world_runtime_owner = HexWorldRuntimeOwner()
        self.player_actor_id = "hero"
        self._actor_binding = FakeActorBinding(self, fail_registration)

    @property
    def hex_world_runtime(self):
        return self.hex_world_runtime_owner.runtime

    @property
    def hex_actor_binding(self):
        return self._actor_binding

    def register_gameplay_placements(self, _catalog):
        return ()


def make_package(directory, *, include_start=True, start=(0, 0)):
    package_path = Path(directory) / "demo_eldoria"
    shutil.copytree(PACKAGE, package_path)

    manifest_path = package_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["maps"] = "maps"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    presentation_path = package_path / "placements" / "empty.json"
    presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
    presentation["map_id"] = "village"
    presentation_path.write_text(json.dumps(presentation), encoding="utf-8")

    maps = package_path / "maps"
    maps.mkdir()
    (maps / "village.json").write_text(json.dumps({
        "schema_version": 2,
        "map_id": "village",
        "name": "Village",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [0, 1]],
        "cell_overrides": [],
    }), encoding="utf-8")

    if include_start:
        starter_path = package_path / "starter_content.json"
        starter = json.loads(starter_path.read_text(encoding="utf-8"))
        starter["world"]["hex_start"] = {
            "map_id": "village",
            "q": start[0],
            "r": start[1],
        }
        starter_path.write_text(json.dumps(starter), encoding="utf-8")
    return package_path


class TestHexWorldInitializer(unittest.TestCase):
    def test_package_without_hex_maps_does_not_create_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package_path)
            manifest_path = package_path / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("maps")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            service = FakeService(package_path)

            self.assertIsNone(initialize_hex_world(service))
            self.assertIsNone(service.hex_world_runtime)

    def test_real_demo_package_initializes_its_authored_starting_valley(self):
        service = FakeService(PACKAGE)

        runtime = initialize_hex_world(service)

        self.assertIs(runtime, service.hex_world_runtime)
        self.assertEqual(runtime.map_ids, ("starting_valley",))
        self.assertEqual(
            runtime.entity("hero").position,
            EntityPosition("starting_valley", LocalHexPosition(0, 0)),
        )

    def test_hex_maps_require_explicit_player_start(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = make_package(directory, include_start=False)
            service = FakeService(package_path)

            with self.assertRaisesRegex(
                HexWorldInitializationError, "explicit world.hex_start",
            ):
                initialize_hex_world(service)

            self.assertIsNone(service.hex_world_runtime)

    def test_player_start_must_belong_to_map_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = make_package(directory, start=(9, 9))
            service = FakeService(package_path)

            with self.assertRaisesRegex(
                HexWorldInitializationError, "outside map",
            ):
                initialize_hex_world(service)

            self.assertIsNone(service.hex_world_runtime)

    def test_initializes_session_runtime_and_player_from_explicit_start(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = make_package(directory, start=(1, 0))
            service = FakeService(package_path)

            runtime = initialize_hex_world(service)

            self.assertIs(runtime, service.hex_world_runtime)
            self.assertEqual(runtime.world_id.value, "eldoria_world")
            self.assertEqual(
                runtime.entity("hero").position,
                EntityPosition("village", LocalHexPosition(1, 0)),
            )

    def test_failed_player_registration_discards_empty_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = make_package(directory)
            service = FakeService(package_path, fail_registration=True)

            with self.assertRaisesRegex(RuntimeError, "actor binding rejected"):
                initialize_hex_world(service)

            self.assertIsNone(service.hex_world_runtime)


if __name__ == "__main__":
    unittest.main()
