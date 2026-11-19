"""Typed failures for runtime snapshot persistence."""

from .errors import MapPersistenceError, MapValidationError


class RuntimePersistenceError(MapPersistenceError):
    """Base class for runtime snapshot persistence errors."""


class RuntimeJSONDecodeError(RuntimePersistenceError):
    """Runtime snapshot text is not valid JSON."""


class RuntimeValidationError(MapValidationError, RuntimePersistenceError):
    """Runtime snapshot violates schema or map compatibility rules."""


class RuntimeSchemaVersionError(RuntimeValidationError):
    """Runtime snapshot schema version is unsupported."""


class RuntimeBaseMapMismatchError(RuntimeValidationError):
    """Snapshot was created from a different base map definition."""


class RuntimeWorldMismatchError(RuntimeValidationError):
    """Snapshot belongs to a different world."""


class RuntimeMapMismatchError(RuntimeValidationError):
    """Snapshot belongs to a different map."""


class RuntimeFileWriteError(RuntimePersistenceError):
    """Runtime snapshot could not be safely written."""
