"""Deterministic entity spatial-index build/query benchmark."""
from __future__ import annotations
import json
import statistics
import time
from pathlib import Path
from hex_world_lab.entities import EntityId,EntityKind,EntityLocation,EntityRecord,EntityRegistry,EntityTransform
from hex_world_lab.entities.spatial_index import EntityAABB,EntitySpatialIndex
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.interaction import InteractionProfile
from hex_world_lab.world import HexWorld,MapId,WorldId

def percentile(values:list[float],fraction:float)->float:
    ordered=sorted(values)
    return ordered[min(len(ordered)-1,int((len(ordered)-1)*fraction))]

def run(size:int)->dict:
    world=HexWorld(WorldId(f"bench-world-{size}")); map_id=MapId("bench-map")
    world.register_map(map_id,"Benchmark")
    registry=EntityRegistry(world.world_id,world.map_registry)
    profile=InteractionProfile(True,12.0,frozenset({"inspect"}),0)
    for index in range(size):
        point=WorldPoint(float((index%100)*40),float((index//100)*40))
        registry.register(EntityRecord(EntityId(f"entity-{index:06d}"),EntityKind.NPC,
            EntityTransform(EntityLocation(world.world_id,map_id,point)),
            interaction_profile=profile))
    spatial=EntitySpatialIndex(registry,cell_size=128.0)
    start=time.perf_counter(); spatial.activate_map(map_id)
    build_ms=(time.perf_counter()-start)*1000
    queries=[]
    for index in range(120):
        origin=WorldPoint(float((index%12)*320+80),float((index//12)*320+80))
        area=EntityAABB(origin.x-72,origin.y-72,origin.x+72,origin.y+72)
        start=time.perf_counter(); indexed=spatial.query(map_id,area)
        queries.append((time.perf_counter()-start)*1000)
        if index==0: spatial.differential_candidates(map_id,area)
    linear=[]
    for index in range(30):
        origin=WorldPoint(float((index%12)*320+80),float((index//12)*320+80))
        start=time.perf_counter()
        tuple(e for e in registry.entities_for_map(world.world_id,map_id)
              if abs(e.transform.location.position.x-origin.x)<=84
              and abs(e.transform.location.position.y-origin.y)<=84)
        linear.append((time.perf_counter()-start)*1000)
    return {"entities":size,"build_ms":round(build_ms,4),
        "indexed_query_median_ms":round(statistics.median(queries),5),
        "indexed_query_p95_ms":round(percentile(queries,.95),5),
        "linear_query_median_ms":round(statistics.median(linear),5),
        "indexed_candidate_last_query":len(indexed)}

def main()->int:
    results=[run(size) for size in (100,1000,10000)]
    output=Path("artifacts/phase-09"); output.mkdir(parents=True,exist_ok=True)
    (output/"entity-spatial-benchmark.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps(results,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
