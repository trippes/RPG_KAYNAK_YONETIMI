"""Explicit adapters between content documents and existing environment/physics models."""

from hex_world_lab.environment import (
    EnvironmentalObjectDefinition,
    EnvironmentalObjectPlacement,
    EnvironmentalObjectScene,
)
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.world.map_definition import HexMapDefinition

from hex_world_lab.content.collision import CircleCollider, ConvexPolygonCollider
from hex_world_lab.content.definition import ContentDefinition
from hex_world_lab.content.library import ContentLibrary
from hex_world_lab.content.map_document import MapContentDocument


def definition_to_environment(value: ContentDefinition) -> EnvironmentalObjectDefinition:
    if not isinstance(value, ContentDefinition):
        raise TypeError("value must be ContentDefinition")
    collider = value.collider
    if isinstance(collider, CircleCollider):
        collider = CircleShape(collider.radius, Vector2(collider.center_x, collider.center_y))
    elif isinstance(collider, ConvexPolygonCollider):
        collider = ConvexPolygonShape(tuple(Vector2(x, y) for x, y in collider.vertices))
    return EnvironmentalObjectDefinition(
        value.content_id,
        value.content_id,
        value.visual_document.ground_anchor,
        value.visual_document.depth_anchor,
        collider=collider,
    )


def placement_to_environment(value, map_definition):
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be HexMapDefinition")
    return EnvironmentalObjectPlacement(
        value.instance_id,
        value.content_id,
        map_definition.world_id,
        map_definition.map_id,
        WorldPoint(value.x, value.y),
    )


def to_environment_scene(
    library: ContentLibrary, document: MapContentDocument
) -> EnvironmentalObjectScene:
    if not isinstance(library, ContentLibrary) or not isinstance(document, MapContentDocument):
        raise TypeError("library and document must be ContentLibrary and MapContentDocument")
    document.validate_references(library)
    definitions = tuple(definition_to_environment(item) for item in library.definitions)
    placements = tuple(
        placement_to_environment(item, document.map_definition) for item in document.placements
    )
    return EnvironmentalObjectScene(
        document.map_definition.world_id, document.map_definition.map_id, definitions, placements
    )
