"""Adapters that bind an entity ground anchor to physics and render DTOs."""
from hex_world_lab.physics.body import ActorBodyTransform,BodyDefinition
from hex_world_lab.physics.shapes import CircleShape,ConvexPolygonShape
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.rendering.snapshot import SpriteVisual,ColliderVisual,CircleVisual,PolygonVisual
from .entity import EntityRecord

def body_transform(entity:EntityRecord)->ActorBodyTransform:
    if not isinstance(entity,EntityRecord): raise TypeError("entity must be an EntityRecord")
    return ActorBodyTransform(entity.transform.location.position,entity.transform.rotation_radians)

def sprite_visual(entity:EntityRecord,asset_key:str,layer_priority:int=0)->SpriteVisual:
    if not isinstance(entity,EntityRecord): raise TypeError("entity must be an EntityRecord")
    if not isinstance(asset_key,str) or not asset_key.strip(): raise ValueError("asset_key must be non-empty")
    point=entity.transform.location.position
    return SpriteVisual(entity.entity_id.value,asset_key,point,point.y,layer_priority)

def collider_visual(entity:EntityRecord)->ColliderVisual|None:
    if not isinstance(entity,EntityRecord): raise TypeError("entity must be an EntityRecord")
    if entity.body is None: return None
    if not isinstance(entity.body,BodyDefinition): raise TypeError("entity body must be a BodyDefinition")
    shape=body_transform(entity).transform_shape(entity.body)
    if isinstance(shape,CircleShape):
        visual=CircleVisual(WorldPoint(shape.center.x,shape.center.y),shape.radius)
    elif isinstance(shape,ConvexPolygonShape):
        visual=PolygonVisual(tuple(WorldPoint(v.x,v.y) for v in shape.vertices))
    else: raise TypeError("unsupported transformed collider shape")
    return ColliderVisual(entity.entity_id.value,visual,"entity")
