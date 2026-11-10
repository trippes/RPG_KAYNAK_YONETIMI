import tempfile
import unittest
from pathlib import Path

from core.entity import Entity, EntityType
from character import ItemDefinition
from containers import ContainerDefinition, ContainerInstance
from resources import ResourceDefinition
from world import Location, WorldMap

from application import (
    GameApplication,
    GameplayChainStage,
    GameplayService,
    GameplayServiceError,
    ProductionFacility,
    ProductionFacilityRegistry,
    SessionBundle,
    SessionHolder,
)
from core.application import GameSession
from resources import (
    Inventory,
    ProductionJobManager,
    ProductionJobState,
    Quantity,
    Recipe,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestGameplayService(unittest.TestCase):
    def setUp(self):
        session = GameSession()
        world = session.worlds.create("Playable", world_id="world_playable")
        session.worlds.set_active(world.world_id)

        self.ore = ResourceType("ore")
        self.ingot = ResourceType("ingot")
        self.tool = ResourceType("tool")
        inventory = Inventory()
        nodes = WorldResourceNodeManager(session.worlds)
        nodes.add(WorldResourceNode(
            "ore-node", world.world_id, self.ore,
            Quantity(6, ResourceUnit.ITEM),
            Quantity(10, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        self.recipes = {
            "smelt": Recipe(
                "smelt",
                ((self.ore, Quantity(2, ResourceUnit.ITEM)),),
                ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
                processing_time=2,
                facility_type="smelter",
            ),
            "tool": Recipe(
                "tool",
                ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
                ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
                processing_time=3,
                facility_type="workshop",
            ),
        }
        facilities = ProductionFacilityRegistry()
        facilities.add(ProductionFacility("smelter-1", "smelter", 1))
        facilities.add(ProductionFacility("workshop-1", "workshop", 1))
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=ProductionJobManager(session.simulation),
            resource_nodes=nodes,
            inventories={"main": inventory},
            recipes=self.recipes,
            facilities=facilities,
            items={"bread": ItemDefinition("bread", "Bread", weight=0.5, volume_liters=0.25, tags=("food",))},
            resource_definitions={"wood": ResourceDefinition("wood", "Wood", ResourceUnit.ITEM, 0.5, 0.25, "raw", ("wood",))},
        )
        self.application = GameApplication(SessionHolder(bundle))
        self.service = GameplayService(self.application)
        self.inventory = inventory

    def test_world_object_placement_uses_registered_core_entity_and_map(self):
        world = self.application.aktif_dunya()
        world_map = WorldMap(world.world_id)
        world_map.add_location(Location("village", "Village"))
        world_map.add_location(Location("forest", "Forest"))
        self.service.register_world_map(world_map)
        entity = Entity(EntityType.ESYA, "Sandık", entity_id="chest_01")
        self.application.varlik_ekle(entity)
        placement = self.service.place_world_object("chest_01", "village", 3, 4, width=2, height=1, tags=("container",))
        self.assertEqual(placement.object_id, entity.entity_id)
        self.assertEqual(self.service.blocked_world_object_tiles(world.world_id, "village"), frozenset({(3, 4), (4, 4)}))
        moved = self.service.transfer_world_object("chest_01", "forest", 1, 1)
        self.assertEqual(moved.location_id, "forest")
        self.assertEqual(self.service.world_objects_for_location(world.world_id, "forest"), (moved,))


    def test_container_registration_and_item_transfer_are_application_owned(self):
        self.service.register_container_definition(ContainerDefinition(
            "chest", "Chest", max_contents_weight_kg=2, max_slots=2,
            max_contents_volume_liters=2,
        ))
        entity = Entity(EntityType.ESYA, "Chest", entity_id="entity_chest")
        self.application.varlik_ekle(entity)
        instance = self.service.register_container(
            ContainerInstance("chest_01", entity.entity_id, "chest")
        )
        self.inventory.add_item("bread", 3)

        self.service.transfer_item_to_container("main", "chest_01", "bread", 2)
        view = self.service.container_state("chest_01")

        self.assertEqual(instance.entity_id, "entity_chest")
        self.assertEqual(self.inventory.item_quantity("bread"), 1)
        self.assertEqual(view.items, (("bread", 2),))
        self.assertEqual(view.contents_slots, 1)
        self.service.transfer_item_from_container("chest_01", "main", "bread", 1)
        self.assertEqual(self.inventory.item_quantity("bread"), 2)
        self.assertEqual(self.service.container_state("chest_01").items, (("bread", 1),))

    def test_container_transfer_rolls_back_source_when_capacity_rejects(self):
        self.service.register_container_definition(ContainerDefinition(
            "tiny_chest", "Tiny chest", max_contents_weight_kg=0.5,
            max_slots=1, max_contents_volume_liters=0.25,
        ))
        entity = Entity(EntityType.ESYA, "Tiny chest", entity_id="entity_tiny_chest")
        self.application.varlik_ekle(entity)
        self.service.register_container(ContainerInstance(
            "tiny_chest_01", entity.entity_id, "tiny_chest"
        ))
        self.inventory.add_item("bread", 2)

        with self.assertRaises(ValueError):
            self.service.transfer_item_to_container("main", "tiny_chest_01", "bread", 2)

        self.assertEqual(self.inventory.item_quantity("bread"), 2)
        self.assertEqual(self.service.container_state("tiny_chest_01").items, ())

    def test_container_resource_transfer_uses_resource_physical_catalog(self):
        self.service.register_container_definition(ContainerDefinition(
            "resource_crate", "Resource crate", max_contents_weight_kg=5,
            max_slots=2, max_contents_volume_liters=5,
        ))
        entity = Entity(EntityType.ESYA, "Resource crate", entity_id="entity_resource_crate")
        self.application.varlik_ekle(entity)
        self.service.register_container(ContainerInstance(
            "resource_crate_01", entity.entity_id, "resource_crate"
        ))
        wood = ResourceType("wood")
        self.inventory.add(wood, Quantity(3, ResourceUnit.ITEM))

        self.service.transfer_resource_to_container(
            "main", "resource_crate_01", wood, Quantity(2, ResourceUnit.ITEM)
        )
        view = self.service.container_state("resource_crate_01")
        self.assertEqual(self.inventory.get(wood), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(view.stocks, (("wood", 2, "item"),))

        self.service.transfer_resource_from_container(
            "resource_crate_01", "main", wood, Quantity(1, ResourceUnit.ITEM)
        )
        self.assertEqual(self.inventory.get(wood), Quantity(2, ResourceUnit.ITEM))

    def test_container_can_be_placed_and_nested_without_duplicate_world_placement(self):
        self.service.register_container_definition(ContainerDefinition(
            "chest", "Chest", max_contents_weight_kg=10, max_slots=10,
            max_contents_volume_liters=10, max_nesting_depth=2,
        ))
        self.service.register_container_definition(ContainerDefinition(
            "bag", "Bag", max_contents_weight_kg=5, max_slots=5,
            max_contents_volume_liters=5, max_nesting_depth=1,
        ))
        world = self.application.aktif_dunya()
        world_map = WorldMap(world.world_id)
        world_map.add_location(Location("village", "Village"))
        self.service.register_world_map(world_map)
        parent_entity = Entity(EntityType.ESYA, "Chest", entity_id="nested_parent_entity")
        child_entity = Entity(EntityType.ESYA, "Bag", entity_id="nested_child_entity")
        self.application.varlik_ekle(parent_entity)
        self.application.varlik_ekle(child_entity)
        self.service.register_container(ContainerInstance("parent", parent_entity.entity_id, "chest"))
        self.service.register_container(ContainerInstance("child", child_entity.entity_id, "bag"))
        self.service.place_container("child", "village", 2, 2)

        self.service.contain_container("parent", "child")

        self.assertIsNotNone(self.application.holder.current.containers.parent_of("child"))
        self.assertEqual(self.service.world_objects_for_location(world.world_id, "village"), ())

    def test_collects_from_active_world_atomically(self):
        self.service.collect("ore-node", "main", Quantity(4, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.get(self.ore), Quantity(4, ResourceUnit.ITEM))
        self.assertEqual(
            self.application.holder.current.resource_nodes.get("ore-node").quantity,
            Quantity(2, ResourceUnit.ITEM),
        )

    def test_invalid_node_inventory_and_wrong_world_are_rejected(self):
        with self.assertRaises(KeyError):
            self.service.collect("missing", "main", Quantity(1, ResourceUnit.ITEM))
        with self.assertRaises(KeyError):
            self.service.collect("ore-node", "missing", Quantity(1, ResourceUnit.ITEM))

        other = self.application.dunya_olustur("Other", world_id="world_other", aktif_yap=False)
        self.application.holder.current.resource_nodes.add(WorldResourceNode(
            "other-node", other.world_id, self.ore,
            Quantity(1, ResourceUnit.ITEM), Quantity(1, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        with self.assertRaises(GameplayServiceError):
            self.service.collect("other-node", "main", Quantity(1, ResourceUnit.ITEM))

    def test_insufficient_collection_preserves_node_and_inventory(self):
        before = self.service.state()
        with self.assertRaises(ResourceNodeInsufficientError):
            self.service.collect("ore-node", "main", Quantity(7, ResourceUnit.ITEM))
        after = self.service.state()
        self.assertEqual(before.inventories, after.inventories)
        self.assertEqual(before.nodes, after.nodes)

    def test_single_production_uses_tick_runtime_and_is_idempotent(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        job = self.service.start_production("smelt", "main", "smelter-1")
        self.service.advance_to(1)
        self.assertEqual(job.state, ProductionJobState.RUNNING)
        self.assertIsNone(self.inventory.get(self.ingot))
        self.service.advance_to(2)
        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(self.inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))
        self.service.advance_to(2)
        self.assertEqual(self.inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))

    def test_wrong_facility_and_capacity_are_rejected_without_consumption(self):
        self.service.collect("ore-node", "main", Quantity(4, ResourceUnit.ITEM))
        before = self.inventory.snapshot()
        with self.assertRaises(ValueError):
            self.service.start_production("smelt", "main", "workshop-1")
        self.assertEqual(self.inventory.snapshot(), before)

        self.service.start_production("smelt", "main", "smelter-1")
        with self.assertRaises(ValueError):
            self.service.start_production("smelt", "main", "smelter-1")
        self.assertEqual(self.application.holder.current.facilities.get("smelter-1").capacity.reserved, 1)

    def test_two_stage_chain_uses_intermediate_output(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        chain = self.service.start_chain("ore-to-tool", (
            GameplayChainStage("smelt", "main", "smelter-1"),
            GameplayChainStage("tool", "main", "workshop-1"),
        ))
        self.service.advance_to(1)
        self.assertEqual(chain.current_stage_index, 0)
        self.assertIsNone(self.inventory.get(self.ingot))
        self.service.advance_to(2)
        self.assertEqual(chain.current_stage_index, 1)
        # The second stage consumes the intermediate product at its start.
        self.assertIsNone(self.inventory.get(self.ingot))
        self.assertIsNone(self.inventory.get(self.tool))
        self.service.advance_to(5)
        self.assertEqual(chain.state.value, "completed")
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        self.service.advance_to(5)
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_state_is_read_only_and_save_load_preserves_active_job(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_production("smelt", "main", "smelter-1")
        snapshot = self.service.state()
        self.assertEqual(snapshot.simulation_tick, 0)
        self.assertEqual(snapshot.inventories[0].stocks, ())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "playable-save.json"
            self.service.save(path)
            self.service.load(path)
            restored = self.service.state()
            self.assertEqual(restored.simulation_tick, 0)
            self.assertEqual(restored.facilities[0].active_job_ids, ("facility:smelter-1:job:000001",))
            self.service.advance_to(2)
            self.service.advance_to(2)
            self.assertEqual(self.service.inventory("main").stocks, (("ingot", 1, "item"),))

    def test_load_switch_discards_runtime_only_chain_registry(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_chain("chain", (("smelt", "main", "smelter-1"),))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chain-save.json"
            self.service.save(path)
            self.service.load(path)
            self.assertEqual(self.service.state().chains, ())


if __name__ == "__main__":
    unittest.main()
