"""Regression guards for the GameplayService/UI architectural boundary."""

from pathlib import Path


def test_game_ui_does_not_reach_gameplay_service_internals():
    ui_root = Path(__file__).resolve().parents[2] / "game_ui"
    forbidden = (
        "service.application",
        "self.service.application",
        "self.service._character_factory",
        "self.service._creation_from_eren",
        "self.service._player_name_confirmed",
        "self.service._dialogue_context",
    )
    violations = []
    for source_path in sorted(ui_root.rglob("*.py")):
        source = source_path.read_text(encoding="utf-8")
        for expression in forbidden:
            if expression in source:
                violations.append(
                    f"{source_path.relative_to(ui_root)}: {expression}"
                )
    assert not violations, "\n".join(violations)


def test_gameplay_service_does_not_publish_application_escape_hatch():
    from application.gameplay_service import GameplayService

    assert not hasattr(GameplayService, "application")
