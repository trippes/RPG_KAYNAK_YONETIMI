"""Small deterministic NPC behaviour state machine."""
from __future__ import annotations
from enum import Enum

class BehaviorState(Enum): IDLE="idle"; PATROL="patrol"; WORK="work"; FLEE="flee"; FOLLOW="follow"; TALK="talk"

class BehaviorController:
    def __init__(self, state=BehaviorState.IDLE): self.state = BehaviorState(state)
    def decide(self, *, threat=False, has_work=False, follow_target=False, talking=False) -> BehaviorState:
        self.state = (BehaviorState.FLEE if threat else BehaviorState.TALK if talking else BehaviorState.FOLLOW if follow_target else BehaviorState.WORK if has_work else BehaviorState.IDLE)
        return self.state

__all__ = ["BehaviorState", "BehaviorController"]
