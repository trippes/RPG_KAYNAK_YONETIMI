"""Content persistence error hierarchy."""


class ContentPersistenceError(Exception):
    """Base error for content document storage and validation."""


class ContentValidationError(ContentPersistenceError, ValueError):
    """A content document violates its schema or domain invariants."""

    def __init__(self, message, path="$"):
        self.path = path
        super().__init__(f"{path}: {message}")


class UnsupportedContentVersionError(ContentValidationError):
    """A document uses an unsupported schema or visual document version."""
