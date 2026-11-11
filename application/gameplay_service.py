"""Application-level playable gameplay loop orchestration.

This service deliberately owns no canonical gameplay state.  It resolves the
current SessionBundle for each operation and delegates mutations to the
resource, production and canonical simulation components that already own
those rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Iterable

from core.time import Tick
from core.actions import ActionType, action_tick_cost
from core.foundation import Identifier
from core.entity import EntityType

from resources import Inventory, Quantity, Recipe, ResourceType, ResourceUnit
from containers import ContainerDefinition, ContainerInstance
from locks import ForceProfile, KeyDefinition, LockDefinition, LockInstance, LockpickProfile
from economy import Currency, MarketOffer, Money, TradeService, Merchant, MarketProfile

from .game_application import GameApplication
from .production_chain import ProductionChain, ProductionChainStage
from .actor_system import ActivityView, ActorView, WorldActor
from character import EquipmentSlot, ItemDefinition
from .movement import MovementManager
from world import WorldMap, LocalMapDefinition
from .world_object_placement import WorldObjectPlacement
from npc import Faction, NPC
from quests import Dialogue, Quest
from .social_runtime import SocialRuntimeError
from .combat_runtime import Combatant

from core.errors import RPGError

class GameplayServiceError(RuntimeError, RPGError):
    """Controlled failure at the playable application boundary."""


@dataclass(frozen=True)
class GameplayChainStage:
    """Stable request for one application-level chain stage."""

    recipe_id: str
    inventory_id: str
    facility_id: str


@dataclass(frozen=True)
class InventoryView:
    inventory_id: str
    stocks: tuple[tuple[str, int, str], ...]
    items: tuple[tuple[str, int], ...] = ()
    weight: float = 0.0


@dataclass(frozen=True)
class ContainerView:
    container_id: str
    entity_id: str
    definition_id: str
    name: str
    items: tuple[tuple[str, int], ...]
    stocks: tuple[tuple[str, int, str], ...]
    contents_weight_kg: float
    contents_slots: int
    contents_volume_liters: float
    durability: float | None
    broken: bool
    custody_inventory_id: str | None = None
    max_contents_weight_kg: float | None = None
    max_slots: int | None = None
    max_contents_volume_liters: float | None = None


@dataclass(frozen=True)
class LockView:
    lock_id: str
    entity_id: str
    definition_id: str
    name: str
    locked: bool
    jammed: bool
    broken: bool
    required_key_id: str | None = None
    lockpick_profile_id: str | None = None
    force_profile_id: str | None = None
    lockpick_difficulty_class: int | None = None
    lockpick_allowed_tool_tags: tuple[str, ...] = ()
    lockpick_requires_tool: bool = False
    lockpick_minimum_skill: int = 0
    force_difficulty_class: int | None = None
    force_required_tool_tags: tuple[str, ...] = ()
    force_minimum_strength: int = 0


@dataclass(frozen=True)
class LockAttemptResult:
    action: str
    roll: int | None
    modifier: int
    difficulty_class: int | None
    total: int | None
    success: bool
    attempted: bool
    message: str


@dataclass(frozen=True)
class ResourceNodeView:
    node_id: str
    world_id: str
    resource_type: str
    quantity: tuple[int, str]
    capacity: tuple[int, str]
    regeneration_rate: tuple[int, str]
    last_simulation_tick: int
    location_id: str | None = None


@dataclass(frozen=True)
class LocationInteractionView:
    actor_id: str
    location_id: str
    location_name: str
    character_id: str | None
    resource_node_ids: tuple[str, ...]
    actor_ids: tuple[str, ...]


@dataclass(frozen=True)
class FacilityView:
    facility_id: str
    facility_type: str
    active: bool
    capabilities: tuple[str, ...]
    capacity: int
    reserved: int
    active_job_ids: tuple[str, ...]


@dataclass(frozen=True)
class JobView:
    job_id: str
    recipe_id: str
    inventory_id: str
    state: str
    start_tick: int
    end_tick: int


@dataclass(frozen=True)
class ChainView:
    chain_id: str
    state: str
    current_stage_index: int | None
    job_ids: tuple[str, ...]


@dataclass(frozen=True)
class GameplaySnapshotView:
    world_id: str | None
    simulation_tick: int
    inventories: tuple[InventoryView, ...]
    nodes: tuple[ResourceNodeView, ...]
    facilities: tuple[FacilityView, ...]
    jobs: tuple[JobView, ...]
    chains: tuple[ChainView, ...]
    actors: tuple[ActorView, ...] = ()
    activities: tuple[ActivityView, ...] = ()
    movements: tuple = ()


class GameplayService:
    """Coordinate the existing gameplay components for a playable loop."""

    def __init__(self, application: GameApplication) -> None:
        if not isinstance(application, GameApplication):
            raise TypeError("application must be GameApplication.")
        self._application = application
        self._chains: dict[str, ProductionChain] = {}
        self._bundle = None
        self._character_factory = None
        self._quest_reward_accounts: dict[str, str] = {}
        self._quest_reward_inventories: dict[str, str] = {}
        self._dialogue_actions: dict[str, Callable[[str, str], None]] = {}

    @property
    def application(self) -> GameApplication:
        return self._application

    def register_character_factory(self, factory) -> None:
        self._character_factory = factory

    def collect(self, node_id: str, inventory_id: str, quantity: Quantity) -> None:
        """Atomically extract from an active-world node into a registered inventory."""
        bundle = self._current_bundle()
        world = bundle.session.worlds.get_active()
        if world is None:
            raise GameplayServiceError("An active world is required for collection.")
        inventory = self._inventory(bundle, inventory_id)
        node = bundle.resource_nodes.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        if node.world_id != world.world_id:
            raise GameplayServiceError(
                f"Resource node {node_id} does not belong to the active world."
            )
        bundle.resource_nodes.extract(node_id, inventory, quantity)
        self._advance_quests("collect", node_id, quantity.value, "hero", inventory_id)

    def action_cost(self, action_type: ActionType | str) -> int:
        """Return a fixed gameplay action's canonical cost in ticks."""
        return action_tick_cost(action_type).value

    def _complete_timed_action(self, action_type: ActionType, owner_id: str, callback):
        """Run an immediate gameplay operation through the canonical action runtime."""
        bundle = self._current_bundle()
        duration = action_tick_cost(action_type)
        action = bundle.simulation.actions.create(
            Identifier(owner_id),
            duration,
            context={"action_type": action_type.value},
        )
        bundle.simulation.actions.schedule(
            action.action_id,
            bundle.simulation.current_tick,
        )
        bundle.production_jobs.advance_by(duration)
        if action.state.value != "completed":
            raise GameplayServiceError(
                f"Timed action did not complete: {action.action_id}"
            )
        return callback()

    def start_production(
        self,
        recipe_id: str,
        inventory_id: str,
        facility_id: str,
    ):
        """Start one job through the existing facility and job managers."""
        bundle = self._current_bundle()
        self._require_active_world(bundle)
        recipe = self._recipe(bundle, recipe_id)
        inventory = self._inventory(bundle, inventory_id)
        facility = bundle.facilities.get(facility_id)
        if facility is None:
            raise KeyError(f"Production facility not found: {facility_id}")
        return facility.start(bundle.production_jobs, recipe, inventory)

    def start_chain(
        self,
        chain_id: str,
        stages: Iterable[GameplayChainStage | tuple[str, str, str]],
    ) -> ProductionChain:
        """Start an explicit-facility sequential chain using existing jobs."""
        bundle = self._current_bundle()
        self._require_active_world(bundle)
        if not isinstance(chain_id, str) or not chain_id.strip():
            raise ValueError("chain_id cannot be empty.")
        if chain_id in self._chains:
            raise ValueError(f"Gameplay chain already exists: {chain_id}")

        requests = tuple(self._normalize_stage(stage) for stage in stages)
        if not requests:
            raise ValueError("A gameplay chain must contain at least one stage.")
        normalized = tuple(
            ProductionChainStage(
                recipe=self._recipe(bundle, request.recipe_id),
                inventory=self._inventory(bundle, request.inventory_id),
                facility_id=request.facility_id,
            )
            for request in requests
        )
        chain = ProductionChain(
            bundle.production_jobs,
            normalized,
            chain_id=chain_id,
            facilities=bundle.facilities,
        )
        try:
            chain.start()
        except Exception:
            chain.dispose()
            raise
        self._chains[chain_id] = chain
        return chain

    def advance_to(self, target_tick: Tick | int):
        """Advance canonical simulation and dispatch production events."""
        bundle = self._current_bundle()
        self._require_active_world(bundle)
        return bundle.production_jobs.advance_to(target_tick)

    def advance_by(self, delta: Tick | int):
        bundle = self._current_bundle()
        self._require_active_world(bundle)
        return bundle.production_jobs.advance_by(delta)

    def save(self, path):
        return self._application.save(path)

    def load(self, path):
        result = self._application.load(path)
        self._chains.clear()
        self._bundle = result
        result.actor_activities.bind_gameplay_service(self)
        self._rebind_content_quests()
        return result

    def _rebind_content_quests(self) -> None:
        quest_log = self._current_bundle().quest_log
        for attribute in (
            "available_forest_quest",
            "carpenter_quest",
            "inn_quest",
            "blacksmith_quest",
        ):
            current = getattr(self, attribute, None)
            quest_id = getattr(current, "quest_id", None)
            if quest_id is None:
                continue
            restored = quest_log.get(quest_id)
            if restored is not None:
                setattr(self, attribute, restored)
                if attribute in ("carpenter_quest", "inn_quest"):
                    self._quest_reward_accounts.setdefault(quest_id, "hero")
                    self._quest_reward_inventories.setdefault(quest_id, "player")

    def register_actor(self, actor_id: str, role: str, world_id: str | None = None, active: bool = True, character_id: str | None = None, inventory_id: str | None = None) -> ActorView:
        bundle = self._current_bundle()
        target_world = world_id
        if target_world is None:
            world = bundle.session.worlds.get_active()
            if world is None:
                raise GameplayServiceError("An active world is required to register an actor.")
            target_world = world.world_id
        character = None
        if character_id is not None:
            character = bundle.characters.get(character_id)
            if character is None:
                raise KeyError(f"Character not found: {character_id}")
            if character.actor_id is not None and character.actor_id != actor_id:
                raise ValueError(
                    f"Character already references another actor: {character_id}"
                )
        if inventory_id is not None:
            self._inventory(bundle, inventory_id)
        actor = WorldActor(actor_id, target_world, role, active, inventory_id=inventory_id)
        bundle.actors.add(actor)
        if character is not None:
            bundle.actors.bind_character(actor_id, character)
        bundle.validate()
        return actor.view()

    def bind_actor_inventory(self, actor_id: str, inventory_id: str) -> ActorView:
        """Bind one registered inventory to an actor for possession checks."""
        bundle = self._current_bundle()
        self._inventory(bundle, inventory_id)
        bundle.actors.bind_inventory(actor_id, inventory_id)
        bundle.validate()
        return bundle.actors.get(actor_id)

    def bind_actor_character(self, actor_id: str, character_id: str) -> ActorView:
        """Bind an existing actor and character while checking both sides."""
        bundle = self._current_bundle()
        character = bundle.characters.get(character_id)
        if character is None:
            raise KeyError(f"Character not found: {character_id}")
        bundle.actors.bind_character(actor_id, character)
        bundle.validate()
        return bundle.actors.get(actor_id)

    def register_world_map(self, world_map: WorldMap, *, local_map_width: int = 32, local_map_height: int = 32) -> None:
        """Register the movement graph and local tile-map dimensions."""
        bundle = self._current_bundle()
        if not isinstance(world_map, WorldMap):
            raise TypeError("world_map must be WorldMap.")
        for name, value in (("local_map_width", local_map_width), ("local_map_height", local_map_height)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        bundle.movement.register_map(world_map)
        for location in world_map.locations():
            bundle.world_objects.register_local_map(LocalMapDefinition(world_map.world_id, location.location_id, local_map_width, local_map_height))

    def place_world_object(self, object_id: str, location_id: str, x: int, y: int, *, width: int = 1, height: int = 1, blocks_movement: bool = True, layer: int = 0, tags: tuple[str, ...] = ()) -> WorldObjectPlacement:
        """Place a registered Core Entity on a local map tile footprint."""
        bundle = self._current_bundle()
        entity = bundle.session.entities.get(object_id)
        if entity is None:
            raise KeyError(f"Entity not found: {object_id}")
        if entity.world_id is None:
            raise GameplayServiceError("World objects must belong to a Core World.")
        container = bundle.containers.for_entity(object_id)
        if container is not None and (
            bundle.containers.parent_of(container.container_id) is not None
            or bundle.containers.inventory_custody(container.container_id) is not None
        ):
            raise GameplayServiceError("A container with existing custody cannot be independently placed in the world.")
        world_map = bundle.movement.map_for(entity.world_id)
        if world_map is None or world_map.get(location_id) is None:
            raise KeyError(f"Location is not registered in the object's world: {location_id}")
        return bundle.world_objects.place(WorldObjectPlacement(object_id, entity.world_id, location_id, x, y, width, height, blocks_movement, layer, tags))

    def move_world_object(self, object_id: str, x: int, y: int) -> WorldObjectPlacement:
        return self._current_bundle().world_objects.move(object_id, x, y)

    def transfer_world_object(self, object_id: str, location_id: str, x: int, y: int) -> WorldObjectPlacement:
        bundle = self._current_bundle()
        current = bundle.world_objects.get(object_id)
        if current is None:
            raise KeyError(f"World object placement not found: {object_id}")
        world_map = bundle.movement.map_for(current.world_id)
        if world_map is None or world_map.get(location_id) is None:
            raise KeyError(f"Location not found in object's world: {location_id}")
        return bundle.world_objects.transfer(object_id, location_id, x, y)

    def remove_world_object_placement(self, object_id: str) -> WorldObjectPlacement:
        return self._current_bundle().world_objects.remove(object_id)

    def world_objects_for_location(self, world_id: str, location_id: str) -> tuple[WorldObjectPlacement, ...]:
        return self._current_bundle().world_objects.for_location(world_id, location_id)

    def blocked_world_object_tiles(self, world_id: str, location_id: str) -> frozenset[tuple[int, int]]:
        return self._current_bundle().world_objects.blocked_tiles(world_id, location_id)

    def register_container_definition(self, definition: ContainerDefinition) -> ContainerDefinition:
        """Register one immutable content definition in the active session."""
        if not isinstance(definition, ContainerDefinition):
            raise TypeError("definition must be ContainerDefinition.")
        return self._current_bundle().containers.register_definition(definition)

    def register_container(self, instance: ContainerInstance, inventory: Inventory | None = None) -> ContainerInstance:
        """Attach a container capability to an existing Core item entity."""
        bundle = self._current_bundle()
        if not isinstance(instance, ContainerInstance):
            raise TypeError("instance must be ContainerInstance.")
        entity = bundle.session.entities.get(instance.entity_id)
        if entity is None:
            raise KeyError(f"Entity not found: {instance.entity_id}")
        if entity.entity_type != EntityType.ESYA:
            raise GameplayServiceError("A container capability can only be attached to an ESYA entity.")
        if inventory is not None and (
            any(inventory is existing for existing in bundle.inventories.values())
            or any(inventory is existing for existing in bundle.containers.all_inventories())
        ):
            raise GameplayServiceError("A container must own an independent Inventory.")
        return bundle.containers.register(instance, inventory)

    def container_state(self, container_id: str) -> ContainerView:
        """Return a read-only projection of a container and its contents."""
        bundle = self._current_bundle()
        instance = bundle.containers.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        definition = bundle.containers.definition(instance.definition_id)
        inventory = bundle.containers.inventory(container_id)
        usage = bundle.containers.usage(container_id)
        return ContainerView(
            instance.container_id, instance.entity_id, instance.definition_id,
            definition.name, inventory.item_snapshot(),
            tuple((resource.value, quantity.value, quantity.unit.value)
                  for resource, quantity in inventory.snapshot()),
            usage.weight_kg, usage.slots, usage.volume_liters,
            instance.durability, instance.broken,
            bundle.containers.inventory_custody(container_id),
            definition.max_contents_weight_kg,
            definition.max_slots,
            definition.max_contents_volume_liters,
        )

    def container_for_entity(self, entity_id: str) -> str | None:
        """Return the container instance attached to a Core entity."""
        instance = self._current_bundle().containers.for_entity(entity_id)
        return instance.container_id if instance is not None else None

    def container_lock_state(self, container_id: str) -> LockView | None:
        """Return lock status for a container without exposing its contents."""
        bundle = self._current_bundle()
        container = bundle.containers.get(container_id)
        if container is None:
            raise KeyError(f"Container not found: {container_id}")
        lock = bundle.locks.for_entity(container.entity_id)
        return self.lock_state(lock.lock_id) if lock is not None else None

    def register_lockpick_profile(self, profile: LockpickProfile) -> LockpickProfile:
        return self._current_bundle().locks.register_lockpick_profile(profile)

    def register_force_profile(self, profile: ForceProfile) -> ForceProfile:
        return self._current_bundle().locks.register_force_profile(profile)

    def register_lock_definition(self, definition: LockDefinition) -> LockDefinition:
        return self._current_bundle().locks.register_lock_definition(definition)

    def register_key_definition(self, definition: KeyDefinition) -> KeyDefinition:
        return self._current_bundle().locks.register_key_definition(definition)

    def register_lock(self, instance: LockInstance) -> LockInstance:
        """Attach a lock capability to an existing Core entity without changing its type."""
        bundle = self._current_bundle()
        if not isinstance(instance, LockInstance):
            raise TypeError("instance must be LockInstance.")
        if bundle.session.entities.get(instance.entity_id) is None:
            raise KeyError(f"Entity not found: {instance.entity_id}")
        return bundle.locks.register(instance)

    def lock_state(self, lock_id: str) -> LockView:
        bundle = self._current_bundle()
        instance = bundle.locks.get(lock_id)
        if instance is None:
            raise KeyError(f"Lock not found: {lock_id}")
        definition = bundle.locks.definition(instance.definition_id)
        lockpick = bundle.locks.lockpick_profile(definition.lockpick_profile_id) if definition.lockpick_profile_id else None
        force = bundle.locks.force_profile(definition.force_profile_id) if definition.force_profile_id else None
        return LockView(
            instance.lock_id, instance.entity_id, instance.definition_id,
            definition.name, instance.locked, instance.jammed, instance.broken,
            definition.required_key_id, definition.lockpick_profile_id,
            definition.force_profile_id,
            lockpick.difficulty_class if lockpick else None,
            lockpick.allowed_tool_tags if lockpick else (),
            lockpick.require_tool if lockpick else False,
            lockpick.minimum_skill if lockpick else 0,
            force.difficulty_class if force else None,
            force.required_tool_tags if force else (),
            force.minimum_strength if force else 0,
        )

    def bind_key_owner(self, key_id: str, actor_id: str) -> None:
        bundle = self._current_bundle()
        if bundle.actors.get(actor_id) is None:
            raise KeyError(f"Actor not found: {actor_id}")
        bundle.locks.bind_key_owner(key_id, actor_id)

    def unlock_with_key(
        self, actor_id: str, inventory_id: str, lock_id: str, key_id: str
    ) -> bool:
        """Unlock only when the exact key item is present in the supplied actor inventory."""
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        inventory = self._inventory_for_actor(bundle, actor_id, inventory_id)
        if inventory.item_quantity(key_id) < 1:
            return False
        return bundle.locks.unlock_with_key(
            lock_id, key_id, actor_id, key_available=True
        )

    def resolve_lockpick(self, actor_id: str, inventory_id: str, lock_id: str, *, tool_item_id: str | None = None) -> LockAttemptResult:
        """Roll a d20 lockpicking check using the actor skill and carried tools."""
        from core.dice import zar_at
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        character = self._character_for_actor(bundle, actor_id)
        inventory = self._inventory_for_actor(bundle, actor_id, inventory_id)
        instance = bundle.locks.get(lock_id)
        if instance is None:
            raise KeyError(f"Lock not found: {lock_id}")
        definition = bundle.locks.definition(instance.definition_id)
        profile = bundle.locks.lockpick_profile(definition.lockpick_profile_id) if definition.lockpick_profile_id else None
        if profile is None:
            return LockAttemptResult("lockpick", None, 0, None, None, False, False, "Bu kilit maymuncukla açılamaz.")
        dexterity_score = character.attributes.get("dexterity")
        dexterity_modifier = character.attributes.modifier("dexterity")
        tool_tags = self._carried_tool_tags(bundle, inventory, tool_item_id)
        if dexterity_score < 2:
            return LockAttemptResult("lockpick", None, dexterity_modifier, profile.difficulty_class, None, False, False, "Çeviklik seviyesi maymuncuk kullanmak için yetersiz (en az 2 olmalı).")
        if profile.require_skill and dexterity_score < profile.minimum_skill:
            return LockAttemptResult("lockpick", None, dexterity_modifier, profile.difficulty_class, None, False, False, "Bu kilit için çeviklik seviyesi yetersiz.")
        if not set(tool_tags).intersection(profile.allowed_tool_tags):
            return LockAttemptResult("lockpick", None, dexterity_modifier, profile.difficulty_class, None, False, False, "Maymuncuk aleti envanterde bulunamadı.")
        roll = zar_at(20)
        total = roll + dexterity_modifier
        success = total >= profile.difficulty_class
        bundle.locks.attempt_lockpick(lock_id, skill=dexterity_score, tool_tags=tool_tags, success=success)
        message = "Kilit başarıyla açıldı." if success else "Maymuncuk denemesi başarısız."
        return LockAttemptResult("lockpick", roll, dexterity_modifier, profile.difficulty_class, total, success, True, message)

    def attempt_lockpick(self, actor_id: str, inventory_id: str, lock_id: str, *, tool_item_id: str | None = None) -> bool:
        return self.resolve_lockpick(actor_id, inventory_id, lock_id, tool_item_id=tool_item_id).success

    def resolve_force_lock(self, actor_id: str, inventory_id: str, lock_id: str, *, tool_item_id: str | None = None) -> LockAttemptResult:
        """Roll a d20 forced-opening check using the actor strength modifier."""
        from core.dice import zar_at
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        character = self._character_for_actor(bundle, actor_id)
        inventory = self._inventory_for_actor(bundle, actor_id, inventory_id)
        instance = bundle.locks.get(lock_id)
        if instance is None:
            raise KeyError(f"Lock not found: {lock_id}")
        definition = bundle.locks.definition(instance.definition_id)
        profile = bundle.locks.force_profile(definition.force_profile_id) if definition.force_profile_id else None
        if profile is None or not profile.allowed:
            return LockAttemptResult("force", None, 0, None, None, False, False, "Bu kilit zorlanarak açılamaz.")
        strength_score = character.attributes.get("strength")
        modifier = character.attributes.modifier("strength")
        tool_tags = self._carried_tool_tags(bundle, inventory, tool_item_id)
        if strength_score < profile.minimum_strength:
            return LockAttemptResult("force", None, modifier, profile.difficulty_class, None, False, False, "Karakterin gücü bu kilidi zorlamak için yetersiz.")
        if profile.required_tool_tags and not set(tool_tags).intersection(profile.required_tool_tags):
            return LockAttemptResult("force", None, modifier, profile.difficulty_class, None, False, False, "Gerekli zorlama aleti envanterde bulunamadı.")
        roll = zar_at(20)
        total = roll + modifier
        success = roll == 20 or (roll != 1 and total >= profile.difficulty_class)
        bundle.locks.attempt_force(lock_id, strength=strength_score, tool_tags=tool_tags, success=success)
        message = "Kilit zorlanarak açıldı." if success else "Zorlama denemesi başarısız."
        return LockAttemptResult("force", roll, modifier, profile.difficulty_class, total, success, True, message)

    def attempt_force_lock(self, actor_id: str, inventory_id: str, lock_id: str, *, tool_item_id: str | None = None) -> bool:
        return self.resolve_force_lock(actor_id, inventory_id, lock_id, tool_item_id=tool_item_id).success
    @staticmethod
    def _inventory_for_actor(bundle, actor_id: str, inventory_id: str) -> Inventory:
        actor = bundle.actors.get(actor_id)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        if actor.inventory_id is None:
            raise GameplayServiceError(
                f"Actor has no bound inventory for possession checks: {actor_id}"
            )
        if actor.inventory_id != inventory_id:
            raise GameplayServiceError(
                f"Inventory {inventory_id} does not belong to actor {actor_id}."
            )
        return GameplayService._inventory(bundle, inventory_id)

    @staticmethod
    def _character_for_actor(bundle, actor_id: str):
        actor = bundle.actors.get(actor_id)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        if actor.character_id is None:
            raise GameplayServiceError(
                f"Actor has no registered character for character-based checks: {actor_id}"
            )
        character = bundle.characters.get(actor.character_id)
        if character is None:
            raise GameplayServiceError(
                f"Actor character is not registered: {actor.character_id}"
            )
        return character

    @staticmethod
    def _carried_tool_tags(bundle, inventory, tool_item_id: str | None) -> tuple[str, ...]:
        if tool_item_id is None:
            return ()
        if inventory.item_quantity(tool_item_id) < 1:
            return ()
        item = bundle.items.get(tool_item_id)
        if item is None:
            raise KeyError(f"Item definition not found: {tool_item_id}")
        return item.tags

    def open_container(self, actor_id: str, inventory_id: str, container_id: str) -> ContainerView:
        """Expose container contents only after its attached lock has been opened."""
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        self._inventory_for_actor(bundle, actor_id, inventory_id)
        container = bundle.containers.get(container_id)
        if container is None:
            raise KeyError(f"Container not found: {container_id}")
        lock = bundle.locks.for_entity(container.entity_id)
        if lock is not None and (lock.locked or lock.jammed):
            raise GameplayServiceError("Container is not accessible while its lock is locked, jammed, or broken.")
        return self.container_state(container_id)

    def place_container(self, container_id: str, location_id: str, x: int, y: int, *,
                        width: int = 1, height: int = 1, blocks_movement: bool = True,
                        layer: int = 0, tags: tuple[str, ...] = ("container",)) -> WorldObjectPlacement:
        """Place a registered container entity on its world's local map."""
        bundle = self._current_bundle()
        instance = bundle.containers.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        if bundle.containers.parent_of(container_id) is not None:
            raise GameplayServiceError("A nested container cannot also be placed in the world.")
        if bundle.containers.inventory_custody(container_id) is not None:
            raise GameplayServiceError("A carried container must be dropped before world placement.")
        return self.place_world_object(
            instance.entity_id, location_id, x, y, width=width, height=height,
            blocks_movement=blocks_movement, layer=layer, tags=tags,
        )


    def carry_container(self, container_id: str, inventory_id: str) -> None:
        """Assign a unique container instance to a registered character/NPC inventory."""
        bundle = self._current_bundle()
        self._inventory(bundle, inventory_id)
        instance = bundle.containers.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        if bundle.world_objects.get(instance.entity_id) is not None:
            raise GameplayServiceError("A world-placed container must be picked up before it can be carried.")
        bundle.containers.set_inventory_custody(container_id, inventory_id)
        try:
            bundle.validate()
        except Exception:
            bundle.containers.clear_inventory_custody(container_id, inventory_id)
            raise

    def pickup_container(self, container_id: str, inventory_id: str) -> None:
        """Pick up a world-placed container into a registered inventory."""
        bundle = self._current_bundle()
        self._inventory(bundle, inventory_id)
        instance = bundle.containers.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        placement = bundle.world_objects.get(instance.entity_id)
        if placement is None:
            raise GameplayServiceError("Container is not placed in the world.")
        bundle.containers.set_inventory_custody(container_id, inventory_id)
        try:
            bundle.world_objects.remove(instance.entity_id)
            bundle.validate()
        except Exception:
            if bundle.world_objects.get(instance.entity_id) is None:
                bundle.world_objects.place(placement)
            bundle.containers.clear_inventory_custody(container_id, inventory_id)
            raise

    def transfer_container_custody(self, container_id: str, source_inventory_id: str,
                                   target_inventory_id: str) -> None:
        """Transfer a unique container instance between registered inventories."""
        bundle = self._current_bundle()
        self._inventory(bundle, source_inventory_id)
        self._inventory(bundle, target_inventory_id)
        bundle.containers.clear_inventory_custody(container_id, source_inventory_id)
        try:
            bundle.containers.set_inventory_custody(container_id, target_inventory_id)
            bundle.validate()
        except Exception:
            if bundle.containers.inventory_custody(container_id) == target_inventory_id:
                bundle.containers.clear_inventory_custody(container_id, target_inventory_id)
            if bundle.containers.inventory_custody(container_id) is None:
                bundle.containers.set_inventory_custody(container_id, source_inventory_id)
            raise

    def drop_container(self, container_id: str, location_id: str, x: int, y: int, *,
                       width: int = 1, height: int = 1, blocks_movement: bool = True,
                       layer: int = 0, tags: tuple[str, ...] = ("container",)) -> WorldObjectPlacement:
        """Drop a carried container into the world without losing custody on failure."""
        bundle = self._current_bundle()
        owner_inventory_id = bundle.containers.inventory_custody(container_id)
        if owner_inventory_id is None:
            raise GameplayServiceError("Container is not currently carried by an inventory.")
        instance = bundle.containers.get(container_id)
        bundle.containers.clear_inventory_custody(container_id, owner_inventory_id)
        try:
            placement = self.place_world_object(
                instance.entity_id, location_id, x, y, width=width, height=height,
                blocks_movement=blocks_movement, layer=layer, tags=tags,
            )
        except Exception:
            bundle.containers.set_inventory_custody(container_id, owner_inventory_id)
            raise
        try:
            bundle.validate()
        except Exception:
            bundle.world_objects.remove(placement.object_id)
            bundle.containers.set_inventory_custody(container_id, owner_inventory_id)
            raise
        return placement

    def contain_container(self, parent_id: str, child_id: str) -> ContainerInstance:
        """Move a placed child container into another container."""
        bundle = self._current_bundle()
        child = bundle.containers.get(child_id)
        if child is None:
            raise KeyError(f"Container not found: {child_id}")
        placement = bundle.world_objects.get(child.entity_id)
        result = bundle.containers.contain(parent_id, child_id)
        if placement is not None:
            bundle.world_objects.remove(placement.object_id)
        return result

    def transfer_actor_item_to_container(
        self, actor_id: str, source_inventory_id: str, container_id: str,
        item_id: str, quantity: int = 1,
    ) -> None:
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        self._inventory_for_actor(bundle, actor_id, source_inventory_id)
        self.transfer_item_to_container(source_inventory_id, container_id, item_id, quantity)

    def transfer_actor_item_from_container(
        self, actor_id: str, target_inventory_id: str, container_id: str,
        item_id: str, quantity: int = 1,
    ) -> None:
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        self._inventory_for_actor(bundle, actor_id, target_inventory_id)
        self.transfer_item_from_container(container_id, target_inventory_id, item_id, quantity)

    def transfer_item_to_container(self, source_inventory_id: str, container_id: str,
                                   item_id: str, quantity: int = 1) -> None:
        """Atomically transfer item quantity from a registered inventory into a container."""
        bundle = self._current_bundle()
        source = self._inventory(bundle, source_inventory_id)
        target = bundle.containers.inventory(container_id)
        Inventory._validate_item(item_id, quantity)
        if source.item_quantity(item_id) < quantity:
            raise ValueError("Insufficient item stock in source inventory.")
        source_before, target_before = source.item_snapshot(), target.item_snapshot()
        try:
            source.remove_item(item_id, quantity)
            bundle.containers.add_item(container_id, item_id, quantity)
        except Exception:
            source._restore_item_snapshot(source_before)
            target._restore_item_snapshot(target_before)
            raise

    def transfer_item_from_container(self, container_id: str, target_inventory_id: str,
                                     item_id: str, quantity: int = 1) -> None:
        """Atomically transfer item quantity from a container into a registered inventory."""
        bundle = self._current_bundle()
        source = bundle.containers.inventory(container_id)
        target = self._inventory(bundle, target_inventory_id)
        Inventory._validate_item(item_id, quantity)
        if source.item_quantity(item_id) < quantity:
            raise ValueError("Insufficient item stock in container.")
        source_before, target_before = source.item_snapshot(), target.item_snapshot()
        try:
            source.remove_item(item_id, quantity)
            target.add_item(item_id, quantity)
        except Exception:
            source._restore_item_snapshot(source_before)
            target._restore_item_snapshot(target_before)
            raise

    def transfer_resource_to_container(self, source_inventory_id: str, container_id: str,
                                       resource_type: ResourceType, quantity: Quantity) -> None:
        """Atomically transfer resource stock into a container."""
        bundle = self._current_bundle()
        source = self._inventory(bundle, source_inventory_id)
        target = bundle.containers.inventory(container_id)
        if not isinstance(resource_type, ResourceType) or not isinstance(quantity, Quantity):
            raise TypeError("resource_type and quantity must be ResourceType and Quantity.")
        current = source.get(resource_type)
        if current is None or current.unit != quantity.unit or current.value < quantity.value:
            raise ValueError("Insufficient or incompatible resource stock in source inventory.")
        source_before, target_before = source.snapshot(), target.snapshot()
        try:
            source.remove(resource_type, quantity)
            bundle.containers.add_resource(container_id, resource_type, quantity)
        except Exception:
            source._restore_snapshot(source_before)
            target._restore_snapshot(target_before)
            raise

    def transfer_resource_from_container(self, container_id: str, target_inventory_id: str,
                                         resource_type: ResourceType, quantity: Quantity) -> None:
        """Atomically transfer resource stock from a container into a registered inventory."""
        bundle = self._current_bundle()
        source = bundle.containers.inventory(container_id)
        target = self._inventory(bundle, target_inventory_id)
        if not isinstance(resource_type, ResourceType) or not isinstance(quantity, Quantity):
            raise TypeError("resource_type and quantity must be ResourceType and Quantity.")
        current = source.get(resource_type)
        if current is None or current.unit != quantity.unit or current.value < quantity.value:
            raise ValueError("Insufficient or incompatible resource stock in container.")
        source_before, target_before = source.snapshot(), target.snapshot()
        try:
            source.remove(resource_type, quantity)
            target.add(resource_type, quantity)
        except Exception:
            source._restore_snapshot(source_before)
            target._restore_snapshot(target_before)
            raise


    def place_actor(self, actor_id: str, location_id: str) -> ActorView:
        self._current_bundle().movement.set_position(actor_id, location_id)
        return self._current_bundle().actors.get(actor_id)

    def set_actor_tile_position(self, actor_id: str, x: int, y: int) -> ActorView:
        self._current_bundle().movement.set_tile_position(actor_id, x, y)
        return self._current_bundle().actors.get(actor_id)

    def move_actor(self, actor_id: str, destination_id: str, action_id: str | None = None):
        """Schedule neighbor-based movement; completion occurs on a simulation tick."""
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        return bundle.movement.move(actor_id, destination_id, action_id)

    def movement(self, action_id: str):
        return self._current_bundle().movement.get(action_id)

    def movements_state(self):
        return self._current_bundle().movement.movements()

    def actor(self, actor_id: str) -> ActorView | None:
        return self._current_bundle().actors.get(actor_id)

    def actor_character(self, actor_id: str):
        """Return the character aggregate linked to an actor."""
        bundle = self._current_bundle()
        actor = bundle.actors.get(actor_id)
        if actor is None or actor.character_id is None:
            return None
        return bundle.characters.get(actor.character_id)

    def actor_stats(self, actor_id: str) -> dict[str, object] | None:
        """Read character stats through the actor relationship."""
        character = self.actor_character(actor_id)
        if character is None:
            return None
        return {
            "character_id": character.character_id,
            "name": character.name,
            "age": character.age,
            "attributes": character.attributes.to_dict(),
            "modifiers": {
                attribute: character.attributes.modifier(attribute)
                for attribute in character.attributes.to_dict()
            },
            "skills": character.skills.to_dict(),
            "level": character.progression.level,
            "experience": character.progression.experience,
            "experience_to_next_level": character.progression.experience_to_next_level,
            "unspent_points": character.progression.unspent_points,
            "current_hit_points": character.current_hit_points,
            "max_hit_points": character.max_hit_points,
            "attack_bonus": character.attack_bonus,
            "defense_bonus": character.defense_bonus,
            "initiative_bonus": character.initiative_bonus,
            "weapon_damage": character.weapon_damage,
            "equipment": character.equipment.snapshot(),
        }

    def item(self, item_id: str) -> ItemDefinition | None:
        return self._current_bundle().items.get(item_id)

    def equipment(self, actor_id: str) -> dict[str, str]:
        character = self.actor_character(actor_id)
        if character is None:
            raise GameplayServiceError("Actor must be linked to a character.")
        return character.equipment.snapshot()

    def equip_item(self, actor_id: str, inventory_id: str, item_id: str):
        """Equip one catalog item, returning the replaced item to the inventory."""
        bundle = self._current_bundle()
        character = self.actor_character(actor_id)
        if character is None:
            raise GameplayServiceError("Actor must be linked to a character.")
        item = bundle.items.get(item_id)
        if item is None:
            raise KeyError(f"Item not found: {item_id}")
        inventory = self._inventory(bundle, inventory_id)
        if inventory.item_quantity(item_id) < 1:
            raise ValueError(f"Item is not in inventory: {item_id}")

        def equip():
            previous = character.equip(item)
            inventory.remove_item(item_id)
            if previous is not None:
                inventory.add_item(previous)
            character.current_hit_points = min(
                character.max_hit_points,
                character.current_hit_points,
            )
            return character.equipment.snapshot()

        return self._complete_timed_action(ActionType.INTERACT, actor_id, equip)

    def unequip_item(self, actor_id: str, inventory_id: str, slot: EquipmentSlot | str):
        bundle = self._current_bundle()
        character = self.actor_character(actor_id)
        if character is None:
            raise GameplayServiceError("Actor must be linked to a character.")
        inventory = self._inventory(bundle, inventory_id)

        def unequip():
            item_id = character.unequip(slot)
            if item_id is None:
                raise ValueError(f"No item equipped in slot: {slot}")
            inventory.add_item(item_id)
            return item_id

        return self._complete_timed_action(ActionType.INTERACT, actor_id, unequip)

    def set_actor_active(self, actor_id: str, active: bool) -> ActorView:
        bundle = self._current_bundle()
        bundle.actors.set_active(actor_id, active)
        return bundle.actors.get(actor_id)

    def start_gathering(
        self,
        actor_id: str,
        node_id: str,
        inventory_id: str,
        quantity: Quantity,
        activity_id: str | None = None,
    ) -> ActivityView:
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        result = bundle.actor_activities.start_gathering(
            activity_id, actor_id, node_id, inventory_id, quantity, self,
        )
        self._advance_quests("collect", node_id, quantity.value, actor_id, inventory_id)
        return result

    def gathering_duration(self, actor_id: str) -> int:
        """Return gathering duration after applying the character skill."""
        character = self.actor_character(actor_id)
        skill = character.skills.get("gathering") if character is not None else 0
        return max(1, 150 - (skill * 15))

    def interact_with_location(self, actor_id: str, location_id: str) -> LocationInteractionView:
        """Inspect a location from an actor currently standing there."""
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        actor = bundle.actors.get(actor_id)
        world_map = bundle.movement.map_for(actor.world_id)
        if world_map is None:
            raise GameplayServiceError(f"No movement map registered for world: {actor.world_id}")
        location = world_map.get(location_id)
        if location is None:
            raise KeyError(f"Location not found: {location_id}")
        if actor.location_id != location_id:
            raise GameplayServiceError(
                f"Actor {actor_id} is not at location: {location_id}"
            )
        resource_node_ids = tuple(
            node.node_id for node in bundle.resource_nodes.for_world(actor.world_id)
            if node.location_id is None or node.location_id == location_id
        )
        actor_ids = tuple(
            other.actor_id
            for other in bundle.actors.for_world(actor.world_id)
            if other.location_id == location_id
        )
        return self._complete_timed_action(
            ActionType.INTERACT,
            actor_id,
            lambda: LocationInteractionView(
                actor_id, location.location_id, location.name, actor.character_id,
                resource_node_ids, actor_ids,
            ),
        )

    def start_gathering_at_location(
        self, actor_id: str, location_id: str, node_id: str,
        inventory_id: str, quantity: Quantity, activity_id: str | None = None,
    ) -> ActivityView:
        """Gather only after validating the actor's location interaction."""
        self.interact_with_location(actor_id, location_id)
        node = self._current_bundle().resource_nodes.get(node_id)
        if node is None:
            raise KeyError(f"Resource node not found: {node_id}")
        if node.location_id is not None and node.location_id != location_id:
            raise GameplayServiceError(f"Resource node is not at location: {location_id}")
        return self.start_gathering(actor_id, node_id, inventory_id, quantity, activity_id)

    def start_actor_production(
        self,
        actor_id: str,
        recipe_id: str,
        inventory_id: str,
        facility_id: str,
        activity_id: str | None = None,
    ) -> ActivityView:
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        return bundle.actor_activities.start_production(
            activity_id, actor_id, recipe_id, inventory_id, facility_id, self,
        )

    def cancel_activity(self, activity_id: str, reason: str = "cancelled") -> ActivityView:
        return self._current_bundle().actor_activities.cancel(activity_id, reason)

    def activity(self, activity_id: str) -> ActivityView | None:
        return self._current_bundle().actor_activities.get(activity_id)

    def actor_activity(self, actor_id: str) -> ActivityView | None:
        actor = self._current_bundle().actors.get(actor_id)
        if actor is None or actor.activity_id is None:
            return None
        return self.activity(actor.activity_id)

    def inventory(self, inventory_id: str) -> InventoryView:
        bundle = self._current_bundle()
        inventory = self._inventory(bundle, inventory_id)
        return InventoryView(
            inventory_id,
            tuple((resource.value, quantity.value, quantity.unit.value)
                  for resource, quantity in inventory.snapshot()),
            inventory.item_snapshot(),
            inventory.total_weight(bundle.items),
        )

    def consume_item(self, actor_id: str, inventory_id: str, resource_id: str) -> int:
        """Consume one item and apply its supported character effect."""
        bundle = self._current_bundle()
        character = self.actor_character(actor_id)
        if character is None:
            raise GameplayServiceError("Actor must be linked to a character to consume items.")
        resource = ResourceType(resource_id)
        effects = {"bread": 2, "water": 1}
        healing = effects.get(resource.value)
        if healing is None:
            raise GameplayServiceError(f"Resource is not consumable: {resource_id}")
        inventory = self._inventory(bundle, inventory_id)
        return self._complete_timed_action(
            ActionType.CONSUME_ITEM,
            actor_id,
            lambda: self._consume_and_apply(
                inventory, resource, character, healing,
            ),
        )

    @staticmethod
    def _consume_and_apply(inventory, resource, character, healing: int) -> int:
        inventory.remove(resource, Quantity(1, ResourceUnit.ITEM))
        character.current_hit_points = min(
            character.max_hit_points,
            character.current_hit_points + healing,
        )
        return character.current_hit_points

    def balance(self, account_id: str, currency_id: str) -> Money:
        bundle = self._current_bundle()
        return bundle.economy.ledger.balance(account_id, Currency(currency_id))

    def credit(self, account_id: str, currency_id: str, amount: int) -> Money:
        bundle = self._current_bundle()
        bundle.economy.ledger.credit(account_id, Money(amount, Currency(currency_id)), "application credit")
        return self.balance(account_id, currency_id)

    def exchange_currency(
        self, account_id: str, source_currency_id: str,
        target_currency_id: str, amount: int,
    ) -> Money:
        """Exchange an exact amount of one coin denomination for another."""
        bundle = self._current_bundle()
        source = Money(amount, Currency(source_currency_id))
        return bundle.economy.exchange_currency(
            account_id, source, Currency(target_currency_id),
        )

    def publish_offer(
        self, offer_id: str, seller_id: str, seller_inventory_id: str,
        resource_type: ResourceType, quantity: int, unit_price: Money, expires_at: int | None = None,
        market_id: str = "default",
    ) -> MarketOffer:
        bundle = self._current_bundle()
        self._inventory(bundle, seller_inventory_id)
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        stock = bundle.inventories[seller_inventory_id].get(resource_type)
        reserved = bundle.economy.market.reserved_quantity(seller_inventory_id, resource_type)
        if stock is None or stock.value - reserved < quantity:
            raise GameplayServiceError("Seller inventory cannot reserve the offered quantity.")
        offer = MarketOffer(offer_id, seller_id, resource_type, quantity, unit_price, seller_inventory_id, expires_at, market_id)
        bundle.economy.market.publish(offer)
        return offer

    def register_merchant(self, merchant: Merchant) -> Merchant:
        return self._current_bundle().economy.register_merchant(merchant)

    def buy_offer(self, offer_id: str, buyer_id: str, buyer_inventory_id: str, quantity: int | None = None):
        bundle = self._current_bundle()
        offer = bundle.economy.market.get(offer_id)
        if offer is None:
            raise KeyError(f"Market offer not found: {offer_id}")
        if offer.inventory_id is None:
            raise GameplayServiceError("Market offer has no seller inventory.")
        profile = bundle.economy.market.profile(offer.market_id)
        if profile is not None:
            self._require_actor_in_active_world(bundle, buyer_id)
            buyer_actor = bundle.actors.get(buyer_id)
            if buyer_actor.location_id != profile.location_id:
                raise GameplayServiceError(
                    "Buyer must be at the market's registered location."
                )
        buyer_inventory = self._inventory(bundle, buyer_inventory_id)
        seller_inventory = self._inventory(bundle, offer.inventory_id)
        stock = seller_inventory.get(offer.resource_type)
        if stock is None:
            raise GameplayServiceError("Seller inventory does not contain the offered resource.")
        purchased = offer.quantity if quantity is None else quantity
        if isinstance(purchased, bool) or not isinstance(purchased, int) or purchased <= 0 or purchased > offer.quantity:
            raise GameplayServiceError("Purchase quantity is invalid for this offer.")
        def execute_trade():
            trade = TradeService(bundle.economy.ledger).execute(
                buyer_id, offer.seller_id, buyer_inventory, seller_inventory,
                offer.resource_type,
                Quantity(purchased, stock.unit),
                offer.unit_price,
            )
            if bundle.economy.market.profile(offer.market_id) is not None:
                bundle.economy.market.record_purchase(
                    offer.market_id, offer.resource_type, purchased,
                )
            bundle.economy.market.withdraw(offer_id)
            if purchased < offer.quantity:
                bundle.economy.market.publish(MarketOffer(
                    offer.offer_id, offer.seller_id, offer.resource_type,
                    offer.quantity - purchased, offer.unit_price,
                    offer.inventory_id, offer.expires_at, offer.market_id,
                ))
            self._advance_quests(
                "collect", offer.resource_type.value, purchased,
                buyer_id, buyer_inventory_id,
            )
            return trade

        return self._complete_timed_action(ActionType.TRADE, buyer_id, execute_trade)

    def cancel_offer(self, offer_id: str, seller_id: str) -> MarketOffer:
        bundle = self._current_bundle()
        offer = bundle.economy.market.get(offer_id)
        if offer is None:
            raise KeyError(f"Market offer not found: {offer_id}")
        if offer.seller_id != seller_id:
            raise GameplayServiceError("Only the seller can cancel a market offer.")
        return bundle.economy.market.withdraw(offer_id)

    def register_market_profile(self, profile: MarketProfile, inventory: Inventory | None = None) -> MarketProfile:
        bundle = self._current_bundle()
        if not isinstance(profile, MarketProfile):
            raise TypeError("profile must be MarketProfile.")
        inventories = dict(bundle.inventories)
        if profile.inventory_id in inventories:
            if inventory is not None and inventories[profile.inventory_id] is not inventory:
                raise ValueError(f"Market inventory already exists: {profile.inventory_id}")
            market_inventory = inventories[profile.inventory_id]
        else:
            market_inventory = inventory if inventory is not None else Inventory()
            inventories[profile.inventory_id] = market_inventory
            object.__setattr__(bundle, "inventories", MappingProxyType(inventories))
        existing_profile = bundle.economy.market.profile(profile.market_id)
        if existing_profile is not None:
            existing_config = (
                existing_profile.location_id, existing_profile.npc_id,
                existing_profile.merchant_id, existing_profile.inventory_id,
                existing_profile.restock_interval, existing_profile.catalog,
                existing_profile.visible_products,
            )
            requested_config = (
                profile.location_id, profile.npc_id, profile.merchant_id,
                profile.inventory_id, profile.restock_interval, profile.catalog,
                profile.visible_products,
            )
            if existing_config != requested_config:
                raise ValueError(f"Conflicting market profile: {profile.market_id}")
            profile = existing_profile
        else:
            bundle.economy.market.register_profile(profile)
        if profile.merchant_id not in bundle.economy.merchants:
            self.register_merchant(Merchant(
                profile.merchant_id, market_inventory,
                account_id=profile.merchant_id, inventory_id=profile.inventory_id,
            ))
        return profile

    def market_for_npc(self, npc_id: str):
        return self._current_bundle().economy.market.profile_for_npc(npc_id)

    def register_trade_partner(
        self, npc_id: str, merchant_id: str, inventory_id: str,
        accepted_resources, initial_gold: int, buyback_rate: int = 50,
        unit_prices=None,
    ) -> Merchant:
        bundle = self._current_bundle()
        npc = bundle.social.npcs.get(npc_id)
        if npc is None:
            raise KeyError(f"Trade partner NPC not found: {npc_id}")
        resources = tuple(
            value if isinstance(value, ResourceType) else ResourceType(value)
            for value in accepted_resources
        )
        inventories = dict(bundle.inventories)
        inventory = inventories.get(inventory_id)
        if inventory is None:
            inventory = Inventory()
            inventories[inventory_id] = inventory
            object.__setattr__(bundle, "inventories", MappingProxyType(inventories))
        existing = bundle.economy.merchants.get(merchant_id)
        is_new_partner = existing is None
        if existing is None:
            merchant = Merchant(
                merchant_id, inventory, account_id=merchant_id,
                inventory_id=inventory_id, npc_id=npc_id,
                accepted_resources=resources, buyback_rate=buyback_rate,
            )
            bundle.economy.register_merchant(merchant)
        else:
            if (
                existing.npc_id != npc_id
                or existing.inventory_id != inventory_id
                or existing.accepted_resources != resources
                or existing.buyback_rate != buyback_rate
            ):
                raise ValueError(f"Conflicting trade partner profile: {npc_id}")
            merchant = existing
            merchant.inventory = inventory
        currency = Currency("gold")
        if isinstance(initial_gold, bool) or not isinstance(initial_gold, int) or initial_gold < 0:
            raise ValueError("initial_gold must be a non-negative integer.")
        if is_new_partner and initial_gold:
            bundle.economy.ledger.credit(
                merchant.account_id, Money(initial_gold, currency), "trade_partner_funding",
            )
        for resource_id, amount in (unit_prices or {}).items():
            if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
                raise ValueError("Trade unit prices must be positive integers.")
            bundle.economy.market.prices.set(
                ResourceType(resource_id), Money(amount, currency),
            )
        return merchant

    def trade_partner_for_npc(self, npc_id: str) -> Merchant | None:
        return next(
            (merchant for merchant in self._current_bundle().economy.merchants.values()
             if merchant.npc_id == npc_id and merchant.accepted_resources),
            None,
        )

    def trade_sellable_items(self, npc_id: str, inventory_id: str = "player"):
        bundle = self._current_bundle()
        merchant = self.trade_partner_for_npc(npc_id)
        if merchant is None:
            raise KeyError(f"NPC has no trade profile: {npc_id}")
        inventory = self._inventory(bundle, inventory_id)
        currency = Currency("gold")
        quotes = []
        for resource_type in merchant.accepted_resources:
            stock = inventory.get(resource_type)
            price = bundle.economy.market.prices.get(resource_type, currency)
            if stock is None or stock.value <= 0 or price is None:
                continue
            amount = max(1, price.money.amount * merchant.buyback_rate // 100)
            if bundle.economy.ledger.balance(merchant.account_id, currency).amount < amount:
                continue
            quotes.append((resource_type, stock.value, Money(amount, currency)))
        return tuple(quotes)

    def sell_to_npc(
        self, npc_id: str, resource_type: ResourceType, quantity: int = 1,
        actor_id: str = "hero", inventory_id: str = "player",
    ):
        bundle = self._current_bundle()
        merchant = self.trade_partner_for_npc(npc_id)
        if merchant is None:
            raise KeyError(f"NPC has no trade profile: {npc_id}")
        npc = bundle.social.npcs.get(npc_id)
        self._require_actor_in_active_world(bundle, actor_id)
        actor = bundle.actors.get(actor_id)
        if actor.location_id != npc.location_id:
            raise GameplayServiceError("Player must be at the NPC's location to trade.")
        if resource_type not in merchant.accepted_resources:
            raise GameplayServiceError("This NPC does not buy that resource.")
        seller_inventory = self._inventory(bundle, inventory_id)
        stock = seller_inventory.get(resource_type)
        if stock is None or quantity <= 0 or quantity > stock.value:
            raise GameplayServiceError("Trade quantity exceeds available player stock.")
        quote = bundle.economy.market.prices.get(resource_type, Currency("gold"))
        if quote is None:
            raise GameplayServiceError("No trade price is configured for this resource.")
        unit_price = Money(
            max(1, quote.money.amount * merchant.buyback_rate // 100),
            quote.money.currency,
        )
        return TradeService(bundle.economy.ledger).execute(
            merchant.account_id, actor_id, merchant.inventory, seller_inventory,
            resource_type, Quantity(quantity, stock.unit), unit_price,
        )

    def market_offers(self, market_id: str | None = None) -> tuple[MarketOffer, ...]:
        bundle = self._current_bundle()
        if market_id is not None:
            profile = bundle.economy.market.profile(market_id)
            if profile is None:
                raise KeyError(f"Market not found: {market_id}")
            self._require_actor_in_active_world(bundle, "hero")
            actor = bundle.actors.get("hero")
            if actor.location_id != profile.location_id:
                raise GameplayServiceError(
                    "Player must be at the market's registered location."
                )
            inventory = self._inventory(bundle, profile.inventory_id)
            bundle.economy.market.restock(
                market_id, inventory, bundle.simulation.current_tick.value,
            )
        return bundle.economy.market.offers(market_id)

    def expire_market_offers(self, current_tick: int | None = None):
        tick = self._current_bundle().simulation.current_tick.value if current_tick is None else current_tick
        return self._current_bundle().economy.market.expire(tick)

    def register_npc(self, npc: NPC) -> NPC:
        return self._current_bundle().social.add_npc(npc)

    def register_faction(self, faction: Faction) -> Faction:
        return self._current_bundle().social.add_faction(faction)

    def change_reputation(self, faction_id: str, amount: int) -> int:
        return self._current_bundle().social.change_reputation(faction_id, amount)

    def reputation(self, faction_id: str) -> tuple[int, str]:
        ledger = self._current_bundle().social.reputation
        return ledger.get(faction_id), ledger.tier(faction_id)

    def relationship(self, source_id: str, target_id: str):
        return self._current_bundle().social.relation(source_id, target_id)

    def register_dialogue(self, dialogue: Dialogue) -> Dialogue:
        return self._current_bundle().social.add_dialogue(dialogue)
    def register_dialogue_action(
        self,
        action_id: str,
        handler: Callable[[str, str], None],
    ) -> None:
        """Register a reusable handler for a dialogue action."""
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("action_id must be a non-empty string.")
        if not callable(handler):
            raise TypeError("handler must be callable.")
        if action_id in self._dialogue_actions:
            raise ValueError(f"Dialogue action already registered: {action_id}")

        self._dialogue_actions[action_id] = handler

    def talk_to_npc(self, actor_id: str, npc_id: str, dialogue_id: str, node_id: str | None = None):
        bundle = self._current_bundle()
        self._require_actor_in_active_world(bundle, actor_id)
        actor = bundle.actors.get(actor_id)
        npc = bundle.social.npcs.get(npc_id)
        if npc is None:
            raise KeyError(f"NPC not found: {npc_id}")
        if npc.location_id is not None and npc.location_id != actor.location_id:
            raise GameplayServiceError("Actor and NPC must be at the same location.")
        dialogue = bundle.social.dialogues.get(dialogue_id)
        if dialogue is None:
            raise KeyError(f"Dialogue not found: {dialogue_id}")
        selected_node_id = node_id or dialogue.start_node_id

        def read_node():
            result = bundle.social.node_for(
                dialogue_id,
                selected_node_id,
                self._dialogue_context(actor_id, npc_id),
            )
            self._advance_quests("talk", npc_id, 1, actor_id, None)
            return result

        return self._complete_timed_action(ActionType.DIALOGUE, actor_id, read_node)

    def choose_dialogue(self, actor_id: str, npc_id: str, dialogue_id: str, node_id: str, choice_id: str):
        bundle = self._current_bundle()
        dialogue = bundle.social.dialogues.get(dialogue_id)
        if dialogue is None: raise KeyError(f"Dialogue not found: {dialogue_id}")
        choice = next(
            (
                item for item in dialogue.available_choices(
                    node_id, self._dialogue_context(actor_id, npc_id)
                )
                if item.choice_id == choice_id
            ),
            None,
        )
        if choice is None: raise ValueError(f"Dialogue choice not available: {choice_id}")
        def choose():
            bundle.social.change_relationship(actor_id, npc_id, value=2, trust=1)
            self._run_dialogue_action(choice.action or choice_id, actor_id, npc_id)
            if choice.next_node_id is None:
                return None
            return bundle.social.node_for(
                dialogue_id,
                choice.next_node_id,
                self._dialogue_context(actor_id, npc_id),
            )

        return self._complete_timed_action(ActionType.DIALOGUE_CHOICE, actor_id, choose)

    def _dialogue_context(self, actor_id: str, npc_id: str) -> dict:
        bundle = self._current_bundle()
        objectives = {}
        quests = bundle.quest_log.all()
        for quest in quests:
            try:
                quest_objectives = getattr(quest, "objectives", ()) or ()
                for objective in quest_objectives:
                    objective_id = getattr(objective, "objective_id", None)
                    progress = getattr(objective, "progress", None)
                    if (
                        isinstance(objective_id, str)
                        and objective_id
                        and isinstance(progress, int)
                        and not isinstance(progress, bool)
                    ):
                        objectives[objective_id] = progress
            except (AttributeError, TypeError, ValueError, RuntimeError):
                continue

        items = {}
        try:
            items = {
                getattr(resource, "value", str(resource)): amount
                for resource, amount, _unit in self.inventory("player").stocks
            }
        except (KeyError, ValueError, RuntimeError, AttributeError, TypeError):
            pass

        flags = {}
        for quest in quests:
            quest_id = getattr(quest, "quest_id", None)
            state = getattr(getattr(quest, "state", None), "value", None)
            if isinstance(quest_id, str) and quest_id and isinstance(state, str):
                flags[f"quest:{quest_id}"] = state

        return {
            "actor_id": actor_id,
            "npc_id": npc_id,
            "objectives": objectives,
            "items": items,
            "flags": flags,
        }

    def _run_dialogue_action(self, action: str, actor_id: str, npc_id: str) -> None:
        actions = {
            "accept_carpenter_quest": lambda: self.accept_carpenter_quest(actor_id, "player"),
            "deliver_carpenter_wood": lambda: self.deliver_carpenter_wood(actor_id, npc_id, "player"),
            "accept_inn_quest": lambda: self.accept_inn_quest(actor_id, "player"),
            "deliver_inn_supplies": lambda: self.deliver_inn_supplies(actor_id, npc_id, "player"),
            "accept_blacksmith_quest": lambda: self.accept_blacksmith_quest(actor_id, "player"),
            "deliver_blacksmith_ore": lambda: self.deliver_blacksmith_ore(actor_id, npc_id, "player"),
            "accept_caravan_quest": lambda: self.accept_caravan_quest(actor_id, "player"),
        }
        handler = actions.get(action)
        if handler is not None:
            handler()

    def start_quest(self, quest: Quest, context=None, owner_id: str | None = None, reward_inventory_id: str | None = None) -> Quest:
        bundle = self._current_bundle()
        quest.start(context or {})
        registered = bundle.quest_log.get(quest.quest_id)
        if registered is None:
            bundle.quest_log.add(quest)
        elif registered is not quest:
            raise ValueError(f"Quest ID is already registered: {quest.quest_id}")
        if owner_id is not None:
            self._quest_reward_accounts[quest.quest_id] = owner_id
        if reward_inventory_id is not None:
            self._quest_reward_inventories[quest.quest_id] = reward_inventory_id
        return quest

    def accept_carpenter_quest(self, owner_id: str, inventory_id: str):
        quest = getattr(self, "carpenter_quest", None)
        if quest is None:
            raise RuntimeError("Marangoz görevi bulunamadı.")
        if quest.state.value == "active":
            return quest
        if quest.state.value == "completed":
            raise ValueError("Marangoz görevi zaten tamamlandı.")
        return self.start_quest(
            quest, owner_id=owner_id, reward_inventory_id=inventory_id,
        )

    def deliver_carpenter_wood(self, actor_id: str, npc_id: str, inventory_id: str):
        quest = getattr(self, "carpenter_quest", None)
        if quest is None or quest.state.value != "active":
            raise ValueError("Hilmi'nin aktif bir odun görevi yok.")
        if npc_id != "village_carpenter":
            raise ValueError("Odun yalnızca Marangoz Hilmi'ye teslim edilebilir.")
        inventory = self._inventory(self._current_bundle(), inventory_id)
        wood = ResourceType("wood")
        stock = inventory.get(wood)
        if stock is None or stock.value < 3:
            raise ValueError("Teslim etmek için en az 3 odun gerekli.")
        inventory.remove(wood, Quantity(3, ResourceUnit.ITEM))
        self.update_quest_objective(
            quest.quest_id, "deliver_wood", 1, actor_id, inventory_id,
        )
        return quest

    def accept_inn_quest(self, owner_id: str, inventory_id: str):
        quest = getattr(self, "inn_quest", None)
        if quest is None:
            raise RuntimeError("Han görevi bulunamadı.")
        if quest.state.value == "active":
            return quest
        if quest.state.value == "completed":
            raise ValueError("Han görevi zaten tamamlandı.")
        carpenter = getattr(self, "carpenter_quest", None)
        if carpenter is None or carpenter.state.value != "completed":
            raise ValueError("Önce Hilmi'nin odun görevini tamamlamalısın.")
        return self.start_quest(
            quest, owner_id=owner_id, reward_inventory_id=inventory_id,
        )

    def accept_blacksmith_quest(self, owner_id: str, inventory_id: str):
        quest = getattr(self, "blacksmith_quest", None)
        if quest is None:
            raise RuntimeError("Demirci görevi bulunamadı.")
        if quest.state.value == "active":
            return quest
        if quest.state.value == "completed":
            raise ValueError("Demirci görevi zaten tamamlandı.")
        return self.start_quest(quest, owner_id=owner_id, reward_inventory_id=inventory_id)

    def deliver_blacksmith_ore(self, actor_id: str, npc_id: str, inventory_id: str):
        quest = getattr(self, "blacksmith_quest", None)
        if quest is None or quest.state.value != "active":
            raise ValueError("Demircinin aktif bir cevher görevi yok.")
        if npc_id != "village_blacksmith":
            raise ValueError("Demir cevheri yalnızca demirciye teslim edilebilir.")
        inventory = self._inventory(self._current_bundle(), inventory_id)
        ore = ResourceType("iron_ore")
        stock = inventory.get(ore)
        if stock is None or stock.value < 3:
            raise ValueError("Teslim etmek için en az 3 demir cevheri gerekli.")
        inventory.remove(ore, Quantity(3, ResourceUnit.ITEM))
        self.update_quest_objective(
            quest.quest_id, "deliver_iron_ore", 1, actor_id, inventory_id,
        )
        return quest

    def deliver_inn_supplies(self, actor_id: str, npc_id: str, inventory_id: str):
        quest = getattr(self, "inn_quest", None)
        if quest is None or quest.state.value != "active":
            raise ValueError("Hilmi'nin aktif bir han görevi yok.")
        if npc_id != "village_carpenter":
            raise ValueError("Erzaklar Hilmi'ye teslim edilmelidir.")
        inventory = self._inventory(self._current_bundle(), inventory_id)
        bread = inventory.get(ResourceType("bread"))
        water = inventory.get(ResourceType("water"))
        if bread is None or bread.value < 1 or water is None or water.value < 1:
            raise ValueError("Teslim etmek için 1 ekmek ve 1 su gerekli.")
        inventory.remove(ResourceType("bread"), Quantity(1, ResourceUnit.ITEM))
        inventory.remove(ResourceType("water"), Quantity(1, ResourceUnit.ITEM))
        self.update_quest_objective(
            quest.quest_id, "deliver_supplies", 1, actor_id, inventory_id,
        )
        return quest

    def update_quest_objective(self, quest_id: str, objective_id: str, amount: int = 1, owner_id: str | None = None, inventory_id: str | None = None):
        bundle = self._current_bundle()
        quest = bundle.quest_log.get(quest_id)
        if quest is None:
            raise KeyError(f"Quest not found: {quest_id}")
        previous = quest.state
        quest.update(objective_id, amount)
        if previous != quest.state and quest.state.value == "completed":
            self._grant_quest_reward(quest, owner_id, inventory_id)
        return quest.state

    def grant_experience(self, actor_id: str, amount: int) -> int:
        """Award XP through the canonical character progression model."""
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError("Experience must be a non-negative integer.")
        character = self.actor_character(actor_id)
        if character is None:
            raise KeyError(f"Character not found for actor: {actor_id}")
        return character.progression.add_experience(amount)

    def improve_skill(self, actor_id: str, skill: str) -> int:
        """Spend one earned progression point on a class skill."""
        character = self.actor_character(actor_id)
        if character is None:
            raise KeyError(f"Character not found for actor: {actor_id}")
        character.progression.spend_point()
        try:
            character.skills = character.skills.improve(skill)
        except (KeyError, TypeError, ValueError):
            character.progression.unspent_points += 1
            raise
        return character.skills.get(skill)

    def add_combatant(self, combatant: Combatant) -> Combatant:
        self._current_bundle().combat.add(combatant)
        return combatant

    def create_combat_encounter(self, encounter_id: str, combatant_ids, initiative_scores=None):
        return self._current_bundle().combat.create_encounter(encounter_id, combatant_ids, initiative_scores)

    def next_combat_turn(self, encounter_id: str):
        return self._complete_timed_action(
            ActionType.COMBAT_TURN,
            "combat",
            lambda: self._current_bundle().combat.next_turn(encounter_id),
        )

    def combat_attack(self, attacker_id: str, defender_id: str):
        def attack():
            combat = self._current_bundle().combat
            attacker = combat.get(attacker_id)
            defender = combat.get(defender_id)
            if attacker is None:
                raise KeyError(f"Combatant not found: {attacker_id}")
            if defender is None:
                raise KeyError(f"Combatant not found: {defender_id}")
            attacker_character = self.actor_character(attacker_id)
            defender_character = self.actor_character(defender_id)
            weapon_bonus = attacker_character.weapon_damage if attacker_character else 0
            armor_bonus = defender_character.defense_bonus if defender_character else 0
            attacker.attack += weapon_bonus
            defender.defense += armor_bonus
            try:
                result = combat.attack_once(attacker_id, defender_id)
            finally:
                attacker.attack -= weapon_bonus
                defender.defense -= armor_bonus
            if result.defender_defeated:
                self._advance_quests("kill", defender_id, 1, attacker_id, None)
            return result

        return self._complete_timed_action(ActionType.COMBAT_ATTACK, attacker_id, attack)

    def advance_combat_round(self, actor_id: str = "combat") -> None:
        self._complete_timed_action(
            ActionType.COMBAT_TURN,
            actor_id,
            self._current_bundle().combat.advance_round,
        )

    def _advance_quests(self, objective_type: str, target_id: str, amount: int, owner_id: str | None, inventory_id: str | None):
        for quest in self._current_bundle().quest_log.active():
            for objective in quest.objectives:
                target_matches = objective.target_id is None or objective.target_id == target_id
                if (
                    objective_type == "collect"
                    and not target_matches
                    and objective.target_id is not None
                ):
                    source = self._current_bundle().resource_nodes.get(objective.target_id)
                    gathered = self._current_bundle().resource_nodes.get(target_id)
                    target_matches = (
                        source is not None
                        and gathered is not None
                        and source.resource_type == gathered.resource_type
                    )
                if objective.objective_type.value == objective_type and target_matches:
                    self.update_quest_objective(quest.quest_id, objective.objective_id, amount, owner_id, inventory_id)

    def _grant_quest_reward(self, quest: Quest, owner_id: str | None, inventory_id: str | None) -> None:
        bundle = self._current_bundle()
        account_id = owner_id or self._quest_reward_accounts.get(quest.quest_id)
        if quest.reward.experience and account_id:
            self.grant_experience(account_id, quest.reward.experience)
        if quest.reward.currency and account_id:
            bundle.economy.ledger.credit(account_id, Money(quest.reward.currency, Currency("gold")), "quest reward")
        target_inventory_id = inventory_id or self._quest_reward_inventories.get(quest.quest_id)
        if target_inventory_id and quest.reward.items:
            inventory = self._inventory(bundle, target_inventory_id)
            for resource_id, amount in quest.reward.items:
                inventory.add(ResourceType(resource_id), Quantity(amount, ResourceUnit.ITEM))
        for faction_id, amount in quest.reward.reputation:
            bundle.social.change_reputation(faction_id, amount)

    def state(self) -> GameplaySnapshotView:
        """Return a deterministic read-only view without mutating the session."""
        bundle = self._current_bundle()
        world = bundle.session.worlds.get_active()
        inventories = tuple(self.inventory(inventory_id) for inventory_id in sorted(bundle.inventories))
        nodes = tuple(
            ResourceNodeView(
                node.node_id,
                node.world_id,
                node.resource_type.value,
                (node.quantity.value, node.quantity.unit.value),
                (node.capacity.value, node.capacity.unit.value),
                (node.regeneration_rate.value, node.regeneration_rate.unit.value),
                node.last_simulation_tick.value,
                node.location_id,
            )
            for node in bundle.resource_nodes.nodes()
        )
        facilities = tuple(
            FacilityView(
                facility.facility_id,
                facility.facility_type,
                facility.active,
                facility.capabilities,
                facility.capacity.capacity,
                facility.capacity.reserved,
                facility.active_job_ids,
            )
            for facility in bundle.facilities.facilities()
        )
        inventory_ids = {id(inventory): inventory_id for inventory_id, inventory in bundle.inventories.items()}
        jobs = tuple(
            JobView(
                job.job_id,
                job.recipe.recipe_id,
                inventory_ids[id(job.inventory)],
                job.state.value,
                job.start_tick.value,
                job.end_tick.value,
            )
            for job in bundle.production_jobs.jobs()
        )
        chains = tuple(
            ChainView(
                chain.chain_id,
                chain.state.value,
                chain.current_stage_index,
                tuple(job.job_id for job in chain.jobs),
            )
            for chain in (self._chains[key] for key in sorted(self._chains))
        )
        return GameplaySnapshotView(
            None if world is None else world.world_id,
            bundle.simulation.current_tick.value,
            inventories,
            nodes,
            facilities,
            jobs,
            chains,
            self._current_bundle().actors.actors(),
            self._current_bundle().actor_activities.activities(),
            self._current_bundle().movement.movements(),
        )

    def actors_state(self) -> tuple[ActorView, ...]:
        return self._current_bundle().actors.actors()

    def activities_state(self) -> tuple[ActivityView, ...]:
        return self._current_bundle().actor_activities.activities()

    def _current_bundle(self):
        bundle = self._application.holder.current
        if bundle is not self._bundle:
            for chain in self._chains.values():
                chain.dispose()
            self._chains.clear()
            self._bundle = bundle
        return bundle

    @staticmethod
    def _require_active_world(bundle):
        if bundle.session.worlds.get_active() is None:
            raise GameplayServiceError("An active world is required.")

    @staticmethod
    def _inventory(bundle, inventory_id: str) -> Inventory:
        if not isinstance(inventory_id, str) or not inventory_id.strip():
            raise TypeError("inventory_id must be a non-empty string.")
        inventory = bundle.inventories.get(inventory_id)
        if inventory is None:
            raise KeyError(f"Inventory not found: {inventory_id}")
        return inventory

    @staticmethod
    def _recipe(bundle, recipe_id: str) -> Recipe:
        if not isinstance(recipe_id, str) or not recipe_id.strip():
            raise TypeError("recipe_id must be a non-empty string.")
        recipe = bundle.recipes.get(recipe_id)
        if recipe is None:
            raise KeyError(f"Recipe not found: {recipe_id}")
        return recipe

    @staticmethod
    def _require_actor_in_active_world(bundle, actor_id: str):
        world = bundle.session.worlds.get_active()
        if world is None:
            raise GameplayServiceError("An active world is required.")
        actor = bundle.actors.get(actor_id)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        if not actor.active:
            raise GameplayServiceError(f"Actor is inactive: {actor_id}")
        if actor.world_id != world.world_id:
            raise GameplayServiceError(
                f"Actor {actor_id} does not belong to the active world."
            )

    @staticmethod
    def _normalize_stage(stage) -> GameplayChainStage:
        if isinstance(stage, GameplayChainStage):
            return stage
        if isinstance(stage, (tuple, list)) and len(stage) == 3:
            return GameplayChainStage(*stage)
        raise TypeError(
            "chain stages must be GameplayChainStage or (recipe_id, inventory_id, facility_id)."
        )


__all__ = [
    "GameplayService",
    "GameplayServiceError",
    "GameplayChainStage",
    "InventoryView",
    "ResourceNodeView",
    "LocationInteractionView",
    "FacilityView",
    "JobView",
    "ChainView",
    "GameplaySnapshotView",
    "ContainerView",
    "LockAttemptResult",
]
