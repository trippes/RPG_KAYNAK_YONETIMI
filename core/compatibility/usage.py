"""Deterministic static and runtime compatibility usage reporting."""

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from .migration import DEFAULT_REGISTRY

_runtime_counts: Counter[str] = Counter()
_runtime_lock = Lock()


def record_usage(legacy_identifier: str) -> None:
    if not DEFAULT_REGISTRY.is_legacy(legacy_identifier):
        raise KeyError(f"Unknown legacy API: {legacy_identifier}")
    with _runtime_lock:
        _runtime_counts[legacy_identifier] += 1


def runtime_usage_counts() -> dict[str, int]:
    with _runtime_lock:
        return dict(_runtime_counts)


def reset_runtime_usage() -> None:
    with _runtime_lock:
        _runtime_counts.clear()


@dataclass(frozen=True)
class StaticUsage:
    legacy_name: str
    path: str
    line: int
    usage_kind: str


@dataclass(frozen=True)
class UsageReportEntry:
    legacy_name: str
    canonical_replacement: str
    static_usage_count: int
    runtime_usage_count: int


_SIMPLE_NAMES = {
    "EventBus": "core.event_bus.EventBus",
    "EventQueue": "core.events.EventQueue",
    "EventType": "core.event_types.EventType",
    "GameClock": "core.clock.GameClock",
    "Scheduler": "time_system.Scheduler",
    "Action": "core.actions.Action",
    "ActionManager": "core.actions.ActionManager",
    "Position": "core.entity.position.Position",
}

_IMPORT_ALIASES = {
    ("time_system.tick", "Tick"): "time_system.Tick",
    ("time_system.scheduler", "Scheduler"): "time_system.Scheduler",
    ("core.actions.action", "Action"): "core.actions.Action",
    ("core.actions.action_manager", "ActionManager"): "core.actions.ActionManager",
    ("core.entity.position", "Position"): "core.entity.position.Position",
}


def _files(root: Path):
    ignored = {"tests", "docs", ".git", "__pycache__"}
    return sorted(path for path in root.rglob("*.py") if not any(part in ignored for part in path.parts))


def scan_static_usage(root: str | Path) -> tuple[StaticUsage, ...]:
    root = Path(root).resolve()
    found = []
    known = DEFAULT_REGISTRY.as_mapping()
    for path in _files(root):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    full = f"{node.module}.{alias.name}"
                    identifier = _IMPORT_ALIASES.get((node.module, alias.name), full)
                    if identifier in known:
                        found.append(StaticUsage(identifier, str(path.relative_to(root)), node.lineno, "import"))
                    elif node.module == "core.constants" and alias.name.startswith("OLAY_"):
                        found.append(StaticUsage("core.constants event constants", str(path.relative_to(root)), node.lineno, "import"))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in known:
                        found.append(StaticUsage(alias.name, str(path.relative_to(root)), node.lineno, "import"))
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in _SIMPLE_NAMES:
                        found.append(StaticUsage(_SIMPLE_NAMES[base.id], str(path.relative_to(root)), node.lineno, "inheritance"))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in _SIMPLE_NAMES:
                    found.append(StaticUsage(_SIMPLE_NAMES[node.func.id], str(path.relative_to(root)), node.lineno, "construction"))
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "dunya_olaylarini_aktar":
                    found.append(StaticUsage("Game.dunya_olaylarini_aktar", str(path.relative_to(root)), node.lineno, "method_call"))
            elif isinstance(node, ast.Attribute) and node.attr == "world_id":
                # Avoid counting World/WorldManager IDs as Entity.world_id.
                if (isinstance(node.value, ast.Name) and node.value.id == "entity") or path.name == "entity.py":
                    found.append(StaticUsage("Entity.world_id", str(path.relative_to(root)), node.lineno, "attribute"))
            elif isinstance(node, ast.Attribute) and node.attr == "_entities":
                # Only the World projection is this migration item; repository
                # internals are canonical storage and are intentionally excluded.
                if path.as_posix().endswith("core/world/world.py"):
                    found.append(StaticUsage("World._entities", str(path.relative_to(root)), node.lineno, "attribute"))
    return tuple(sorted(found, key=lambda item: (item.path, item.line, item.usage_kind, item.legacy_name)))


def usage_report(root: str | Path) -> tuple[UsageReportEntry, ...]:
    static = Counter(item.legacy_name for item in scan_static_usage(root))
    runtime = runtime_usage_counts()
    return tuple(
        UsageReportEntry(entry.legacy_name, entry.canonical_replacement, static[entry.legacy_name], runtime.get(entry.legacy_name, 0))
        for entry in DEFAULT_REGISTRY.get_all_mappings()
    )


if __name__ == "__main__":
    import json
    import sys
    report = usage_report(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
    print(json.dumps([entry.__dict__ for entry in report], ensure_ascii=False, indent=2))
