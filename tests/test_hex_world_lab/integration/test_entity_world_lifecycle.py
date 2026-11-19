"""Integration coverage for world, entity, spatial, and companion lifecycle."""

from hex_world_lab.application.entity_world_coordinator import EntityWorldCoordinator
from hex_world_lab.entities import (
    EntityId,
    EntityKind,
    EntityLocation,
    EntityRecord,
    EntityTransform,
)
from hex_world_lab.entities.spatial_index import EntityAABB
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.interaction import InteractionProfile
from hex_world_lab.world import HexMapDefinition, HexWorld, MapId, WorldId


def build_world():
    world = HexWorld(WorldId("lifecycle-world"))
    map_id = MapId("village")
    world.register_map(map_id, "Village")
    definition = HexMapDefinition(
        world.world_id,
        map_id,
        "Village",
        HexLayout(HexOrientation.FLAT_TOP, 32),
        {},
    )
    world.load_map(definition)
    return world, map_id, definition


def test_map_unload_retains_entities_and_companion_relationship_then_reload_reindexes():
    world, map_id, definition = build_world()
    coordinator = EntityWorldCoordinator(world)
    coordinator.spatial_index.activate_map(map_id)

    player = EntityRecord(
        EntityId("player"),
        EntityKind.PLAYER,
        EntityTransform(EntityLocation(world.world_id, map_id, WorldPoint(0, 0))),
    )
    npc = EntityRecord(
        EntityId("npc"),
        EntityKind.NPC,
        EntityTransform(EntityLocation(world.world_id, map_id, WorldPoint(10, 0))),
        interaction_profile=InteractionProfile(),
    )
    coordinator.register_entity(player)
    coordinator.register_entity(npc)
    coordinator.companions.recruit(player.entity_id, npc.entity_id)

    coordinator.unload_map(map_id)
    assert coordinator.registry.get(npc.entity_id) is not None
    assert coordinator.companions.get_relationship(npc.entity_id) is not None
    dormant_area = EntityAABB(-20, -20, 30, 20)
    assert coordinator.spatial_index.query(map_id, dormant_area) == ()

    coordinator.load_map(definition)
    # The fixture player has no body or interaction bounds, so only the NPC
    # is expected in the spatial broadphase after map reload.
    assert {
        entity.entity_id
        for entity in coordinator.spatial_index.query(map_id, dormant_area)
    } == {npc.entity_id}

    removed = coordinator.remove_map(map_id)
    assert {entity.entity_id for entity in removed} == {
        player.entity_id,
        npc.entity_id,
    }
    assert coordinator.companions.get_relationship(npc.entity_id) is None
    assert coordinator.registry.all_entities() == ()
