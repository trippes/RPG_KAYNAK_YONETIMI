"""Measure sparse runtime snapshot serialization and file persistence."""

from __future__ import annotations

import tempfile
import time
import tracemalloc
from pathlib import Path

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import CellAddress, HexCellData, HexMapDefinition, HexWorld, MapId, WorldId
from hex_world_lab.world.persistence import (
    deserialize_runtime_payload,
    runtime_to_payload,
    save_runtime_file,
    serialize_runtime,
    load_runtime_file,
)


def run_case(count: int) -> None:
    world_id, map_id = WorldId("benchmark"), MapId(f"map_{count}")
    cells = {
        AxialCoord(index, 0): HexCellData("grass", True, False)
        for index in range(count)
    }
    definition = HexMapDefinition(
        world_id, map_id, "Runtime persistence benchmark",
        HexLayout(HexOrientation.POINTY_TOP, 1.0), cells,
    )
    world = HexWorld(world_id)
    world.register_map(map_id, definition.name)
    world.load_map(definition)
    for index in range(count):
        world.runtime.set_terrain(
            CellAddress(world_id, map_id, AxialCoord(index, 0)),
            f"terrain_{index}",
        )

    tracemalloc.start()
    start = time.perf_counter()
    text = serialize_runtime(world.runtime, definition)
    serialize_ms = (time.perf_counter() - start) * 1000
    payload = runtime_to_payload(world.runtime, definition)
    start = time.perf_counter()
    deserialize_runtime_payload(payload, definition)
    deserialize_ms = (time.perf_counter() - start) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "runtime.json"
        start = time.perf_counter()
        save_runtime_file(world.runtime, definition, path)
        save_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        load_runtime_file(path, definition)
        load_ms = (time.perf_counter() - start) * 1000

    print(
        f"{count:>6} overrides | {len(text.encode('utf-8')):>9} bytes | "
        f"serialize {serialize_ms:>8.2f} ms | deserialize {deserialize_ms:>8.2f} ms | "
        f"save {save_ms:>8.2f} ms | load {load_ms:>8.2f} ms | "
        f"peak {peak / 1024:>9.1f} KiB"
    )


if __name__ == "__main__":
    print("Runtime persistence benchmark (single local run; no timing guarantee)")
    for size in (100, 1_000, 10_000):
        run_case(size)
