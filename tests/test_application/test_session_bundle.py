import unittest
from application import SessionBundle, SessionHolder
from application.hex_map_definition import HexCell, HexMapDefinition
from application.hex_world_runtime import HexWorldRuntime, HexWorldRuntimeOwner
from core.application import GameSession
from core.simulation import SimulationRuntime
from core.domain.spatial import LocalHexPosition
from locks import KeyDefinition, LockDefinition, LockManager
from resources import (
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNodeManager,
)


def make_hex_runtime():
    cell = LocalHexPosition(0, 0)
    definition = HexMapDefinition(
        schema_version=2,
        map_id="session_test_map",
        name="Session test map",
        description="",
        default_terrain="grass",
        valid_cells=frozenset({cell}),
        cells={cell: HexCell(cell, "grass")},
        terrain_ids=frozenset({"grass"}),
    )
    return HexWorldRuntime({definition.map_id: definition})


def make_bundle(hex_world_runtime=None):
    session = GameSession()
    return SessionBundle(
        session=session,
        simulation=session.simulation,
        production_jobs=ProductionJobManager(session.simulation),
        resource_nodes=WorldResourceNodeManager(session.worlds),
        inventories={},
        recipes={},
        hex_world_runtime_owner=HexWorldRuntimeOwner(hex_world_runtime),
    )


class TestSessionBundle(unittest.TestCase):
    def test_default_bundle_has_no_hex_runtime_until_content_is_loaded(self):
        bundle = SessionBundle.create_default()
        self.assertIsNone(bundle.hex_world_runtime)

    def test_hex_runtime_is_owned_by_session_bundle(self):
        runtime = make_hex_runtime()
        bundle = make_bundle(runtime)
        self.assertIs(bundle.hex_world_runtime, runtime)

    def test_runtime_owner_reuses_the_same_runtime_for_reopened_views(self):
        owner = HexWorldRuntimeOwner()
        runtime = owner.get_or_create(make_hex_runtime)

        self.assertIs(owner.get_or_create(lambda: self.fail("runtime recreated")), runtime)
        self.assertIs(owner.runtime, runtime)

    def test_invalid_hex_runtime_type_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "hex_world_runtime"):
            make_bundle(object())

    def test_candidate_cannot_share_hex_runtime_with_current_bundle(self):
        runtime = make_hex_runtime()
        current = make_bundle(runtime)
        candidate = make_bundle(runtime)
        holder = SessionHolder(current)

        with self.assertRaisesRegex(ValueError, "mutable runtime state"):
            holder.publish(candidate)

        self.assertIs(holder.current, current)

    def test_default_bundle_owns_one_shared_runtime(self):
        bundle = SessionBundle.create_default()

        self.assertIs(bundle.simulation, bundle.session.simulation)
        self.assertIs(bundle.production_jobs.runtime, bundle.simulation)
        self.assertEqual(bundle.simulation.dispatcher.consumer_count(), 1)
        self.assertEqual(bundle.inventories, {})
        self.assertIsInstance(bundle.resource_nodes, WorldResourceNodeManager)
        from containers import ContainerManager
        self.assertIsInstance(bundle.containers, ContainerManager)

    def test_production_job_runs_on_bundle_runtime(self):
        bundle = SessionBundle.create_default()
        wood = ResourceType("wood")
        tool = ResourceType("tool")
        inventory = Inventory()
        inventory.add(wood, Quantity(3, ResourceUnit.ITEM))
        recipe = Recipe(
            "tool_recipe",
            ((wood, Quantity(3, ResourceUnit.ITEM)),),
            ((tool, Quantity(1, ResourceUnit.ITEM)),),
        )

        job = bundle.production_jobs.start(recipe, inventory, 2, job_id="job_a")
        bundle.production_jobs.advance_to(2)

        self.assertIs(job.inventory, inventory)
        self.assertEqual(job.state.value, "completed")
        self.assertEqual(inventory.get(tool), Quantity(1, ResourceUnit.ITEM))
        self.assertIs(bundle.production_jobs.runtime, bundle.session.simulation)

    def test_independent_bundles_do_not_share_mutable_runtime_state(self):
        first = SessionBundle.create_default()
        second = SessionBundle.create_default()

        self.assertIsNot(first.session, second.session)
        self.assertIsNot(first.simulation, second.simulation)
        self.assertIsNot(first.production_jobs, second.production_jobs)
        self.assertIsNot(first.resource_nodes, second.resource_nodes)
        self.assertIsNot(first.production_jobs.runtime.dispatcher, second.production_jobs.runtime.dispatcher)

    def test_invalid_bundle_invariants_are_rejected(self):
        session = GameSession()
        with self.assertRaises(ValueError):
            SessionBundle(
                session=session,
                simulation=SimulationRuntime(),
                production_jobs=ProductionJobManager(session.simulation),
                resource_nodes=WorldResourceNodeManager(),
                inventories={},
                recipes={},
            )

    def test_owner_bound_key_must_reference_registered_actor(self):
        session = GameSession()
        locks = LockManager()
        locks.register_lock_definition(
            LockDefinition("owner_lock", "Owner lock", "owner_key")
        )
        locks.register_key_definition(
            KeyDefinition("owner_key", "Owner key", "owner_lock", True)
        )
        locks.bind_key_owner("owner_key", "missing_actor")

        with self.assertRaisesRegex(ValueError, "unknown actor"):
            SessionBundle(
                session=session,
                simulation=session.simulation,
                production_jobs=ProductionJobManager(session.simulation),
                resource_nodes=WorldResourceNodeManager(session.worlds),
                inventories={},
                recipes={},
                locks=locks,
            )

    def test_candidate_creation_failure_does_not_change_holder(self):
        holder = SessionHolder()
        old = holder.current

        with self.assertRaises(TypeError):
            SessionBundle(
                session=GameSession(),
                simulation=SimulationRuntime(),
                production_jobs=ProductionJobManager(object()),
                resource_nodes=WorldResourceNodeManager(),
                inventories={},
                recipes={},
            )

        self.assertIs(holder.current, old)

    def test_invalid_candidate_is_not_published(self):
        holder = SessionHolder()
        old = holder.current
        invalid = object()

        with self.assertRaises(TypeError):
            holder.publish(invalid)

        self.assertIs(holder.current, old)

    def test_successful_publish_replaces_only_holder_reference(self):
        holder = SessionHolder()
        old = holder.current
        candidate = SessionBundle.create_default()

        result = holder.publish(candidate)

        self.assertIs(result, candidate)
        self.assertIs(holder.current, candidate)
        self.assertIsNot(holder.current, old)
        self.assertIsNot(old.session, candidate.session)
        self.assertIs(old.production_jobs.runtime, old.simulation)

    def test_shared_inventory_cannot_be_published_as_candidate(self):
        inventory = Inventory()
        old_session = GameSession()
        old = SessionBundle(
            session=old_session,
            simulation=old_session.simulation,
            production_jobs=ProductionJobManager(old_session.simulation),
            resource_nodes=WorldResourceNodeManager(),
            inventories={"main": inventory},
            recipes={},
        )
        candidate_session = GameSession()
        candidate = SessionBundle(
            session=candidate_session,
            simulation=candidate_session.simulation,
            production_jobs=ProductionJobManager(candidate_session.simulation),
            resource_nodes=WorldResourceNodeManager(),
            inventories={"candidate": inventory},
            recipes={},
        )
        holder = SessionHolder(old)

        with self.assertRaises(ValueError):
            holder.publish(candidate)

        self.assertIs(holder.current, old)

    def test_job_inventory_must_be_registered_in_bundle(self):
        wood = ResourceType("wood")
        tool = ResourceType("tool")
        inventory = Inventory()
        inventory.add(wood, Quantity(3, ResourceUnit.ITEM))
        recipe = Recipe(
            "tool_recipe",
            ((wood, Quantity(3, ResourceUnit.ITEM)),),
            ((tool, Quantity(1, ResourceUnit.ITEM)),),
        )
        session = GameSession()
        jobs = ProductionJobManager(session.simulation)
        jobs.start(recipe, inventory, 2, job_id="job_a")

        with self.assertRaises(ValueError):
            SessionBundle(
                session=session,
                simulation=session.simulation,
                production_jobs=jobs,
                resource_nodes=WorldResourceNodeManager(),
                inventories={},
                recipes={recipe.recipe_id: recipe},
            )


if __name__ == "__main__":
    unittest.main()
