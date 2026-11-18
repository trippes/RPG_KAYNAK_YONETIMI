from pathlib import Path


def test_environment_domain_does_not_import_pygame_or_main_game_modules():
    root = Path(__file__).resolve().parents[2] / "src" / "hex_world_lab" / "environment"
    for path in root.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import pygame" not in source
        assert "game_ui" not in source
