"""Phase 9 dependency-direction guards."""
import ast
from pathlib import Path

def imports_in(path):
    tree=ast.parse(path.read_text(encoding="utf-8"))
    result=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): result.extend(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom): result.append(node.module or "")
    return result

def test_entity_interaction_and_companion_domains_do_not_import_pygame():
    root=Path(__file__).resolve().parents[2]/"src"/"hex_world_lab"
    violations=[]
    for package in ("entities","interaction","companions"):
        for path in (root/package).rglob("*.py"):
            for name in imports_in(path):
                if name=="pygame" or name.startswith("pygame."): violations.append(f"{path}:{name}")
    assert not violations

def test_geometry_world_and_spatial_do_not_import_entity_domains():
    root=Path(__file__).resolve().parents[2]/"src"/"hex_world_lab"
    violations=[]
    for package in ("geometry","world","spatial"):
        for path in (root/package).rglob("*.py"):
            for name in imports_in(path):
                if any(part in name.split(".") for part in ("entities","interaction","companions")):
                    violations.append(f"{path}:{name}")
    assert not violations
