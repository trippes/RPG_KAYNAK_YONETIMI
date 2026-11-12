"""Run the local release-candidate verification gate.

The gate intentionally checks only deterministic, headless checks.  The
interactive Pygame loop remains a separate manual smoke test because it
requires a display and human input.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def run(label: str, *args: str) -> None:
    print(f"==> {label}")
    subprocess.run(args, cwd=ROOT, check=True)


def verify_installed_content_package() -> None:
    """Build and install a wheel, then load its shipped map content off-source."""
    with tempfile.TemporaryDirectory(prefix="rpg-release-package-") as directory:
        temporary_root = Path(directory)
        wheel_dir = temporary_root / "wheel"
        install_dir = temporary_root / "install"
        wheel_dir.mkdir()

        run(
            "build distributable wheel",
            PYTHON,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
            str(ROOT),
        )
        wheels = tuple(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(
                f"Expected exactly one wheel, found {len(wheels)}."
            )

        run(
            "install wheel into isolated target",
            PYTHON,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(install_dir),
            str(wheels[0]),
        )

        package_dir = install_dir / "content" / "demo_eldoria"
        if not (package_dir / "manifest.json").is_file():
            raise RuntimeError(
                "Installed wheel is missing content/demo_eldoria/manifest.json."
            )

        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(install_dir)
            if not existing_pythonpath
            else str(install_dir) + os.pathsep + existing_pythonpath
        )
        package_check = (
            "import sys; "
            "from pathlib import Path; "
            "from application.content_loader import load_content_package; "
            "package = load_content_package(Path(sys.argv[1])); "
            "assert package.package_id == 'demo_eldoria'; "
            "assert len(package.map_definitions) == 9, "
            "f'Expected 9 shipped maps, found {len(package.map_definitions)}'; "
            "print('Installed content package verified:', package.package_id, "
            "len(package.map_definitions), 'maps')"
        )
        subprocess.run(
            [PYTHON, "-c", package_check, str(package_dir)],
            cwd=temporary_root,
            env=environment,
            check=True,
        )


def main() -> int:
    run(
        "unit tests",
        PYTHON,
        "-m",
        "pytest",
        "-q",
    )
    run(
        "compileall",
        PYTHON,
        "-m",
        "compileall",
        "-q",
        "core",
        "application",
        "character",
        "combat",
        "economy",
        "npc",
        "quests",
        "resources",
        "world",
        "game_ui",
        "tests",
    )
    verify_installed_content_package()
    run("application smoke", PYTHON, "main.py")
    print("Release-candidate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
