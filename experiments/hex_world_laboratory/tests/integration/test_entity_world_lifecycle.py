"""Integration coverage for map lifecycle, target selection, and the entity demo."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
import pytest
from hex_world_lab.application.entity_world_coordinator import EntityWorldCoordinator
from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.entities import EntityId,EntityKind,EntityLocation,EntityRecord,EntityTransform
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.interaction import InteractionProfile
from hex_world_lab.world import HexWorld,HexMapDefinition,MapId,WorldId
from hex_world_lab.geometry import HexLayout,HexOrientation

def build_world():
    world=HexWorld(WorldId("lifecycle-world")); map_id=MapId("village")
    world.register_map(map_id,"Village")
    definition=HexMapDefinition(world.world_id,map_id,"Village",
        HexLayout(HexOrientation.FLAT_TOP,32),{})
    world.load_map(definition)
    return world,map_id,definition

def test_map_unload_retains_entities_and_companion_relationship_then_reload_reindexes():
    world,map_id,definition=build_world(); coordinator=EntityWorldCoordinator(world)
    coordinator.spatial_index.activate_map(map_id)
    player=EntityRecord(EntityId("player"),EntityKind.PLAYER,
        EntityTransform(EntityLocation(world.world_id,map_id,WorldPoint(0,0))))
    npc=EntityRecord(EntityId("npc"),EntityKind.NPC,
        EntityTransform(EntityLocation(world.world_id,map_id,WorldPoint(10,0))),
        interaction_profile=InteractionProfile())
    coordinator.register_entity(player); coordinator.register_entity(npc)
    coordinator.companions.recruit(player.entity_id,npc.entity_id)
    coordinator.unload_map(map_id)
    assert coordinator.registry.get(npc.entity_id) is not None
    assert coordinator.companions.get_relationship(npc.entity_id) is not None
    from hex_world_lab.entities.spatial_index import EntityAABB
    dormant_area = EntityAABB(-20, -20, 30, 20)
    assert coordinator.spatial_index.query(map_id, dormant_area) == ()
    coordinator.load_map(definition)
    # The fixture player has no body or interaction bounds, so only the
    # NPC is expected in the spatial broadphase after map reload.
    assert {e.entity_id for e in coordinator.spatial_index.query(map_id, dormant_area)} == {
        npc.entity_id
    }
    assert coordinator.spatial_index.query(map_id,
        __import__("hex_world_lab.entities.spatial_index",fromlist=["EntityAABB"]).EntityAABB(-20,-20,30,20))
    removed=coordinator.remove_map(map_id)
    assert {e.entity_id for e in removed}=={player.entity_id,npc.entity_id}
    assert coordinator.companions.get_relationship(npc.entity_id) is None
    assert coordinator.registry.all_entities()==()

def test_entity_demo_contains_player_two_npcs_two_resources_and_companion_commands():
    pygame.init()
    try:
        demo=EntityDemo()
        snapshot=demo.build_render_snapshot()
        assert len(demo.coordinator.registry.all_entities())==5
        assert len(snapshot.sprites)==5
        assert len(demo.npc_ids)==2 and len(demo.resource_ids)==2
        guard=demo.coordinator.registry.require(demo.npc_ids[0])
        relation=demo.recruit_guard()
        assert relation.command is CompanionCommand.FOLLOW
        wait=demo.issue_guard_command(CompanionCommand.WAIT)
        assert wait.wait_position==guard.transform.location.position
        assert demo.coordinator.registry.require(demo.npc_ids[0]).transform.location.position==guard.transform.location.position
        surface=pygame.Surface((960,640))
        demo.render(surface,60.0)
        assert surface.get_at((480,320))[:3] != (21,25,34)
    finally:
        pygame.quit()


def test_entity_mouse_selection_is_zoom_invariant():
    from hex_world_lab.camera import ScreenPoint
    pygame.init()
    try:
        demo=EntityDemo()
        target=demo.coordinator.registry.require(demo.npc_ids[0])
        world_point=target.transform.location.position
        assert demo.select_world_point(world_point)==demo.npc_ids[0]
        screen=demo.movement.camera.transform.world_to_screen(world_point)
        assert demo.select_screen_point(ScreenPoint(round(screen.x),round(screen.y)))==demo.npc_ids[0]
        demo.movement.camera.zoom_by_steps(2)
        zoomed=demo.movement.camera.transform.world_to_screen(world_point)
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,{"button":1,"pos":(round(zoomed.x),round(zoomed.y))})
        assert demo.handle_event(event)==demo.npc_ids[0]
    finally:
        pygame.quit()
