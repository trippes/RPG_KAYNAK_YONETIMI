"""Generic spatial indexing primitives."""
from .entry import SpatialEntry
from .grid import UniformGrid
from .protocols import Bounds2D, SpatialIndex
from .quadtree import Quadtree

__all__ = ["Bounds2D", "Quadtree", "SpatialEntry", "SpatialIndex", "UniformGrid"]
