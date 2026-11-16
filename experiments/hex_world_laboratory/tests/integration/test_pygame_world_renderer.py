"""Renderer integration tests across both supported hex orientations."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from hex_world_lab.camera import CameraController, Viewport
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
)
from hex_world_lab.rendering import CellVisual, PygameWorldRenderer, WorldRenderSnapshot


@pytest.mark.parametrize(
    "orientation",
    [HexOrientation.FLAT_TOP, HexOrientation.POINTY_TOP],
)
def test_renderer_uses_camera_transform_for_both_hex_orientations(orientation):
    pygame.init()
    try:
        layout = HexLayout(orientation, radius=20.0)
        camera = CameraController(
            Viewport(200, 160),
            WorldPoint(15.0, -8.0),
            zoom=2.0,
        )
        snapshot = WorldRenderSnapshot(
            cells=(CellVisual(AxialCoord(0, 0)),),
            circles=(),
            polygons=(),
            boundaries=(),
            house_lines=(),
            actor_position=WorldPoint(15.0, -8.0),
            actor_radius=5.0,
        )
        surface = pygame.Surface((200, 160))

        PygameWorldRenderer().render(
            surface,
            snapshot,
            layout,
            camera.transform,
        )

        assert surface.get_at((100, 80))[:3] == (231, 93, 83)
        assert surface.get_at((100, 70))[:3] != (21, 25, 34)
    finally:
        pygame.quit()
