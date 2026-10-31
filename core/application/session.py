from core.application.entity_repository import EntityRepository
from core.application.ownership import WorldMembershipService
from core.entity.entity import Entity
from core.simulation.runtime import SimulationRuntime
from core.world.world_manager import WorldManager
from core.world.world import World
from core.application.world_runtime import WorldRuntimeBoundary
from core.entity.position import Position
from core.persistence import RestoreContract, CanonicalRestoreState


class GameSession:
    """Application/runtime boundary for Core 2.0 ownership operations."""

    def __init__(self, world_registry=None, entity_repository=None, event_transport=None, start_tick=0) -> None:
        self._worlds = world_registry if world_registry is not None else WorldManager()
        self._entities = entity_repository if entity_repository is not None else EntityRepository()
        self._membership = WorldMembershipService(self._entities, self._worlds)
        self._simulation = SimulationRuntime(start_tick=start_tick, event_transport=event_transport)
        self._world_runtime = WorldRuntimeBoundary(self._simulation)

    @property
    def worlds(self) -> WorldManager:
        return self._worlds

    @property
    def entities(self) -> EntityRepository:
        return self._entities

    @property
    def membership(self) -> WorldMembershipService:
        return self._membership

    @property
    def simulation(self) -> SimulationRuntime:
        return self._simulation

    @property
    def world_runtime(self) -> WorldRuntimeBoundary:
        return self._world_runtime

    def dispatch_world_events(self, world):
        return self._world_runtime.dispatch_world_events(world)

    def active_world(self):
        return self._worlds.get_active()

    def add_entity(self, entity: Entity, world_id: str | None = None) -> Entity:
        self._entities.add(entity)
        try:
            if world_id is not None:
                self._membership.add(entity.entity_id, world_id)
        except Exception:
            self._entities.remove(entity.entity_id)
            raise
        return entity

    def remove_entity(self, entity_id: str) -> Entity:
        if self._membership.world_id_for(entity_id) is not None:
            self._membership.remove(entity_id)
        return self._entities.remove(entity_id)

    def transfer_entity(self, entity_id: str, target_world_id: str) -> Entity:
        return self._membership.transfer(entity_id, target_world_id)

    def remove_world(self, world_id: str):
        """Remove an empty World through the application ownership boundary."""
        if self._membership.entity_ids_for(world_id):
            raise ValueError("Entity membership bulunan World silinemez.")
        return self._worlds.remove(world_id)

    def activate_restore(self, plan: CanonicalRestoreState) -> "GameSession":
        """Atomically replace this session with a validated restore plan."""
        registrations = self._simulation.dispatcher.registration_snapshot()
        tick_listeners = self._simulation.tick_listener_snapshot()
        validated = RestoreContract.prepare(plan.state) if isinstance(plan, CanonicalRestoreState) else None
        if validated is None:
            raise TypeError("plan must be CanonicalRestoreState.")

        # Build a complete replacement graph locally. The current session is
        # not touched until every World, Entity, membership and runtime value
        # has been constructed successfully.
        worlds = WorldManager()
        for world_state in validated.worlds:
            worlds.add(World(
                name=world_state.name,
                width=world_state.width,
                height=world_state.height,
                world_id=world_state.world_id.value,
            ))

        entities = EntityRepository()
        restored_entities = {}
        for record in validated.entities.records:
            entity = Entity(
                entity_type=record.entity_type,
                name=record.name,
                entity_id=record.entity_id.value,
                position=Position(record.position.x, record.position.y),
            )
            self._apply_entity_state(entity, record.state)
            entities.add(entity)
            restored_entities[record.entity_id.value] = entity

        membership = WorldMembershipService(entities, worlds)
        for record in validated.memberships.records:
            membership.add(record.entity_id, record.world_id)

        if validated.active_world_id is not None:
            worlds.set_active(validated.active_world_id)

        simulation = SimulationRuntime(start_tick=validated.simulation_tick)
        for consumer, event_types in registrations:
            simulation.dispatcher.register(consumer, event_types)
        for listener in tick_listeners:
            simulation.register_tick_listener(listener)
        world_runtime = WorldRuntimeBoundary(simulation)

        self._worlds = worlds
        self._entities = entities
        self._membership = membership
        self._simulation = simulation
        self._world_runtime = world_runtime
        return self

    @staticmethod
    def _apply_entity_state(entity: Entity, state) -> None:
        if not hasattr(state, "get"):
            raise TypeError("Entity canonical state must be a mapping.")
        status = state.get("durum")
        if status == entity.state.DURUM_AKTIF:
            pass
        elif status == entity.state.DURUM_PASIF:
            entity.deactivate()
        elif status == entity.state.DURUM_OLU:
            entity.kill()
        else:
            raise ValueError("Entity canonical state contains an invalid status.")

        alive = state.get("canli")
        if alive is not None and not isinstance(alive, bool):
            raise TypeError("Entity canonical alive state must be boolean.")
        if alive is not None and alive != entity.is_alive():
            raise ValueError("Entity canonical state has inconsistent alive status.")
