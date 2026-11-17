"""Acceptance tests for generated Phase 7 visual scenes."""

import importlib.util
from pathlib import Path

import pygame

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "render_phase_07_scenes.py"
_SPEC = importlib.util.spec_from_file_location("phase_07_scene_generator", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
render_scenes = _MODULE.render_scenes


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
