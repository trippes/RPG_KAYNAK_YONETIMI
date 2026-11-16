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

## Movement modes

- [ ] Normal movement shows `Mode: NORMAL`, `Multiplier: 1.00x` and the configured base speed.
- [ ] Hold left or right Shift: actor moves at 1.5x and the panel shows `RUNNING` / `1.50x`.
- [ ] Release Shift: mode returns to Normal.
- [ ] Press Alt once: `STEALTH` / `0.50x` activates and remains active after Alt is released.
- [ ] Press Alt a second time (after releasing it): Stealth turns off and mode returns to Normal when Shift is not held.
- [ ] Hold Alt down: Stealth toggles only once; it does not repeatedly switch while held.
- [ ] Press both left and right Alt together: they produce one toggle, not two.
- [ ] While Stealth is active, hold Shift: Stealth remains active.
- [ ] While Stealth and Shift are both active, press Alt again: Stealth turns off and Running becomes active.
- [ ] On focus loss, Stealth resets and movement stops; after focus regain, a still-held Alt key does not reactivate Stealth until Alt is released and pressed again.
- [ ] When the actor is stationary, the selected mode and theoretical mode speed remain visible while actual Velocity speed is zero.
- [ ] While moving, Velocity reports the actual movement vector and speed.
- [ ] If the configured base speed is changed, Mode speed changes proportionally (for example, base 40 gives 40 / 60 / 20 units per second).

## Hex-world integration

- [ ] The highlighted axial cell follows the actor's physical position.
- [ ] The actor crosses cell boundaries without snapping to cell centers.
- [ ] Position diagnostics retain fractional world coordinates.
- [ ] Move beyond the explicit map cell set: the actor continues moving and cell data reports absent.
- [ ] The actor marker remains tied to its world position, not the selected cell center.

## Timing and diagnostics

- [ ] Diagnostics show WorldId and MapId.
- [ ] Position, actual velocity, actual speed, axial q/r and cell-data status are visible.
- [ ] Mode, configured multiplier and theoretical mode speed are visible as separate diagnostics.
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
