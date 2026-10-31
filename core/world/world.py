from core.entity.entity import Entity
from core.world.world_id import WorldIDGenerator
from core.domain import WorldDomainState
from core.foundation import WorldId
from core.world.legacy_runtime import LegacyWorldRuntime


class World:
    """
    Motor içerisindeki temel dünya nesnesini temsil eder.

    World;
    - Entity kayıtlarını
    - Dünya zamanını
    - Dünya olay kuyruğunu
    - Zamanlanmış olayları
    yönetir.
    """

    _id_generator = WorldIDGenerator()

    def __init__(
        self,
        name,
        width=None,
        height=None,
        world_id=None,
        start_tick=0,
    ):
        if not isinstance(name, str):
            raise TypeError(
                "World adı metin olmalıdır."
            )

        if not name.strip():
            raise ValueError(
                "World adı boş olamaz."
            )

        if width is not None:
            if isinstance(width, bool) or not isinstance(width, int):
                raise TypeError(
                    "World genişliği tam sayı olmalıdır."
                )

            if width <= 0:
                raise ValueError(
                    "World genişliği 0'dan büyük olmalıdır."
                )

        if height is not None:
            if isinstance(height, bool) or not isinstance(height, int):
                raise TypeError(
                    "World yüksekliği tam sayı olmalıdır."
                )

            if height <= 0:
                raise ValueError(
                    "World yüksekliği 0'dan büyük olmalıdır."
                )

        if world_id is None:
            world_id = self._id_generator.generate()

        if not isinstance(world_id, str):
            raise TypeError(
                "World ID metin olmalıdır."
            )

        if not world_id.strip():
            raise ValueError(
                "World ID boş olamaz."
            )

        if not isinstance(start_tick, int):
            raise TypeError(
                "start_tick tam sayı olmalıdır."
            )

        if start_tick < 0:
            raise ValueError(
                "Başlangıç zamanı negatif olamaz."
            )

        self.world_id = world_id
        self.name = name
        self.width = width
        self.height = height

        self._entities = {}

        # Dünya zamanı
        self._legacy_runtime = LegacyWorldRuntime(start_tick)
        self._clock = self._legacy_runtime.clock
        self._event_queue = self._legacy_runtime.event_queue
        self._scheduler = self._legacy_runtime.scheduler

    @property
    def domain_state(self) -> WorldDomainState:
        """Return the runtime-free canonical World contract."""
        return WorldDomainState(WorldId(self.world_id), self.name, self.width, self.height)

    # ========================================================
    # CLOCK
    # ========================================================

    @property
    def clock(self):
        return self._clock

    @property
    def total_ticks(self):
        return self._clock.total_ticks

    @property
    def time(self):
        return self._clock.time

    @property
    def running(self):
        return self._clock.running

    def advance(self, ticks):
        return self._clock.advance(ticks)

    def advance_seconds(self, seconds):
        return self._clock.advance_seconds(seconds)

    def advance_minutes(self, minutes):
        return self._clock.advance_minutes(minutes)

    def advance_hours(self, hours):
        return self._clock.advance_hours(hours)

    def advance_days(self, days):
        return self._clock.advance_days(days)

    def advance_months(self, months):
        return self._clock.advance_months(months)

    def advance_years(self, years):
        return self._clock.advance_years(years)

    def pause(self):
        self._clock.pause()

    def resume(self):
        self._clock.resume()

    def reset_time(self):
        self._clock.reset()

    def set_time(self, total_ticks):
        self._clock.set_time(total_ticks)

    # ========================================================
    # SCHEDULER
    # ========================================================

    @property
    def scheduler(self):
        """
        World'ün zamanlanmış olay yöneticisini döndürür.
        """
        return self._scheduler

    def schedule_event(
        self,
        trigger_tick,
        callback,
        description="",
    ):
        """
        Belirli bir World zamanında callback çalıştırır.

        Dönen değer Scheduler tarafından verilen event_id'dir.
        """

        return self._scheduler.schedule(
            trigger_tick=trigger_tick,
            callback=callback,
            description=description,
        )

    def cancel_scheduled_event(self, event_id):
        """
        Zamanlanmış olayı iptal eder.

        Başarılıysa True, bulunamazsa False döner.
        """

        return self._scheduler.cancel(
            event_id
        )

    @property
    def scheduled_event_count(self):
        """
        Bekleyen zamanlanmış olay sayısını döndürür.
        """
        return self._scheduler.pending_count

    def clear_scheduled_events(self):
        """
        Tüm zamanlanmış olayları temizler.
        """
        self._scheduler.clear()

    # ========================================================
    # EVENT
    # ========================================================

    @property
    def event_queue(self):
        return self._event_queue

    def emit_event(self, tur, veri=None):
        """
        Yeni Event oluşturur ve World olay kuyruğuna ekler.
        """

        olay = self._legacy_runtime.create_event(tur, veri)

        self._event_queue.ekle(olay)

        return olay

    def add_event(self, olay):
        """
        Mevcut Event nesnesini World olay kuyruğuna ekler.
        """

        self._event_queue.ekle(olay)

    def get_event(self):
        """
        Kuyruktaki ilk olayı çıkarıp döndürür.
        """

        return self._event_queue.al()

    def pending_event_count(self):
        return self._event_queue.bekleyen_sayi()

    def has_pending_events(self):
        return not self._event_queue.bos_mu()

    def list_events(self):
        return self._event_queue.listele()

    def clear_events(self):
        self._event_queue.temizle()

    # ========================================================
    # ENTITY
    # ========================================================

    def add_entity(self, entity):
        """
        Entity'yi World'e ekler.
        """

        return self._compat_add_entity(entity)

    def _compat_add_entity(self, entity):
        """1.x membership projection writer used by WorldMembershipService."""
        if not isinstance(entity, Entity):
            raise TypeError(
                "Yalnızca Entity nesneleri World içerisine eklenebilir."
            )

        if entity.entity_id in self._entities:
            raise ValueError(
                f"Bu Entity zaten World içerisinde kayıtlı: "
                f"{entity.entity_id}"
            )

        if entity.has_world():
            raise ValueError(
                "Entity zaten başka bir World'e bağlı."
            )

        entity.assign_world(self.world_id)
        self._entities[entity.entity_id] = entity

    def _compat_attach_entity(self, entity):
        """Synchronize the legacy projection from canonical membership state."""
        if not isinstance(entity, Entity):
            raise TypeError("Yalnızca Entity nesneleri World içerisine eklenebilir.")
        projected = self._entities.get(entity.entity_id)
        if projected is not None and projected is not entity:
            raise ValueError("World membership projection is inconsistent.")
        if projected is None:
            if entity.has_world():
                entity.remove_from_world()
            entity.assign_world(self.world_id)
            self._entities[entity.entity_id] = entity

    def remove_entity(self, entity_id):
        """
        Entity'yi World'den çıkarır.
        """

        return self._compat_remove_entity(entity_id)

    def _compat_remove_entity(self, entity_id):
        """1.x membership projection removal used by the application boundary."""
        if entity_id not in self._entities:
            raise KeyError(
                f"Entity World içerisinde bulunamadı: {entity_id}"
            )

        entity = self._entities.pop(entity_id)
        entity.remove_from_world()

        return entity

    def _compat_detach_entity(self, entity):
        """Remove a projection without making it an ownership decision."""
        projected = self._entities.pop(entity.entity_id, None)
        if projected is not None and projected is not entity:
            self._entities[entity.entity_id] = projected
            raise RuntimeError("World membership projection is inconsistent.")
        if entity.world_id == self.world_id:
            entity.remove_from_world()

    def get_entity(self, entity_id):
        return self._entities.get(entity_id)

    def has_entity(self, entity_id):
        return entity_id in self._entities

    def get_entities(self):
        return list(self._entities.values())

    def entity_count(self):
        return len(self._entities)

    def get_entities_by_type(self, entity_type):
        return [
            entity
            for entity in self._entities.values()
            if entity.entity_type == entity_type
        ]

    def get_entities_by_position(self, position):
        return [
            entity
            for entity in self._entities.values()
            if entity.position.x == position.x and entity.position.y == position.y
        ]

    def clear_entities(self):
        entities = list(self._entities.values())

        for entity in entities:
            entity.remove_from_world()

        self._entities.clear()

    # ========================================================
    # INFO
    # ========================================================

    def get_info(self):
        return {
            "id": self.world_id,
            "ad": self.name,
            "genislik": self.width,
            "yukseklik": self.height,
            "entity_sayisi": self.entity_count(),
            "total_ticks": self.total_ticks,
            "bekleyen_olay_sayisi": self.pending_event_count(),
            "zamanlanmis_olay_sayisi": self.scheduled_event_count,
        }
