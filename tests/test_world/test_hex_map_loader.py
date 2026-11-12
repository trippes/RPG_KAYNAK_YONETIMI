import json
import tempfile
import unittest
from pathlib import Path
from core.domain.spatial import HexDirection, LocalHexPosition
from application.hex_map_definition import HexMapDefinitionError, parse_hex_map, load_hex_map_definition

DATA={
 "schema_version":2,"map_id":"test_hex","name":"Test","description":"",
 "geometry":{"type":"hex_axial","orientation":"pointy_top","coordinate_system":"axial"},
 "terrain_ids":["grass","water"],"default_terrain":"grass",
 "valid_cells":[[0,0],[1,0],[0,-1],[-1,0],[5,5]],
 "cell_overrides":[{"q":0,"r":-1,"terrain":"water","blocked":True}],
 "features":[{"id":"river","type":"river","cells":[[0,-1]]}],
 "landmarks":[{"id":"mine","name":"Mine","position":[-1,0],"resource_node_id":"ore_node"}],
 "transitions":[{"id":"exit","source_cells":[[1,0]],"exit_direction":"east","target_map_id":"future_map","target_entry_direction":"west","target_cells":[[-3,0]],"active":False,"traversal_mode":"one_way"}]
}

class TestHexMapLoader(unittest.TestCase):
 def test_mask_lookup_blocked_and_missing(self):
  m=parse_hex_map(DATA)
  self.assertTrue(m.has_cell(LocalHexPosition(0,0)))
  self.assertTrue(m.is_blocked(LocalHexPosition(0,-1)))
  self.assertIsNone(m.get_cell(LocalHexPosition(9,9)))
  self.assertFalse(m.is_blocked(LocalHexPosition(9,9)))
 def test_holes_and_disconnected_islands_are_valid(self):
  d=dict(DATA); d["valid_cells"]=[[0,0],[9,-4]]
  d["cell_overrides"]=[]; d["features"]=[]; d["landmarks"]=[]; d["transitions"]=[]
  self.assertEqual(len(parse_hex_map(d).valid_cells),2)
 def test_collections_immutable(self):
  m=parse_hex_map(DATA)
  with self.assertRaises(TypeError): m.cells[LocalHexPosition(8,8)]=None
 def test_six_directions_and_modes(self):
  for direction in HexDirection:
   d=dict(DATA); d["transitions"]=[{"id":"exit","source_cells":[[0,0]],"exit_direction":direction.name.lower(),"target_map_id":"not_loaded","traversal_mode":"bidirectional"}]
   self.assertEqual(parse_hex_map(d).transitions[0].exit_direction,direction)
 def test_rejects_schema_unknown_geometry_and_coordinate_types(self):
  cases=[]
  for change in (
   lambda d:d.update({"schema_version":3}),
   lambda d:d.update({"unknown":1}),
   lambda d:d["geometry"].update({"type":"square"}),
   lambda d:d["geometry"].update({"orientation":"flat_top"}),
   lambda d:d["geometry"].update({"coordinate_system":"offset"}),
   lambda d:d.update({"valid_cells":[[0.5,0]]}),
   lambda d:d.update({"valid_cells":[[True,0]]}),
   lambda d:d.update({"valid_cells":[[0,0],[0,0]]}),
   lambda d:d.update({"valid_cells":[]}),
  ):
   d=json.loads(json.dumps(DATA)); change(d); cases.append(d)
  for d in cases:
   with self.subTest(d=d),self.assertRaises(ValueError): parse_hex_map(d)
 def test_duplicate_and_outside_override_rejected(self):
  d=json.loads(json.dumps(DATA)); d["cell_overrides"].append(dict(d["cell_overrides"][0]))
  with self.assertRaises(ValueError): parse_hex_map(d)
  d=json.loads(json.dumps(DATA)); d["cell_overrides"]=[{"q":99,"r":0}]
  with self.assertRaises(ValueError): parse_hex_map(d)
 def test_unknown_terrain_rejected(self):
  d=json.loads(json.dumps(DATA)); d["cell_overrides"][0]["terrain"]="lava"
  with self.assertRaises(ValueError): parse_hex_map(d)
 def test_feature_landmark_transition_outside_mask_rejected(self):
  for key,value in (
   ("features",[{"id":"f","type":"wall","cells":[[90,0]]}]),
   ("landmarks",[{"id":"l","name":"Bad","position":[90,0]}]),
   ("transitions",[{"id":"t","source_cells":[[90,0]],"exit_direction":"west","target_map_id":"x"}]),
  ):
   d=json.loads(json.dumps(DATA)); d[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError): parse_hex_map(d)
 def test_bad_json_reports_path_and_line(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"broken.json"; p.write_text("{\n",encoding="utf-8")
   with self.assertRaisesRegex(ValueError,"broken.json.*line"): load_hex_map_definition(p)

if __name__=="__main__": unittest.main()
