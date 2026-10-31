"""Application-level playable gameplay loop orchestration.

This service deliberately owns no canonical gameplay state.  It resolves the
current SessionBundle for each operation and delegates mutations to the
resource, production and canonical simulation components that already own
those rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.time import Tick

from resources import Inventory, Quantity, Recipe, ResourceType, ResourceUnit
from economy import Currency, MarketOffer, Money, TradeService, Merchant

from .game_application import GameApplication
from .production_chain import ProductionChain, ProductionChainStage
from .actor_system import ActivityView, ActorView, WorldActor
from .movement import MovementManager
from world import WorldMap
from npc import Faction, NPC
from quests import Dialogue, Quest
from .social_runtime import SocialRuntimeError
from .combat_runtime import Combatant


class GameplayServiceError(RuntimeError):
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
        self._rebind_content_quests()
        return result

    def _rebind_content_quests(self) -> None:
        """Reconnect optional content aliases to the restored canonical quest log."""
        quest_log = self._current_bundle().quest_log
        for attribute in ("available_forest_quest", "carpenter_quest", "inn_quest", "blacksmith_quest"):
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

    def register_actor(self, actor_id: str, role: str, world_id: str | None = None, active: bool = True, character_id: str | None = None) -> ActorView:
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
        actor = WorldActor(actor_id, target_world, role, active)
        bundle.actors.add(actor)
        if character is not None:
            bundle.actors.bind_character(actor_id, character)
        bundle.validate()
        return actor.view()

    def bind_actor_character(self, actor_id: str, character_id: str) -> ActorView:
        """Bind an existing actor and character while checking both sides."""
        bundle = self._current_bundle()
        character = bundle.characters.get(character_id)
        if character is None:
            raise KeyError(f"Character not found: {character_id}")
        bundle.actors.bind_character(actor_id, character)
        bundle.validate()
        return bundle.actors.get(actor_id)

    def register_world_map(self, world_map: WorldMap) -> None:
        """Register the application movement graph for a world."""
        self._current_bundle().movement.register_map(world_map)

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
            "attributes": character.attributes.to_dict(),
            "skills": character.skills.to_dict(),
            "level": character.progression.level,
            "current_hit_points": character.current_hit_points,
            "max_hit_points": character.max_hit_points,
        }

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
        return LocationInteractionView(
            actor_id, location.location_id, location.name, actor.character_id,
            resource_node_ids, actor_ids,
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

    def inventory(self, inventory_id: str) -> InventoryView:
        bundle = self._current_bundle()
        inventory = self._inventory(bundle, inventory_id)
        return InventoryView(
            inventory_id,
            tuple((resource.value, quantity.value, quantity.unit.value)
                  for resource, quantity in inventory.snapshot()),
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

    def publish_offer(
        self, offer_id: str, seller_id: str, seller_inventory_id: str,
        resource_type: ResourceType, quantity: int, unit_price: Money, expires_at: int | None = None,
    ) -> MarketOffer:
        bundle = self._current_bundle()
        self._inventory(bundle, seller_inventory_id)
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        stock = bundle.inventories[seller_inventory_id].get(resource_type)
        reserved = bundle.economy.market.reserved_quantity(seller_inventory_id, resource_type)
        if stock is None or stock.value - reserved < quantity:
            raise GameplayServiceError("Seller inventory cannot reserve the offered quantity.")
        offer = MarketOffer(offer_id, seller_id, resource_type, quantity, unit_price, seller_inventory_id, expires_at)
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
        buyer_inventory = self._inventory(bundle, buyer_inventory_id)
        seller_inventory = self._inventory(bundle, offer.inventory_id)
        stock = seller_inventory.get(offer.resource_type)
        if stock is None:
            raise GameplayServiceError("Seller inventory does not contain the offered resource.")
        purchased = offer.quantity if quantity is None else quantity
        if isinstance(purchased, bool) or not isinstance(purchased, int) or purchased <= 0 or purchased > offer.quantity:
            raise GameplayServiceError("Purchase quantity is invalid for this offer.")
        trade = TradeService(bundle.economy.ledger).execute(
            buyer_id, offer.seller_id, buyer_inventory, seller_inventory,
            offer.resource_type,
            Quantity(purchased, stock.unit),
            offer.unit_price,
        )
        bundle.economy.market.withdraw(offer_id)
        if purchased < offer.quantity:
            bundle.economy.market.publish(MarketOffer(
                offer.offer_id, offer.seller_id, offer.resource_type,
                offer.quantity - purchased, offer.unit_price,
                offer.inventory_id, offer.expires_at,
            ))
        self._advance_quests(
            "collect", offer.resource_type.value, purchased,
            buyer_id, buyer_inventory_id,
        )
        return trade

    def cancel_offer(self, offer_id: str, seller_id: str) -> MarketOffer:
        bundle = self._current_bundle()
        offer = bundle.economy.market.get(offer_id)
        if offer is None:
            raise KeyError(f"Market offer not found: {offer_id}")
        if offer.seller_id != seller_id:
            raise GameplayServiceError("Only the seller can cancel a market offer.")
        return bundle.economy.market.withdraw(offer_id)

    def market_offers(self) -> tuple[MarketOffer, ...]:
        return self._current_bundle().economy.market.offers()

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
        result = bundle.social.node_for(
            dialogue_id,
            node_id or dialogue.start_node_id,
            self._dialogue_context(actor_id, npc_id),
        )
        self._advance_quests("talk", npc_id, 1, actor_id, None)
        return result

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
        bundle.social.change_relationship(actor_id, npc_id, value=2, trust=1)
        self._run_dialogue_action(choice.action or choice_id, actor_id, npc_id)
        if choice.next_node_id is None: return None
        return self.talk_to_npc(actor_id, npc_id, dialogue_id, choice.next_node_id)

    def _dialogue_context(self, actor_id: str, npc_id: str) -> dict:
        bundle = self._current_bundle()
        objectives = {
            objective.objective_id: objective.progress
            for quest in bundle.quest_log.all()
            for objective in quest.objectives
        }
        items = {}
        try:
            items = {
                getattr(resource, "value", str(resource)): amount
                for resource, amount, _unit in self.inventory("player").stocks
            }
        except (KeyError, ValueError, RuntimeError):
            pass
        return {
            "actor_id": actor_id,
            "npc_id": npc_id,
            "objectives": objectives,
            "items": items,
            "flags": {
                f"quest:{quest.quest_id}": quest.state.value
                for quest in bundle.quest_log.all()
            },
        }

    def _run_dialogue_action(self, action: str, actor_id: str, npc_id: str) -> None:
        actions = {
            "accept_carpenter_quest": lambda: self.accept_carpenter_quest(actor_id, "player"),
            "deliver_carpenter_wood": lambda: self.deliver_carpenter_wood(actor_id, npc_id, "player"),
            "accept_inn_quest": lambda: self.accept_inn_quest(actor_id, "player"),
            "deliver_inn_supplies": lambda: self.deliver_inn_supplies(actor_id, npc_id, "player"),
            "accept_blacksmith_quest": lambda: self.accept_blacksmith_quest(actor_id, "player"),
            "deliver_blacksmith_ore": lambda: self.deliver_blacksmith_ore(actor_id, npc_id, "player"),
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

    def add_combatant(self, combatant: Combatant) -> Combatant:
        self._current_bundle().combat.add(combatant)
        return combatant

    def create_combat_encounter(self, encounter_id: str, combatant_ids, initiative_scores=None):
        return self._current_bundle().combat.create_encounter(encounter_id, combatant_ids, initiative_scores)

    def next_combat_turn(self, encounter_id: str):
        return self._current_bundle().combat.next_turn(encounter_id)

    def combat_attack(self, attacker_id: str, defender_id: str):
        result = self._current_bundle().combat.attack_once(attacker_id, defender_id)
        if result.defender_defeated:
            self._advance_quests("kill", defender_id, 1, attacker_id, None)
        return result

    def advance_combat_round(self) -> None:
        self._current_bundle().combat.advance_round()

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
]
