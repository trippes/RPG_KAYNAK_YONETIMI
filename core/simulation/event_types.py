"""Canonical Core 2.0 simulation event type registry."""


class CanonicalEventType:
    GAME_STARTED = "GameStarted"
    GAME_PAUSED = "GamePaused"
    GAME_RESUMED = "GameResumed"
    GAME_ENDED = "GameEnded"
    ENTITY_CREATED = "EntityCreated"
    ENTITY_DESTROYED = "EntityDestroyed"
    ENTITY_STATE_CHANGED = "EntityStateChanged"
    POSITION_CHANGED = "PositionChanged"
    TIME_ADVANCED = "TimeAdvanced"
    ACTION_CREATED = "ActionCreated"
    ACTION_SCHEDULED = "ActionScheduled"
    ACTION_STARTED = "ActionStarted"
    ACTION_COMPLETED = "ActionCompleted"
    ACTION_FAILED = "ActionFailed"
    ACTION_CANCELLED = "ActionCancelled"


DEFAULT_SCHEMA_VERSION = 1

# Legacy names remain public, but their canonical meaning is explicit here.
LEGACY_EVENT_ALIASES = {
    "oyun_baslatildi": CanonicalEventType.GAME_STARTED,
    "oyun_duraklatildi": CanonicalEventType.GAME_PAUSED,
    "oyun_devam_ettirildi": CanonicalEventType.GAME_RESUMED,
    "oyun_bitti": CanonicalEventType.GAME_ENDED,
    "entity_olusturuldu": CanonicalEventType.ENTITY_CREATED,
    "entity_yok_edildi": CanonicalEventType.ENTITY_DESTROYED,
    "entity_durum_degisti": CanonicalEventType.ENTITY_STATE_CHANGED,
    "position_degisti": CanonicalEventType.POSITION_CHANGED,
    "zaman_ilerledi": CanonicalEventType.TIME_ADVANCED,
    "aksiyon_baslatildi": CanonicalEventType.ACTION_STARTED,
    "aksiyon_tamamlandi": CanonicalEventType.ACTION_COMPLETED,
    "aksiyon_iptal_edildi": CanonicalEventType.ACTION_CANCELLED,
}


def canonical_event_type(event_type: str) -> str:
    """Return the canonical type for a legacy or canonical event name."""
    return LEGACY_EVENT_ALIASES.get(event_type, event_type)


SimulationEventType = CanonicalEventType
