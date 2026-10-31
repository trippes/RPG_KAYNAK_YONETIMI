from core.simulation.action_processor import ActionProcessor
from core.simulation.events import SimulationEvent
from core.time import Tick
from core.simulation.transport import CanonicalEventTransport, LegacyEventAdapter
from core.simulation.dispatcher import CanonicalEventDispatcher
from core.foundation import Identifier


class SimulationRuntime:
    """Minimal deterministic simulation progression boundary."""

    def __init__(self, start_tick: Tick | int = Tick(0), action_processor=None, event_transport=None) -> None:
        self._event_transport = (
            event_transport if event_transport is not None else CanonicalEventTransport()
        )
        self._actions = action_processor or ActionProcessor(
            start_tick=start_tick, event_transport=self._event_transport
        )
        if self._actions.event_transport is not self._event_transport:
            raise ValueError("ActionProcessor must use the runtime event transport.")
        self._dispatcher = CanonicalEventDispatcher(self._event_transport)
        self._tick_listeners = []

    @property
    def current_tick(self) -> Tick:
        return self._actions.current_tick

    @property
    def actions(self) -> ActionProcessor:
        return self._actions

    @property
    def event_transport(self) -> CanonicalEventTransport:
        return self._event_transport

    @property
    def events(self) -> CanonicalEventTransport:
        """Canonical transport alias for runtime/application consumers."""
        return self._event_transport

    @property
    def dispatcher(self) -> CanonicalEventDispatcher:
        return self._dispatcher

    def advance_to(self, target_tick: Tick | int) -> tuple[SimulationEvent, ...]:
        target = target_tick if isinstance(target_tick, Tick) else Tick(target_tick)
        previous = self.current_tick
        events = self._actions.advance_to(target)
        if target > self.current_tick:
            raise RuntimeError("Action processor failed to advance simulation time.")
        if self.current_tick > previous:
            for listener in tuple(self._tick_listeners):
                listener.advance_to(self.current_tick)
        return events

    def register_tick_listener(self, listener) -> None:
        """Register an idempotent deterministic observer of successful time advances."""
        if not callable(getattr(listener, "advance_to", None)):
            raise TypeError("listener must provide advance_to(tick).")
        if all(existing is not listener for existing in self._tick_listeners):
            self._tick_listeners.append(listener)

    def tick_listener_snapshot(self) -> tuple[object, ...]:
        """Return registered listeners for atomic runtime replacement."""
        return tuple(self._tick_listeners)

    def unregister_tick_listener(self, listener) -> bool:
        for index, existing in enumerate(self._tick_listeners):
            if existing is listener:
                del self._tick_listeners[index]
                return True
        return False

    def advance_by(self, delta: Tick | int) -> tuple[SimulationEvent, ...]:
        delta = delta if isinstance(delta, Tick) else Tick(delta)
        if delta.value < 0:
            raise ValueError("Simulation delta cannot be negative.")
        return self.advance_to(self.current_tick + delta)

    def dispatch_world_events(self, world) -> tuple[SimulationEvent, ...]:
        """Route a World-local legacy queue through the canonical boundary."""
        if world is None or not hasattr(world, "get_event"):
            raise TypeError("world must provide the World event queue API.")
        adapter = LegacyEventAdapter(self._event_transport)
        routed = []
        while world.has_pending_events():
            legacy_event = world.get_event()
            routed.append(adapter.enqueue(
                legacy_event,
                simulation_tick=Tick(world.total_ticks),
                source_id=Identifier(str(world.world_id)),
            ))
        return tuple(routed)
