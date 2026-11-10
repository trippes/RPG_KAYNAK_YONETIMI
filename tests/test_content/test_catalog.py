import json
import tempfile
import unittest
from pathlib import Path

from content import ContentCatalogError, load_content_catalog


class TestContentCatalog(unittest.TestCase):
    def _catalog(self, root: Path):
        (root / "packs" / "base" / "npcs").mkdir(parents=True)
        (root / "packs" / "items" / "items").mkdir(parents=True)
        (root / "manifest.json").write_text(
            json.dumps({
                "schema_version": 1,
                "packs": [
                    {"id": "base", "manifest": "packs/base/pack.json"},
                    {"id": "items", "manifest": "packs/items/pack.json"},
                ],
            }),
            encoding="utf-8",
        )
        (root / "packs" / "base" / "pack.json").write_text(
            json.dumps({
                "schema_version": 1,
                "id": "base",
                "version": "1.0.0",
                "dependencies": [],
                "files": [{"kind": "npc", "path": "npcs/warden.json"}],
            }),
            encoding="utf-8",
        )
        (root / "packs" / "base" / "npcs" / "warden.json").write_text(
            json.dumps({"id": "warden_lyra", "name": "Lyra"}),
            encoding="utf-8",
        )
        (root / "packs" / "items" / "pack.json").write_text(
            json.dumps({
                "schema_version": 1,
                "id": "items",
                "version": "1.0.0",
                "dependencies": ["base"],
                "files": [{"kind": "item", "path": "items/sword.json"}],
            }),
            encoding="utf-8",
        )
        (root / "packs" / "items" / "items" / "sword.json").write_text(
            json.dumps({
                "id": "iron_sword",
                "name": "Iron Sword",
                "references": [{"kind": "npc", "id": "warden_lyra"}],
            }),
            encoding="utf-8",
        )

    def test_loads_multiple_content_types_and_resolves_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            catalog = load_content_catalog(root)

        self.assertEqual(catalog.pack_ids(), ("base", "items"))
        self.assertEqual(catalog.get("npc", "warden_lyra").data["name"], "Lyra")
        self.assertEqual(catalog.get("item", "iron_sword").data["name"], "Iron Sword")
        self.assertEqual(len(catalog.all()), 2)

    def test_can_disable_a_pack_without_loading_its_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            catalog = load_content_catalog(root, enabled_pack_ids={"base"})

        self.assertEqual(catalog.pack_ids(), ("base",))
        self.assertIsNone(catalog.get("item", "iron_sword"))

    def test_rejects_enabled_pack_with_disabled_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            with self.assertRaisesRegex(ContentCatalogError, "requires disabled"):
                load_content_catalog(root, enabled_pack_ids={"items"})

    def test_rejects_duplicate_content_ids_within_same_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            second = root / "packs" / "base" / "npcs" / "second.json"
            second.write_text(json.dumps({"id": "warden_lyra"}), encoding="utf-8")
            pack_path = root / "packs" / "base" / "pack.json"
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
            pack["files"].append({"kind": "npc", "path": "npcs/second.json"})
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "Duplicate npc"):
                load_content_catalog(root)

    def test_rejects_missing_cross_content_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            item_path = root / "packs" / "items" / "items" / "sword.json"
            item = json.loads(item_path.read_text(encoding="utf-8"))
            item["references"][0]["id"] = "missing_npc"
            item_path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "references missing"):
                load_content_catalog(root)

    def test_rejects_dependency_cycles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            base_path = root / "packs" / "base" / "pack.json"
            base = json.loads(base_path.read_text(encoding="utf-8"))
            base["dependencies"] = ["items"]
            base_path.write_text(json.dumps(base), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "dependency cycle"):
                load_content_catalog(root)

    def test_rejects_paths_that_escape_catalog_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            pack_path = root / "packs" / "base" / "pack.json"
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
            pack["files"][0]["path"] = "../../../outside.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "escapes catalog root"):
                load_content_catalog(root)

    def test_rejects_unknown_schema_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = 99
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "Unsupported content catalog"):
                load_content_catalog(root)

    def test_rejects_unknown_enabled_pack_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            with self.assertRaisesRegex(ContentCatalogError, "Unknown enabled"):
                load_content_catalog(root, enabled_pack_ids={"missing"})

    def test_content_kind_is_extensible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._catalog(root)
            pack_path = root / "packs" / "base" / "pack.json"
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
            pack["files"].append({"kind": "building", "path": "npcs/warden.json"})
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            with self.assertRaisesRegex(ContentCatalogError, "Duplicate"):
                load_content_catalog(root)


if __name__ == "__main__":
    unittest.main()
