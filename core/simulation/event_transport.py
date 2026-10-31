"""Backward-compatible import location for the Phase 4 event transport."""

from .transport import (
    CanonicalEventQueue,
    CanonicalEventTransport,
    EventTransport,
    LegacyEventAdapter,
)

__all__ = [
    "CanonicalEventQueue",
    "CanonicalEventTransport",
    "EventTransport",
    "LegacyEventAdapter",
]
