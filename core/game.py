"""
RPG Kaynak Yönetimi
Çekirdek 1.6 - Oyun Çekirdeği

Game sınıfı, oyunun temel sistemlerini bir araya getirir.
"""

from core.game_state import GameState
from core.application.session import GameSession
from core.event_manager import EventManager
from core.event_types import EventType
from core.entity.entity import Entity
from core.world.world_manager import WorldManager
from core.constants import (
    OLAY_OYUN_BASLATILDI,
    OLAY_OYUN_DURAKLATILDI,
    OLAY_OYUN_DEVAM_ETTIRILDI,
    OLAY_OYUN_BITTI,
)
from core.compatibility import CanonicalActionAdapter, deprecated_api


class Game:
    """
    Oyunun temel çekirdek nesnesidir.

    Bu aşamada Game:
        - oyun durumunu,
        - olay yöneticisini,
        - temel yaşam döngüsünü

    yönetir.
    """

    def __init__(self):
        self.state = GameState()
        self.event_manager = EventManager()

        # Canonical Core 2.x runtime boundary. The public aliases below keep
        # the existing 1.x Game surface available during migration.
        self.session = GameSession()
        self.worlds = self.session.worlds
        self.entities = self.session.entities
        self.actions = CanonicalActionAdapter(self.session.simulation.actions)

        # Mevcut API korunuyor.
        self.events = self.event_manager.event_queue

    def baslat(self):
        """Oyunu başlatır."""

        self.state.baslat()

        if self.worlds.has_active():
            self.worlds.resume_active()

        self.event_manager.ekle(
            OLAY_OYUN_BASLATILDI
        )

    def duraklat(self):
        """Oyunu duraklatır."""

        self.state.duraklat()

        if self.worlds.has_active():
            self.worlds.pause_active()

        self.event_manager.ekle(
            OLAY_OYUN_DURAKLATILDI
        )

    def devam_ettir(self):
        """Duraklatılmış oyunu devam ettirir."""

        self.state.devam_ettir()

        if self.worlds.has_active():
            self.worlds.resume_active()

        self.event_manager.ekle(
            OLAY_OYUN_DEVAM_ETTIRILDI
        )

    def bitir(self):
        """Oyunu sonlandırır."""

        self.state.bitir()

        if self.worlds.has_active():
            self.worlds.pause_active()

        self.event_manager.ekle(
            OLAY_OYUN_BITTI
        )

    def sifirla(self):
        """Oyunu başlangıç durumuna döndürür."""

        self.state.sifirla()
        self.event_manager.temizle()

    # ========================================================
    # DÜNYA VE VARLIK ENTEGRASYONU
    # ========================================================

    def dunya_olustur(self, name, width=None, height=None, world_id=None,
                       aktif_yap=True):
        """Yeni bir dünya oluşturur ve istenirse aktif dünya yapar."""

        world = self.worlds.create(
            name=name,
            width=width,
            height=height,
            world_id=world_id,
        )

        if aktif_yap:
            self.worlds.set_active(world.world_id)
            if not self.state.calisiyor:
                world.pause()

        return world

    def aktif_dunya(self):
        """Aktif dünyayı döndürür; aktif dünya yoksa ``None`` döner."""

        return self.worlds.get_active()

    def advance_simulation(self, target_tick):
        """Advance the canonical Core 2.x simulation runtime.

        The existing ``zamani_ilerlet`` API remains the 1.x World-clock
        compatibility path. This method exposes the new deterministic runtime
        without changing that behavior.
        """

        return self.session.simulation.advance_to(target_tick)

    @deprecated_api("Game.dunya_olaylarini_aktar")
    def dunya_olaylarini_aktar(self, world=None):
        """Bir dünyanın bekleyen olaylarını ana oyun olay kuyruğuna taşır.

        Dünya zamanlayıcısı gibi alt sistemlerin ürettiği olaylar böylece
        oyun seviyesindeki abonelere aynı ``EventBus`` üzerinden ulaşır.
        """

        if world is None:
            world = self.aktif_dunya()

        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")

        aktarilan_sayi = 0
        while world.has_pending_events():
            self.event_manager.event_queue.ekle(world.get_event())
            aktarilan_sayi += 1

        return aktarilan_sayi

    def dunya_olaylarini_canonical_aktar(self, world=None):
        """Route World-local events through the Core 2.x canonical transport."""
        if world is None:
            world = self.aktif_dunya()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")
        return self.session.dispatch_world_events(world)

    def varlik_ekle(self, entity, world_id=None):
        """Varlığı merkezi kayda ve seçilen dünyaya atomik olarak ekler."""

        if not isinstance(entity, Entity):
            raise TypeError("Yalnızca Entity nesneleri oyuna eklenebilir.")

        world = None
        if world_id is not None:
            world = self.worlds.get(world_id)
            if world is None:
                raise KeyError(f"World bulunamadı: {world_id}")
        elif self.worlds.has_active():
            world = self.worlds.get_active()

        if world is not None and entity.has_world():
            raise ValueError("World'e bağlı bir Entity yeniden eklenemez.")

        try:
            self.session.add_entity(
                entity,
                world_id=world.world_id if world is not None else None,
            )
        except Exception:
            raise

        self.event_manager.ekle(
            EventType.ENTITY_OLUSTURULDU,
            {"entity_id": entity.entity_id, "world_id": self.session.membership.world_id_for(entity.entity_id)},
        )
        return entity

    def varlik_cikar(self, entity_id):
        """Varlığı bağlı dünyadan ve merkezi kayıttan kaldırır."""

        entity = self.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity bulunamadı: {entity_id}")

        if self.session.membership.world_id_for(entity_id) is not None:
            self.session.remove_entity(entity_id)
        else:
            # Compatibility path for callers that used World.add_entity()
            # directly in 1.x, bypassing the canonical service.
            if entity.world_id is not None:
                world = self.worlds.get(entity.world_id)
                if world is not None and world.has_entity(entity_id):
                    world.remove_entity(entity_id)
            self.entities.remove(entity_id)
        self.event_manager.ekle(
            EventType.ENTITY_YOK_EDILDI,
            {"entity_id": entity_id},
        )
        return entity

    # ========================================================
    # ZAMAN VE AKSİYON ENTEGRASYONU
    # ========================================================

    def zamani_ilerlet(self, ticks):
        """Aktif dünyanın zamanını ilerletir ve süresi dolan aksiyonları işler."""

        if not self.state.calisiyor:
            raise RuntimeError("Zamanı ilerletmek için oyun aktif olmalıdır.")

        world = self.aktif_dunya()
        if world is None:
            raise RuntimeError("Aktif World bulunmamaktadır.")
        runtime = self.session.simulation
        onceki_tick, current_tick = self.session.world_runtime.advance_world(world, ticks)
        onceki_tick = onceki_tick.value
        zaman = world.time

        # Dünya durmuşsa zaman ve aksiyon durumu değişmez.
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
        # Internal 1.x forwarding is an implementation detail; avoid treating
        # it as an external deprecated call and emitting a warning.
        self.dunya_olaylarini_aktar.__wrapped__(self, world)
        return zaman

    def aksiyon_baslat(self, tur, sahip, sure, veri=None):
        """Aktif dünya zamanına bağlı yeni bir aksiyon başlatır."""

        if not self.state.calisiyor:
            raise RuntimeError("Aksiyon başlatmak için oyun aktif olmalıdır.")

        world = self.aktif_dunya()
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
        """Sıradaki oyun olayını döndürür."""

        return self.event_manager.event_queue.al()

    def bekleyen_olay_sayisi(self):
        """Bekleyen olay sayısını döndürür."""

        return self.event_manager.bekleyen_sayi()

    def olaylari_islet(self):
        """Bekleyen tüm oyun olaylarını EventBus üzerinden işler."""

        return self.event_manager.islet()

    def bilgi(self):
        """Oyunun mevcut çekirdek durumunu döndürür."""

        return {
            "state": self.state.bilgi(),
            "bekleyen_olay_sayisi": self.bekleyen_olay_sayisi(),
            "world_sayisi": self.worlds.count(),
            "aktif_world_id": self.worlds.get_active_id(),
            "entity_sayisi": self.entities.count(),
            "aksiyon_sayisi": self.actions.aksiyon_sayisi(),
        }
