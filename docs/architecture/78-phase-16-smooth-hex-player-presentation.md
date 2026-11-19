# Phase 16 — Smooth Hex-Cell Player Presentation

Date: 2026-11-19

## Finding

The reported "cell skipping" impression was caused by the presentation layer, not by an intentional movement design. The authoritative runtime correctly committed movement one adjacent axial cell at a time, but `HexGameplayView.render` drew the player directly at the latest logical cell center. The character renderer was also always called with `moving=False`.

## Change

On `experiment/map-cleanup`:
- Added a presentation-only interpolated player position between adjacent axial cell centers.
- Applied the interpolation to keyboard movement and click-to-move.
- The camera now follows the interpolated visual position, rather than jumping between logical cell centers.
- The character renderer receives the actual moving state so its procedural walk cycle is active during movement.
- The authoritative `HexWorldRuntime` position, occupancy, pathfinding, collision checks, and save state remain cell-based and unchanged.
- Map transitions reset the visual interpolation state instead of animating across unrelated map coordinate spaces.
- Added tests for midpoint interpolation and completion at the destination.

Movement step interval and interpolation duration are currently both 0.18 seconds. This preserves the existing movement cadence while rendering the motion continuously.

## Verification

GitHub Actions: [44542287358](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44542287358)

Both Linux and Windows completed successfully:
- 2,275 tests passed on each platform;
- 235 subtests passed on each platform;
- Ruff, legacy-map boundary, and release-candidate verification passed.

## Manual acceptance still requested

Please relaunch the game and compare:
- keyboard movement across adjacent cells;
- click-to-move over a multi-cell route;
- movement around blocked cells.

The visual movement is now interpolated, but the final feel (speed, walk cycle, and camera follow) should be judged in the actual desktop build. Any tuning should change presentation timing only, not the authoritative hex movement or collision rules.
