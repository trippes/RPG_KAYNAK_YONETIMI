"""Guard dependency direction between the simulation core and Pygame."""

import ast
from pathlib import Path

CORE_PACKAGES = ("geometry", "movement", "physics", "simulation", "world")


def test_simulation_core_packages_do_not_import_pygame() -> None:
    package_root = Path(__file__).resolve().parents[2] / "src" / "hex_world_lab"
    violations: list[str] = []

    for package in CORE_PACKAGES:
        package_path = package_root / package
        for source_path in sorted(package_path.rglob("*.py")):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported = [node.module or ""]
                else:
                    continue

                if any(
                    name == "pygame" or name.startswith("pygame.")
                    for name in imported
                ):
                    relative_path = source_path.relative_to(package_root)
                    violations.append(f"{relative_path}:{node.lineno}")

    assert not violations, (
         "Pygame imports must stay outside geometry/movement/physics/simulation/world: "
        + ", ".join(violations)
    )
