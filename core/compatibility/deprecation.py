"""Controlled deprecation policy for the 1.x compatibility surface."""

from dataclasses import dataclass
from functools import wraps
from types import MappingProxyType
import warnings


@dataclass(frozen=True)
class CompatibilityEntry:
    legacy_name: str
    canonical_replacement: str
    status: str
    deprecated: bool
    introduced_version: str
    deprecated_version: str | None
    planned_removal_phase: str
    migration_notes: str
    blocker: str

    @property
    def removal_phase(self) -> str:
        return self.planned_removal_phase


_ENTRIES = (
    CompatibilityEntry("core.event_bus.EventBus", "CanonicalEventDispatcher", "compatibility", False, "1.x", None, "Phase 7+", "Keep handler behavior stable.", "handler API users"),
    CompatibilityEntry("core.events.EventQueue", "CanonicalEventTransport", "compatibility", False, "1.x", None, "Phase 7+", "Use adapter during migration.", "1.x callers"),
    CompatibilityEntry("core.event_types.EventType", "CanonicalEventType", "alias", False, "1.x", None, "Phase 6+", "Canonical type aliases remain available.", "public imports"),
    CompatibilityEntry("core.constants event constants", "CanonicalEventType", "alias", False, "1.x", None, "Phase 6+", "Do not remove public constants yet.", "public imports"),
    CompatibilityEntry("Game.dunya_olaylarini_aktar", "Game.dunya_olaylarini_canonical_aktar", "deprecated", True, "1.x", "2.0", "Phase 6+", "Route new code through the runtime dispatcher.", "legacy queue consumers"),
    CompatibilityEntry("core.clock.GameClock", "WorldRuntimeBoundary.advance_world", "compatibility", False, "1.x", None, "Phase 7+", "Only the World compatibility projection may own this adapter.", "1.x world clock callers"),
    CompatibilityEntry("time_system.Scheduler", "CanonicalScheduler", "compatibility", False, "1.x", None, "Phase 7+", "Callback scheduler remains operational.", "callback callers"),
    CompatibilityEntry("core.actions.Action", "core.simulation.Action", "compatibility", False, "1.x", None, "Phase 7+", "Preserve mutable action behavior.", "1.x action callers"),
    CompatibilityEntry("core.actions.ActionManager", "CanonicalActionAdapter", "compatibility", False, "1.x", None, "Phase 7+", "Only direct 1.x callers may instantiate the manager; application code uses the adapter.", "1.x action callers"),
    CompatibilityEntry("Entity.world_id", "WorldMembershipService", "projection", False, "1.x", None, "Phase 7+", "Ownership migration is deferred.", "entity projection"),
    CompatibilityEntry("World._entities", "EntityRepository", "projection", False, "1.x", None, "Phase 7+", "World projection remains for compatibility.", "world projection"),
    CompatibilityEntry("core.entity.position.Position", "core.domain.spatial.Position", "compatibility", False, "1.x", None, "Phase 6+", "Position migration is deferred.", "old imports"),
    CompatibilityEntry("time_system.Tick", "core.time.Tick", "compatibility", False, "1.x", None, "Phase 6+", "Tick migration is deferred.", "old imports"),
)

LEGACY_API_MATRIX = MappingProxyType({entry.legacy_name: entry for entry in _ENTRIES})


def compatibility_entry(api_name: str) -> CompatibilityEntry:
    return LEGACY_API_MATRIX[api_name]


def warn_deprecated(api_name: str, stacklevel: int = 2) -> None:
    entry = compatibility_entry(api_name)
    if not entry.deprecated:
        return
    from .usage import record_usage
    record_usage(api_name)
    warnings.warn(
        f"{api_name} is a legacy compatibility API; use {entry.canonical_replacement}.",
        DeprecationWarning,
        stacklevel=stacklevel,
    )


def deprecated_api(api_name: str):
    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            warn_deprecated(api_name, stacklevel=3)
            return function(*args, **kwargs)
        return wrapped
    return decorator
