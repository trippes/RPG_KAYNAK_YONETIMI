"""Contract tests for modular structure catalog definitions."""
import unittest

from core.domain.spatial import WorldPoint
from core.domain.structures import (
    StructureConnectionPort,
    StructureDefinition,
    StructureDefinitionCatalog,
    StructureGeometryDefinition,
    StructurePartDefinition,
)


def part(part_id="wall", *, ports=()):
    return StructurePartDefinition(
        part_definition_id=part_id,
        category="wall",
        geometry=StructureGeometryDefinition(
            shape_kind="rectangular_prism", width=2.0, depth=0.25, height=3.0,
        ),
        connection_ports=tuple(ports),
    )


class StructureGeometryDefinitionTests(unittest.TestCase):
    def test_geometry_requires_positive_finite_world_unit_dimensions(self):
        geometry = StructureGeometryDefinition("box", 2, 1, 3)
        self.assertEqual((geometry.width, geometry.depth, geometry.height), (2.0, 1.0, 3.0))
        for dimensions in ((0, 1, 1), (-1, 1, 1), (1, float("inf"), 1)):
            with self.subTest(dimensions=dimensions), self.assertRaises(ValueError):
                StructureGeometryDefinition("box", *dimensions)
        with self.assertRaises(TypeError):
            StructureGeometryDefinition("box", True, 1, 1)

    def test_geometry_accepts_explicit_unique_local_footprint_points(self):
        footprint = (WorldPoint(-1.0, 0.0), WorldPoint(1.0, 0.0))
        geometry = StructureGeometryDefinition(
            "custom", 2.0, 1.0, 3.0, footprint_local_points=footprint,
        )
        self.assertEqual(geometry.footprint_local_points, footprint)
        with self.assertRaisesRegex(ValueError, "duplicates"):
            StructureGeometryDefinition(
                "custom", 2.0, 1.0, 3.0,
                footprint_local_points=(WorldPoint(0, 0), WorldPoint(0, 0)),
            )
        with self.assertRaises(TypeError):
            StructureGeometryDefinition(
                "custom", 2.0, 1.0, 3.0, footprint_local_points=((0, 0),),
            )

    def test_connection_ports_require_valid_identity_and_capacity(self):
        with self.assertRaises(ValueError):
            StructureConnectionPort("", "edge", "wall")
        with self.assertRaises(ValueError):
            StructureConnectionPort("north", "edge", "wall", max_connections=0)
        with self.assertRaises(TypeError):
            StructureConnectionPort("north", "edge", "wall", required=1)

    def test_connection_compatibility_is_deterministic(self):
        wall_edge = StructureConnectionPort("edge_a", "edge", "wall-standard")
        matching = StructureConnectionPort("edge_b", "edge", "wall-standard")
        wrong_kind = StructureConnectionPort("socket", "socket", "wall-standard")
        wrong_key = StructureConnectionPort("edge_c", "edge", "floor-standard")
        self.assertTrue(wall_edge.is_compatible_with(matching))
        self.assertFalse(wall_edge.is_compatible_with(wrong_kind))
        self.assertFalse(wall_edge.is_compatible_with(wrong_key))

    def test_part_definition_is_immutable_and_rejects_duplicate_ports(self):
        ports = (
            StructureConnectionPort("north", "edge", "wall"),
            StructureConnectionPort("south", "edge", "wall"),
        )
        definition = part(ports=ports)
        self.assertEqual(tuple(port.port_id for port in definition.connection_ports), ("north", "south"))
        with self.assertRaises((AttributeError, TypeError)):
            definition.category = "floor"
        with self.assertRaisesRegex(ValueError, "unique"):
            part(ports=(ports[0], ports[0]))

    def test_part_definition_rejects_unknown_policies_and_schema_versions(self):
        base = {
            "part_definition_id": "wall",
            "category": "wall",
            "geometry": StructureGeometryDefinition("box", 1, 1, 1),
        }
        with self.assertRaises(ValueError):
            StructurePartDefinition(**base, orientation_policy="hex")
        with self.assertRaises(ValueError):
            StructurePartDefinition(**base, schema_version=99)

    def test_structure_definition_requires_unique_nonempty_part_references(self):
        with self.assertRaises(ValueError):
            StructureDefinition("house", "House", ())
        with self.assertRaises(ValueError):
            StructureDefinition("house", "House", ("wall", "wall"))
        definition = StructureDefinition("house", "House", ("wall",), tags=("residential",))
        self.assertEqual(definition.allowed_part_definition_ids, ("wall",))

    def test_catalog_rejects_duplicate_ids_and_dangling_part_references(self):
        with self.assertRaisesRegex(ValueError, "Duplicate structure part"):
            StructureDefinitionCatalog(parts=(part(), part()))
        with self.assertRaisesRegex(ValueError, "Duplicate structure definition"):
            StructureDefinitionCatalog(
                structures=(
                    StructureDefinition("house", "House", ("wall",)),
                    StructureDefinition("house", "House 2", ("wall",)),
                ),
                parts=(part(),),
            )
        with self.assertRaisesRegex(ValueError, "unknown part definitions"):
            StructureDefinitionCatalog(
                structures=(StructureDefinition("house", "House", ("missing",)),),
            )

    def test_catalog_lookup_is_deterministic_and_definitions_are_shared(self):
        wall = part()
        house = StructureDefinition("house", "House", ("wall",))
        catalog = StructureDefinitionCatalog((house,), (wall,))
        self.assertIs(catalog.structure("house"), house)
        self.assertIs(catalog.part("wall"), wall)
        self.assertIsNone(catalog.structure("missing"))
        self.assertEqual(tuple(item.structure_definition_id for item in catalog.structures()), ("house",))
        self.assertEqual(tuple(item.part_definition_id for item in catalog.parts()), ("wall",))


if __name__ == "__main__":
    unittest.main()
