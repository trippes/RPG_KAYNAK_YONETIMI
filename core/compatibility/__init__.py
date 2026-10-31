"""Explicit 1.x compatibility boundary and deprecation metadata."""

from .deprecation import LEGACY_API_MATRIX, CompatibilityEntry, compatibility_entry, deprecated_api, warn_deprecated
from .migration import DEFAULT_REGISTRY, canonical_for, get_all_mappings, get_mapping, is_legacy, status_for
from .action_adapter import CanonicalActionAdapter


def record_usage(*args, **kwargs):
    from .usage import record_usage as function
    return function(*args, **kwargs)


def reset_runtime_usage(*args, **kwargs):
    from .usage import reset_runtime_usage as function
    return function(*args, **kwargs)


def runtime_usage_counts(*args, **kwargs):
    from .usage import runtime_usage_counts as function
    return function(*args, **kwargs)


def scan_static_usage(*args, **kwargs):
    from .usage import scan_static_usage as function
    return function(*args, **kwargs)


def usage_report(*args, **kwargs):
    from .usage import usage_report as function
    return function(*args, **kwargs)

__all__ = [
    "LEGACY_API_MATRIX", "CompatibilityEntry", "compatibility_entry", "deprecated_api", "warn_deprecated",
    "DEFAULT_REGISTRY", "get_mapping", "get_all_mappings", "is_legacy", "canonical_for", "status_for",
    "record_usage", "reset_runtime_usage", "runtime_usage_counts", "scan_static_usage", "usage_report",
    "CanonicalActionAdapter",
]
