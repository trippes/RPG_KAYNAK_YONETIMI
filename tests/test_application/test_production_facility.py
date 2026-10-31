import tempfile
import unittest
from pathlib import Path

from application import (
    GameApplication,
    ProductionFacility,
    ProductionFacilityError,
    ProductionFacilityRegistry,
    ProductionChain,
    ProductionChainStage,
    ProductionChainState,
    SessionBundle,
    SessionHolder,
)
from core.application import GameSession
from core.simulation import SimulationRuntime
from resources import (
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNodeManager,
)


class TestProductionFacility(unittest.TestCase):
    def setUp(self):
        self.ore = ResourceType("ore")
        self.ingot = ResourceType("ingot")
        self.recipe = Recipe(
            "smelt",
            ((self.ore, Quantity(1, ResourceUnit.ITEM)),),
            ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
            processing_time=3,
            facility_type="smelter",
            required_capabilities=("heat",),
        )

    def _context(self):
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        inventory = Inventory()
        inventory.add(self.ore, Quantity(2, ResourceUnit.ITEM))
        facility = ProductionFacility("smelter-1", "smelter", 1, ("heat",))
        return runtime, jobs, inventory, facility

    def test_facility_enforces_recipe_and_processing_time(self):
        _, jobs, inventory, facility = self._context()
        job = facility.start(jobs, self.recipe, inventory, job_id="smelt-1")
        self.assertEqual(job.duration.value, 3)
        self.assertEqual(facility.capacity.reserved, 1)
        jobs.advance_to(2)
        self.assertIsNone(inventory.get(self.ingot))
        jobs.advance_to(3)
        self.assertEqual(inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(facility.capacity.reserved, 0)
        self.assertEqual(facility.active_job_ids, ())

    def test_inactive_or_incompatible_facility_rejects_without_mutation(self):
        _, jobs, inventory, facility = self._context()
        before = inventory.snapshot()
        facility.set_active(False)
        with self.assertRaises(ProductionFacilityError):
            facility.start(jobs, self.recipe, inventory, job_id="inactive")
        self.assertEqual(inventory.snapshot(), before)
        self.assertEqual(facility.capacity.reserved, 0)

        facility.set_active(True)
        incompatible = ProductionFacility("forge-1", "forge", 1, ("heat",))
        with self.assertRaises(ProductionFacilityError):
            incompatible.start(jobs, self.recipe, inventory, job_id="wrong")
        self.assertEqual(inventory.snapshot(), before)

    def test_labor_energy_and_fuel_are_normal_atomic_recipe_inputs(self):
        _, jobs, inventory, facility = self._context()
        labor = ResourceType("labor")
        energy = ResourceType("energy")
        fuel = ResourceType("fuel")
        recipe = Recipe(
            "costed-smelt",
            (
                (self.ore, Quantity(1, ResourceUnit.ITEM)),
                (labor, Quantity(1, ResourceUnit.ITEM)),
                (energy, Quantity(2, ResourceUnit.ITEM)),
                (fuel, Quantity(1, ResourceUnit.ITEM)),
            ),
            ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
            processing_time=1,
            facility_type="smelter",
            required_capabilities=("heat",),
        )
        inventory.add(labor, Quantity(1, ResourceUnit.ITEM))
        inventory.add(energy, Quantity(2, ResourceUnit.ITEM))
        inventory.add(fuel, Quantity(1, ResourceUnit.ITEM))
        facility.start(jobs, recipe, inventory, job_id="costed")
        self.assertIsNone(inventory.get(labor))
        self.assertIsNone(inventory.get(energy))
        self.assertIsNone(inventory.get(fuel))
        jobs.advance_to(1)
        self.assertEqual(inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(facility.capacity.reserved, 0)

    def test_facilities_have_independent_capacity_pools(self):
        _, jobs, inventory, first = self._context()
        second = ProductionFacility("smelter-2", "smelter", 1, ("heat",))
        first.start(jobs, self.recipe, inventory, job_id="first")
        second.start(jobs, self.recipe, inventory, job_id="second")
        self.assertEqual(first.capacity.reserved, 1)
        self.assertEqual(second.capacity.reserved, 1)
        self.assertEqual(inventory.get(self.ore), None)

    def test_facility_bound_chain_uses_explicit_facilities(self):
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        inventory = Inventory()
        inventory.add(self.ore, Quantity(1, ResourceUnit.ITEM))
        registry = ProductionFacilityRegistry()
        registry.add(ProductionFacility("smelter", "smelter", 1, ("heat",)))
        chain = ProductionChain(
            jobs,
            (ProductionChainStage(self.recipe, inventory, None, facility_id="smelter"),),
            "facility-chain",
            facilities=registry,
        )
        chain.start()
        chain.advance_to(3)
        self.assertEqual(chain.state, ProductionChainState.COMPLETED)
        self.assertEqual(inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))

    def test_facility_and_active_job_round_trip_through_application_save(self):
        session = GameSession()
        session.worlds.create("Main", world_id="main")
        inventory = Inventory()
        inventory.add(self.ore, Quantity(1, ResourceUnit.ITEM))
        jobs = ProductionJobManager(session.simulation)
        facilities = ProductionFacilityRegistry()
        facility = ProductionFacility("smelter", "smelter", 1, ("heat",))
        facilities.add(facility)
        facility.start(jobs, self.recipe, inventory, job_id="job-1")
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=jobs,
            resource_nodes=WorldResourceNodeManager(),
            inventories={"main": inventory},
            recipes={self.recipe.recipe_id: self.recipe},
            facilities=facilities,
        )
        application = GameApplication(SessionHolder(bundle))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            application.save(path)
            application.load(path)
        restored = application.holder.current
        restored_facility = restored.facilities.get("smelter")
        self.assertIsNotNone(restored_facility)
        self.assertEqual(restored_facility.capacity.reserved, 1)
        restored.production_jobs.advance_to(3)
        self.assertEqual(restored.facilities.get("smelter").capacity.reserved, 0)
        self.assertEqual(restored.inventories["main"].get(self.ingot), Quantity(1, ResourceUnit.ITEM))


if __name__ == "__main__":
    unittest.main()
