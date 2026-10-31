"""1.x World runtime projection kept outside the canonical World contract."""

from core.clock import GameClock
from core.events import Event, EventQueue
from time_system.scheduler import Scheduler


class LegacyWorldRuntime:
    """Compatibility owner for World clock, local queue and callback scheduler."""

    def __init__(self, start_tick: int) -> None:
        self.clock = GameClock(start_tick=start_tick)
        self.event_queue = EventQueue()
        self.scheduler = Scheduler()
        self.clock.attach_scheduler(self.scheduler)

    def create_event(self, event_type, payload=None):
        return Event(tur=event_type, veri=payload)
