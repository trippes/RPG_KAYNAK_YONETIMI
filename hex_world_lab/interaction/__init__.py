"""World-space interaction query contracts."""
from .profile import InteractionProfile
from .range import world_distance, within_world_range, within_hex_range
from .target_query import TargetCandidate, TargetQuery
from .selection import select_target
__all__=["InteractionProfile","world_distance","within_world_range","within_hex_range","TargetCandidate","TargetQuery","select_target"]
