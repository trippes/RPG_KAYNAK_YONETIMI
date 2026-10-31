"""Canonical persistence contracts, JSON codec and file adapter boundaries."""

from .contracts import (
    CANONICAL_PERSISTENCE_SCHEMA,
    PERSISTENCE_SCHEMA_VERSION,
    PERSISTENCE_EXCLUSIONS,
    PersistenceDocument,
    PersistenceSchemaError,
    UnsupportedPersistenceSchemaError,
    deserialize_identifier,
    deserialize_position,
    deserialize_tick,
    serialize_identifier,
    serialize_position,
    serialize_tick,
)
from .state import (
    CanonicalEntityRecord,
    CanonicalSessionState,
    EntityRepositoryState,
    MembershipRecord,
    WorldMembershipState,
)
from .restore import (
    CanonicalRestoreState,
    PersistenceAdapter,
    PersistenceMigrationBoundary,
    RestoreContract,
    RestorePlan,
    RestoreValidationError,
    RuntimeActivationBoundary,
    validate_canonical_state,
)
from .json_codec import JsonPersistenceCodec, decode_document, encode_document
from .file_adapter import (
    FilePersistenceAdapter,
    PersistenceFileError,
    PersistenceFileReadError,
    PersistenceFileWriteError,
)

__all__ = [
    "CANONICAL_PERSISTENCE_SCHEMA", "PERSISTENCE_SCHEMA_VERSION", "PERSISTENCE_EXCLUSIONS",
    "PersistenceDocument", "PersistenceSchemaError", "UnsupportedPersistenceSchemaError",
    "serialize_identifier", "deserialize_identifier", "serialize_position", "deserialize_position",
    "serialize_tick", "deserialize_tick", "CanonicalEntityRecord", "EntityRepositoryState",
    "MembershipRecord", "WorldMembershipState", "CanonicalSessionState",
    "CanonicalRestoreState", "RestorePlan", "RestoreContract", "RestoreValidationError",
    "RuntimeActivationBoundary", "PersistenceAdapter", "PersistenceMigrationBoundary",
    "validate_canonical_state",
    "JsonPersistenceCodec", "encode_document", "decode_document",
    "FilePersistenceAdapter", "PersistenceFileError", "PersistenceFileReadError",
    "PersistenceFileWriteError",
]
