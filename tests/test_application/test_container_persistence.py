import unittest
import tempfile
from pathlib import Path

from application import (
    ContainerSnapshot, GameApplication, GameSaveDocument, GameplayService, SaveJsonCodec,
    WorldObjectPlacement, WorldObjectPlacementRegistry,
)
from character import ItemDefinition
from containers import (
    BreakProfile, BreakProfileRegistry, ContainerDefinition,
    ContainerInstance, ContainerManager,
)
from resources import (
    GameplaySnapshot, Inventory, ProductionJobManager, Quantity,
    ResourceDefinition, ResourceType, ResourceUnit, WorldResourceNodeManager,
)
from core.application import GameSession
from core.persistence import CanonicalSessionState, PersistenceDocument
from world.local_map import LocalMapDefinition
from core.entity.entity import Entity
from core.entity import EntityType
from application.content_pack import build_starter_world_map


class TestContainerPersistence(unittest.TestCase):
    def _runtime(self):
        items = {
            "iron_sword": ItemDefinition(
                "iron_sword", "Iron sword", weight=2.0, volume_liters=1.5,
                category="weapon", tags=("metal",),
            )
        }
        resources = {
            "wood": ResourceDefinition(
                "wood", "Wood", ResourceUnit.ITEM,
                weight_kg_per_unit=0.5, volume_liters_per_unit=1.0,
                category="material", tags=("wood",),
            )
        }
        profiles = BreakProfileRegistry((BreakProfile(
            "wooden_chest", 100.0, {"fire": 0.25}, True,
        ),))
        manager = ContainerManager(items, resources, profiles)
        manager.register_definition(ContainerDefinition(
            "small_chest", "Small chest",
            empty_weight_kg=1.0, outer_volume_liters=8.0,
            max_contents_weight_kg=20.0, max_slots=5,
            max_contents_volume_liters=15.0,
            break_profile_id="wooden_chest",
        ))
        inventory = Inventory()
        inventory.add_item("iron_sword", 2)
        inventory.add(ResourceType("wood"), Quantity(3, ResourceUnit.ITEM))
        manager.register(ContainerInstance(
            "chest_01", "chest_entity", "small_chest", 75.0, False,
        ), inventory)
        placements = WorldObjectPlacementRegistry()
        placements.register_local_map(LocalMapDefinition("world_main", "village", 20, 20))
        placements.place(WorldObjectPlacement(
            "chest_entity", "world_main", "village", 4, 6,
            width=2, height=1, blocks_movement=True, layer=1,
            tags=("container", "wood"),
        ))
        return manager, placements, items, resources

    def test_snapshot_round_trip_preserves_definition_contents_damage_and_placement(self):
        manager, placements, items, resources = self._runtime()
        snapshot = ContainerSnapshot.from_runtime(manager, placements, items, resources)
        decoded = ContainerSnapshot.from_dict(snapshot.to_dict())
        restored, restored_items, restored_resources, restored_placements = decoded.restore()

        instance = restored.get("chest_01")
        self.assertEqual(instance.entity_id, "chest_entity")
        self.assertEqual(instance.definition_id, "small_chest")
        self.assertEqual(instance.durability, 75.0)
        self.assertFalse(instance.broken)
        self.assertEqual(restored.inventory("chest_01").item_quantity("iron_sword"), 2)
        self.assertEqual(
            restored.inventory("chest_01").get(ResourceType("wood")),
            Quantity(3, ResourceUnit.ITEM),
        )
        self.assertEqual(restored_items["iron_sword"], items["iron_sword"])
        self.assertEqual(restored_resources["wood"], resources["wood"])
        self.assertEqual(restored.definition("small_chest").max_slots, 5)
        self.assertEqual(restored.max_global_nesting_depth, 8)
        self.assertEqual(restored.break_profiles.get("wooden_chest").damage_resistances["fire"], 0.25)
        self.assertEqual(len(restored_placements), 1)
        self.assertEqual(restored_placements[0].occupied_tiles, ((4, 6), (5, 6)))

    def test_snapshot_preserves_nested_and_inventory_custody_relationships(self):
        manager, placements, items, resources = self._runtime()
        placements.remove("chest_entity")
        manager.register_definition(ContainerDefinition(
            "small_bag", "Small bag", max_contents_weight_kg=5,
            max_slots=3, max_contents_volume_liters=5,
        ))
        manager.register(ContainerInstance("bag_01", "bag_entity", "small_bag"))
        manager.contain("chest_01", "bag_01")
        manager.set_inventory_custody("chest_01", "main")

        snapshot = ContainerSnapshot.from_runtime(manager, placements, items, resources)
        restored, _, _, restored_placements = ContainerSnapshot.from_dict(snapshot.to_dict()).restore()

        self.assertEqual(restored.parent_of("bag_01").container_id, "chest_01")
        self.assertEqual(restored.inventory_custody("chest_01"), "main")
        self.assertIsNone(restored.inventory_custody("bag_01"))
        self.assertEqual(restored_placements, ())

    def test_outer_save_document_round_trips_container_section(self):
        manager, placements, items, resources = self._runtime()
        container_snapshot = ContainerSnapshot.from_runtime(manager, placements, items, resources)
        session = GameSession()
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(session))
        gameplay = GameplaySnapshot.from_runtime(
            {}, WorldResourceNodeManager(), ProductionJobManager(session.simulation),
        )
        document = GameSaveDocument(core=core, gameplay=gameplay, containers=container_snapshot)

        encoded = SaveJsonCodec.encode(document)
        decoded = SaveJsonCodec.decode(encoded)

        self.assertEqual(decoded.schema_version, 2)
        self.assertEqual(decoded.containers.to_dict(), container_snapshot.to_dict())
        self.assertEqual(SaveJsonCodec.encode(decoded), encoded)

    def test_game_application_save_load_restores_world_container_placement(self):
        application = GameApplication.create_default()
        world = application.dunya_olustur("Main", world_id="world_main")
        service = GameplayService(application)
        world_map = build_starter_world_map(world.world_id)
        service.register_world_map(world_map)
        location_id = world_map.locations()[0].location_id
        entity = Entity(EntityType.ESYA, "Chest", entity_id="chest_entity")
        application.varlik_ekle(entity)
        service.register_container_definition(ContainerDefinition(
            "basic_chest", "Basic chest", max_contents_weight_kg=10,
            max_slots=5, max_contents_volume_liters=10,
        ))
        service.register_container(ContainerInstance(
            "chest_01", entity.entity_id, "basic_chest",
        ))
        service.place_container("chest_01", location_id, 2, 3)

        restored_application = GameApplication.create_default()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            application.save(path)
            restored_bundle = restored_application.load(path)

        restored_instance = restored_bundle.containers.get("chest_01")
        self.assertIsNotNone(restored_instance)
        self.assertEqual(restored_instance.entity_id, "chest_entity")
        placement = restored_bundle.world_objects.get("chest_entity")
        self.assertIsNotNone(placement)
        self.assertEqual((placement.location_id, placement.x, placement.y), (location_id, 2, 3))

    def test_snapshot_rejects_duplicate_or_unknown_relationships(self):
        manager, placements, items, resources = self._runtime()
        data = ContainerSnapshot.from_runtime(manager, placements, items, resources).to_dict()
        data["custodies"] = [{"container_id": "missing", "inventory_id": "main"}]
        with self.assertRaises(ValueError):
            ContainerSnapshot.from_dict(data)


if __name__ == "__main__":
    unittest.main()
