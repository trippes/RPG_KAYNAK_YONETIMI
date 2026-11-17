"""Multi-entity acceptance scene composed around the existing player movement demo."""
from __future__ import annotations
import pygame
from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.application.entity_world_coordinator import EntityWorldCoordinator
from hex_world_lab.entities import EntityId, EntityKind, EntityLocation, EntityRecord, EntityTransform
from hex_world_lab.entities.spatial_index import EntitySpatialIndex
from hex_world_lab.interaction import InteractionProfile, TargetQuery
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.geometry import AxialCoord, WorldPoint, axial_to_world
from hex_world_lab.physics import BodyDefinition, CircleShape, ActorBodyTransform
from hex_world_lab.movement import Vector2
from hex_world_lab.rendering import (WorldRenderSnapshot, SpriteVisual, ColliderVisual,
                                     CircleVisual, PolygonVisual, RenderDebugOptions)
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset

class EntityDemo:
    """Player movement remains authoritative in MovementDemo; other entities are stationary."""
    def __init__(self, movement_demo: MovementDemo | None = None) -> None:
        self.movement = movement_demo or MovementDemo()
        self.world, self.map_id = self.movement.world, self.movement.map_id
        self.coordinator = EntityWorldCoordinator(self.world)
        self.coordinator.spatial_index.activate_map(self.map_id)
        self.player_id = EntityId("entity-demo-player")
        self.npc_ids = (EntityId("npc-guard"), EntityId("npc-trader"))
        self.resource_ids = (EntityId("resource-herb"), EntityId("resource-ore"))
        player_profile = InteractionProfile(True, 36.0, frozenset({"inspect"}), 10)
        self.coordinator.register_entity(EntityRecord(
            self.player_id, EntityKind.PLAYER,
            EntityTransform(EntityLocation(self.world.world_id,self.map_id,self.movement.state.position)),
            self.movement.body_definition, player_profile))
        npc_points = (WorldPoint(92.0, 38.0), WorldPoint(128.0, -42.0))
        for index,(entity_id,point) in enumerate(zip(self.npc_ids,npc_points)):
            body=BodyDefinition(entity_id.value,CircleShape(7.0),body_height=1.7)
            profile=InteractionProfile(True,22.0,frozenset({"talk","inspect"}),8-index)
            self.coordinator.register_entity(EntityRecord(
                entity_id,EntityKind.NPC,
                EntityTransform(EntityLocation(self.world.world_id,self.map_id,point)),
                body,profile))
        resource_points = (
            axial_to_world(AxialCoord(2,-1),self.movement._layout),
            axial_to_world(AxialCoord(-1,1),self.movement._layout),
        )
        for entity_id,point in zip(self.resource_ids,resource_points):
            profile=InteractionProfile(True,18.0,frozenset({"gather","inspect"}),2)
            self.coordinator.register_entity(EntityRecord(
                entity_id,EntityKind.RESOURCE,
                EntityTransform(EntityLocation(self.world.world_id,self.map_id,point)),
                None,profile))
        self.target_query=TargetQuery(self.coordinator.registry,self.coordinator.spatial_index)
        self._register_placeholder_assets()
    def _register_placeholder_assets(self)->None:
        colors={"npc-guard":(92,145,196),"npc-trader":(191,151,83),
                "resource-herb":(83,169,103),"resource-ore":(143,151,165)}
        for key,color in colors.items():
            size=(24,34) if key.startswith("npc-") else (24,24)
            surface=pygame.Surface(size,pygame.SRCALPHA)
            if key.startswith("npc-"):
                pygame.draw.ellipse(surface,(36,43,54),(4,23,7,10))
                pygame.draw.ellipse(surface,(36,43,54),(13,23,7,10))
                pygame.draw.polygon(surface,color,((4,13),(20,13),(19,27),(5,27)))
                pygame.draw.circle(surface,(225,190,154),(12,8),6)
            elif key=="resource-herb":
                pygame.draw.circle(surface,color,(12,12),9)
                pygame.draw.line(surface,(214,231,190),(12,20),(12,5),2)
                pygame.draw.ellipse(surface,(126,194,121),(4,7,9,5))
                pygame.draw.ellipse(surface,(126,194,121),(12,4,9,5))
            else:
                pygame.draw.polygon(surface,color,((12,1),(22,8),(18,21),(6,22),(2,10)))
                pygame.draw.polygon(surface,(210,216,226),((12,1),(22,8),(18,21),(6,22),(2,10)),2)
            self.movement.renderer.register_sprite_asset(key,SpriteAsset(surface,0.5,1.0))
    def sync_player(self)->None:
        entity=self.coordinator.registry.require(self.player_id)
        position=self.movement.state.position
        if entity.transform.location.position != position:
            transform=EntityTransform(EntityLocation(self.world.world_id,self.map_id,position),
                                      entity.transform.rotation_radians)
            self.coordinator.update_transform(self.player_id,transform)
    def recruit_guard(self):
        return self.coordinator.companions.recruit(self.player_id,self.npc_ids[0])
    def issue_guard_command(self,command:CompanionCommand):
        return self.coordinator.companions.issue_command(self.npc_ids[0],command)
    def build_render_snapshot(self,debug_options:RenderDebugOptions|None=None)->WorldRenderSnapshot:
        self.sync_player()
        base=self.movement.build_render_snapshot(debug_options=debug_options)
        sprites=list(base.sprites); colliders=list(base.colliders)
        for entity in self.coordinator.registry.entities_for_map(self.world.world_id,self.map_id):
            if entity.entity_id==self.player_id: continue
            point=entity.transform.location.position
            if entity.kind is EntityKind.NPC:
                sprites.append(SpriteVisual(entity.entity_id.value,entity.entity_id.value,point,point.y,12))
            else:
                sprites.append(SpriteVisual(entity.entity_id.value,entity.entity_id.value,point,point.y,18))
                radius=entity.interaction_profile.interaction_radius
                colliders.append(ColliderVisual(entity.entity_id.value,
                    CircleVisual(point,radius),"interaction"))
            if entity.body is not None:
                shape=ActorBodyTransform(point,entity.transform.rotation_radians).transform_shape(entity.body)
                if isinstance(shape,CircleShape):
                    visual=CircleVisual(WorldPoint(shape.center.x,shape.center.y),shape.radius)
                else:
                    visual=PolygonVisual(tuple(WorldPoint(v.x,v.y) for v in shape.vertices))
                colliders.append(ColliderVisual(entity.entity_id.value,visual,"entity"))
        return WorldRenderSnapshot(
            cells=base.cells,circles=base.circles,polygons=base.polygons,
            boundaries=base.boundaries,house_lines=base.house_lines,
            actor_position=base.actor_position,actor_radius=base.actor_radius,
            selected_cell=base.selected_cell,sprites=tuple(sprites),
            colliders=tuple(colliders),debug_options=base.debug_options,
            visible_region=base.visible_region)
    def render(self,surface:pygame.Surface,render_fps:float=0.0,
               debug_options:RenderDebugOptions|None=None)->None:
        snapshot=self.build_render_snapshot(debug_options)
        self.movement.renderer.render(surface,snapshot,self.movement._layout,
                                      self.movement.camera.transform)
        if self.movement._font is None:
            self.movement._font=pygame.font.Font(None,23)
            self.movement._small_font=pygame.font.Font(None,19)
        self.movement._draw_diagnostics(surface,render_fps)
