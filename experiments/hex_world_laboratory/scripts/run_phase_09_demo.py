"""Backward-compatible Phase 9 launcher.

Use the laboratory's original entry point instead:
    python -m hex_world_lab
This wrapper intentionally delegates to that same application.
"""
from hex_world_lab.app import main


if __name__ == "__main__":
    main()
