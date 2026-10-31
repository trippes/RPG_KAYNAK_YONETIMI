"""Runtime composition for a Core session and resource gameplay state."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from core.application import GameSession
from core.simulation import SimulationRuntime

from resources import Inventory, ProductionJobManager, Recipe, WorldResourceNodeManager

from .production_facility import ProductionFacilityRegistry
from .actor_system import ActorActivityManager, WorldActorRegistry
from .movement import MovementManager
from character import Character
from quests import QuestLog
from economy import Economy
from .social_runtime import SocialRuntime
from .combat_runtime import CombatRuntime


@dataclass(frozen=True)
class SessionBundle:
    """One independently owned Core/gameplay runtime composition."""

    session: GameSession
    simulation: SimulationRuntime
    production_jobs: ProductionJobManager
    resource_nodes: WorldResourceNodeManager
    inventories: Mapping[str, Inventory]
    recipes: Mapping[str, Recipe]
    facilities: ProductionFacilityRegistry | None = None
    actors: WorldActorRegistry | None = None
    actor_activities: ActorActivityManager | None = None
    characters: Mapping[str, Character] | None = None
    movement: MovementManager | None = None
    quest_log: QuestLog | None = None
    economy: Economy | None = None
    social: SocialRuntime | None = None
    combat: CombatRuntime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.session, GameSession):
            raise TypeError("session must be GameSession.")
        if not isinstance(self.simulation, SimulationRuntime):
            raise TypeError("simulation must be SimulationRuntime.")
        if not isinstance(self.production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        if not isinstance(self.resource_nodes, WorldResourceNodeManager):
            raise TypeError("resource_nodes must be WorldResourceNodeManager.")
        if not isinstance(self.inventories, Mapping):
            raise TypeError("inventories must be a mapping.")
        if not isinstance(self.recipes, Mapping):
            raise TypeError("recipes must be a mapping.")
        if self.characters is None:
            object.__setattr__(self, "characters", {})
        if not isinstance(self.characters, Mapping) or any(not isinstance(value, Character) for value in self.characters.values()):
            raise TypeError("characters must be a mapping of Character values.")
        for character_id, character in self.characters.items():
            if character_id != character.character_id:
                raise ValueError("character registry key must match character.character_id.")
        if self.facilities is None:
            object.__setattr__(self, "facilities", ProductionFacilityRegistry())
        if not isinstance(self.facilities, ProductionFacilityRegistry):
            raise TypeError("facilities must be ProductionFacilityRegistry.")
        self.facilities.validate()
        if self.actors is None:
            object.__setattr__(self, "actors", WorldActorRegistry(self.session.worlds))
        if not isinstance(self.actors, WorldActorRegistry):
            raise TypeError("actors must be WorldActorRegistry.")
        self.actors.bind_world_registry(self.session.worlds)
        self._validate_character_actor_links()
        if self.actor_activities is None:
            object.__setattr__(
                self,
                "actor_activities",
                ActorActivityManager(self.actors, self.production_jobs, self.facilities),
            )
        if not isinstance(self.actor_activities, ActorActivityManager):
            raise TypeError("actor_activities must be ActorActivityManager.")
        if self.actor_activities.actors is not self.actors:
            raise ValueError("actor_activities must use bundle actors.")
        if self.actor_activities.runtime is not self.simulation:
            raise ValueError("actor_activities must use the bundle simulation.")
        if self.actor_activities.production_jobs is not self.production_jobs:
            raise ValueError("actor_activities must use bundle production_jobs.")
        if self.actor_activities.facilities is not self.facilities:
            raise ValueError("actor_activities must use bundle facilities.")
        if self.movement is None:
            object.__setattr__(self, "movement", MovementManager(self.actors, self.simulation))
        if not isinstance(self.movement, MovementManager):
            raise TypeError("movement must be MovementManager.")
        if self.movement._actors is not self.actors or self.movement._runtime is not self.simulation:
            raise ValueError("movement must use bundle actors and simulation.")
        if self.quest_log is None:
            object.__setattr__(self, "quest_log", QuestLog())
        if not isinstance(self.quest_log, QuestLog):
            raise TypeError("quest_log must be QuestLog.")
        if self.economy is None:
            object.__setattr__(self, "economy", Economy())
        if not isinstance(self.economy, Economy):
            raise TypeError("economy must be Economy.")
        if self.social is None:
            object.__setattr__(self, "social", SocialRuntime())
        if not isinstance(self.social, SocialRuntime):
            raise TypeError("social must be SocialRuntime.")
        if self.combat is None:
            object.__setattr__(self, "combat", CombatRuntime())
        if not isinstance(self.combat, CombatRuntime):
            raise TypeError("combat must be CombatRuntime.")

        if self.simulation is not self.session.simulation:
            raise ValueError("simulation must be session.simulation.")
        if self.production_jobs.runtime is not self.simulation:
            raise ValueError("production_jobs must use the bundle simulation.")

        self.resource_nodes.bind_world_registry(self.session.worlds)
        self.resource_nodes.validate_world_references()
        self.simulation.register_tick_listener(self.resource_nodes)

        inventory_values = tuple(self.inventories.values())
        if any(not isinstance(inventory, Inventory) for inventory in inventory_values):
            raise TypeError("inventories must contain Inventory values.")
        if len({id(inventory) for inventory in inventory_values}) != len(inventory_values):
            raise ValueError("An Inventory cannot be registered under multiple IDs.")
        for inventory_id in self.inventories:
            if not isinstance(inventory_id, str) or not inventory_id.strip():
                raise ValueError("inventory IDs must be non-empty strings.")

        if any(not isinstance(recipe, Recipe) for recipe in self.recipes.values()):
            raise TypeError("recipes must contain Recipe values.")
        for recipe_id, recipe in self.recipes.items():
            if not isinstance(recipe_id, str) or not recipe_id.strip():
                raise ValueError("recipe IDs must be non-empty strings.")
            if recipe.recipe_id != recipe_id:
                raise ValueError("recipe registry key must match recipe.recipe_id.")

        registered_inventory_ids = {id(inventory) for inventory in inventory_values}
        for job in self.production_jobs.jobs():
            if id(job.inventory) not in registered_inventory_ids:
                raise ValueError(
                    f"Production job inventory is not registered: {job.job_id}"
                )

        object.__setattr__(self, "inventories", MappingProxyType(dict(self.inventories)))
        object.__setattr__(self, "recipes", MappingProxyType(dict(self.recipes)))
        object.__setattr__(self, "characters", MappingProxyType(dict(self.characters)))

    @classmethod
    def create_default(cls) -> "SessionBundle":
        session = GameSession()
        simulation = session.simulation
        return cls(
            session=session,
            simulation=simulation,
            production_jobs=ProductionJobManager(simulation),
            resource_nodes=WorldResourceNodeManager(session.worlds),
            inventories={},
            recipes={},
        )

    def validate(self) -> None:
        """Re-check the publication invariants without mutating the bundle."""
        self.__post_init__()

    def _validate_character_actor_links(self) -> None:
        """Ensure every persisted character/actor link is reciprocal."""
        actors = self.actors.actors()
        actor_by_id = {actor.actor_id: actor for actor in actors}
        for character in self.characters.values():
            if character.actor_id is None:
                continue
            actor = actor_by_id.get(character.actor_id)
            if actor is None or actor.character_id != character.character_id:
                raise ValueError(f"Character {character.character_id} has an invalid actor link.")
        character_by_id = dict(self.characters)
        for actor in actors:
            if actor.character_id is None:
                continue
            character = character_by_id.get(actor.character_id)
            if character is None or character.actor_id != actor.actor_id:
                raise ValueError(f"Actor {actor.actor_id} has an invalid character link.")


class SessionHolder:
    """Own the active bundle reference and publish complete candidates."""

    def __init__(self, bundle: SessionBundle | None = None) -> None:
        self._current = bundle if bundle is not None else SessionBundle.create_default()
        self._current.validate()

    @property
    def current(self) -> SessionBundle:
        return self._current

    def publish(self, candidate: SessionBundle) -> SessionBundle:
        if not isinstance(candidate, SessionBundle):
            raise TypeError("candidate must be SessionBundle.")
        candidate.validate()
        if candidate is self._current:
            raise ValueError("The current bundle cannot be published as a candidate.")
        if self._shares_mutable_state(self._current, candidate):
            raise ValueError("Candidate bundle shares mutable runtime state with current bundle.")

        self._current = candidate
        return candidate

    @staticmethod
    def _shares_mutable_state(first: SessionBundle, second: SessionBundle) -> bool:
        if (
            first.session is second.session
            or first.simulation is second.simulation
            or first.production_jobs is second.production_jobs
            or first.resource_nodes is second.resource_nodes
            or first.facilities is second.facilities
            or first.actors is second.actors
            or first.actor_activities is second.actor_activities
            or first.economy is second.economy
            or first.social is second.social
            or first.combat is second.combat
        ):
            return True
        return any(
            inventory is other_inventory
            for inventory in first.inventories.values()
            for other_inventory in second.inventories.values()
        )
