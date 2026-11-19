"""Map definition persistence (schema v1)."""

from .errors import (
    MapFileAccessError,
    MapFileAlreadyExistsError,
    MapFileNotFoundError,
    MapFileWriteError,
    MapJSONDecodeError,
    MapPersistenceError,
    MapValidationError,
    UnsupportedMapSchemaVersionError,
)
from .file_storage import load_map_file, save_map_file
from .map_deserializer import deserialize_map_payload
from .map_serializer import map_to_payload, serialize_map
from .map_validator import validate_map_payload

__all__ = [
    "MapFileAccessError",
    "MapFileAlreadyExistsError",
    "MapFileNotFoundError",
    "MapFileWriteError",
    "MapJSONDecodeError",
    "MapPersistenceError",
    "MapValidationError",
    "UnsupportedMapSchemaVersionError",
    "deserialize_map_payload",
    "load_map_file",
    "map_to_payload",
    "save_map_file",
    "serialize_map",
    "validate_map_payload",
]

from .runtime_deserializer import RuntimeMapSnapshot, deserialize_runtime_payload
from .runtime_errors import (
    RuntimeBaseMapMismatchError,
    RuntimeFileWriteError,
    RuntimeJSONDecodeError,
    RuntimeMapMismatchError,
    RuntimePersistenceError,
    RuntimeSchemaVersionError,
    RuntimeValidationError,
    RuntimeWorldMismatchError,
)
from .runtime_file_storage import load_runtime_file, restore_runtime_file, save_runtime_file
from .runtime_serializer import runtime_to_payload, serialize_runtime
from .runtime_validator import base_map_sha256, validate_runtime_payload

__all__ += [
    "RuntimeBaseMapMismatchError",
    "RuntimeFileWriteError",
    "RuntimeJSONDecodeError",
    "RuntimeMapMismatchError",
    "RuntimeMapSnapshot",
    "RuntimePersistenceError",
    "RuntimeSchemaVersionError",
    "RuntimeValidationError",
    "RuntimeWorldMismatchError",
    "base_map_sha256",
    "deserialize_runtime_payload",
    "load_runtime_file",
    "restore_runtime_file",
    "runtime_to_payload",
    "save_runtime_file",
    "serialize_runtime",
    "validate_runtime_payload",
]
