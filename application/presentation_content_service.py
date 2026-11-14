"""UI-independent application services for presentation content authoring tools.

The service is a narrow facade over the established package loader, catalog
models, placement model, and safe persistence store. It contains no Pygame or
editor-widget dependencies.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .content_loader import ContentPackage, ContentPackageError, load_content_package
from .presentation_content_store import (
    ContentMigrationResult,
    ContentWriteResult,
    PresentationContentStore,
    PresentationContentStoreError,
)


class PresentationContentServiceError(RuntimeError):
    """A presentation-content service operation could not be completed."""


@dataclass(frozen=True, slots=True)
class ContentValidationIssue:
    """Structured validation finding suitable for any future UI or CLI."""

    code: str
    message: str
    severity: str = "error"
    source: str | None = None


@dataclass(frozen=True, slots=True)
class ContentValidationResult:
    """Validation outcome; warnings do not make an otherwise valid package fail."""

    valid: bool
    issues: tuple[ContentValidationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ContentMigrationStatus:
    """Describes the presentation source layout without changing package files."""

    source_format: str
    schema_version: int | None
    migration_available: bool


class PresentationContentService:
    """Stable, UI-neutral read/validate/save boundary for one content package."""

    MANIFEST_NAME = "manifest.json"

    def __init__(self, content_root: str | Path) -> None:
        self.content_root = Path(content_root).resolve()
        self._store = PresentationContentStore(self.content_root)

    def load_package(self) -> ContentPackage:
        """Load and fully validate the package through the canonical loader."""
        try:
            return load_content_package(self.content_root)
        except (ContentPackageError, OSError, ValueError, TypeError) as error:
            raise PresentationContentServiceError(str(error)) from error

    def load_asset_catalog(self):
        """Return the validated asset catalog, or None when the package has none."""
        return self.load_package().presentation_catalog

    def list_assets(self, category: str | None = None) -> tuple:
        """List immutable asset definitions, optionally filtered by category."""
        catalog = self.load_asset_catalog()
        return () if catalog is None else catalog.list_assets(category)

    def get_asset(self, asset_id: str):
        """Resolve an asset ID; return None when the ID is not present."""
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ValueError("asset_id must be a non-empty string.")
        catalog = self.load_asset_catalog()
        return None if catalog is None else catalog.get(asset_id)

    def load_map_placements(self, map_id: str) -> tuple:
        """Return immutable placements for a known map."""
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        package = self.load_package()
        if map_id not in package.hex_map_definitions:
            raise PresentationContentServiceError(f"Unknown hex map ID: {map_id}")
        catalog = package.scene_placements
        return () if catalog is None else catalog.objects_for_map(map_id)

    def validate_content_package(self) -> ContentValidationResult:
        """Validate the whole package and expose cached PNG diagnostics as warnings."""
        try:
            package = self.load_package()
        except PresentationContentServiceError as error:
            return ContentValidationResult(
                False,
                (ContentValidationIssue("invalid_package", str(error)),),
            )
        issues = []
        catalog = package.presentation_catalog
        if catalog is not None:
            issues.extend(
                ContentValidationIssue(
                    issue.code,
                    issue.message,
                    "warning",
                    issue.asset_id,
                )
                for issue in catalog.validate_assets()
            )
        return ContentValidationResult(True, tuple(issues))

    def validate_asset_catalog(self, draft: dict) -> ContentValidationResult:
        """Validate an in-memory catalog draft against the complete package."""
        return self._validate_draft("asset_catalog", draft)

    def validate_map_placements(
        self, map_id: str, draft: dict
    ) -> ContentValidationResult:
        """Validate an in-memory map placement draft without touching live files."""
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        return self._validate_draft("placements", draft, map_id=map_id)

    def save_asset_catalog(self, draft: dict) -> ContentWriteResult:
        """Persist a valid catalog draft through the safe store."""
        try:
            result = self._store.save_asset_catalog(draft)
            self.load_package()
            return result
        except (PresentationContentStoreError, PresentationContentServiceError) as error:
            raise PresentationContentServiceError(str(error)) from error

    def save_map_placements(self, map_id: str, draft: dict) -> ContentWriteResult:
        """Persist one valid map draft through the safe store."""
        try:
            result = self._store.save_map_placements(map_id, draft)
            self.load_package()
            return result
        except (PresentationContentStoreError, PresentationContentServiceError) as error:
            raise PresentationContentServiceError(str(error)) from error

    def migration_status(self) -> ContentMigrationStatus:
        """Report legacy/split source state without performing a migration."""
        manifest_path = self.content_root / self.MANIFEST_NAME
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PresentationContentServiceError(
                f"Content package manifest could not be read: {manifest_path}"
            ) from error
        if not isinstance(manifest, dict):
            raise PresentationContentServiceError("Content package manifest must be an object.")
        has_catalog = "asset_catalog" in manifest
        has_placements = "map_placements" in manifest
        if has_catalog != has_placements:
            raise PresentationContentServiceError(
                "Package declares an incomplete split presentation source."
            )
        source_format = "none"
        source_path = None
        migration_available = False
        if has_catalog:
            source_format = "split"
            source_path = manifest.get("asset_catalog")
        elif manifest.get("presentation_assets") is not None:
            source_format = "legacy_combined"
            source_path = manifest.get("presentation_assets")
            migration_available = True
        if source_path is None:
            return ContentMigrationStatus(source_format, None, migration_available)
        if not isinstance(source_path, str) or not source_path.strip():
            raise PresentationContentServiceError("Presentation source path is invalid.")
        try:
            schema_document = json.loads(
                (self.content_root / source_path).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PresentationContentServiceError(
                f"Presentation schema source could not be read: {source_path}"
            ) from error
        schema_version = (
            schema_document.get("schema_version")
            if isinstance(schema_document, dict)
            and type(schema_document.get("schema_version")) is int
            else None
        )
        return ContentMigrationStatus(
            source_format, schema_version, migration_available
        )

    def migrate_legacy_content(self) -> ContentMigrationResult:
        """Explicitly migrate legacy presentation data; never run during reads."""
        try:
            result = self._store.migrate_legacy_combined_presentation()
            self.load_package()
            return result
        except (PresentationContentStoreError, PresentationContentServiceError) as error:
            raise PresentationContentServiceError(str(error)) from error

    def _validate_draft(
        self, kind: str, draft: dict, *, map_id: str | None = None
    ) -> ContentValidationResult:
        if not isinstance(draft, dict):
            raise TypeError("Content draft must be a JSON object.")
        try:
            with tempfile.TemporaryDirectory(prefix="eldoria-content-validation-") as temp:
                staged_root = Path(temp) / self.content_root.name
                shutil.copytree(
                    self.content_root,
                    staged_root,
                    symlinks=True,
                    ignore=shutil.ignore_patterns(".manifest.json.lock"),
                )
                staged_store = PresentationContentStore(staged_root)
                if kind == "asset_catalog":
                    staged_store.save_asset_catalog(draft)
                else:
                    staged_store.save_map_placements(map_id, draft)
                load_content_package(staged_root)
        except (
            OSError,
            ValueError,
            TypeError,
            PresentationContentStoreError,
            ContentPackageError,
        ) as error:
            return ContentValidationResult(
                False,
                (ContentValidationIssue("invalid_draft", str(error), source=kind),),
            )
        return ContentValidationResult(True)
