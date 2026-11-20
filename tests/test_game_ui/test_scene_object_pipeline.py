import json
import shutil
import tempfile
from pathlib import Path

from core.domain.spatial import HexCoord, WorldPoint, axial_to_world_point
from game_ui.world_rendering.scene_object_pipeline import SceneObjectPipeline


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "content" / "demo_eldoria"


class FakeImage:
    def get_size(self):
        return (256, 256)

    def convert_alpha(self):
        return self


class FakeImageLoader:
    def load(self, _path):
        return FakeImage()


class FakePygame:
    error = OSError
    image = FakeImageLoader()


def test_pipeline_loads_map_scoped_objects_and_caches_referenced_assets():
    pipeline = SceneObjectPipeline(PACKAGE_ROOT, FakePygame(), 32.0)

    objects = pipeline.objects_for_map("starting_valley")

    assert len(objects) == 15
    workbench = next(obj for obj in objects if obj.object_id == "village-workbench")
    assert workbench.kind == "structure"
    assert pipeline.loaded_asset_count == 3
    assert pipeline.objects_for_map("missing_map") == ()


def test_prop_hit_test_uses_trunk_collider_not_entire_canopy():
    pipeline = SceneObjectPipeline(PACKAGE_ROOT, FakePygame(), 32.0)
    obj = pipeline.objects_for_map("starting_valley")[0]
    center = axial_to_world_point(
        HexCoord(-3, 0),
        32.0,
    )

    hit = pipeline.object_at_world_point(
        "starting_valley", WorldPoint(center.x, center.y - 7),
    )
    canopy_only = pipeline.object_at_world_point(
        "starting_valley", WorldPoint(center.x + 40, center.y - 40),
    )

    assert hit is not None
    assert hit.object_id == obj.object_id
    assert canopy_only is None


def test_pipeline_preserves_structure_kind_for_interaction_routing():
    with tempfile.TemporaryDirectory() as directory:
        package_path = Path(directory) / "demo_eldoria"
        shutil.copytree(PACKAGE_ROOT, package_path)
        placement_path = package_path / "placements" / "empty.json"
        definition = json.loads(placement_path.read_text(encoding="utf-8"))
        definition["objects"][0]["kind"] = "structure"
        placement_path.write_text(
            json.dumps(definition), encoding="utf-8",
        )

        pipeline = SceneObjectPipeline(package_path, FakePygame(), 32.0)

        assert pipeline.objects_for_map("starting_valley")[0].kind == "structure"
