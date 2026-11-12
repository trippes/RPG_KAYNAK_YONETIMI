# MainScreen — Axial Hex Runtime Integration

**Branch:** `demo_eldoria`  
**Scope:** Pygame presentation/input integration for the existing hex runtime  
**Status:** Implemented; automated CI verification pending

## Design boundary

The square-map gameplay model remains authoritative for the existing world. The
hex world is entered as a separate runtime session owned by
`HexWorldView`. While that view is active, the legacy square-world actor's
location and tile coordinates are not rewritten. Leaving the hex view discards
the temporary hex session and returns to the unchanged square-world state.

This is an integration bridge, not yet the final in-world portal implementation.
The **H** key is a temporary development entrance/exit so the two world models
can be exercised without selecting or revealing the future Easter-egg location.
The final portal should later be authored as an interactable world feature and
must preserve the same return-position contract.

## Runtime and presentation

- `HexWorldView` loads the content package's `hex_map_definitions` and
  `world_map_definition`.
- The player is registered in `HexWorldRuntime` on
  `hex_forest_demo`, starting at axial cell `(0, 0)`.
- The existing `HexWorldRuntime` remains responsible for six-direction
  movement, blocked-cell checks, occupancy, pathfinding, and map transitions.
- Pygame renders pointy-top axial hexes from the domain geometry helpers.
- Mouse clicks resolve pixel coordinates to axial coordinates and use runtime
  pathfinding to reach valid cells.
- The active reciprocal transition between `hex_forest_demo` and
  `hex_clearing_demo` is invoked with Enter while standing on its source cell.

## Controls

| Input | Action |
| --- | --- |
| H | Enter/leave the hex-world development bridge |
| Up | North-east |
| Right | East |
| Down | South-east |
| Left | West |
| Z | North-west |
| X | South-west |
| Left mouse click | Pathfind to a valid hex cell |
| Enter | Use a transition on the current cell |
| Escape | Open/close the in-game menu |

## Verification coverage

`tests/test_game_ui/test_hex_world_view.py` covers player registration,
keyboard movement through the runtime, blocked-cell rejection, reciprocal
hex-map transitions, preservation of the legacy actor state, and MainScreen's
development bridge toggle.

The GitHub Actions Core quality workflow is the authoritative automated
verification for this branch. Manual Pygame visual/input verification remains
necessary after pulling the branch locally.
