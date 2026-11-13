"""Tests for composing independent atlas parts through the animated tree rig."""
import unittest

from game_ui.world_rendering.tree_rig_renderer import TreeRigRenderer
from game_ui.world_rendering.tree_skeleton import DEFAULT_TREE_SKELETON


class FakeSurface:
    def __init__(self, size):
        self.size = size

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]


class FakeTransform:
    @staticmethod
    def smoothscale(surface, size):
        return FakeSurface(size)

    @staticmethod
    def rotate(surface, _angle):
        return surface


class FakePygame:
    transform = FakeTransform()


class FakeTarget:
    def __init__(self):
        self.calls = []

    def blit(self, surface, destination):
        self.calls.append((surface, destination))


class FakeRenderer:
    def __init__(self):
        self.pg = FakePygame()
        self.surface = FakeTarget()


class FakeAtlas:
    rig_layers = (
        {
            "component_id": "trunk",
            "order": 0,
            "anchor": [0.5, 0.9],
            "pivot": [0.5, 1.0],
            "size": [0.3, 0.8],
            "motion": {"kind": "trunk"},
        },
        {
            "component_id": "foliage",
            "order": 1,
            "anchor": [0.5, 0.3],
            "pivot": [0.5, 0.5],
            "size": [0.5, 0.4],
            "motion": {"kind": "leaf", "index": 0},
        },
    )

    def __init__(self):
        self.parts = {
            "trunk": FakeSurface((20, 80)),
            "foliage": FakeSurface((50, 40)),
        }

    def get(self, component_id):
        return self.parts.get(component_id)


class TestTreeRigRenderer(unittest.TestCase):
    def test_draw_composes_every_configured_layer(self):
        renderer = FakeRenderer()
        rig = TreeRigRenderer()
        self.assertTrue(rig.draw(
            renderer, FakeAtlas(), DEFAULT_TREE_SKELETON,
            (100, 200), (120, 180), 1.0, 0.0,
        ))
        self.assertEqual(len(renderer.surface.calls), 2)

    def test_leaf_layer_moves_while_ground_anchor_stays_fixed(self):
        atlas = FakeAtlas()
        rig = TreeRigRenderer()
        first = FakeRenderer()
        second = FakeRenderer()
        rig.draw(first, atlas, DEFAULT_TREE_SKELETON, (100, 200), (120, 180), 1.0, 0.0)
        rig.draw(second, atlas, DEFAULT_TREE_SKELETON, (100, 200), (120, 180), 1.0, 1.0)
        self.assertEqual(first.surface.calls[0][1], second.surface.calls[0][1])
        self.assertNotEqual(first.surface.calls[1][1], second.surface.calls[1][1])

    def test_missing_rig_metadata_keeps_legacy_renderer_available(self):
        class EmptyAtlas:
            rig_layers = ()

        renderer = FakeRenderer()
        self.assertFalse(TreeRigRenderer().draw(
            renderer, EmptyAtlas(), DEFAULT_TREE_SKELETON,
            (0, 0), (100, 100), 1.0, 0.0,
        ))
        self.assertEqual(renderer.surface.calls, [])


if __name__ == "__main__":
    unittest.main()
