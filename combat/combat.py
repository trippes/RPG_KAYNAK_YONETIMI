"""Deterministic combat domain runtime."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Combatant:
    combatant_id: str
    max_hit_points: int
    attack: int = 1
    defense: int = 0
    hit_points: int | None = None
    statuses: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.combatant_id, str) or not self.combatant_id.strip():
            raise ValueError("combatant_id must be non-empty.")
        if self.max_hit_points <= 0 or self.attack < 0 or self.defense < 0:
            raise ValueError("Invalid combatant configuration.")
        self.hit_points = self.max_hit_points if self.hit_points is None else self.hit_points
        if not 0 <= self.hit_points <= self.max_hit_points:
            raise ValueError("hit_points out of range.")

    @property
    def defeated(self) -> bool:
        return self.hit_points == 0

    def add_status(self, status_id: str, duration: int) -> None:
        if not isinstance(status_id, str) or not status_id.strip() or duration <= 0:
            raise ValueError("Status ID and positive duration are required.")
        self.statuses[status_id] = max(duration, self.statuses.get(status_id, 0))

    def tick_statuses(self) -> None:
        self.statuses = {key: value - 1 for key, value in self.statuses.items() if value > 1}

@dataclass(frozen=True)
class CombatResult:
    attacker_id: str
    defender_id: str
    damage: int
    defender_hit_points: int
    defender_defeated: bool

@dataclass
class CombatEncounter:
    encounter_id: str
    initiative_order: tuple[str, ...]
    round_number: int = 1
    active_index: int = 0

    @property
    def active_combatant_id(self) -> str:
        return self.initiative_order[self.active_index]

    def next_turn(self) -> str:
        self.active_index = (self.active_index + 1) % len(self.initiative_order)
        if self.active_index == 0: self.round_number += 1
        return self.active_combatant_id

class CombatRuntime:
    def __init__(self):
        self._combatants: dict[str, Combatant] = {}
        self._encounters: dict[str, CombatEncounter] = {}

    def add(self, combatant: Combatant) -> None:
        if not isinstance(combatant, Combatant): raise TypeError("combatant must be Combatant.")
        if combatant.combatant_id in self._combatants: raise ValueError(f"Duplicate combatant ID: {combatant.combatant_id}")
        self._combatants[combatant.combatant_id] = combatant

    def get(self, combatant_id: str) -> Combatant | None:
        return self._combatants.get(combatant_id)

    def attack_once(self, attacker_id: str, defender_id: str) -> CombatResult:
        attacker = self._require(attacker_id); defender = self._require(defender_id)
        if attacker.defeated or defender.defeated: raise ValueError("Defeated combatants cannot attack.")
        damage = max(0, attacker.attack - defender.defense)
        defender.hit_points = max(0, defender.hit_points - damage)
        return CombatResult(attacker_id, defender_id, damage, defender.hit_points, defender.defeated)

    def advance_round(self) -> None:
        for combatant in self._combatants.values(): combatant.tick_statuses()

    def create_encounter(self, encounter_id: str, combatant_ids, initiative_scores=None) -> CombatEncounter:
        if encounter_id in self._encounters: raise ValueError(f"Duplicate encounter ID: {encounter_id}")
        ids = tuple(combatant_ids)
        if not ids or len(set(ids)) != len(ids): raise ValueError("Encounter needs unique combatants.")
        for combatant_id in ids: self._require(combatant_id)
        scores = initiative_scores or {}
        encounter = CombatEncounter(encounter_id, tuple(sorted(ids, key=lambda item: (-scores.get(item, 0), item))))
        self._encounters[encounter_id] = encounter
        return encounter

    def encounter(self, encounter_id: str) -> CombatEncounter | None:
        return self._encounters.get(encounter_id)

    def next_turn(self, encounter_id: str) -> str:
        encounter = self.encounter(encounter_id)
        if encounter is None: raise KeyError(f"Encounter not found: {encounter_id}")
        self.advance_round()
        return encounter.next_turn()

    def encounters(self) -> tuple[CombatEncounter, ...]:
        return tuple(self._encounters[key] for key in sorted(self._encounters))

    def all(self) -> tuple[Combatant, ...]:
        return tuple(self._combatants[key] for key in sorted(self._combatants))

    def _require(self, combatant_id: str) -> Combatant:
        combatant = self.get(combatant_id)
        if combatant is None: raise KeyError(f"Combatant not found: {combatant_id}")
        return combatant
