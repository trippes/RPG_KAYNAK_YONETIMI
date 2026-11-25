"""End-to-end GameApplication save/load coverage for authoritative hex state."""

import json

import pytest

from application import (
    GameApplication,
    GameplayService,
    HexWorldPersistenceError,
)
from application.content_loader import load_content_package
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId
from npc import NPC
from resources import Quantity, ResourceType, ResourceUnit, WorldResourceNode


def create_content_package(tmp_path):
    root = tmp_path / "hex-save-package"
    maps = root / "maps"
    maps.mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "package_id": "hex-save-test",
        "package_version": "1.0.0",
        "files": {"starter": "starter.json"},
        "maps": "maps",
        "world_map": "world-map.json",
    }), encoding="utf-8")
    (root / "starter.json").write_text(
        json.dumps({"schema_version": 1}),
        encoding="utf-8",
    )
    (maps / "field.json").write_text(json.dumps({
        "schema_version": 2,
        "map_id": "field",
        "name": "Field",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0]],
        "cell_overrides": [],
        "transitions": [],
    }), encoding="utf-8")
    (root / "world-map.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "test-world-map",
        "name": "Test World Map",
        "maps": [{
            "map_id": "field",
            "position": {"q": 0, "r": 0},
        }],
    }), encoding="utf-8")
    return root


def make_application(tmp_path):
    app = GameApplication.create_default()
    app._content_package_path = create_content_package(tmp_path)
    bundle = app.holder.current
    world = bundle.session.worlds.create("Save World", world_id="save-world")
    bundle.session.worlds.set_active(world.world_id)

    service = GameplayService(app)
    service.configure_player_context("hero", "player", "hero")
    service.register_actor("hero", "player")
    service.register_npc(NPC("guard", "Guard"))
    service.register_actor("guard", "npc")
    bundle = app.holder.current
    bundle.resource_nodes.add(WorldResourceNode(
        "iron-node",
        world.world_id,
        ResourceType("iron"),
        Quantity(8, ResourceUnit.ITEM),
        Quantity(10, ResourceUnit.ITEM),
        Quantity(1, ResourceUnit.ITEM),
    ))

    package = load_content_package(app._content_package_path)
    runtime = HexWorldRuntime(
        package.hex_map_definitions,
        world_map_definition=package.world_map_definition,
        world_id=WorldId(world.world_id),
    )
    service.hex_world_runtime_owner.get_or_create(lambda: runtime)
    service.hex_actor_binding.register_spatial(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )
    service.npc_hex_binding.register_spatial(
        "guard",
        EntityPosition("field", LocalHexPosition(1, 0)),
    )
    service.resource_node_hex_binding.register_spatial(
        "iron-node",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )
    runtime.restore_patrol_indices({"guard": 2})
    return app, bundle, runtime


def test_game_application_save_load_round_trips_hex_runtime_and_domain_owners(tmp_path):
    app, _bundle, source_runtime = make_application(tmp_path)
    save_path = tmp_path / "hex-save.json"

    app.save(save_path)
    loaded_bundle = app.load(save_path)
    restored_runtime = loaded_bundle.hex_world_runtime

    assert restored_runtime is not None
    assert restored_runtime.world_id == WorldId("save-world")
    assert restored_runtime.entities() == source_runtime.entities()
    assert restored_runtime.occupancy.snapshot() == source_runtime.occupancy.snapshot()
    assert dict(restored_runtime.patrol_indices) == {"guard": 2}
    assert loaded_bundle.actors.get("hero").world_id == "save-world"
    assert loaded_bundle.social.npcs.get("guard") is not None
    assert loaded_bundle.resource_nodes.get("iron-node") is not None


def test_game_application_save_rejects_unowned_spatial_objects(tmp_path):
    app, _bundle, runtime = make_application(tmp_path)
    runtime.register_entity(
        "unknown-object",
        "object",
        EntityPosition("field", LocalHexPosition(2, 0)),
        MovementProfile(can_move=False),
    )

    with pytest.raises(HexWorldPersistenceError, match="no resource/container owner"):
        app.save(tmp_path / "invalid-save.json")


def test_game_application_load_rejects_hex_snapshot_for_another_world_atomically(tmp_path):
    app, original_bundle, _runtime = make_application(tmp_path)
    save_path = tmp_path / "hex-save.json"
    app.save(save_path)

    data = json.loads(save_path.read_text(encoding="utf-8"))
    data["hex_world"]["world_id"] = "other-world"
    save_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(HexWorldPersistenceError, match="actor belongs to another world"):
        app.load(save_path)

    assert app.holder.current is original_bundle


def test_game_application_save_rejects_runtime_outside_active_world(tmp_path):
    app, bundle, _runtime = make_application(tmp_path)
    other = bundle.session.worlds.create("Other", world_id="other-world")
    bundle.session.worlds.set_active(other.world_id)

    with pytest.raises(ValueError, match="scoped to the active Core world"):
        app.save(tmp_path / "wrong-world-save.json")
