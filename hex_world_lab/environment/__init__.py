"""Static environmental object domain and existing-system adapters."""
from .definition import EnvironmentalObjectDefinition
from .placement import EnvironmentalObjectPlacement
from .scene import EnvironmentalObjectScene
from .presentation import environment_debug_visuals, environment_obstacles, environment_sprite_visuals

__all__ = [
    "EnvironmentalObjectDefinition",
    "EnvironmentalObjectPlacement",
    "EnvironmentalObjectScene",
    "environment_debug_visuals",
    "environment_obstacles",
    "environment_sprite_visuals",
]
