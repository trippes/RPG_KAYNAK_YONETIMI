"""Read-only migration registry facade."""

from types import MappingProxyType

from .deprecation import CompatibilityEntry, LEGACY_API_MATRIX


class MigrationRegistry:
    def __init__(self, mappings=None) -> None:
        source = LEGACY_API_MATRIX if mappings is None else mappings
        self._mappings = MappingProxyType(dict(sorted(source.items())))

    def get_mapping(self, legacy_identifier: str) -> CompatibilityEntry:
        return self._mappings[legacy_identifier]

    def get_all_mappings(self) -> tuple[CompatibilityEntry, ...]:
        return tuple(self._mappings.values())

    def is_legacy(self, identifier: str) -> bool:
        return identifier in self._mappings

    def canonical_for(self, legacy_identifier: str) -> str:
        return self.get_mapping(legacy_identifier).canonical_replacement

    def status_for(self, legacy_identifier: str) -> str:
        return self.get_mapping(legacy_identifier).status

    def as_mapping(self):
        return self._mappings


DEFAULT_REGISTRY = MigrationRegistry()

get_mapping = DEFAULT_REGISTRY.get_mapping
get_all_mappings = DEFAULT_REGISTRY.get_all_mappings
is_legacy = DEFAULT_REGISTRY.is_legacy
canonical_for = DEFAULT_REGISTRY.canonical_for
status_for = DEFAULT_REGISTRY.status_for
