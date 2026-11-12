"""Run the local release-candidate verification gate.

The gate intentionally checks only deterministic, headless checks.  The
interactive Pygame loop remains a separate manual smoke test because it
requires a display and human input.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def run(label: str, *args: str) -> None:
    print(f"==> {label}")
    subprocess.run(args, cwd=ROOT, check=True)


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
    run("application smoke", PYTHON, "main.py")
    print("Release-candidate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
