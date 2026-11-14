# Presentation Content Safe Persistence and Migration

## 1. Purpose and boundary

This document records the Phase 8.6 persistence contract for the split presentation-content sources. It provides a UI-independent filesystem boundary for future content-authoring tools.

The implementation is not a Content Editor. It adds no Save button, editor window, preview, gameplay mode, or Pygame dependency. It does not change asset rendering, map geometry, movement, collision, depth sorting, map transitions, or square-map support.

## 2. Service boundary

`application.presentation_content_store.PresentationContentStore` owns writes for one content package.

Supported operations:

- `save_asset_catalog(payload)`: validate the complete staged package and atomically replace the manifest-declared split asset catalog.
- `save_map_placements(map_id, payload)`: validate the complete staged package and atomically replace one map's placement document.
- `migrate_legacy_combined_presentation()`: explicitly migrate a legacy combined `presentation_assets.json` package to split catalog/placement sources.

The service accepts plain JSON-compatible data. It has no UI or Pygame imports at module load time. Validation delegates to the existing `load_content_package`, `AssetCatalog`, and `ScenePlacementCatalog` contracts; it does not create parallel schema models.

## 3. Validation-before-write

Every operation works against a temporary copy of the complete package:

1. Copy the package while preserving symlinks so the normal path-boundary checks can detect escapes.
2. Apply the candidate JSON only to the staged copy.
3. Serialize with UTF-8, sorted object keys, stable indentation, a final newline, and `allow_nan=False`.
4. Reject non-string object keys, unsupported Python values, and non-finite numbers before writing.
5. Load the staged package through `load_content_package`. This validates manifest paths, schema versions, catalog records, all placement references, map IDs, and valid map cells.
6. Only after the complete staged package is valid, replace the live target.

A missing/corrupt PNG remains the established non-fatal catalog diagnostic; malformed metadata or broken package references remain fatal. An invalid candidate never replaces the current source file.

## 4. Atomic writes, backups, and rollback

Each live file is replaced with a same-directory temporary file using `os.replace`. The temporary file is flushed and fsynced before replacement. On POSIX systems, the containing directory is fsynced after the directory entry changes.

Before the first replacement in an operation, the service writes a sidecar `.bak` containing the exact previous bytes of every existing target. The original source is not truncated in place. If a later replacement fails during a multi-file operation, already replaced files are restored in reverse order. Newly created targets are removed and newly created empty directories are cleaned up. If rollback itself fails, the error reports the recovery backup paths.

The package manifest is committed last during the legacy split migration. Therefore:
- Before the manifest pointer changes, the loader continues using the untouched legacy combined source.
- Once the new manifest is visible, all referenced split files have already been committed.
- If a process stops before the manifest update, the migration can be retried. Byte-identical orphaned files from the interrupted attempt are reused; conflicting unmanaged files are rejected rather than overwritten.
- The legacy `presentation_assets.json` is retained and never deleted by this migration.

A filesystem cannot atomically replace several independent paths in one primitive. Manifest-last publication plus prewritten backups and rollback is the package consistency strategy; it avoids publishing references to files that have not yet been committed.

## 5. Schema migration

The existing combined presentation format and the split presentation format both use their already-supported schema version 1. The migration changes the package manifest's source layout, not the meaning or version of the asset/placement records:

- `assets` becomes `asset_catalog.json` with `schema_version: 1`.
- Legacy object records are grouped by `map_id`.
- The per-object `map_id` is moved to the root of each `placements/<map_id>.json` document.
- Placement records retain their other fields and are validated by the current placement model.
- The manifest receives `asset_catalog` and `map_placements` pointers.
- The legacy combined file remains available for compatibility and comparison.

The migration is explicit, validates the source package before transforming it, validates the complete output package before committing, and is idempotent. It refuses a partially declared split manifest, conflicting orphaned files, unsupported fields, or invalid legacy content. It does not silently coerce or discard unknown placement fields.

The game-save migration in `application/migrations.py` remains separate; presentation-content schema migration must not be mixed into the player-save envelope.

## 6. Path and concurrency safety

All manifest-declared paths must be relative, use POSIX separators, contain no drive/absolute path or parent traversal, resolve inside the package root, and contain no symlink component. Map IDs used as placement filenames must be a single safe filename component.

A package-scoped cross-thread/cross-process lock serializes writes. The existing save-lock implementation is reused only as a generic lock primitive; game-save document schemas and save-slot behavior are not reused for content files.

## 7. Verification

Automated tests cover:

- deterministic UTF-8 serialization and successful reload;
- preservation of the previous file in `.bak`;
- invalid asset catalog and unsupported schema rejection without source replacement;
- rejection of non-finite values;
- invalid map placement rejection without source replacement;
- successful placement write and reload;
- manifest path traversal rejection;
- legacy combined-to-split migration and repeat-call idempotency;
- preservation of the legacy source;
- recovery from byte-identical orphaned files left by an interrupted migration;
- rejection of conflicting orphaned files and invalid legacy content;
- rollback when a later replacement in a multi-file migration fails.

The full repository CI matrix and release-candidate verification remain the final automated quality gates. Visual gameplay acceptance remains part of the broader Phase 8.8 gate, not a substitute for these persistence tests.
