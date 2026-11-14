# Presentation Content Service API Contract

## Purpose and boundary

Phase 8.7 introduces a small application-level facade for future content-authoring
clients. The facade is UI-independent: it accepts plain Python/JSON data and
returns immutable domain objects or structured result records. It does not
import Pygame, process input events, draw previews, or add an editor mode.

## Public entry point

`application.presentation_content_service.PresentationContentService`

Construct it with the root directory of one content package. The service
reuses the existing `load_content_package`, `AssetCatalog`,
`ScenePlacementCatalog`, and `PresentationContentStore` contracts. It does
not define parallel asset, placement, or persistence schemas.

## Read operations

- `load_package()`: load the complete package through the canonical loader.
- `load_asset_catalog()`: return the validated asset catalog, or `None`.
- `list_assets(category=None)`: return immutable asset definitions.
- `get_asset(asset_id)`: resolve one asset; return `None` for an unknown ID.
- `load_map_placements(map_id)`: return immutable placements for a known hex map.

Every read reloads the current package snapshot through the canonical loader.
Consequently, invalid metadata or broken references cannot be hidden behind a
stale service cache. Unknown map IDs are explicit service errors.

## Validation operations

`validate_content_package()`, `validate_asset_catalog(draft)`, and
`validate_map_placements(map_id, draft)` return
`ContentValidationResult(valid, issues)`.

Each issue is a `ContentValidationIssue(code, message, severity, source)`.
Fatal package/draft failures use severity `error`; missing or corrupt image
files retain the established non-fatal behavior and are exposed as
`warning` diagnostics. Validation of an in-memory draft is performed against
a temporary copy of the whole package using the same safe-store write path.
The live package is never changed and no backup is created by validation.

## Persistence operations

- `save_asset_catalog(draft)`
- `save_map_placements(map_id, draft)`

Both delegate to `PresentationContentStore`, which validates the complete
staged package, atomically commits the target, and preserves backups. The
service then reloads the package before returning the write result. Errors are
surfaced as `PresentationContentServiceError`.

## Migration status and explicit migration

- `migration_status()` reports `split`, `legacy_combined`, or `none`
  without modifying files.
- `migrate_legacy_content()` explicitly delegates the legacy migration to
  the safe store. Migration is never triggered implicitly by a read.

The status record is `ContentMigrationStatus(source_format, schema_version,
migration_available)`. The existing schema version 1 is retained; this
phase does not introduce a new content schema.

## Error and dependency policy

The service raises `PresentationContentServiceError` for package, store, and
service-boundary failures. Input type errors and blank IDs are rejected at the
method boundary. Validation methods return structured findings for expected
invalid content rather than requiring a UI to parse exception text.

This module has no Pygame import and does not depend on screen/window classes.
The existing catalog and placement models remain the authority for metadata
and geometry validation. The game runtime continues to use its existing
`ContentPackage` snapshot and renderer integration.

## Verification

The service contract tests cover asset lookup/listing, map placement queries,
unknown map rejection, whole-package diagnostics, non-mutating valid/invalid
draft validation, safe-store delegation, read-only migration status, explicit
legacy migration, and structured invalid-package results.
