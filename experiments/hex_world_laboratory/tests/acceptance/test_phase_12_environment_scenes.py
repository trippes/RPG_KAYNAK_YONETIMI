import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from pathlib import Path
import importlib.util
import pygame

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "render_phase_12_scenes.py"
_SPEC = importlib.util.spec_from_file_location("phase_12_scene_generator", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_phase_12_visual_evidence_contains_environment_and_debug_scenes(tmp_path):
    paths = _MODULE.render_scenes(tmp_path)
    assert len(paths) == 5
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
    pygame.init()
    try:
        for path in paths:
            image = pygame.image.load(str(path))
            assert image.get_size() == (960, 640)
    finally:
        pygame.quit()
