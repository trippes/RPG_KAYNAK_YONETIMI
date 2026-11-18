"""The content domain must remain independent of Pygame and rendering."""
import ast
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
            if any(name == "pygame" or name.startswith("pygame.") or name == "hex_world_lab.rendering" or name.startswith("hex_world_lab.rendering.") for name in names):
                violations.append(f"{path.name}:{node.lineno}")
    assert not violations, ", ".join(violations)
