"""Typed errors raised by map persistence operations."""


class MapPersistenceError(Exception):
    """Base class for controlled map persistence failures."""


class MapFileNotFoundError(MapPersistenceError):
    """The requested map file does not exist."""


class MapFileAccessError(MapPersistenceError):
    """A map file could not be read or accessed."""


class MapJSONDecodeError(MapPersistenceError):
    """The file is not valid JSON or contains duplicate object keys."""


class MapValidationError(MapPersistenceError):
    """Parsed JSON does not satisfy map schema v1."""

    def __init__(self, message: str, path: str = "$") -> None:
        self.path = path
        super().__init__(f"{path}: {message}")


class UnsupportedMapSchemaVersionError(MapValidationError):
    """The map file declares a schema version not supported by this reader."""


class MapFileAlreadyExistsError(MapPersistenceError):
    """Create-only save mode refuses to overwrite an existing file."""


class MapFileWriteError(MapPersistenceError):
    """A map file could not be written safely."""
