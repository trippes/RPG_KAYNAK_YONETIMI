"""Application-level facade for the active Core/gameplay session bundle."""


from core.application.session import GameSession
from core.constants import (
    OLAY_OYUN_BASLATILDI,
    OLAY_OYUN_BITTI,
    OLAY_OYUN_DEVAM_ETTIRILDI,
    OLAY_OYUN_DURAKLATILDI,
)
from core.entity.entity import Entity
from core.event_manager import EventManager
from core.event_types import EventType
from core.game_state import GameState
from core.compatibility import CanonicalActionAdapter, deprecated_api
from core.persistence import (
    CanonicalSessionState,
    PersistenceDocument,
    RestoreContract,
)
from resources import GameplaySnapshot

from application.session_bundle import SessionBundle, SessionHolder
from application.save_file_adapter import GameSaveFileAdapter
from application.save_document import GameSaveDocument
from application.production_persistence import ProductionSnapshot
from application.actor_persistence import ActorSnapshot
from character import Character, CharacterFactory, CharacterSnapshot
from types import MappingProxyType
from application.production_facility import ProductionFacilityRegistry
from quests import QuestLog, QuestSnapshot
from application.actor_system import WorldActor
from economy import Economy, EconomySnapshot
from application.extended_persistence import SocialSnapshot, CombatSnapshot
from core.domain.spatial import Position


class GameApplication:
    """Run application operations against the currently published bundle.

    The legacy ``ActionManager`` remains application-owned and deliberately
    separate from the canonical ``SimulationRuntime`` action registry.  Core
    ``Game`` is not modified; this facade mirrors its public compatibility
    operations while resolving session-owned objects from one bundle per call.
    """

    def __init__(self, holder: SessionHolder | None = None) -> None:
        self.holder = holder if holder is not None else SessionHolder()
        self.state = GameState()
        self.event_manager = EventManager()
        self._action_adapters = {}
        self.events = self.event_manager.event_queue

    @classmethod
    def create_default(cls) -> "GameApplication":
        return cls(SessionHolder(SessionBundle.create_default()))

    @property
    def actions(self):
        processor = self.holder.current.simulation.actions
        adapter = self._action_adapters.get(id(processor))
        if adapter is None:
            adapter = CanonicalActionAdapter(processor)
            self._action_adapters[id(processor)] = adapter
        return adapter
    
    def load(self, path):
        """Load a unified save into a disposable candidate bundle.

        The active bundle is not touched until every Core/gameplay
        validation and cross-reference check succeeds.
        """
        document = GameSaveFileAdapter.load(path)
        candidate_session = GameSession()
        core_state = document.core.to_state()
        core_plan = RestoreContract.prepare(core_state)
        candidate_session.activate_restore(core_plan)

        candidate_runtime = candidate_session.simulation
        restored = document.gameplay.restore(runtime=candidate_runtime)

        restored.nodes.bind_world_registry(candidate_session.worlds)
        restored.nodes.validate_world_references()
        facilities = (
            document.production.restore(restored.jobs)
            if document.production is not None
            else ProductionFacilityRegistry()
        )
        characters = document.characters.restore() if document.characters is not None else {}
        actors = None
        actor_activities = None
        if document.actors is not None:
            actors, actor_activities = document.actors.restore(
                candidate_session.worlds,
                restored.jobs,
                restored.nodes,
                facilities,
                restored.inventories,
                restored.recipes,
                characters,
            )

        candidate = SessionBundle(
            session=candidate_session,
            simulation=candidate_runtime,
            production_jobs=restored.jobs,
            resource_nodes=restored.nodes,
            inventories=restored.inventories,
            recipes=restored.recipes,
            facilities=facilities,
            actors=actors,
            actor_activities=actor_activities,
            characters=characters,
            quest_log=document.quests.restore({}) if document.quests is not None else QuestLog(),
            economy=(
                Economy(*document.economy.restore())
                if document.economy is not None else Economy()
            ),
            social=document.social.restore() if document.social is not None else None,
            combat=document.combat.restore() if document.combat is not None else None,
        )

        # Older saves did not persist NPC tile positions. Restore the demo
        # defaults for those records so existing slots remain interactive.
        legacy_npc_positions = {
            "warden_lyra": Position(16, 30),
            "village_carpenter": Position(21, 15),
            "village_innkeeper": Position(20, 23),
        }
        for npc_id, position in legacy_npc_positions.items():
            npc = candidate.social.npcs.get(npc_id)
            if npc is not None and npc.position == Position():
                npc.position = position
        
    
        from application.content_pack import build_demo_world_map

        # Rebuild demo maps only when they match saved actor locations.
        for world in candidate.session.worlds.get_all():
            world_map = build_demo_world_map(world.world_id)

            saved_location_ids = {
                actor.location_id
                for actor in candidate.actors.actors()
                if actor.world_id == world.world_id
                and actor.location_id is not None
            } if candidate.actors is not None else set()

            demo_location_ids = {
                location.location_id
                for location in world_map.locations()
            }

            if saved_location_ids and not saved_location_ids.issubset(demo_location_ids):
                continue

            candidate.movement.register_map(world_map)

        # Restore actor positions only when their locations exist in the map.
        if candidate.actors is not None:
            for actor_view in candidate.actors.actors():
                if actor_view.location_id is None:
                    continue

                world_map = candidate.movement.map_for(actor_view.world_id)
                if world_map is None:
                    continue

                if world_map.get(actor_view.location_id) is None:
                    continue

                candidate.movement.set_position(
                    actor_view.actor_id,
                    actor_view.location_id,
                )
                if actor_view.position is not None:
                    candidate.movement.set_tile_position(
                        actor_view.actor_id,
                        int(actor_view.position.x),
                        int(actor_view.position.y),
                    )

        self.holder.publish(candidate)
        return self.holder.current

    def save(self, path):
        """Persist one consistent snapshot of the currently active bu   ndle."""
        bundle = self.holder.current
        bundle.validate()
        core_state = CanonicalSessionState.from_session(bundle.session)
        core_document = PersistenceDocument.from_state(core_state)
        gameplay_snapshot = GameplaySnapshot.from_runtime(
            bundle.inventories,
            bundle.resource_nodes,
            bundle.production_jobs,
            bundle.recipes,
        )
        production_snapshot = (
            ProductionSnapshot.from_registry(bundle.facilities)
            if bundle.facilities.count()
            else None
        )
        actor_snapshot = (
            ActorSnapshot.from_runtime(bundle.actors, bundle.actor_activities, bundle.characters)
            if bundle.actors.count() or bundle.actor_activities.count()
            else None
        )
        document = GameSaveDocument(
            core=core_document,
            gameplay=gameplay_snapshot,
            production=production_snapshot,
            actors=actor_snapshot,
            characters=(CharacterSnapshot.from_characters(bundle.characters) if bundle.characters else None),
            quests=(QuestSnapshot.from_log(bundle.quest_log) if bundle.quest_log.all() else None),
            economy=(
                EconomySnapshot.from_runtime(bundle.economy.ledger, bundle.economy.market, bundle.economy.merchants)
                if bundle.economy.ledger.accounts() or bundle.economy.market.prices.prices() or bundle.economy.market.offers()
                else None
            ),
            social=(SocialSnapshot.from_runtime(bundle.social) if bundle.social.npcs.all() or bundle.social.dialogues or bundle.social.relationships.all() else None),
            combat=(CombatSnapshot.from_runtime(bundle.combat) if bundle.combat.all() else None),
        )
        return GameSaveFileAdapter.save(document, path)

    def karakter_olustur(self, factory: CharacterFactory, character_id: str, name: str, race_id: str, class_id: str, actor_id: str | None = None) -> Character:
        """Create and register a basic character in the active session."""
        if not isinstance(factory, CharacterFactory):
            raise TypeError("factory must be CharacterFactory.")
        bundle = self.holder.current
        actor_id = actor_id or character_id
        world = bundle.session.worlds.get_active()
        if world is None:
            raise RuntimeError("Karakter oluşturmak için aktif bir dünya gereklidir.")
        if bundle.actors.get(actor_id) is not None:
            raise ValueError(f"Duplicate actor ID: {actor_id}")
        character = factory.create_basic(character_id, name, race_id, class_id, actor_id)
        characters = dict(bundle.characters)
        if character.character_id in characters:
            raise ValueError(f"Duplicate character ID: {character.character_id}")
        characters[character.character_id] = character
        actor = WorldActor(actor_id, world.world_id, character.character_class.name)
        bundle.actors.add(actor)
        bundle.actors.bind_character(actor_id, character)
        object.__setattr__(bundle, "characters", MappingProxyType(characters))
        bundle.validate()
        return character

    def baslat(self):
        bundle = self.holder.current
        self.state.baslat()
        if bundle.session.worlds.has_active():
            bundle.session.worlds.resume_active()
        self.event_manager.ekle(OLAY_OYUN_BASLATILDI)

    def duraklat(self):
        bundle = self.holder.current
        self.state.duraklat()
        if bundle.session.worlds.has_active():
            bundle.session.worlds.pause_active()
        self.event_manager.ekle(OLAY_OYUN_DURAKLATILDI)

    def devam_ettir(self):
        bundle = self.holder.current
        self.state.devam_ettir()
        if bundle.session.worlds.has_active():
            bundle.session.worlds.resume_active()
        self.event_manager.ekle(OLAY_OYUN_DEVAM_ETTIRILDI)

    def bitir(self):
        bundle = self.holder.current
        self.state.bitir()
        if bundle.session.worlds.has_active():
            bundle.session.worlds.pause_active()
        self.event_manager.ekle(OLAY_OYUN_BITTI)

    def sifirla(self):
        self.state.sifirla()
        self.event_manager.temizle()

    def dunya_olustur(self, name, width=None, height=None, world_id=None,
                       aktif_yap=True):
        bundle = self.holder.current
        world = bundle.session.worlds.create(
            name=name, width=width, height=height, world_id=world_id,
        )
        if aktif_yap:
            bundle.session.worlds.set_active(world.world_id)
            if not self.state.calisiyor:
                world.pause()
        return world

    def aktif_dunya(self):
        return self.holder.current.session.worlds.get_active()

    def advance_simulation(self, target_tick):
        return self.holder.current.simulation.advance_to(target_tick)

    def dunya_olaylarini_canonical_aktar(self, world=None):
        bundle = self.holder.current
        if world is None:
            world = bundle.session.worlds.get_active()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")
        return bundle.session.dispatch_world_events(world)

    @deprecated_api("Game.dunya_olaylarini_aktar")
    def dunya_olaylarini_aktar(self, world=None):
        """Forward legacy world events to the application event queue."""
        bundle = self.holder.current
        if world is None:
            world = bundle.session.worlds.get_active()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")

        aktarilan_sayi = 0
        while world.has_pending_events():
            self.event_manager.event_queue.ekle(world.get_event())
            aktarilan_sayi += 1
        return aktarilan_sayi

    def varlik_ekle(self, entity, world_id=None):
        bundle = self.holder.current
        if not isinstance(entity, Entity):
            raise TypeError("Yalnızca Entity nesneleri oyuna eklenebilir.")

        world = None
        if world_id is not None:
            world = bundle.session.worlds.get(world_id)
            if world is None:
                raise KeyError(f"World bulunamadı: {world_id}")
        elif bundle.session.worlds.has_active():
            world = bundle.session.worlds.get_active()

        if world is not None and entity.has_world():
            raise ValueError("World'e bağlı bir Entity yeniden eklenemez.")

        bundle.session.add_entity(
            entity,
            world_id=world.world_id if world is not None else None,
        )
        self.event_manager.ekle(
            EventType.ENTITY_OLUSTURULDU,
            {
                "entity_id": entity.entity_id,
                "world_id": bundle.session.membership.world_id_for(entity.entity_id),
            },
        )
        return entity

    def varlik_cikar(self, entity_id):
        bundle = self.holder.current
        entity = bundle.session.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity bulunamadı: {entity_id}")

        if bundle.session.membership.world_id_for(entity_id) is not None:
            bundle.session.remove_entity(entity_id)
        else:
            if entity.world_id is not None:
                world = bundle.session.worlds.get(entity.world_id)
                if world is not None and world.has_entity(entity_id):
                    world.remove_entity(entity_id)
            bundle.session.entities.remove(entity_id)
        self.event_manager.ekle(
            EventType.ENTITY_YOK_EDILDI, {"entity_id": entity_id},
        )
        return entity

    def zamani_ilerlet(self, ticks):
        bundle = self.holder.current
        if not self.state.calisiyor:
            raise RuntimeError("Zamanı ilerletmek için oyun aktif olmalıdır.")
        world = bundle.session.worlds.get_active()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")
        runtime = bundle.simulation
        onceki_tick, current_tick = bundle.session.world_runtime.advance_world(world, ticks)
        onceki_tick = onceki_tick.value
        zaman = world.time
        if world.total_ticks == onceki_tick:
            return zaman

        tamamlananlar = self.actions.guncelle(current_tick.value)
        self.event_manager.ekle(
            EventType.ZAMAN_ILERLEDI,
            {
                "world_id": world.world_id,
                "onceki_tick": onceki_tick,
                "toplam_tick": world.total_ticks,
            },
        )
        for aksiyon in tamamlananlar:
            self.event_manager.ekle(
                EventType.AKSIYON_TAMAMLANDI,
                {"aksiyon_id": aksiyon.id, "sahip": aksiyon.sahip},
            )
        self.dunya_olaylarini_canonical_aktar(world)
        return zaman

    def aksiyon_baslat(self, tur, sahip, sure, veri=None):
        bundle = self.holder.current
        if not self.state.calisiyor:
            raise RuntimeError("Aksiyon başlatmak için oyun aktif olmalıdır.")
        world = bundle.session.worlds.get_active()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")
        aksiyon = self.actions.aksiyon_olustur(tur, sahip, sure, veri)
        self.actions.aksiyon_baslat(aksiyon.id, world.total_ticks)
        self.event_manager.ekle(
            EventType.AKSIYON_BASLATILDI,
            {"aksiyon_id": aksiyon.id, "tur": tur, "sahip": sahip},
        )
        return aksiyon

    def olay_al(self):
        return self.event_manager.event_queue.al()

    def bekleyen_olay_sayisi(self):
        return self.event_manager.bekleyen_sayi()

    def olaylari_islet(self):
        return self.event_manager.islet()

    def bilgi(self):
        bundle = self.holder.current
        return {
            "state": self.state.bilgi(),
            "bekleyen_olay_sayisi": self.bekleyen_olay_sayisi(),
            "world_sayisi": bundle.session.worlds.count(),
            "aktif_world_id": bundle.session.worlds.get_active_id(),
            "entity_sayisi": bundle.session.entities.count(),
            "aksiyon_sayisi": self.actions.aksiyon_sayisi(),
        }
