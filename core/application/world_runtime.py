"""Application-owned World runtime boundary."""

from core.foundation import Identifier
from core.simulation.transport import LegacyEventAdapter
from core.time import Tick


class WorldRuntimeBoundary:
    """Routes World compatibility projections into canonical runtime services."""

    def __init__(self, simulation_runtime) -> None:
        self._simulation = simulation_runtime

    @property
    def simulation(self):
        return self._simulation

    @property
    def canonical_scheduler(self):
        return self._simulation.actions.scheduler

    @property
    def event_transport(self):
        return self._simulation.event_transport

    def advance_world(self, world, delta: Tick | int):
        """Advance canonical simulation time and mirror it to a World projection."""
        if world is None or not hasattr(world, "set_time"):
            raise TypeError("world must provide the World time projection API.")
        delta = delta if isinstance(delta, Tick) else Tick(delta)
        if delta.value < 0:
            raise ValueError("Simulation delta cannot be negative.")
        previous = self._simulation.current_tick
        self._simulation.advance_by(delta)
        world.set_time(self._simulation.current_tick.value)
        # A zero-length legacy advance processes callbacks at the mirrored tick.
        world.advance(0)
        return previous, self._simulation.current_tick

    def dispatch_world_events(self, world):
        if world is None or not hasattr(world, "get_event"):
            raise TypeError("world must provide the World compatibility event API.")
        adapter = LegacyEventAdapter(self._simulation.event_transport)
        routed = []
        while world.has_pending_events():
            routed.append(adapter.enqueue(
                world.get_event(),
                simulation_tick=Tick(world.total_ticks),
                source_id=Identifier(str(world.world_id)),
            ))
        return tuple(routed)
