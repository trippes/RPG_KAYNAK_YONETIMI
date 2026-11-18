"""Map plus placed content; updates return new immutable documents."""

from dataclasses import dataclass, replace

from hex_world_lab.world.map_definition import HexMapDefinition

from .library import ContentLibrary
from .placement import ContentPlacement
from .values import non_empty_id


@dataclass(frozen=True, slots=True)
class MapContentDocument:
    map_definition: HexMapDefinition
    placements: tuple[ContentPlacement, ...] = ()

    def __post_init__(self):
        if not isinstance(self.map_definition, HexMapDefinition):
            raise TypeError("map_definition must be HexMapDefinition")
        placements = tuple(self.placements)
        if any(not isinstance(item, ContentPlacement) for item in placements):
            raise TypeError("placements must contain ContentPlacement values")
        ids = [item.instance_id for item in placements]
        if len(ids) != len(set(ids)):
            raise ValueError("placement instance IDs must be unique")
        object.__setattr__(
            self, "placements", tuple(sorted(placements, key=lambda item: item.instance_id))
        )

    def add_placement(self, placement: ContentPlacement, library: ContentLibrary):
        if not isinstance(placement, ContentPlacement):
            raise TypeError("placement must be ContentPlacement")
        if not isinstance(library, ContentLibrary):
            raise TypeError("library must be ContentLibrary")
        library.resolve(placement.content_id)
        if any(item.instance_id == placement.instance_id for item in self.placements):
            raise ValueError(f"duplicate placement instance ID: {placement.instance_id}")
        return replace(self, placements=self.placements + (placement,))

    def update_placement(
        self,
        instance_id: str,
        *,
        x: float | None = None,
        y: float | None = None,
        content_id: str | None = None,
        library: ContentLibrary | None = None,
    ):
        non_empty_id(instance_id, "instance_id")
        current = next((item for item in self.placements if item.instance_id == instance_id), None)
        if current is None:
            raise KeyError(instance_id)
        selected_content = current.content_id if content_id is None else content_id
        if content_id is not None:
            if library is None:
                raise ValueError("library is required when changing content_id")
            if not isinstance(library, ContentLibrary):
                raise TypeError("library must be ContentLibrary")
            library.resolve(selected_content)
        updated = ContentPlacement(
            instance_id,
            selected_content,
            current.x if x is None else x,
            current.y if y is None else y,
        )
        return replace(
            self,
            placements=tuple(
                updated if item.instance_id == instance_id else item for item in self.placements
            ),
        )

    def remove_placement(self, instance_id: str):
        non_empty_id(instance_id, "instance_id")
        if not any(item.instance_id == instance_id for item in self.placements):
            raise KeyError(instance_id)
        return replace(
            self,
            placements=tuple(item for item in self.placements if item.instance_id != instance_id),
        )

    def validate_references(self, library: ContentLibrary):
        if not isinstance(library, ContentLibrary):
            raise TypeError("library must be ContentLibrary")
        for item in self.placements:
            library.resolve(item.content_id)
        return self
