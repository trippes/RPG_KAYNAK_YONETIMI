"""Market spatial anchor tests; the associated NPC remains the only position owner."""

import pytest

from application import (
    GameApplication,
    GameplayService,
    MarketHexAnchorError,
    ProductionFacilityRegistry,
    SessionBundle,
    SessionHolder,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.application import GameSession
from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition
from core.foundation import WorldId
from economy import Currency, MarketCatalogEntry, MarketProfile, Money
from npc import NPC
from resources import (
    Inventory,
    ProductionJobManager,
    ResourceType,
    WorldResourceNodeManager,
)


def make_service():
    session = GameSession()
    world = session.worlds.create("Market World", world_id="market_world")
    session.worlds.set_active(world.world_id)
    bundle = SessionBundle(
        session=session,
        simulation=session.simulation,
        production_jobs=ProductionJobManager(session.simulation),
        resource_nodes=WorldResourceNodeManager(session.worlds),
        inventories={"main": Inventory()},
        recipes={},
        facilities=ProductionFacilityRegistry(),
    )
    service = GameplayService(GameApplication(SessionHolder(bundle)))
    service.configure_player_context("hero", "main", "hero")
    runtime = HexWorldRuntime(
        {"field": make_map()},
        world_id=WorldId("market_world"),
    )
    bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)
    return service, bundle, runtime


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "field",
        "name": "Field",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0]],
        "cell_overrides": [],
        "transitions": [],
    })


def register_market(service, *, register_spatial=True):
    service.register_npc(NPC("trader", "Trader"))
    service.register_actor("trader", "npc")
    if register_spatial:
        service.npc_hex_binding.register_spatial(
            "trader",
            EntityPosition("field", LocalHexPosition(0, 0)),
        )
    profile = MarketProfile(
        "iron-market",
        "legacy-square-village-id",
        "trader",
        "merchant-trader",
        "merchant-inventory",
        1,
        (
            MarketCatalogEntry(
                ResourceType("iron"),
                Money(3, Currency("gold")),
                1,
                2,
            ),
        ),
    )
    service.register_market_profile(profile)
    return profile


def test_market_position_is_derived_from_its_npc_not_legacy_location_id():
    service, _bundle, runtime = make_service()
    profile = register_market(service)

    position = service.market_hex_anchor.position("iron-market")

    assert profile.location_id == "legacy-square-village-id"
    assert position == EntityPosition("field", LocalHexPosition(0, 0))
    assert tuple(entity.entity_id for entity in runtime.entities()) == ("trader",)


def test_market_anchor_tracks_npc_movement_without_storing_a_second_position():
    service, _bundle, runtime = make_service()
    register_market(service)

    moved = service.npc_hex_binding.move("trader", HexDirection.EAST)
    position = service.market_hex_anchor.position("iron-market")

    assert moved.success
    assert position == EntityPosition("field", LocalHexPosition(1, 0))
    assert tuple(entity.entity_id for entity in runtime.entities()) == ("trader",)


def test_market_anchor_requires_its_associated_npc_to_be_spatially_registered():
    service, _bundle, _runtime = make_service()
    register_market(service, register_spatial=False)

    with pytest.raises(MarketHexAnchorError, match="no spatially registered NPC anchor"):
        service.market_hex_anchor.position("iron-market")


def test_market_anchor_rejects_unknown_market_profile():
    service, _bundle, _runtime = make_service()

    with pytest.raises(KeyError, match="Market profile not found"):
        service.market_hex_anchor.position("missing-market")



def test_market_anchor_rejects_npc_actor_from_another_world():
    service, bundle, _runtime = make_service()
    other_world = bundle.session.worlds.create("Other", world_id="other_market_world")
    service.register_npc(NPC("trader", "Trader"))
    service.register_actor("trader", "npc", world_id=other_world.world_id)
    service.register_market_profile(MarketProfile(
        "iron-market",
        "legacy-square-village-id",
        "trader",
        "merchant-trader",
        "merchant-inventory",
        1,
        (
            MarketCatalogEntry(
                ResourceType("iron"),
                Money(3, Currency("gold")),
                1,
                2,
            ),
        ),
    ))

    with pytest.raises(MarketHexAnchorError, match="no spatially registered NPC anchor"):
        service.market_hex_anchor.position("iron-market")
