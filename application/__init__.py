"""Application composition boundaries outside the canonical Core package."""

from .game_application import GameApplication
from .save_document import GameSaveDocument
from .save_codec import SaveJsonCodec
from .save_file_adapter import GameSaveFileAdapter
from .save_storage import MigrationReport, SaveStorage, SaveStorageError, documents_directory
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
    CombatEncounterView,
    CombatSnapshotView,
    CombatantView,
    ContainerView,
    LockView,
    LockAttemptResult,
    ChainView,
    FacilityView,
    GameplayChainStage,
    GameplayService,
    GameplayServiceError,
    GameplaySnapshotView,
    WorldView,
    RaceOptionView,
    ClassOptionView,
    CharacterCreationStateView,
    TradePartnerView,
    QuestObjectiveView,
    QuestRewardView,
    QuestBranchView,
    QuestView,
    DialogueSessionView,
    RecipeView,
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
    ActorIdentity,
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
from .social_runtime import SocialRuntime, SocialRuntimeError
from .combat_runtime import Combatant, CombatResult, CombatRuntime
from .extended_persistence import SocialSnapshot, CombatSnapshot
from .migrations import CURRENT_SAVE_SCHEMA_VERSION, migrate_save_data
from .container_persistence import (
    CONTAINER_SCHEMA,
    CONTAINER_SCHEMA_VERSION,
    ContainerPersistenceError,
    ContainerSnapshot,
)
from .lock_persistence import (
    LOCK_SCHEMA,
    LOCK_SCHEMA_VERSION,
    LockPersistenceError,
    LockSnapshot,
)
from .world_map_definition import (
    WorldMapDefinition,
    WorldMapDefinitionError,
    WorldMapPlacement,
    parse_world_map,
    validate_world_map,
)
from .hex_movement_rules import MovementRules
from .hex_pathfinding import HexPathfinder
from .hex_occupancy import HexOccupant, HexOccupancyRegistry
from .hex_world_runtime import HexMovableEntity, HexWorldRuntime
from .hex_transition_service import HexMapTransitionService
from .hex_interaction import HexInteractionService
from .npc_hex_binding import NPCSpatialBindingError, NPCSpatialBindingService
from .resource_node_hex_binding import (
    ResourceNodeHexBindingError,
    ResourceNodeHexBindingService,
)
from .market_hex_anchor import MarketHexAnchorError, MarketHexAnchorService
from .hex_world_persistence import (
    HEX_WORLD_SCHEMA,
    HEX_WORLD_SCHEMA_VERSION,
    HexWorldEntityRecord,
    HexWorldPersistenceError,
    HexWorldSnapshot,
)
from .hex_world_initializer import (
    HexWorldInitializationError,
    initialize_hex_world,
)
from .gameplay_placement_catalog import (
    GameplayPlacement,
    GameplayPlacementCatalog,
    GameplayPlacementCatalogError,
)
from .presentation_content_service import (
    ContentMigrationStatus,
    ContentValidationIssue,
    ContentValidationResult,
    PresentationContentService,
    PresentationContentServiceError,
)

__all__ = [
    "GameApplication",
    "GameSaveDocument",
    "GameSaveFileAdapter",
    "SaveJsonCodec",
    "SaveStorage",
    "SaveStorageError",
    "MigrationReport",
    "documents_directory",
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
    "CombatEncounterView",
    "CombatSnapshotView",
    "CombatantView",
    "ContainerView",
    "LockView",
    "LockAttemptResult",
    "GameplayService",
    "GameplayServiceError",
    "GameplayChainStage",
    "GameplaySnapshotView",
    "WorldView",
    "RaceOptionView",
    "ClassOptionView",
    "CharacterCreationStateView",
    "TradePartnerView",
    "QuestObjectiveView",
    "QuestRewardView",
    "QuestBranchView",
    "QuestView",
    "DialogueSessionView",
    "RecipeView",
    "InventoryView",
    "ResourceNodeView",
    "FacilityView",
    "JobView",
    "ChainView",
    "ActorError",
    "ActorIdentity",
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
    "SocialRuntime",
    "SocialRuntimeError",
    "Combatant",
    "CombatResult",
    "CombatRuntime",
    "SocialSnapshot",
    "CombatSnapshot",
    "CURRENT_SAVE_SCHEMA_VERSION",
    "migrate_save_data",
    "WorldMapDefinition",
    "WorldMapDefinitionError",
    "WorldMapPlacement",
    "parse_world_map",
    "validate_world_map",
    "CONTAINER_SCHEMA",
    "CONTAINER_SCHEMA_VERSION",
    "ContainerPersistenceError",
    "ContainerSnapshot",
    "LOCK_SCHEMA",
    "LOCK_SCHEMA_VERSION",
    "LockPersistenceError",
    "LockSnapshot",
    "MovementRules",
    "HexPathfinder",
    "HexOccupant",
    "HexOccupancyRegistry",
    "HexMovableEntity",
    "HexWorldRuntime",
    "HexMapTransitionService",
    "HexInteractionService",
    "NPCSpatialBindingError",
    "NPCSpatialBindingService",
    "ResourceNodeHexBindingError",
    "ResourceNodeHexBindingService",
    "MarketHexAnchorError",
    "MarketHexAnchorService",
    "HEX_WORLD_SCHEMA",
    "HEX_WORLD_SCHEMA_VERSION",
    "HexWorldEntityRecord",
    "HexWorldPersistenceError",
    "HexWorldSnapshot",
    "HexWorldInitializationError",
    "initialize_hex_world",
    "GameplayPlacement",
    "GameplayPlacementCatalog",
    "GameplayPlacementCatalogError",
    "ContentMigrationStatus",
    "ContentValidationIssue",
    "ContentValidationResult",
    "PresentationContentService",
    "PresentationContentServiceError",
]
