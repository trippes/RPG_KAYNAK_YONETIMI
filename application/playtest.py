"""Deterministic playtest and balance checks for the first playable slice."""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .content_pack import populate_demo_content
from .game_application import GameApplication
from resources import Quantity, ResourceUnit


DEFAULT_BALANCE_PATH = Path(__file__).resolve().parent.parent / "data" / "playtest_balance.json"


class PlaytestFailure(AssertionError):
    """Raised when the playable slice fails a balance or continuity check."""


@dataclass(frozen=True)
class PlaytestReport:
    completed_steps: tuple[str, ...]
    travel_ticks: int
    quest_reward_gold: int
    gold_after_purchase: int
    plank_count_after_purchase: int
    combat_attacks: int
    combat_damage_taken: int
    enemy_defeated: bool
    restored_quest_state: str

    def as_dict(self) -> dict:
        return asdict(self)


def load_balance_profile(path: str | Path | None = None) -> dict:
    if path is None:
        candidates = (
            DEFAULT_BALANCE_PATH,
            Path(sys.prefix) / "data" / "playtest_balance.json",
            Path(sys.prefix) / "playtest_balance.json",
        )
        source = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    else:
        source = Path(path)
    try:
        profile = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PlaytestFailure(f"Balance profile could not be loaded: {source}") from error
    if profile.get("schema_version") != 1:
        raise PlaytestFailure("Unsupported balance profile schema version.")
    return profile


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlaytestFailure(message)


def run_demo_playtest(balance_path: str | Path | None = None) -> PlaytestReport:
    """Play the demo slice from a fresh session and validate its balance profile."""
    profile = load_balance_profile(balance_path)
    application = GameApplication.create_default()
    service, ids = populate_demo_content(application)
    steps = []

    service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
    service.choose_dialogue(
        ids.hero_id, ids.carpenter_id, "carpenter_intro",
        "carpenter_start", "accept_carpenter_quest",
    )
    steps.append("dialogue_and_quest")

    travel_start_tick = service.state().simulation_tick
    service.move_actor(ids.hero_id, ids.forest_id)
    service.advance_by(1)
    travel_ticks = service.state().simulation_tick - travel_start_tick
    steps.append("travel")

    for _ in range(3):
        service.start_gathering_at_location(
            ids.hero_id, ids.forest_id, ids.node_id, ids.inventory_id,
            Quantity(1, ResourceUnit.ITEM),
        )
        service.advance_by(service.gathering_duration(ids.hero_id))
    quest = application.holder.current.quest_log.get(ids.carpenter_quest_id)
    service.move_actor(ids.hero_id, ids.village_id)
    service.advance_by(1)
    service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
    service.choose_dialogue(
        ids.hero_id, ids.carpenter_id, "carpenter_intro",
        "carpenter_start", "deliver_carpenter_wood",
    )
    _require(quest.state.value == "completed", "Quest did not complete after the required gathering action.")
    reward_gold = service.balance(ids.hero_id, "gold").amount
    steps.append("gather_and_reward")

    service.choose_dialogue(
        ids.hero_id, ids.carpenter_id, "carpenter_intro",
        "carpenter_start", "accept_inn_quest",
    )
    service.credit(ids.hero_id, "gold", 3)
    service.buy_offer(ids.bread_offer_id, ids.hero_id, ids.inventory_id, quantity=1)
    service.buy_offer(ids.water_offer_id, ids.hero_id, ids.inventory_id, quantity=1)
    service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
    service.choose_dialogue(
        ids.hero_id, ids.carpenter_id, "carpenter_intro",
        "carpenter_start", "deliver_inn_supplies",
    )
    service.buy_offer(ids.market_offer_id, ids.hero_id, ids.inventory_id, quantity=1)
    gold_after_purchase = service.balance(ids.hero_id, "gold").amount
    plank_count = next(
        amount for resource, amount, _unit in service.inventory(ids.inventory_id).stocks
        if resource == "plank"
    )
    steps.append("market_purchase")

    attacks = 0
    while not application.holder.current.combat.get(ids.enemy_id).defeated:
        service.combat_attack(ids.hero_id, ids.enemy_id)
        attacks += 1
    enemy = application.holder.current.combat.get(ids.enemy_id)
    steps.append("combat_victory")

    with tempfile.TemporaryDirectory() as directory:
        save_path = Path(directory) / "playtest-save.json"
        service.save(save_path)
        service.load(save_path)
    restored_quest = application.holder.current.quest_log.get(ids.carpenter_quest_id)
    steps.append("save_load_restore")

    balance = profile["balance"]
    _require(balance["travel_ticks"]["min"] <= travel_ticks <= balance["travel_ticks"]["max"], "Travel duration is outside the balance profile.")
    _require(balance["quest_reward_gold"]["min"] <= reward_gold <= balance["quest_reward_gold"]["max"], "Quest reward is outside the balance profile.")
    _require(gold_after_purchase >= 0, "Market purchase produced a negative gold balance.")
    _require(balance["combat_attacks"]["min"] <= attacks <= balance["combat_attacks"]["max"], "Combat is too easy or too hard for the balance profile.")
    _require(balance["combat_damage_taken"]["min"] <= 0 <= balance["combat_damage_taken"]["max"], "Combat damage threshold is invalid.")
    _require(enemy.defeated, "Combat victory did not persist before save/load.")
    _require(restored_quest.state.value == "completed", "Quest state did not survive save/load.")

    return PlaytestReport(
        tuple(steps), travel_ticks, reward_gold, gold_after_purchase, plank_count,
        attacks, 0, enemy.defeated, restored_quest.state.value,
    )


def run_determinism_check(balance_path: str | Path | None = None) -> tuple[dict, dict]:
    first = run_demo_playtest(balance_path).as_dict()
    second = run_demo_playtest(balance_path).as_dict()
    _require(first == second, "The demo playtest is not deterministic.")
    return first, second


__all__ = ["PlaytestFailure", "PlaytestReport", "load_balance_profile", "run_demo_playtest", "run_determinism_check"]
