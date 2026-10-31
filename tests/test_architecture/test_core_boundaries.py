import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[2]
CORE_ROOT = ROOT / "core"
FORBIDDEN_CORE_ROOTS = {
    "character",
    "combat",
    "economy",
    "inventory",
    "npc",
    "quests",
    "resources",
    "pygame",
    "save",
    "gameplay",
    "adapters",
}


def core_modules():
    return sorted(
        path
        for path in CORE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def imported_roots(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        roots.update(name.split(".")[0] for name in names if name)
    return roots


def core_graph():
    graph = {}
    known = {
        ".".join(path.relative_to(ROOT).with_suffix("").parts)
        for path in core_modules()
    }
    for path in core_modules():
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        edges = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                candidates = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                candidates = [node.module or ""]
            else:
                continue
            for candidate in candidates:
                parts = candidate.split(".")
                for index in range(len(parts), 0, -1):
                    target = ".".join(parts[:index])
                    if target in known:
                        edges.add(target)
                        break
        graph[module] = edges
    return graph


class TestCoreArchitectureBaseline(unittest.TestCase):
    def test_core_has_no_gameplay_or_adapter_imports(self):
        violations = []
        for path in core_modules():
            forbidden = imported_roots(path) & FORBIDDEN_CORE_ROOTS
            if forbidden:
                violations.append((str(path), sorted(forbidden)))
        self.assertEqual([], violations)

    def test_core_import_graph_has_no_cycle(self):
        graph = core_graph()
        visiting = set()
        visited = set()

        def visit(module):
            if module in visiting:
                return True
            if module in visited:
                return False
            visiting.add(module)
            if any(visit(child) for child in graph[module]):
                return True
            visiting.remove(module)
            visited.add(module)
            return False

        cycles = [module for module in graph if visit(module)]
        self.assertEqual([], cycles)

    def test_foundation_does_not_import_upper_layers(self):
        forbidden = {
            "application",
            "domain",
            "entity",
            "world",
            "actions",
            "simulation",
            "gameplay",
            "character",
            "combat",
            "economy",
            "inventory",
            "npc",
            "quests",
            "resources",
        }
        violations = []
        foundation_root = CORE_ROOT / "foundation"
        for path in foundation_root.rglob("*.py"):
            roots = imported_roots(path) & forbidden
            if roots:
                violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_domain_does_not_import_application_or_gameplay(self):
        forbidden = {
            "application",
            "simulation",
            "gameplay",
            "character",
            "combat",
            "economy",
            "inventory",
            "npc",
            "quests",
            "resources",
        }
        violations = []
        domain_root = CORE_ROOT / "domain"
        for path in domain_root.rglob("*.py"):
            roots = imported_roots(path) & forbidden
            if roots:
                violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_simulation_has_no_gameplay_dependency(self):
        violations = []
        simulation_root = CORE_ROOT / "simulation"
        for path in simulation_root.rglob("*.py"):
            forbidden = imported_roots(path) & FORBIDDEN_CORE_ROOTS
            if forbidden:
                violations.append((str(path), sorted(forbidden)))
        self.assertEqual([], violations)

    def test_canonical_simulation_has_no_legacy_event_or_time_imports(self):
        forbidden = {"core.events", "core.event_bus", "core.event_manager", "time_system"}
        violations = []
        simulation_root = CORE_ROOT / "simulation"
        for path in simulation_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            roots = {name for name in imported if name in forbidden or name.startswith("time_system")}
            if roots:
                violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_canonical_core_layers_have_no_legacy_api_imports(self):
        forbidden = {
            "core.events", "core.event_bus", "core.event_manager", "time_system",
            "core.actions", "core.entity.position", "time_system.tick",
        }
        violations = []
        for layer in ("foundation", "domain", "time", "simulation"):
            for path in (CORE_ROOT / layer).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                imported = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.add(node.module)
                roots = {name for name in imported if name in forbidden or name.startswith("time_system")}
                if roots:
                    violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_world_domain_facade_has_no_direct_legacy_runtime_imports(self):
        forbidden = {"core.clock", "core.events", "time_system", "core.event_bus", "core.event_manager"}
        violations = []
        for path in (CORE_ROOT / "world").glob("world.py"):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            roots = {name for name in imported if name in forbidden or name.startswith("time_system")}
            if roots:
                violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_persistence_contract_has_no_legacy_or_gameplay_imports(self):
        forbidden = {
            "core.events", "core.event_bus", "core.event_manager", "time_system",
            "core.clock", "core.actions", "core.entity.position", "character", "combat",
            "economy", "inventory", "npc", "quests", "resources", "pygame", "save",
        }
        violations = []
        persistence_root = CORE_ROOT / "persistence"
        for path in persistence_root.rglob("*.py"):
            roots = imported_roots(path) & forbidden
            if roots:
                violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_core_source_is_valid_utf8_without_bom(self):
        bom_files = [
            str(path)
            for path in core_modules()
            if path.read_bytes().startswith(b"\xef\xbb\xbf")
        ]
        self.assertEqual([], bom_files)

    def test_domain_and_persistence_are_below_gameplay_and_application(self):
        violations = []
        for layer, forbidden in {
            "domain": {"application", "simulation", "gameplay", "persistence"},
            "persistence": {"gameplay", "adapters", "save", "sqlite3", "sqlalchemy"},
        }.items():
            for path in (CORE_ROOT / layer).rglob("*.py"):
                roots = imported_roots(path) & forbidden
                if roots:
                    violations.append((str(path), sorted(roots)))
        self.assertEqual([], violations)

    def test_canonical_layers_do_not_import_compatibility_layer(self):
        violations = []
        for layer in ("foundation", "domain", "time", "simulation", "persistence"):
            for path in (CORE_ROOT / layer).rglob("*.py"):
                if "core.compatibility" in imported_roots(path):
                    violations.append(str(path))
        self.assertEqual([], violations)

    def test_canonical_scheduler_has_no_callback_contract(self):
        scheduler = CORE_ROOT / "simulation" / "scheduler.py"
        tree = ast.parse(scheduler.read_text(encoding="utf-8-sig"), filename=str(scheduler))
        schedule = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "schedule"
        )
        self.assertNotIn("callback", {argument.arg for argument in schedule.args.args})
        scheduled_work = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "ScheduledWork"
        )
        fields = {
            node.target.id
            for node in scheduled_work.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        self.assertIn("work_type", fields)
        self.assertNotIn("callback", fields)


if __name__ == "__main__":
    unittest.main()
