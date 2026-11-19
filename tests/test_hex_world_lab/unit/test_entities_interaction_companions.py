"""Unit coverage for the Phase 9 entity, interaction, spatial, and companion contracts."""
import pytest
from hex_world_lab.companions import (CompanionCommand, CompanionRoster,
    CompanionAlreadyRecruitedError, InvalidCompanionOwnerError)
from hex_world_lab.entities import (EntityId,EntityKind,EntityLocation,EntityRecord,
    EntityRegistry,EntityTransform,DuplicateEntityError)
from hex_world_lab.entities.spatial_index import EntityAABB,EntitySpatialIndex
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.interaction import InteractionProfile,TargetQuery,within_world_range,within_hex_range
from hex_world_lab.physics import BodyDefinition,CircleShape
from hex_world_lab.world import HexWorld,MapId,WorldId

def fixture():
    world=HexWorld(WorldId("unit-world")); map_id=MapId("field")
    world.register_map(map_id,"Field")
    registry=EntityRegistry(world.world_id,world.map_registry)
    spatial=EntitySpatialIndex(registry); spatial.activate_map(map_id)
    def add(name,kind,point,profile=None,body=None):
        entity=EntityRecord(EntityId(name),kind,
            EntityTransform(EntityLocation(world.world_id,map_id,point)),body,profile)
        registry.register(entity); spatial.update_entity(entity); return entity
    player=add("player",EntityKind.PLAYER,WorldPoint(0,0),
        InteractionProfile(True,30,frozenset({"inspect"}),10),
        BodyDefinition("player-body",CircleShape(7)))
    npc=add("npc",EntityKind.NPC,WorldPoint(20,0),
        InteractionProfile(True,12,frozenset({"talk","inspect"}),5),
        BodyDefinition("npc-body",CircleShape(6)))
    resource=add("resource",EntityKind.RESOURCE,WorldPoint(70,0),
        InteractionProfile(True,10,frozenset({"gather"}),1))
    return world,map_id,registry,spatial,player,npc,resource

def test_entity_identity_registry_and_fractional_transform_are_stable():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    assert registry.require(player.entity_id).transform.location.position==WorldPoint(0,0)
    moved=EntityTransform(EntityLocation(world.world_id,map_id,WorldPoint(0.25,0.75)),0.5)
    updated=registry.update_transform(player.entity_id,moved)
    assert updated.transform.location.position==WorldPoint(0.25,0.75)
    with pytest.raises(DuplicateEntityError): registry.register(player)
    snapshot=registry.all_entities()
    assert tuple(e.entity_id.value for e in snapshot)==("npc","player","resource")
    assert isinstance(snapshot,tuple)

def test_spatial_candidates_match_brute_force_and_are_map_scoped():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    area=EntityAABB(10,-10,30,10)
    assert tuple(e.entity_id.value for e in spatial.query(map_id,area))==("npc",)
    assert spatial.differential_candidates(map_id,area)==("npc",)
    other=MapId("other"); world.register_map(other,"Other")
    spatial.activate_map(other)
    assert spatial.query(other,area)==()

def test_interaction_uses_exact_world_range_tags_and_deterministic_priority():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    query=TargetQuery(registry,spatial)
    assert query.select_target(WorldPoint(20,0),map_id,frozenset({"talk"}))==npc.entity_id
    assert query.is_in_interaction_range(player.entity_id,npc.entity_id,"talk")
    assert not query.is_in_interaction_range(player.entity_id,resource.entity_id,"talk")
    assert within_world_range(WorldPoint(0,0),WorldPoint(3,4),5)
    assert not within_world_range(WorldPoint(0,0),WorldPoint(3,4),4.9)

def test_companion_commands_capture_wait_position_and_do_not_move_npc():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    roster=CompanionRoster(registry)
    relation=roster.recruit(player.entity_id,npc.entity_id)
    assert relation.command is CompanionCommand.FOLLOW
    with pytest.raises(CompanionAlreadyRecruitedError): roster.recruit(player.entity_id,npc.entity_id)
    wait=roster.issue_command(npc.entity_id,CompanionCommand.WAIT)
    assert wait.wait_position==WorldPoint(20,0) and wait.command_revision==1
    registry.update_transform(npc.entity_id,EntityTransform(EntityLocation(world.world_id,map_id,WorldPoint(40,0))))
    assert roster.get_relationship(npc.entity_id).wait_position==WorldPoint(20,0)
    returned=roster.issue_command(npc.entity_id,CompanionCommand.RETURN)
    assert returned.wait_position is None and returned.command_revision==2
    assert registry.require(npc.entity_id).transform.location.position==WorldPoint(40,0)
    dismissed=roster.dismiss(npc.entity_id)
    assert dismissed.companion_id==npc.entity_id
    assert registry.get(npc.entity_id) is not None

def test_only_players_can_own_and_entity_removal_cascades_relationships():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    roster=CompanionRoster(registry); roster.recruit(player.entity_id,npc.entity_id)
    with pytest.raises(InvalidCompanionOwnerError): roster.recruit(npc.entity_id,resource.entity_id)
    roster.remove_entity(player.entity_id)
    assert roster.get_relationship(npc.entity_id) is None

def test_map_transfer_updates_spatial_membership_without_changing_identity():
    world,map_id,registry,spatial,player,npc,resource=fixture()
    second=MapId("second"); world.register_map(second,"Second"); spatial.activate_map(second)
    moved=EntityTransform(EntityLocation(world.world_id,second,WorldPoint(200,0)))
    updated=registry.update_transform(npc.entity_id,moved); spatial.update_entity(updated)
    old=EntityAABB(10,-10,30,10); new=EntityAABB(190,-10,210,10)
    assert spatial.query(map_id,old)==()
    assert tuple(e.entity_id.value for e in spatial.query(second,new))==("npc",)


def test_presentation_keeps_sprite_anchor_and_physics_anchor_identical():
    from hex_world_lab.entities.presentation import body_transform,collider_visual,sprite_visual
    world,map_id,registry,spatial,player,npc,resource=fixture()
    visual=sprite_visual(player,"player-art",layer_priority=7)
    body=body_transform(player)
    assert visual.ground_anchor==player.transform.location.position
    assert body.ground_anchor==visual.ground_anchor
    collider=collider_visual(player)
    assert collider is not None and collider.owner_id==player.entity_id.value
    assert collider.shape.center==player.transform.location.position
    assert collider.shape.radius==7
    assert collider_visual(resource) is None
