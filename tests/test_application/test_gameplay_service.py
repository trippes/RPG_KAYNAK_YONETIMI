from dataclasses import FrozenInstanceError
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.entity import Entity, EntityType
from character import Attributes, Character, CharacterClass, ItemDefinition, Race, Skills
from containers import ContainerDefinition, ContainerInstance
from locks import ForceProfile, KeyDefinition, LockDefinition, LockInstance, LockpickProfile
from resources import ResourceDefinition
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward

from application import (
    Combatant,
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
            inventories={
                "main": inventory,
                "other": Inventory(),
                "traveler_bag": Inventory(),
            },
            recipes=self.recipes,
            facilities=facilities,
            items={
                "bread": ItemDefinition("bread", "Bread", weight=0.5, volume_liters=0.25, tags=("food",)),
                "lockpick": ItemDefinition("lockpick", "Lockpick", tags=("lockpick",)),
                "breaching_tool": ItemDefinition("breaching_tool", "Breaching tool", tags=("breaching_tool",)),
            },
            characters={
                "hero_character": Character(
                    "hero_character", "Hero", Race("human", "Human"),
                    CharacterClass("rogue", "Rogue"),
                    attributes=Attributes({"strength": 10, "dexterity": 1}),
                    skills=Skills(),
                ),
                "character_001": Character(
                    "character_001", "Traveler", Race("human", "Human"),
                    CharacterClass("rogue", "Rogue"),
                    attributes=Attributes({"strength": 10, "dexterity": 1}),
                    skills=Skills(),
                )
            },
            resource_definitions={"wood": ResourceDefinition("wood", "Wood", ResourceUnit.ITEM, 0.5, 0.25, "raw", ("wood",))},
        )
        self.application = GameApplication(SessionHolder(bundle))
        self.service = GameplayService(self.application)
        self.service.configure_player_context("hero", "main", "hero")
        self.inventory = inventory


    def test_player_context_requires_explicit_configuration(self):
        unconfigured_service = GameplayService(self.application)
        with self.assertRaisesRegex(
            GameplayServiceError, "Player actor ID has not been configured"
        ):
            _ = unconfigured_service.player_actor_id
        with self.assertRaisesRegex(
            GameplayServiceError, "Player inventory ID has not been configured"
        ):
            _ = unconfigured_service.player_inventory_id
        with self.assertRaisesRegex(
            GameplayServiceError, "Player account ID has not been configured"
        ):
            _ = unconfigured_service.player_account_id

    def test_player_context_keeps_actor_inventory_account_and_character_ids_distinct(self):
        self.service.configure_player_context(
            actor_id="traveler_actor",
            inventory_id="traveler_bag",
            account_id="traveler_wallet",
        )
        self.service.register_actor(
            "traveler_actor",
            "player",
            character_id="character_001",
            inventory_id="traveler_bag",
        )

        self.assertEqual(self.service.player_actor_id, "traveler_actor")
        self.assertEqual(self.service.player_inventory_id, "traveler_bag")
        self.assertEqual(self.service.player_account_id, "traveler_wallet")
        self.assertEqual(self.service.player_character_id, "character_001")
        self.assertEqual(
            self.service.actor_character(self.service.player_actor_id).character_id,
            "character_001",
        )
        creation_state = self.service.character_creation_state()
        self.assertEqual(creation_state.character_id, "character_001")
        self.assertEqual(creation_state.race_id, "human")
        self.assertEqual(creation_state.class_id, "rogue")
        with self.assertRaises(FrozenInstanceError):
            creation_state.race_id = "elf"

    def test_missing_account_id_is_not_inferred_from_actor_id(self):
        self.service.configure_player_context(
            actor_id="traveler_actor",
            inventory_id="traveler_bag",
        )

        self.assertEqual(self.service.player_actor_id, "traveler_actor")
        self.assertEqual(self.service.player_inventory_id, "traveler_bag")
        with self.assertRaisesRegex(
            GameplayServiceError, "Player account ID has not been configured"
        ):
            _ = self.service.player_account_id

    def test_empty_account_id_is_rejected_without_replacing_player_context(self):
        self.service.configure_player_context(
            actor_id="avatar_actor",
            inventory_id="main",
            account_id="bank_account",
        )

        with self.assertRaisesRegex(ValueError, "account ID must be a non-empty string"):
            self.service.configure_player_context(
                actor_id="replacement_actor",
                inventory_id="replacement_bag",
                account_id="",
            )

        self.assertEqual(self.service.player_actor_id, "avatar_actor")
        self.assertEqual(self.service.player_inventory_id, "main")
        self.assertEqual(self.service.player_account_id, "bank_account")

    def test_player_character_id_is_none_until_player_actor_is_registered(self):
        self.service.configure_player_context(
            actor_id="not_registered_yet",
            inventory_id="main",
            account_id="bank_account",
        )

        self.service.register_actor(
            "npc_guard",
            "npc",
            character_id="hero_character",
        )

        self.assertIsNone(self.service.player_character_id)


    def test_locked_container_requires_matching_key_before_opening(self):
        self.service.register_container_definition(ContainerDefinition("locked_chest", "Locked chest"))
        entity = Entity(EntityType.ESYA, "Locked chest", entity_id="locked_chest_entity")
        self.application.varlik_ekle(entity)
        self.service.register_container(ContainerInstance("locked_chest_01", entity.entity_id, "locked_chest"))
        self.service.register_lock_definition(
            LockDefinition("locked_chest_lock", "Chest lock", "chest_key")
        )
        self.service.register_key_definition(
            KeyDefinition("chest_key", "Chest key", "locked_chest_lock")
        )
        self.service.register_lock(
            LockInstance("locked_chest_lock_01", entity.entity_id, "locked_chest_lock")
        )
        self.service.register_actor("hero", "player", character_id="hero_character", inventory_id="main")
        self.inventory.add_item("chest_key")

        with self.assertRaises(GameplayServiceError):
            self.service.open_container("hero", "main", "locked_chest_01")

        self.assertFalse(self.service.unlock_with_key(
            "hero", "main", "locked_chest_lock_01", "wrong_key"
        ))
        self.assertTrue(self.service.lock_state("locked_chest_lock_01").locked)
        self.assertTrue(self.service.unlock_with_key(
            "hero", "main", "locked_chest_lock_01", "chest_key"
        ))
        self.assertEqual(
            self.service.open_container("hero", "main", "locked_chest_01").container_id,
            "locked_chest_01",
        )

    @patch("core.dice.zar_at", new=lambda sides: 10)
    def test_lockpick_requires_dexterity_two_and_tool_then_adds_dexterity_modifier(self):
        self.service.register_container_definition(ContainerDefinition("pick_chest", "Pick chest"))
        entity = Entity(EntityType.ESYA, "Pick chest", entity_id="pick_chest_entity")
        self.application.varlik_ekle(entity)
        self.service.register_container(ContainerInstance("pick_chest_01", entity.entity_id, "pick_chest"))
        self.service.register_lockpick_profile(
            LockpickProfile(
                "basic_pick", allowed_tool_tags=("lockpick",),
                require_skill=True, require_tool=True, minimum_skill=2,
                difficulty_class=15,
            )
        )
        self.service.register_lock_definition(
            LockDefinition("pick_chest_lock", "Pickable lock", lockpick_profile_id="basic_pick")
        )
        self.service.register_lock(
            LockInstance("pick_chest_lock_01", entity.entity_id, "pick_chest_lock")
        )
        self.service.register_actor("hero", "player", character_id="hero_character", inventory_id="main")
        self.inventory.add_item("lockpick")

        # Dexterity 1: possessing a lockpick is not enough to attempt the check.
        result = self.service.resolve_lockpick(
            "hero", "main", "pick_chest_lock_01", tool_item_id="lockpick",
        )
        self.assertFalse(result.attempted)
        self.assertIsNone(result.roll)
        self.assertTrue(self.service.lock_state("pick_chest_lock_01").locked)

        # Dexterity 20 grants +5. A d20 result of 10 meets this lock's DC 15.
        self.application.holder.current.characters["hero_character"].attributes = Attributes(
            {"strength": 10, "dexterity": 20}
        )
        self.inventory.remove_item("lockpick")
        result = self.service.resolve_lockpick(
            "hero", "main", "pick_chest_lock_01", tool_item_id="lockpick",
        )
        self.assertFalse(result.attempted)
        self.assertIn("Maymuncuk", result.message)
        self.inventory.add_item("lockpick")
        result = self.service.resolve_lockpick(
            "hero", "main", "pick_chest_lock_01", tool_item_id="lockpick",
        )
        self.assertTrue(result.attempted)
        self.assertEqual(result.roll, 10)
        self.assertEqual(result.modifier, 5)
        self.assertEqual(result.total, 15)
        self.assertTrue(result.success)
        self.assertFalse(self.service.lock_state("pick_chest_lock_01").locked)


    @patch("core.dice.zar_at", new=lambda sides: 20)
    def test_force_open_uses_character_strength_and_carried_tool(self):
        entity = Entity(EntityType.ESYA, "Iron gate", entity_id="iron_gate_entity")
        self.application.varlik_ekle(entity)
        self.service.register_force_profile(
            ForceProfile(
                "heavy_force", minimum_strength=14,
                required_tool_tags=("breaching_tool",), success_effect="break",
            )
        )
        self.service.register_lock_definition(
            LockDefinition("iron_gate_lock", "Iron gate lock", force_profile_id="heavy_force")
        )
        self.service.register_lock(
            LockInstance("iron_gate_lock_01", entity.entity_id, "iron_gate_lock")
        )
        self.service.register_actor("hero", "player", character_id="hero_character", inventory_id="main")
        self.inventory.add_item("breaching_tool")

        self.assertFalse(self.service.attempt_force_lock(
            "hero", "main", "iron_gate_lock_01",
            tool_item_id="breaching_tool",
        ))
        self.application.holder.current.characters["hero_character"].attributes = Attributes({"strength": 14})
        self.inventory.remove_item("breaching_tool")
        self.assertFalse(self.service.attempt_force_lock(
            "hero", "main", "iron_gate_lock_01",
            tool_item_id="breaching_tool",
        ))
        self.inventory.add_item("breaching_tool")
        self.assertTrue(self.service.attempt_force_lock(
            "hero", "main", "iron_gate_lock_01",
            tool_item_id="breaching_tool",
        ))
        state = self.service.lock_state("iron_gate_lock_01")
        self.assertTrue(state.broken)
        self.assertFalse(state.locked)

    @patch("core.dice.zar_at", new=lambda sides: 20)
    def test_force_open_profile_can_unlock_without_breaking(self):
        entity = Entity(EntityType.ESYA, "Wooden door", entity_id="wooden_door_entity")
        self.application.varlik_ekle(entity)
        self.service.register_force_profile(
            ForceProfile("push_door", minimum_strength=10, success_effect="unlock")
        )
        self.service.register_lock_definition(
            LockDefinition("wooden_door_lock", "Wooden door lock", force_profile_id="push_door")
        )
        self.service.register_lock(
            LockInstance("wooden_door_lock_01", entity.entity_id, "wooden_door_lock")
        )
        self.service.register_actor(
            "hero", "player", character_id="hero_character", inventory_id="main"
        )
        self.assertTrue(self.service.attempt_force_lock(
            "hero", "main", "wooden_door_lock_01",
        ))
        state = self.service.lock_state("wooden_door_lock_01")
        self.assertFalse(state.locked)
        self.assertFalse(state.broken)

    def test_lock_and_key_state_survives_game_application_save_load(self):
        self.service.register_container_definition(ContainerDefinition("saved_chest", "Saved chest"))
        entity = Entity(EntityType.ESYA, "Saved chest", entity_id="saved_chest_entity")
        self.application.varlik_ekle(entity)
        self.service.register_container(ContainerInstance("saved_chest_01", entity.entity_id, "saved_chest"))
        self.service.register_lock_definition(
            LockDefinition("saved_chest_lock", "Saved chest lock", "saved_chest_key")
        )
        self.service.register_key_definition(
            KeyDefinition("saved_chest_key", "Saved chest key", "saved_chest_lock", True)
        )
        self.service.register_lock(
            LockInstance("saved_chest_lock_01", entity.entity_id, "saved_chest_lock")
        )
        self.service.register_actor("hero", "player", inventory_id="main")
        self.service.bind_key_owner("saved_chest_key", "hero")
        self.inventory.add_item("saved_chest_key")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "locked-save.json"
            self.application.save(path)
            restored = GameApplication.create_default()
            bundle = restored.load(path)

        self.assertEqual(bundle.locks.for_entity(entity.entity_id).lock_id, "saved_chest_lock_01")
        restored_service = GameplayService(restored)
        with self.assertRaises(GameplayServiceError):
            restored_service.open_container("hero", "main", "saved_chest_01")
        self.assertTrue(restored_service.unlock_with_key(
            "hero", "main", "saved_chest_lock_01", "saved_chest_key"
        ))
        self.assertEqual(
            restored_service.open_container("hero", "main", "saved_chest_01").container_id,
            "saved_chest_01",
        )

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


    def test_container_can_be_nested_without_map_placement(self):
        self.service.register_container_definition(ContainerDefinition(
            "chest", "Chest", max_contents_weight_kg=10, max_slots=10,
            max_contents_volume_liters=10, max_nesting_depth=2,
        ))
        self.service.register_container_definition(ContainerDefinition(
            "bag", "Bag", max_contents_weight_kg=5, max_slots=5,
            max_contents_volume_liters=5, max_nesting_depth=1,
        ))
        parent_entity = Entity(EntityType.ESYA, "Chest", entity_id="nested_parent_entity")
        child_entity = Entity(EntityType.ESYA, "Bag", entity_id="nested_child_entity")
        self.application.varlik_ekle(parent_entity)
        self.application.varlik_ekle(child_entity)
        self.service.register_container(ContainerInstance("parent", parent_entity.entity_id, "chest"))
        self.service.register_container(ContainerInstance("child", child_entity.entity_id, "bag"))

        self.service.contain_container("parent", "child")

        self.assertIsNotNone(self.application.holder.current.containers.parent_of("child"))

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

    def test_quest_journal_read_models_are_immutable_and_read_only(self):
        active = Quest(
            "active_quest", "Active quest",
            (Objective("collect_wood", "Collect wood", ObjectiveType.COLLECT, required=2),),
            Reward(experience=10, items=(("bread", 1),)),
            giver_npc_id="missing_giver",
        )
        active.start()
        active.objectives[0].advance(1)
        completed = Quest(
            "completed_quest", "Completed quest",
            (Objective("finish", "Finish task", ObjectiveType.CUSTOM),),
        )
        completed.start()
        completed.update("finish", 1)
        self.application.holder.current.quest_log.add(active)
        self.application.holder.current.quest_log.add(completed)

        before_tick = self.service.state().simulation_tick
        first = self.service.quest_log_state("active")
        repeated = self.service.quest_log_state("active")
        completed_views = self.service.quest_log_state("completed")

        self.assertEqual(first, repeated)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].quest_id, "active_quest")
        self.assertEqual(first[0].state, "active")
        self.assertEqual(first[0].giver_name, "Bilinmeyen görev veren")
        self.assertEqual(first[0].objectives[0].progress, 1)
        self.assertEqual(first[0].reward.experience, 10)
        self.assertEqual(first[0].reward.items, (("bread", 1),))
        self.assertEqual(tuple(item.quest_id for item in completed_views), ("completed_quest",))
        with self.assertRaises(FrozenInstanceError):
            first[0].title = "Changed"
        with self.assertRaises(FrozenInstanceError):
            first[0].objectives[0].progress = 2
        with self.assertRaises(ValueError):
            self.service.quest_log_state("unknown")
        self.assertEqual(self.service.quest_log_counts(), (1, 1, 0))
        self.assertEqual(self.service.state().simulation_tick, before_tick)

    def test_dialogue_choice_query_hides_blacksmith_delivery_for_incomplete_objective(self):
        from types import SimpleNamespace
        from quests import Dialogue, DialogueChoice, DialogueNode

        self.inventory.add(ResourceType("iron_ore"), Quantity(3, ResourceUnit.ITEM))
        self.service.blacksmith_quest = SimpleNamespace(
            state=SimpleNamespace(value="active"),
            objectives=(SimpleNamespace(objective_id="collect_iron_ore"),),
        )
        dialogue = Dialogue(
            "blacksmith_test",
            (DialogueNode(
                "start", "village_blacksmith", "Need ore",
                (
                    DialogueChoice("deliver_blacksmith_ore", "Deliver ore"),
                    DialogueChoice("ask_question", "Ask a question"),
                ),
            ),),
            "start",
        )
        self.service.register_dialogue(dialogue)

        choices = self.service.dialogue_choices(
            "hero", "village_blacksmith", "blacksmith_test", "start",
        )

        self.assertEqual(tuple(choice.choice_id for choice in choices), ("ask_question",))

    def test_dialogue_choice_query_is_service_owned_and_read_only(self):
        dialogue = Dialogue(
            "service_dialogue",
            (DialogueNode(
                "start", "test_npc", "Hello",
                (DialogueChoice("greet", "Greetings"),),
            ),),
            "start",
        )
        self.service.register_dialogue(dialogue)
        before_tick = self.service.state().simulation_tick

        first = self.service.dialogue_choices(
            "hero", "test_npc", "service_dialogue", "start",
        )
        repeated = self.service.dialogue_choices(
            "hero", "test_npc", "service_dialogue", "start",
        )

        self.assertEqual(first, repeated)
        self.assertEqual(tuple(choice.choice_id for choice in first), ("greet",))
        with self.assertRaises(FrozenInstanceError):
            first[0].text = "Changed"
        self.assertEqual(self.service.state().simulation_tick, before_tick)

    def test_production_catalog_queries_are_immutable_and_service_owned(self):
        before_tick = self.service.state().simulation_tick

        first = self.service.recipes_state()
        repeated = self.service.recipes_state()

        self.assertEqual(tuple(recipe.recipe_id for recipe in first), ("smelt", "tool"))
        self.assertEqual(first, repeated)
        self.assertEqual(first[0].facility_type, "smelter")
        self.assertEqual(
            tuple((resource.value, quantity.value, quantity.unit.value)
                  for resource, quantity in first[0].inputs),
            (("ore", 2, "item"),),
        )
        with self.assertRaises(FrozenInstanceError):
            first[0].recipe_id = "changed"

        smelter = self.service.production_facility_for_recipe("smelt")
        workshop = self.service.production_facility_for_recipe("tool")
        incompatible = self.service.production_facility_for_recipe(
            "smelt", facility_id="workshop-1",
        )

        self.assertEqual(smelter.facility_id, "smelter-1")
        self.assertEqual(workshop.facility_id, "workshop-1")
        self.assertIsNone(incompatible)
        self.assertEqual(self.service.state().simulation_tick, before_tick)

    def test_gameplay_state_returns_detached_immutable_value_views(self):
        self.service.register_actor("z_worker", "worker", inventory_id="other")
        self.service.register_actor("a_worker", "worker", inventory_id="main")

        before = self.service.state()
        repeated = self.service.state()

        self.assertEqual(before, repeated)
        self.assertEqual(
            tuple(item.inventory_id for item in before.inventories),
            ("main", "other", "traveler_bag"),
        )
        self.assertEqual(
            tuple(actor.actor_id for actor in before.actors),
            ("a_worker", "z_worker"),
        )
        self.assertEqual(before.nodes[0].quantity, (6, "item"))

        with self.assertRaises(FrozenInstanceError):
            before.inventories[0].inventory_id = "changed"
        with self.assertRaises(FrozenInstanceError):
            before.nodes[0].quantity = (0, "item")
        with self.assertRaises(FrozenInstanceError):
            before.actors[0].active = False

        self.service.collect("ore-node", "main", Quantity(1, ResourceUnit.ITEM))
        after = self.service.state()

        self.assertEqual(before.nodes[0].quantity, (6, "item"))
        self.assertEqual(after.nodes[0].quantity, (5, "item"))
        self.assertEqual(before.inventories[0].stocks, ())
        self.assertEqual(after.inventories[0].stocks, (("ore", 1, "item"),))
        self.assertEqual(before.simulation_tick, after.simulation_tick)

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

    def test_load_switch_discards_session_bound_runtime_caches(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_chain("chain", (("smelt", "main", "smelter-1"),))
        self.service._hex_physics_snapshots["stale"] = object()
        self.service._companion_command_service = object()
        self.service._npc_behavior_system = object()
        self.service._npc_behavior_system_key = ("old",)
        self.service._npc_avoidance_system = object()
        self.service._npc_avoidance_system_key = ("old",)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chain-save.json"
            self.service.save(path)
            self.service.load(path)
            self.assertEqual(self.service.state().chains, ())
            self.assertEqual(self.service._hex_physics_snapshots, {})
            self.assertIsNone(self.service._companion_command_service)
            self.assertIsNone(self.service._npc_behavior_system)
            self.assertIsNone(self.service._npc_behavior_system_key)
            self.assertIsNone(self.service._npc_avoidance_system)
            self.assertIsNone(self.service._npc_avoidance_system_key)

    def test_active_world_and_quest_panel_queries_are_read_only_views(self):
        before_tick = self.service.state().simulation_tick
        first_world = self.service.active_world_state()
        second_world = self.service.active_world_state()
        self.assertEqual(first_world, second_world)
        self.assertEqual(first_world.world_id, "world_playable")
        self.assertEqual(first_world.name, "Playable")
        with self.assertRaises(FrozenInstanceError):
            first_world.name = "Changed"
        self.assertIsNone(self.service.quest_panel_state())
        self.assertEqual(self.service.state().simulation_tick, before_tick)

    def test_character_creation_service_owns_validation(self):
        with self.assertRaisesRegex(ValueError, "İsim alanı boş bırakılamaz"):
            self.service.customize_player_character(
                "", 25, {"strength": 12}, appearance={}
            )
        with self.assertRaisesRegex(ValueError, "Yaş 13 ile 120"):
            self.service.customize_player_character(
                "Arin", 12, {"strength": 12}, appearance={}
            )


    def test_combat_state_returns_detached_immutable_views(self):
        hero = Combatant("hero", 20)
        goblin = Combatant("goblin", 12)
        self.service.add_combatant(hero)
        self.service.add_combatant(goblin)
        self.service.create_combat_encounter(
            "opening_encounter",
            ("hero", "goblin"),
            initiative_scores={"hero": 10, "goblin": 5},
        )

        snapshot = self.service.combat_state()

        self.assertEqual(
            tuple(item.combatant_id for item in snapshot.combatants),
            ("goblin", "hero"),
        )
        self.assertEqual(snapshot.encounters[0].active_combatant_id, "hero")
        self.assertEqual(snapshot.encounters[0].round_number, 1)
        goblin.add_status("poison", 2)
        goblin.hit_points = 4
        self.assertEqual(snapshot.combatants[0].hit_points, 12)
        self.assertEqual(snapshot.combatants[0].statuses, ())
        with self.assertRaises(FrozenInstanceError):
            snapshot.combatants[0].hit_points = 4


if __name__ == "__main__":
    unittest.main()
