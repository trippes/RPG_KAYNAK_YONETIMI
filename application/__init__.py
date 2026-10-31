"""Application composition boundaries outside the canonical Core package."""

from .game_application import GameApplication
from .save_document import GameSaveDocument
from .save_codec import SaveJsonCodec
from .save_file_adapter import GameSaveFileAdapter
from .session_bundle import SessionBundle, SessionHolder
from .production_chain import ProductionChain, ProductionChainStage, ProductionChainState
from .production_capacity import ProductionCapacity, ProductionCapacityError
from .production_facility import (
    FacilityBinding,
    ProductionFacility,
    ProductionFacilityError,
    ProductionFacilityRegistry,
)
from .production_persistence import (
    FacilityJobRecord,
    FacilityRecord,
    ProductionPersistenceError,
    ProductionSnapshot,
)
from .gameplay_service import (
    ChainView,
    FacilityView,
    GameplayChainStage,
    GameplayService,
    GameplayServiceError,
    GameplaySnapshotView,
    LocationInteractionView,
    InventoryView,
    JobView,
    ResourceNodeView,
)
from .actor_system import (
    ActivityError,
    ActivityState,
    ActivityView,
    ActorActivity,
    ActorActivityManager,
    ActorError,
    ActorView,
    WorldActor,
    WorldActorRegistry,
)
from .actor_persistence import (
    ACTOR_SCHEMA,
    ACTOR_SCHEMA_VERSION,
    ActivityRecord,
    ActorPersistenceError,
    ActorRecord,
    ActorSnapshot,
)
from .movement import MovementManager
from .social_runtime import SocialRuntime, SocialRuntimeError
from .combat_runtime import Combatant, CombatResult, CombatRuntime
from .extended_persistence import SocialSnapshot, CombatSnapshot
from .migrations import CURRENT_SAVE_SCHEMA_VERSION, migrate_save_data

__all__ = [
    "GameApplication",
    "GameSaveDocument",
    "GameSaveFileAdapter",
    "SaveJsonCodec",
    "SessionBundle",
    "SessionHolder",
    "ProductionChain",
    "ProductionChainStage",
    "ProductionChainState",
    "ProductionCapacity",
    "ProductionCapacityError",
    "ProductionFacility",
    "ProductionFacilityError",
    "ProductionFacilityRegistry",
    "FacilityBinding",
    "ProductionSnapshot",
    "ProductionPersistenceError",
    "FacilityRecord",
    "FacilityJobRecord",
    "GameplayService",
    "GameplayServiceError",
    "GameplayChainStage",
    "GameplaySnapshotView",
    "InventoryView",
    "ResourceNodeView",
    "LocationInteractionView",
    "FacilityView",
    "JobView",
    "ChainView",
    "ActorError",
    "ActivityError",
    "ActivityState",
    "ActorView",
    "ActivityView",
    "WorldActor",
    "WorldActorRegistry",
    "ActorActivity",
    "ActorActivityManager",
    "ACTOR_SCHEMA",
    "ACTOR_SCHEMA_VERSION",
    "ActorPersistenceError",
    "ActorRecord",
    "ActivityRecord",
    "ActorSnapshot",
    "MovementManager",
    "SocialRuntime", "SocialRuntimeError", "Combatant", "CombatResult", "CombatRuntime",
    "SocialSnapshot", "CombatSnapshot",
    "CURRENT_SAVE_SCHEMA_VERSION", "migrate_save_data",
]
