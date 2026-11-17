"""Acceptance tests for generated Phase 7 visual scenes."""

import pygame

from scripts.render_phase_07_scenes import render_scenes


def test_phase_07_scene_generator_creates_all_visual_evidence(tmp_path):
    paths = render_scenes(tmp_path)
    assert len(paths) == 7
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)

    pygame.init()
    try:
        for path in paths:
            image = pygame.image.load(str(path))
            assert image.get_size() == (960, 640)
    finally:
        pygame.quit()
