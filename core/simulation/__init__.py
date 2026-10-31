"""Deterministic Core 2.0 simulation runtime primitives."""

from .action import Action, ActionState
from .action_processor import ActionProcessor
from .events import SimulationEvent
from .runtime import SimulationRuntime
from .replay import SimulationReplay
from .scheduler import CanonicalScheduler, ScheduledWork
from .transport import (
    CanonicalEventQueue,
    CanonicalEventTransport,
    EventTransport,
    LegacyEventAdapter,
)
from .event_types import (
    CanonicalEventType,
    SimulationEventType,
    DEFAULT_SCHEMA_VERSION,
    LEGACY_EVENT_ALIASES,
    canonical_event_type,
)
from .dispatcher import CanonicalEventDispatcher, EventConsumer, EventDispatcher

__all__ = [
    "Action",
    "ActionState",
    "ActionProcessor",
    "SimulationEvent",
    "SimulationRuntime",
    "SimulationReplay",
    "CanonicalScheduler",
    "ScheduledWork",
    "CanonicalEventTransport",
    "CanonicalEventQueue",
    "EventTransport",
    "LegacyEventAdapter",
    "CanonicalEventType",
    "SimulationEventType",
    "DEFAULT_SCHEMA_VERSION",
    "LEGACY_EVENT_ALIASES",
    "canonical_event_type",
    "CanonicalEventDispatcher",
    "EventConsumer",
    "EventDispatcher",
]
