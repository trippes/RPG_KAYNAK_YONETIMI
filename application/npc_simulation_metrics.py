"""Low-overhead, opt-in NPC simulation diagnostics."""
from __future__ import annotations
from collections import Counter, defaultdict
from functools import wraps
import math
from statistics import median
from time import perf_counter

def _percentile(values, percentile):
    if not values: return 0.0
    ordered=sorted(values)
    return ordered[max(1, math.ceil(percentile/100.0*len(ordered)))-1]

class NPCSimulationMetrics:
    """Counters and duration samples for one controlled measurement run."""
    def __init__(self):
        self._counts=Counter()
        self._durations=defaultdict(list)
    def increment(self,name,amount=1):
        if not isinstance(name,str) or not name: raise ValueError("metric name must be non-empty")
        if type(amount) is not int or amount<0: raise ValueError("amount must be a non-negative integer")
        self._counts[name]+=amount
    def record_duration(self,name,seconds):
        if not isinstance(name,str) or not name: raise ValueError("metric name must be non-empty")
        if not math.isfinite(seconds) or seconds<0: raise ValueError("duration must be finite and non-negative")
        self._durations[name].append(float(seconds))
    def reset(self):
        self._counts.clear(); self._durations.clear()
    def snapshot(self):
        return {"counts":dict(sorted(self._counts.items())),
          "durations_seconds":{name:{"samples":len(v),"total":sum(v),"median":median(v),
          "p50":_percentile(v,50),"p95":_percentile(v,95),"p99":_percentile(v,99),"max":max(v)}
          for name,v in sorted(self._durations.items()) if v}}

def timed_npc_step(name):
    """Time a system step only when metrics are attached to its runtime."""
    def decorate(method):
        @wraps(method)
        def wrapped(self,*args,**kwargs):
            runtime=getattr(self,"_runtime",None)
            if runtime is None: runtime=getattr(self,"runtime",None)
            metrics=getattr(runtime,"metrics",None)
            if metrics is None: return method(self,*args,**kwargs)
            started=perf_counter()
            try: return method(self,*args,**kwargs)
            finally: metrics.record_duration(name,perf_counter()-started)
        return wrapped
    return decorate

__all__=["NPCSimulationMetrics","timed_npc_step"]
