"""Data-driven content catalog primitives for editor-authored game content."""

from .catalog import (
    CONTENT_CATALOG_SCHEMA_VERSION,
    CONTENT_PACK_SCHEMA_VERSION,
    ContentCatalog,
    ContentCatalogError,
    ContentPackInfo,
    ContentRecord,
    load_content_catalog,
)

__all__ = [
    "CONTENT_CATALOG_SCHEMA_VERSION",
    "CONTENT_PACK_SCHEMA_VERSION",
    "ContentCatalog",
    "ContentCatalogError",
    "ContentPackInfo",
    "ContentRecord",
    "load_content_catalog",
]
