"""Three-session Phase 12 benchmark for environment snapshots, rendering and physics adapters."""
from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.environment import (
    EnvironmentalObjectDefinition, EnvironmentalObjectPlacement, EnvironmentalObjectScene,
    environment_debug_visuals, environment_obstacles, environment_sprite_visuals,
)
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.movement import Vector2
from hex_world_lab.physics import CircleShape, ConvexPolygonShape
from hex_world_lab.rendering import PygameWorldRenderer, SpriteAsset, WorldRenderSnapshot
from hex_world_lab.world import MapId, WorldId


class _UnculledRenderer(PygameWorldRenderer):
    """Same renderer path with only viewport sprite rejection disabled."""

    def _sprite_intersects_viewport(self, sprite, asset, transform) -> bool:
        return True


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))]


def measure(callable_, repeats: int = 20) -> dict[str, float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        callable_()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": percentile(samples, 0.95),
        "p99_ms": percentile(samples, 0.99),
    }


def build_scene(count: int) -> EnvironmentalObjectScene:
    world, map_id = WorldId("phase-12-benchmark"), MapId("environment-benchmark")
    definitions = (
        EnvironmentalObjectDefinition("tree", "tree", (0.5, 0.94), (0.5, 0.82), (0.05, 0.02, 0.9, 0.7), CircleShape(8.5)),
        EnvironmentalObjectDefinition("rock", "rock", (0.5, 0.92), (0.5, 0.84), None,
            ConvexPolygonShape((Vector2(-9, -7), Vector2(7, -9), Vector2(10, 3), Vector2(-3, 10)))),
        EnvironmentalObjectDefinition("bush", "bush", (0.5, 0.92), (0.5, 0.84), (0.05, 0.08, 0.9, 0.78), None),
    )
    placements = tuple(
        EnvironmentalObjectPlacement(
            f"instance-{index:05d}", ("tree", "rock", "bush")[index % 3],
            world, map_id, WorldPoint(float(index % 100) * 48.0, float(index // 100) * 42.0),
        )
        for index in range(count)
    )
    return EnvironmentalObjectScene(world, map_id, definitions, placements)


def build_renderers():
    surfaces = {}
    for key, size, fill in (
        ("tree", (100, 128), (56, 125, 67, 255)),
        ("rock", (48, 36), (115, 125, 140, 255)),
        ("bush", (62, 44), (70, 145, 82, 255)),
    ):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(fill)
        surfaces[key] = SpriteAsset(surface, 0.5, 0.94)
    return PygameWorldRenderer(surfaces), _UnculledRenderer(surfaces), {
        key: asset.surface.get_size() for key, asset in surfaces.items()
    }


def main() -> None:
    pygame.init()
    try:
        renderer, unculled_renderer, asset_sizes = build_renderers()
        viewport = Viewport(960, 640)
        transform = WorldScreenTransform(viewport, WorldPoint(0, 0), 1.0)
        layout = HexLayout(HexOrientation.FLAT_TOP, 32.0)
        surface = pygame.Surface((viewport.width, viewport.height))
        report = {
            "phase": 12,
            "sessions": 3,
            "runtime": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
            },
            "asset_sizes": {key: list(value) for key, value in asset_sizes.items()},
            "profiles": {},
        }
        for count in (10, 100, 1000):
            sessions = []
            tracemalloc.start()
            for _session_index in range(3):
                session = {
                    "scene_construction": measure(lambda: build_scene(count), repeats=10),
                }
                scene = build_scene(count)
                session["obstacle_adapter"] = measure(lambda: environment_obstacles(scene))
                obstacles = environment_obstacles(scene)
                session["sprite_snapshot_adapter"] = measure(
                    lambda: environment_sprite_visuals(scene, asset_sizes)
                )
                sprites = environment_sprite_visuals(scene, asset_sizes)
                session["debug_bounds_adapter"] = measure(
                    lambda: environment_debug_visuals(scene, asset_sizes)
                )
                snapshot = WorldRenderSnapshot(
                    cells=(), circles=(), polygons=(), boundaries=(), house_lines=(),
                    actor_position=WorldPoint(10_000, 10_000), actor_radius=1.0,
                    sprites=sprites,
                )
                session["render_with_culling"] = measure(
                    lambda: renderer.render(surface, snapshot, layout, transform), repeats=8
                )
                session["render_without_culling"] = measure(
                    lambda: unculled_renderer.render(surface, snapshot, layout, transform), repeats=8
                )
                visible_count = sum(
                    renderer._sprite_intersects_viewport(
                        sprite, renderer._sprite_assets[sprite.asset_key], transform
                    )
                    for sprite in sprites
                )
                session["instance_count"] = count
                session["obstacle_count"] = len(obstacles)
                session["visible_sprite_count"] = visible_count
                session["culled_sprite_count"] = count - visible_count
                sessions.append(session)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            report["profiles"][str(count)] = {
                "instances": count,
                "sessions": sessions,
                "peak_traced_bytes": peak,
            }

        output = Path("artifacts/phase-12")
        output.mkdir(parents=True, exist_ok=True)
        path = output / "environment-benchmark.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(path)
        for count, profile in report["profiles"].items():
            def session_median(key: str) -> float:
                return statistics.median(item[key]["median_ms"] for item in profile["sessions"])
            visible = profile["sessions"][0]["visible_sprite_count"]
            culled = profile["sessions"][0]["culled_sprite_count"]
            print(
                f"{count} objects: obstacles={session_median('obstacle_adapter'):.4f}ms "
                f"snapshot={session_median('sprite_snapshot_adapter'):.4f}ms "
                f"debug={session_median('debug_bounds_adapter'):.4f}ms "
                f"render(culled)={session_median('render_with_culling'):.4f}ms "
                f"render(unculled)={session_median('render_without_culling'):.4f}ms "
                f"visible={visible} culled={culled}"
            )
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
