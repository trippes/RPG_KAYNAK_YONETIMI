"""Composable, content-driven quest prerequisite conditions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol


class ConditionExpression(Protocol):
    def evaluate(self, context: Mapping[str, object]) -> bool: ...


@dataclass(frozen=True)
class Condition:
    """Atomic condition evaluated against a read-only context mapping."""

    kind: str
    key: str
    expected: object = True

    def evaluate(self, context: Mapping[str, object]) -> bool:
        if not isinstance(context, Mapping):
            raise TypeError("Condition context must be a mapping.")
        if self.kind == "flag":
            return context.get("flags", {}).get(self.key, False) == self.expected
        if self.kind == "reputation":
            return context.get("reputation", {}).get(self.key, 0) >= self.expected
        if self.kind == "item":
            return context.get("items", {}).get(self.key, 0) >= self.expected
        if self.kind == "objective":
            return context.get("objectives", {}).get(self.key, 0) >= self.expected
        if self.kind == "quest_state":
            state = context.get("quest_states", {}).get(self.key, "available")
            return getattr(state, "value", state) == self.expected
        raise ValueError(f"Unknown condition kind: {self.kind}")


class AllConditions:
    """AND expression: every child condition must be true."""

    def __init__(self, conditions: Iterable[ConditionExpression] = ()) -> None:
        self.conditions = tuple(conditions)
        if any(not callable(getattr(condition, "evaluate", None)) for condition in self.conditions):
            raise TypeError("Every condition must provide evaluate(context).")

    def evaluate(self, context: Mapping[str, object]) -> bool:
        return all(condition.evaluate(context) for condition in self.conditions)


class AnyConditions:
    """OR expression: at least one child condition must be true."""

    def __init__(self, conditions: Iterable[ConditionExpression] = ()) -> None:
        self.conditions = tuple(conditions)
        if any(not callable(getattr(condition, "evaluate", None)) for condition in self.conditions):
            raise TypeError("Every condition must provide evaluate(context).")

    def evaluate(self, context: Mapping[str, object]) -> bool:
        return any(condition.evaluate(context) for condition in self.conditions)


@dataclass(frozen=True)
class NotCondition:
    """Negates one nested condition expression."""

    condition: ConditionExpression

    def __post_init__(self) -> None:
        if not callable(getattr(self.condition, "evaluate", None)):
            raise TypeError("condition must provide evaluate(context).")

    def evaluate(self, context: Mapping[str, object]) -> bool:
        return not self.condition.evaluate(context)


__all__ = [
    "Condition",
    "ConditionExpression",
    "AllConditions",
    "AnyConditions",
    "NotCondition",
]
