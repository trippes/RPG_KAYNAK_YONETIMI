"""Guard dependency direction between the simulation core and Pygame."""

import ast
from pathlib import Path

CORE_PACKAGES = ("camera", "geometry", "movement", "physics", "simulation", "world")


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
         "Pygame imports must stay outside camera/geometry/movement/physics/simulation/world: "
        + ", ".join(violations)
    )


def test_rendering_adapters_do_not_import_simulation_packages() -> None:
    package_root = Path(__file__).resolve().parents[2] / "src" / "hex_world_lab"
    rendering_path = package_root / "rendering"
    forbidden = ("movement", "physics", "simulation", "world")
    violations: list[str] = []

    for source_path in sorted(rendering_path.rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            else:
                continue
            if any(
                name == package or name.startswith(package + ".")
                or name.endswith("." + package)
                for name in imported
                for package in forbidden
            ):
                relative_path = source_path.relative_to(package_root)
                violations.append(f"{relative_path}:{node.lineno}")

    assert not violations, (
        "Rendering may depend on geometry/camera/Pygame, not simulation packages: "
        + ", ".join(violations)
    )


def test_spatial_package_has_no_domain_dependencies() -> None:
    package_root = Path(__file__).resolve().parents[2] / "src" / "hex_world_lab" / "spatial"
    forbidden = ("pygame", "physics", "world", "movement", "simulation")
    violations: list[str] = []
    for source_path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            else:
                continue
            if any(name == item or name.startswith(item + ".") or name.endswith("." + item)
                   for name in imported for item in forbidden):
                violations.append(f"{source_path.name}:{node.lineno}")
    assert not violations, "Spatial must remain domain-independent: " + ", ".join(violations)
