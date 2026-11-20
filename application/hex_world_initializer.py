"""Session-safe initialization of the content-authored axial gameplay world."""

from __future__ import annotations

from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId

from .content_loader import load_content_package
from .hex_world_runtime import HexWorldRuntime


class HexWorldInitializationError(ValueError):
    """The active content package cannot safely initialize its axial world."""


def initialize_hex_world(service, *, content_package_path=None):
    """Create the session Hex runtime only from explicit package map/start data.

    A package without axial maps returns None and leaves the main screen in its
    mapless preparation state. No default map, map ID, or axial coordinate is
    synthesized here.
    """
    from application.content_pack import (
        _resolve_content_package_path,
        load_starter_content,
    )

    requested_path = (
        content_package_path
        or getattr(service, "_content_package_path", None)
    )
    resolved_path = _resolve_content_package_path(requested_path)
    package = load_content_package(resolved_path)
    if not package.hex_map_definitions:
        return None

    starter = load_starter_content(package_path=resolved_path)
    world_config = starter.get("world")
    if not isinstance(world_config, dict):
        raise HexWorldInitializationError(
            "Starter content must define a world object before Hex initialization."
        )
    start = world_config.get("hex_start")
    if not isinstance(start, dict) or set(start) != {"map_id", "q", "r"}:
        raise HexWorldInitializationError(
            "Axial maps require an explicit world.hex_start with map_id, q and r."
        )
    map_id = start["map_id"]
    q, r = start["q"], start["r"]
    if not isinstance(map_id, str) or not map_id.strip():
        raise HexWorldInitializationError("world.hex_start.map_id must be non-empty.")
    if type(q) is not int or type(r) is not int:
        raise HexWorldInitializationError(
            "world.hex_start q/r values must be strict integers."
        )
    map_definition = package.hex_map_definitions.get(map_id)
    if map_definition is None:
        raise HexWorldInitializationError(
            f"world.hex_start references unknown axial map: {map_id}"
        )
    start_position = LocalHexPosition(q, r)
    if not map_definition.has_cell(start_position):
        raise HexWorldInitializationError(
            f"Player start cell q={q}, r={r} is outside map '{map_id}'."
        )
    if len(package.hex_map_definitions) > 1 and package.world_map_definition is None:
        raise HexWorldInitializationError(
            "Multiple axial maps require an explicit world_map definition."
        )

    active_world = service.application.aktif_dunya()
    if active_world is None:
        raise HexWorldInitializationError(
            "An active Core world is required before Hex initialization."
        )
    world_id = WorldId(active_world.world_id)
    runtime_owner = service.hex_world_runtime_owner
    runtime = runtime_owner.runtime
    created_runtime = runtime is None

    if runtime is not None:
        if runtime.world_id != world_id:
            raise HexWorldInitializationError(
                "The session Hex runtime belongs to a different Core world."
            )
        if set(runtime.map_ids) != set(package.hex_map_definitions):
            raise HexWorldInitializationError(
                "The session Hex runtime map registry differs from the active content package."
            )
        if runtime.world_map_definition != package.world_map_definition:
            raise HexWorldInitializationError(
                "The session Hex runtime world topology differs from the active content package."
            )
        if any(
            runtime.map_definition(map_id) != definition
            for map_id, definition in package.hex_map_definitions.items()
        ):
            raise HexWorldInitializationError(
                "The session Hex map definitions differ from the active content package."
            )
        try:
            runtime.entity(service.player_actor_id)
        except KeyError:
            if runtime.entities():
                raise HexWorldInitializationError(
                    "An existing Hex runtime has spatial entities but no player placement."
                )
        else:
            return runtime

    runtime = runtime_owner.get_or_create(
        lambda: HexWorldRuntime(
            package.hex_map_definitions,
            world_map_definition=package.world_map_definition,
            world_id=world_id,
        )
    )
    player_registered = False
    placements_registered = False
    catalog = package.gameplay_placements
    try:
        service.hex_actor_binding.register_spatial(
            service.player_actor_id,
            "player",
            EntityPosition(map_id, start_position),
            MovementProfile(),
            # Player/NPC overlap is resolved by continuous collider physics;
            # cell occupancy remains an index, not a coarse actor collision wall.
            blocks_movement=False,
            blocks_occupancy=False,
        )
        player_registered = True

        if catalog is not None:
            service.register_gameplay_placements(catalog)
            placements_registered = True

        service.application.holder.current.validate()
        return runtime
    except Exception:
        if placements_registered and catalog is not None:
            for placement in reversed(catalog.placements):
                if placement.kind == "npc":
                    service.npc_hex_binding.unregister_spatial(placement.domain_id)
                elif placement.kind == "resource_node":
                    service.resource_node_hex_binding.unregister_spatial(
                        placement.domain_id
                    )
                else:
                    service.container_hex_binding.unregister_spatial(
                        placement.domain_id
                    )
        if player_registered:
            runtime.remove_entity(service.player_actor_id)
        if created_runtime and not runtime.entities():
            runtime_owner.discard_if_empty(runtime)
        raise


__all__ = ["HexWorldInitializationError", "initialize_hex_world"]
