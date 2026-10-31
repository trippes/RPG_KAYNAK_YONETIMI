import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[2]
CORE_ROOT = ROOT / "core"


def imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class TestWorldModelBoundaries(unittest.TestCase):
    def test_world_domain_imports_only_foundation_and_stdlib(self):
        domain_files = list((CORE_ROOT / "domain").rglob("*.py"))
        forbidden = {
            "core.application",
            "core.simulation",
            "core.persistence",
            "core.events",
            "core.event_bus",
            "core.event_manager",
            "core.clock",
            "time_system",
            "scheduler",
            "pygame",
            "character",
            "combat",
            "economy",
            "inventory",
            "npc",
            "quests",
            "resources",
            "world",
        }
        violations = []
        for path in domain_files:
            modules = imported_modules(path)
            matches = sorted(
                module for module in modules
                if module in forbidden or any(module.startswith(item + ".") for item in forbidden)
            )
            if matches:
                violations.append((str(path), matches))
        self.assertEqual([], violations)

    def test_canonical_world_contract_does_not_import_runtime_modules(self):
        modules = imported_modules(CORE_ROOT / "domain" / "world_contract.py")
        forbidden = {
            "core.application", "core.simulation", "core.persistence",
            "core.clock", "core.events", "core.event_bus", "time_system",
        }
        self.assertEqual(
            [],
            sorted(module for module in modules if module in forbidden or any(module.startswith(item + ".") for item in forbidden)),
        )

    def test_root_world_gameplay_package_does_not_depend_on_core_domain(self):
        root_world = ROOT / "world"
        violations = []
        for path in root_world.rglob("*.py"):
            modules = imported_modules(path)
            matches = sorted(module for module in modules if module == "core.domain" or module.startswith("core.domain."))
            if matches:
                violations.append((str(path), matches))
        self.assertEqual([], violations)

    def test_public_world_api_exports_remain_available(self):
        from core.application import GameSession, WorldRuntimeBoundary
        from core.domain import WorldDomainState
        from core.foundation import WorldId
        from core.world import World, WorldManager

        for public_type in (WorldDomainState, WorldId, World, WorldManager, GameSession, WorldRuntimeBoundary):
            self.assertIsNotNone(public_type)

    def test_world_manager_does_not_import_runtime_ownership_or_persistence_layers(self):
        modules = imported_modules(CORE_ROOT / "world" / "world_manager.py")
        forbidden = {
            "core.application",
            "core.persistence",
            "core.simulation",
            "core.event_bus",
            "core.events",
            "time_system",
        }
        self.assertEqual(
            [],
            sorted(module for module in modules if module in forbidden or any(module.startswith(item + ".") for item in forbidden)),
        )

    def test_world_domain_state_does_not_know_registry_or_active_world(self):
        source = (CORE_ROOT / "domain" / "world_contract.py").read_text(encoding="utf-8-sig")
        for forbidden_name in ("WorldManager", "GameSession", "active_world", "EntityRepository", "WorldMembershipService"):
            self.assertNotIn(forbidden_name, source)

    def test_canonical_persistence_does_not_read_legacy_world_projection(self):
        source = (CORE_ROOT / "persistence" / "state.py").read_text(encoding="utf-8-sig")
        self.assertNotIn("_entities", source)
        self.assertNotIn("entity.world_id", source)

    def test_entity_repository_does_not_depend_on_world_ownership(self):
        modules = imported_modules(CORE_ROOT / "application" / "entity_repository.py")
        forbidden = {"core.world", "core.application.ownership", "core.world.world_manager"}
        self.assertEqual([], sorted(module for module in modules if module in forbidden))

    def test_world_manager_does_not_validate_membership_from_projection(self):
        source = (CORE_ROOT / "world" / "world_manager.py").read_text(encoding="utf-8-sig")
        self.assertNotIn("entity_count()", source)
        self.assertNotIn("has_entity(", source)


if __name__ == "__main__":
    unittest.main()
