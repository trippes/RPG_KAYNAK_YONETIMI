"""Regression guards for the GameplayService/UI architectural boundary."""

import re
from pathlib import Path


def test_game_ui_does_not_reach_gameplay_service_internals():
    ui_root = Path(__file__).resolve().parents[2] / "game_ui"
    forbidden = ("service.application", "self.service.application")
    private_service_access = re.compile(
        r"(?:self\\.)?service\\._[A-Za-z][A-Za-z0-9_]*"
    )
    violations = []
    for source_path in sorted(ui_root.rglob("*.py")):
        source = source_path.read_text(encoding="utf-8")
        relative_path = source_path.relative_to(ui_root)
        for expression in forbidden:
            if expression in source:
                violations.append(f"{relative_path}: {expression}")
        for match in private_service_access.finditer(source):
            violations.append(f"{relative_path}: {match.group(0)}")
        # GameWindow is the composition root; screens and renderers are not.
        if source_path.name != "game_window.py":
            for expression in ("application.holder", "holder.current"):
                if expression in source:
                    violations.append(f"{relative_path}: {expression}")
    assert not violations, "\\n".join(violations)


def test_gameplay_service_does_not_publish_application_escape_hatch():
    from application.gameplay_service import GameplayService

    assert not hasattr(GameplayService, "application")
