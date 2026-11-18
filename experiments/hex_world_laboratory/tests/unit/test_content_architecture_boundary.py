"""The content domain must remain independent of Pygame and rendering."""

import ast
import subprocess
import sys
from pathlib import Path


def test_content_domain_does_not_import_pygame_or_rendering():
    root = Path(__file__).resolve().parents[2] / "src" / "hex_world_lab" / "content"
    violations = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(
                name == "pygame"
                or name.startswith("pygame.")
                or name == "hex_world_lab.rendering"
                or name.startswith("hex_world_lab.rendering.")
                or name == "hex_world_lab.environment"
                or name.startswith("hex_world_lab.environment.")
                or name == "hex_world_lab.physics"
                or name.startswith("hex_world_lab.physics.")
                for name in names
            ):
                violations.append(f"{path.name}:{node.lineno}")
    assert not violations, ", ".join(violations)


def test_importing_content_domain_does_not_load_pygame_or_rendering():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import hex_world_lab.content; "
            "assert 'pygame' not in sys.modules; "
            "assert 'hex_world_lab.rendering' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
