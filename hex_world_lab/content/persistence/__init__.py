"""Strict, versioned content document persistence."""

from .codec import (
    deserialize_library,
    deserialize_map_content,
    library_to_payload,
    map_content_to_payload,
    serialize_library,
    serialize_map_content,
)
from .errors import ContentPersistenceError, ContentValidationError, UnsupportedContentVersionError
from .file_storage import (
    load_library_file,
    load_map_content_file,
    save_library_file,
    save_map_content_file,
)

__all__ = [
    "ContentPersistenceError",
    "ContentValidationError",
    "UnsupportedContentVersionError",
    "deserialize_library",
    "deserialize_map_content",
    "library_to_payload",
    "load_library_file",
    "load_map_content_file",
    "map_content_to_payload",
    "save_library_file",
    "save_map_content_file",
    "serialize_library",
    "serialize_map_content",
]
