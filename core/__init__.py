"""Canonical Core package boundary.

The root package intentionally exports no symbols. Consumers should import
from the owning public layer (core.foundation, core.domain, core.simulation,
core.persistence or core.application) explicitly. This prevents legacy Core
modules from becoming accidental public API.
"""

__all__: tuple[str, ...] = ()
