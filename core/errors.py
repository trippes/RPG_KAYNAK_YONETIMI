"""Shared exception root for domain and application failures.

Concrete exceptions keep their standard-library base classes as additional
parents, so existing callers catching ValueError, RuntimeError or OSError
remain compatible while applications can catch RPGError consistently.
"""

class RPGError(Exception):
    """Base class for expected, project-defined RPG failures."""

__all__ = ["RPGError"]
