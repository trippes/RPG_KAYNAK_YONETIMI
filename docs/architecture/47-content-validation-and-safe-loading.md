# Content Validation and Safe Loading Contract

## 1. Purpose

This document defines the Phase 8.5 validation boundary for Eldoria content packages. Its purpose is to ensure that malformed presentation metadata or unresolved map placements are rejected before a package exposes presentation data to the game runtime.

This is a data-loading contract only. It does not introduce a Content Editor UI, persistence operations, schema migrations, or new gameplay behavior.

## 2. Validation boundary

`application.content_loader.load_content_package` is the package entry point. It now completes presentation validation and constructs the presentation snapshot before returning a `ContentPackage`.

The loader reuses the existing domain models rather than creating a second asset or placement implementation:

- `AssetCatalog.load` parses asset metadata, enforces the schema and asset-ID contract, resolves safe relative PNG paths, and records source-file diagnostics.
- `ScenePlacementCatalog.load_directory` parses map-scoped placements, enforces placement geometry and IDs, resolves asset references, and can validate map IDs and map-cell coordinates.
- `HexMapDefinition` remains the authority for valid axial cells.
- `HexWorldView` consumes the already validated catalog and placement snapshot from `ContentPackage`; it does not independently rebuild the split sources on the normal package path.

The catalog and placement models remain Pygame-independent. The package loader imports them only at the presentation-validation boundary.

## 3. Validation layers

| Layer | Validation | Failure behavior |
|---|---|---|
| Package/file | Manifest, declared data files, safe package-relative paths, readable files | Reject package |
| JSON | Valid JSON and expected root object/list types | Reject affected content package |
| Schema | Exact supported integer schema version and required fields | Reject package |
| Identity | Unique non-empty asset and object IDs | Reject package |
| Asset references | Every placement references an existing asset | Reject package |
| Map references | Every placement references a known hex map | Reject package |
| Geometry | Finite offsets/depth, integer axial coordinates, valid footprint/collision geometry | Reject placement set |
| Map-cell compatibility | Each placement q/r resolves to a valid cell in its declared hex map | Reject placement set |
| Source image | PNG signature/chunks/CRC/decompression and metadata dimensions | Retain catalog diagnostic; use existing image fallback path |

The package is not returned with a partially populated presentation catalog or placement set. Split catalog and placement sources are parsed into local variables and attached to the immutable package snapshot only after both have succeeded.

## 4. Fatal errors and non-fatal image diagnostics

Malformed metadata, unsupported schema versions, duplicate IDs, unsafe paths, unknown asset references, unknown map references, and coordinates outside a map's valid cells are fatal content errors. They are surfaced as `ContentPackageError` with the originating validation detail.

Missing, unreadable, corrupt, or dimension-mismatched PNG sources remain catalog diagnostics rather than package-structure failures. This preserves the established deterministic renderer fallback behavior. The diagnostics are available through `AssetCatalog.validate_assets()`; callers do not need to reopen or re-parse PNG files for each query.

The existing `AssetCatalog.available()` semantics are retained for compatibility. It reports whether the referenced path exists; `is_valid()` reports whether the source passed the catalog's cached validation checks.

## 5. Split and legacy content

For split presentation content:

1. Load and validate `asset_catalog.json`.
2. Load every map placement document.
3. Resolve each placement's asset ID.
4. Verify the placement's map ID against the loaded hex map definitions.
5. Verify q/r against the target map's valid-cell set.
6. Publish both immutable snapshots together on `ContentPackage`.

For legacy combined `presentation_assets.json` content, the existing `AssetCatalog.load` parser remains the compatibility path. Its embedded placements receive the same map-ID and valid-cell checks before the package is returned.

When split sources are present, they remain the runtime source of truth; the legacy file is retained for backward compatibility and equivalence checks.

The current placement schema is axial q/r and therefore validates against hex map definitions. Square-map coordinates are not converted to q/r and the square-map loader remains unchanged.

## 6. Runtime handoff

`ContentPackage` now exposes:

- `presentation_catalog`: the validated `AssetCatalog` snapshot, or `None` when the package has no presentation assets.
- `scene_placements`: the validated split `ScenePlacementCatalog`, or `None` for legacy combined content/no split placement source.

The hex world view reuses these instances. This avoids a second parse of the same package presentation files during normal runtime initialization.

A failed presentation validation prevents the package from being returned as a valid package. Existing runtime fallback behavior for individual missing/corrupt image files is separate from fatal package-structure errors.

## 7. Read-only guarantee and phase boundary

Phase 8.5 performs reads and validation only. It does not rewrite, normalize, migrate, repair, or save content files. A failed load therefore cannot replace or truncate a previously valid source file.

Atomic writes, backups, deterministic serialization, and schema migration belong to Phase 8.6 and are intentionally not implemented here.

## 8. Explicitly unchanged systems

- Hex geometry and axial coordinate calculations.
- `HexWorldRuntime`, `WorldTransform`, camera, movement, collision, occupancy, and pathfinding.
- Map transitions and world-map connections.
- Square-map definitions and runtime.
- Renderer depth ordering, tree PNG presentation, and tree-rig default-off behavior.
- AssetManager cache policy and deterministic image fallback.
- Normal gameplay UI; no Content Editor UI or edit mode is introduced.

## 9. Verification expectations

Automated tests cover valid package snapshot creation, duplicate asset IDs, unknown map IDs, coordinates outside valid map cells, unsupported boolean schema versions, missing PNG diagnostics, legacy combined content, and read-only failure behavior. Existing AssetCatalog and placement catalog tests continue to cover malformed JSON, invalid geometry, unknown asset references, duplicate object IDs, and corrupt PNG diagnostics.

Full-suite CI and manual gameplay acceptance remain separate quality gates. A successful unit-test run does not replace the user's visual/manual acceptance.
