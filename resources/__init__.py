"""Gameplay resource domain contracts."""

from .inventory import Inventory
from .jobs import ProductionJob, ProductionJobManager, ProductionJobState
from .resource import Quantity, ResourceType, ResourceUnit
from .production import (
    InsufficientStockError,
    ResourceOperationError,
    ResourceUnitMismatchError,
    consume_resources,
    produce,
)
from .recipe import Recipe, RecipeError
from .transfer import transfer_resources
from .node import (
    ResourceNodeError,
    ResourceNodeInsufficientError,
    WorldResourceNode,
)
from .gathering import WorldResourceNodeManager
from .persistence import (
    GameplayFileAdapter,
    GameplayJsonCodec,
    GameplayPersistenceError,
    GameplaySnapshot,
    RestoredGameplayState,
)

__all__ = [
    "ResourceType", "ResourceUnit", "Quantity", "Inventory", "transfer_resources",
    "Recipe", "RecipeError", "consume_resources", "produce",
    "ResourceOperationError", "InsufficientStockError", "ResourceUnitMismatchError",
    "ProductionJob", "ProductionJobManager", "ProductionJobState",
    "WorldResourceNode", "WorldResourceNodeManager", "ResourceNodeError",
    "ResourceNodeInsufficientError",
    "GameplaySnapshot", "RestoredGameplayState", "GameplayJsonCodec",
    "GameplayFileAdapter", "GameplayPersistenceError",
]
