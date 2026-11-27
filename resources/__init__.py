"""Gameplay resource domain contracts."""
from .inventory import Inventory
from .jobs import ProductionJob, ProductionJobManager, ProductionJobState
from .resource import Quantity, ResourceType, ResourceUnit
from .definition import ResourceDefinition
from .production import (
    InsufficientStockError, InsufficientItemStockError, ResourceOperationError, ResourceUnitMismatchError,
    consume_resources, consume_recipe_inputs, produce,
)
from .recipe import Recipe, RecipeError
from .transfer import transfer_items, transfer_resources
from .node import ResourceNodeError, ResourceNodeInsufficientError, WorldResourceNode
from .gathering import WorldResourceNodeManager
from .persistence import (
    GameplayFileAdapter, GameplayJsonCodec, GameplayPersistenceError,
    GameplaySnapshot, RestoredGameplayState,
)

__all__ = [
    "ResourceType", "ResourceUnit", "Quantity", "ResourceDefinition",
    "Inventory", "transfer_resources", "transfer_items",
    "Recipe", "RecipeError", "consume_resources", "produce",
    "ResourceOperationError", "InsufficientStockError", "InsufficientItemStockError", "ResourceUnitMismatchError", "consume_recipe_inputs",
    "ProductionJob", "ProductionJobManager", "ProductionJobState",
    "WorldResourceNode", "WorldResourceNodeManager", "ResourceNodeError",
    "ResourceNodeInsufficientError", "GameplaySnapshot", "RestoredGameplayState",
    "GameplayJsonCodec", "GameplayFileAdapter", "GameplayPersistenceError",
]
