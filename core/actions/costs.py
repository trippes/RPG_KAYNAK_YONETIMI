"""Canonical tick costs for instantaneous gameplay actions."""

from enum import Enum

from core.time import Tick


class ActionType(str, Enum):
    INTERACT = "interact"
    DIALOGUE = "dialogue"
    DIALOGUE_CHOICE = "dialogue_choice"
    TRADE = "trade"
    CONSUME_ITEM = "consume_item"
    COMBAT_ATTACK = "combat_attack"
    COMBAT_TURN = "combat_turn"


ACTION_TICK_COSTS: dict[ActionType, Tick] = {
    ActionType.INTERACT: Tick(1),
    ActionType.DIALOGUE: Tick(1),
    ActionType.DIALOGUE_CHOICE: Tick(1),
    ActionType.TRADE: Tick(1),
    ActionType.CONSUME_ITEM: Tick(1),
    ActionType.COMBAT_ATTACK: Tick(1),
    ActionType.COMBAT_TURN: Tick(1),
}


def action_tick_cost(action_type: ActionType | str) -> Tick:
    """Return the canonical cost for a fixed-duration gameplay action."""
    try:
        normalized = (
            action_type
            if isinstance(action_type, ActionType)
            else ActionType(action_type)
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"Unknown action type: {action_type}") from error
    return ACTION_TICK_COSTS[normalized]
