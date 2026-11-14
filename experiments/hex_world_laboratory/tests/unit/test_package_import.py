"""Unit tests for package metadata and importability."""

import hex_world_lab


def test_package_exposes_version() -> None:
    assert hex_world_lab.__version__ == "0.1.0"
