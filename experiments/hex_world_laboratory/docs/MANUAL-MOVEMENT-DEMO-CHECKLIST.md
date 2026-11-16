# Manual Movement Demo Acceptance Checklist

**Purpose:** Validate the visible Pygame prototype on a real desktop. Automated/headless CI does not replace these checks.

## Before starting

- [ ] Activate the laboratory virtual environment.
- [ ] Run `python -m pytest -q` from `experiments/hex_world_laboratory`.
- [ ] Launch with `python -m hex_world_lab` (or the documented laboratory launch command).
- [ ] Confirm the window opens and shows the 61-cell flat-top hex test map.

## Movement

- [ ] Hold W / Up: actor moves north in world coordinates.
- [ ] Hold S / Down: actor moves south.
- [ ] Hold A / Left: actor moves west.
- [ ] Hold D / Right: actor moves east.
- [ ] Hold a diagonal direction: speed magnitude does not exceed a single-axis direction.
- [ ] Release all keys: actor stops.
- [ ] Switch focus away from the window while moving: actor stops on the next processed simulation tick.
- [ ] Return focus and press a movement key: movement resumes.

## Hex-world integration

- [ ] The highlighted axial cell follows the actor's physical position.
- [ ] The actor crosses cell boundaries without snapping to cell centers.
- [ ] Position diagnostics retain fractional world coordinates.
- [ ] Move beyond the explicit map cell set: the actor continues moving and cell data reports absent.
- [ ] The actor marker remains tied to its world position, not the selected cell center.

## Timing and diagnostics

- [ ] Diagnostics show WorldId and MapId.
- [ ] Position, velocity, speed, axial q/r and cell-data status are visible.
- [ ] Render FPS and tick-pump tick/debt values are visible.
- [ ] A temporary render slowdown does not silently discard pending tick debt.
- [ ] Close the window normally; the application exits without an exception.

## Result

- Date:
- OS / Python:
- Commit SHA:
- Result: PASS / FAIL / NOT RUN
- Notes / observed defects:

A check marked NOT RUN must remain an open acceptance item in the phase closure report. Do not report CI success as a substitute for this manual visual check.
