"""Fail CI if retired square-map runtime or demo content returns."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RETIRED_PATHS = (
    "world",
    "application/movement.py",
    "game_ui/hex_world_view.py",
    "game_ui/screens/map_screen.py",
    "content/demo_eldoria/maps",
    "content/demo_eldoria/world.json",
    "content/demo_eldoria/presentation_assets.json",
)

RETIRED_IMPORTS = {
    "world.map_catalog",
    "world.map_definition",
    "world.map_loader",
    "world.local_map",
    "world.location",
    "world.map",
    "application.movement",
    "game_ui.hex_world_view",
    "game_ui.screens.map_screen",
}

RETIRED_SYMBOLS = {
    "MovementManager",
    "LocalMapDefinition",
    "WorldObjectPlacementRegistry",
    "HexWorldView",
}


def main() -> int:
    failures: list[str] = []

    for relative in RETIRED_PATHS:
        if (ROOT / relative).exists():
            failures.append(f"retired path exists: {relative}")

    import json

    manifest = json.loads(
        (ROOT / "content/demo_eldoria/manifest.json").read_text(encoding="utf-8")
    )
    if "presentation_assets" in manifest:
        failures.append(
            "legacy combined presentation catalog is still active in manifest"
        )

    for source_root in ("application", "game_ui", "npc", "resources", "economy"):
        root = ROOT / source_root
        for source in root.rglob("*.py"):
            try:
                tree = ast.parse(
                    source.read_text(encoding="utf-8"),
                    filename=str(source),
                )
            except (OSError, SyntaxError) as error:
                failures.append(
                    f"cannot inspect {source.relative_to(ROOT)}: {error}"
                )
                continue
            for node in ast.walk(tree):
                imported = []
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = [node.module]
                for module in imported:
                    if module in RETIRED_IMPORTS:
                        failures.append(
                            f"retired import in {source.relative_to(ROOT)}: {module}"
                        )
                if isinstance(node, ast.Name) and node.id in RETIRED_SYMBOLS:
                    failures.append(
                        f"retired symbol in {source.relative_to(ROOT)}: {node.id}"
                    )

    migration_source = (
        ROOT / "application/migrations.py"
    ).read_text(encoding="utf-8")
    if "_restore_legacy_npc_positions" in migration_source:
        failures.append("legacy square NPC position backfill is still present")

    if failures:
        print("Legacy map cleanup verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Legacy map cleanup boundary verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
