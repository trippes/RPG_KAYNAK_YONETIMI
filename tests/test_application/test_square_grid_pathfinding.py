"""A* correctness, deterministic ordering, clearance and safety tests."""
import math

import pytest

from application.square_grid_coverage import (
    HexCellCoverage,
    SquareGridCellCoverage,
    SquareGridCellStatus,
    SquareGridCoverageMap,
)
from application.square_grid_pathfinding import (
    SquareGridNavigationProfile,
    SquareGridPathfinder,
    make_physics_edge_validator,
)
from core.domain.spatial import (
    LocalHexPosition,
    MovementProfile,
    SquareGridCoord,
    WorldPoint,
)


def _coverage(rows, *, cell_size=1.0):
    cells = {}
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value is None:
                status = SquareGridCellStatus.BLOCKED
                hex_cells = ()
            else:
                status = SquareGridCellStatus.WALKABLE
                terrain_id = value if isinstance(value, str) else "grass"
                hex_cells = (
                    HexCellCoverage(
                        LocalHexPosition(0, 0), terrain_id, False, cell_size * cell_size
                    ),
                )
            coord = SquareGridCoord(x, y)
            cells[coord] = SquareGridCellCoverage(
                coord, WorldPoint(x * cell_size, y * cell_size), hex_cells,
                cell_size * cell_size, 1.0, status,
            )
    return SquareGridCoverageMap(
        "test-map", cell_size, WorldPoint(0.0, 0.0), WorldPoint(0.0, 0.0), cells
    )


def _cost(path):
    total = 0.0
    for left, right in zip(path, path[1:]):
        dx, dy = abs(right.x - left.x), abs(right.y - left.y)
        total += math.sqrt(2.0) if dx and dy else 1.0
    return total


def test_cardinal_and_diagonal_routes_use_eight_neighbours():
    coverage = _coverage([["grass"] * 4 for _ in range(4)])
    cardinal = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(3, 0)
    )
    diagonal = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(3, 3)
    )
    assert cardinal == tuple(SquareGridCoord(x, 0) for x in range(4))
    assert diagonal == tuple(SquareGridCoord(i, i) for i in range(4))
    assert _cost(diagonal) == pytest.approx(3 * math.sqrt(2.0))


def test_diagonal_corner_cutting_is_forbidden():
    coverage = _coverage([
        ["grass", None],
        [None, "grass"],
    ])
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(1, 1)
    ) is None


def test_diagonal_requires_both_orthogonal_cells_to_be_walkable():
    coverage = _coverage([
        ["grass", "grass"],
        [None, "grass"],
    ])
    path = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(1, 1)
    )
    assert path == (
        SquareGridCoord(0, 0),
        SquareGridCoord(1, 0),
        SquareGridCoord(1, 1),
    )


def test_blocked_and_outside_cells_are_not_route_nodes():
    coverage = _coverage([["grass", None, "grass"]])
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(2, 0)
    ) is None


def test_weighted_terrain_prefers_a_longer_but_cheaper_route():
    coverage = _coverage([
        ["grass", "grass", "grass"],
        ["grass", "mud", "grass"],
        ["grass", "grass", "grass"],
    ])
    path = SquareGridPathfinder.find_path(
        coverage,
        SquareGridCoord(0, 1),
        SquareGridCoord(2, 1),
        terrain_costs={"mud": 20.0},
    )
    assert path is not None
    assert SquareGridCoord(1, 1) not in path
    assert len(path) > 3


def test_allowed_terrain_profile_rejects_disallowed_terrain():
    coverage = _coverage([["grass", "water", "grass"]])
    path = SquareGridPathfinder.find_path(
        coverage,
        SquareGridCoord(0, 0),
        SquareGridCoord(2, 0),
        profile=SquareGridNavigationProfile(
            MovementProfile(allowed_terrain_ids=frozenset({"grass"}))
        ),
    )
    assert path is None


def test_collider_clearance_rejects_cells_too_close_to_blocked_geometry():
    rows = [["grass"] * 7 for _ in range(7)]
    rows[3][3] = None
    coverage = _coverage(rows, cell_size=10.0)
    path = SquareGridPathfinder.find_path(
        coverage,
        SquareGridCoord(1, 3),
        SquareGridCoord(5, 3),
        profile=SquareGridNavigationProfile(collider_radius=6.0),
    )
    assert path is not None
    assert SquareGridCoord(3, 3) not in path
    assert len(path) > 5


def test_edge_validator_rejects_physics_blocked_shortcut_and_finds_detour():
    coverage = _coverage([["grass"] * 3 for _ in range(3)])
    rejected = {
        (SquareGridCoord(0, 1), SquareGridCoord(1, 1)),
        (SquareGridCoord(1, 1), SquareGridCoord(2, 1)),
    }
    seen = []

    def validator(start, end):
        seen.append((start, end))
        left = SquareGridCoord(round(start.x), round(start.y))
        right = SquareGridCoord(round(end.x), round(end.y))
        return (left, right) not in rejected

    path = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 1), SquareGridCoord(2, 1),
        edge_validator=validator,
    )
    assert path is not None
    assert SquareGridCoord(1, 1) not in path
    assert seen


def test_deterministic_tie_breaking_returns_same_route_repeatedly():
    coverage = _coverage([["grass"] * 3 for _ in range(3)])
    routes = {
        SquareGridPathfinder.find_path(
            coverage, SquareGridCoord(0, 0), SquareGridCoord(2, 2)
        )
        for _ in range(10)
    }
    assert len(routes) == 1


def test_negative_coordinates_are_supported():
    source = _coverage([["grass"] * 3 for _ in range(3)])
    shifted = {}
    for coord, cell in source.cells.items():
        shifted_coord = SquareGridCoord(coord.x - 2, coord.y - 2)
        shifted[shifted_coord] = SquareGridCellCoverage(
            shifted_coord,
            WorldPoint(shifted_coord.x, shifted_coord.y),
            cell.hex_cells, cell.covered_area, cell.coverage_ratio, cell.status,
        )
    coverage = SquareGridCoverageMap(
        "negative-map", 1.0, WorldPoint(0.0, 0.0), WorldPoint(0.0, 0.0), shifted
    )
    path = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(-2, -2), SquareGridCoord(0, 0)
    )
    assert path == (
        SquareGridCoord(-2, -2),
        SquareGridCoord(-1, -1),
        SquareGridCoord(0, 0),
    )


def test_start_or_goal_outside_walkable_coverage_returns_none():
    coverage = _coverage([["grass", None]])
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(-1, 0), SquareGridCoord(0, 0)
    ) is None
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(1, 0)
    ) is None


def test_disabled_movement_and_dynamic_occupancy_are_respected():
    coverage = _coverage([["grass"] * 3])
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(2, 0),
        profile=SquareGridNavigationProfile(MovementProfile(can_move=False)),
    ) is None
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(2, 0),
        blocked_cells={SquareGridCoord(1, 0)},
    ) is None


def test_occupancy_can_be_ignored_without_ignoring_static_geometry():
    coverage = _coverage([["grass"] * 3])
    path = SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(2, 0),
        profile=SquareGridNavigationProfile(MovementProfile(ignores_occupancy=True)),
        blocked_cells={SquareGridCoord(1, 0)},
    )
    assert path == (
        SquareGridCoord(0, 0), SquareGridCoord(1, 0), SquareGridCoord(2, 0)
    )


def test_profile_can_traverse_blocked_cells_when_physics_allows_it():
    coverage = _coverage([["grass", None, "grass"]])
    path = SquareGridPathfinder.find_path(
        coverage,
        SquareGridCoord(0, 0),
        SquareGridCoord(2, 0),
        profile=SquareGridNavigationProfile(
            MovementProfile(can_traverse_blocked_cells=True)
        ),
        edge_validator=lambda _start, _end: True,
    )
    assert path == (
        SquareGridCoord(0, 0), SquareGridCoord(1, 0), SquareGridCoord(2, 0)
    )


def test_start_equals_goal_returns_single_cell():
    coverage = _coverage([["grass"]])
    assert SquareGridPathfinder.find_path(
        coverage, SquareGridCoord(0, 0), SquareGridCoord(0, 0)
    ) == (SquareGridCoord(0, 0),)


def test_invalid_profiles_and_costs_are_rejected():
    coverage = _coverage([["grass"]])
    with pytest.raises(ValueError):
        SquareGridNavigationProfile(collider_radius=-1.0)
    with pytest.raises(ValueError):
        SquareGridPathfinder.find_path(
            coverage, SquareGridCoord(0, 0), SquareGridCoord(0, 0),
            terrain_costs={"mud": 0.0},
        )


def test_physics_edge_validator_uses_snapshot_and_actual_body_radius():
    from application.hex_map_definition import parse_hex_map
    from application.hex_physics_bridge import build_hex_physics_snapshot
    from core.domain.physics import CircleShape, PhysicsBodyDefinition, StaticObstacle
    from core.foundation import WorldId

    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "physics-validator-map",
        "name": "Physics validator map",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0]],
    })
    body = PhysicsBodyDefinition(
        "test-body", CircleShape(2.0, WorldPoint(0.0, 0.0))
    )
    start = WorldPoint(-8.0, 0.0)
    end = WorldPoint(8.0, 0.0)
    clear_snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"), definition, 32.0
    )
    assert make_physics_edge_validator(clear_snapshot, body)(start, end)

    rock = StaticObstacle(
        "test-rock",
        definition.map_id,
        CircleShape(3.0, WorldPoint(0.0, 0.0)),
        WorldPoint(0.0, 0.0),
    )
    blocked_snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"), definition, 32.0, object_obstacles=(rock,)
    )
    assert not make_physics_edge_validator(blocked_snapshot, body)(start, end)
