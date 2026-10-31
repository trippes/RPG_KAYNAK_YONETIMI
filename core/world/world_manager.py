from typing import Optional

from core.foundation import WorldId
from core.world.world import World


class WorldManager:
    """
    Birden fazla World nesnesini merkezi olarak yöneten sınıf.

    Aynı anda yalnızca bir World aktif olabilir.

    World oluşturma, kayıt, silme ve aktif World seçiminin
    yanında aktif World'ün zaman yönetimini de sağlar.
    """

    def __init__(self):
        self._worlds = {}
        self._active_world_id = None

    # ========================================================
    # WORLD YÖNETM
    # ========================================================

    @staticmethod
    def _world_id_value(world_id):
        """Normalize canonical and compatibility lookup identities at the boundary."""
        if isinstance(world_id, WorldId):
            return world_id.value
        if isinstance(world_id, str) and world_id.strip():
            return world_id
        raise TypeError("world_id must be a WorldId or non-empty string.")

    def add(self, world):
        """
        World nesnesini yönetime ekler.
        """

        if not isinstance(world, World):
            raise TypeError(
                "Yalnızca World nesneleri yönetime eklenebilir."
            )

        world_id = self._world_id_value(world.world_id)
        if world_id in self._worlds:
            raise ValueError(
                f"Bu World ID zaten kayıtlı: {world_id}"
            )

        self._worlds[world_id] = world

    def create(
        self,
        name,
        width=None,
        height=None,
        world_id=None,
    ):
        """
        Yeni World oluşturur, yönetime ekler ve döndürür.

        Yeni oluşturulan World otomatik olarak aktif yapılmaz.
        """

        world = World(
            name=name,
            width=width,
            height=height,
            world_id=world_id,
        )

        self.add(world)

        return world

    def remove(self, world_id):
        """
        World nesnesini yönetimden çıkarır.

        Silinen World aktif World ise aktif World temizlenir.
        """

        world_id = self._world_id_value(world_id)
        if world_id not in self._worlds:
            raise KeyError(
                f"World bulunamadı: {world_id}"
            )

        world = self._worlds.pop(world_id)

        if self._active_world_id == world_id:
            self._active_world_id = None

        return world

    def get(self, world_id) -> Optional[World]:
        """
        ID üzerinden World getirir.
        """

        return self._worlds.get(self._world_id_value(world_id))

    def exists(self, world_id):
        """
        World ID'sinin kayıtlı olup olmadığını kontrol eder.
        """

        return self._world_id_value(world_id) in self._worlds

    def get_all(self):
        """
        Yönetilen tüm World nesnelerini liste olarak döndürür.
        """

        return [
            self._worlds[world_id]
            for world_id in sorted(self._worlds)
        ]

    def count(self):
        """
        Yönetilen World sayısını döndürür.
        """

        return len(self._worlds)

    # ========================================================
    # AKTF WORLD
    # ========================================================

    def set_active(self, world_id):
        """
        Belirtilen World'ü aktif World yapar.
        """

        world_id = self._world_id_value(world_id)
        if world_id not in self._worlds:
            raise KeyError(
                f"Aktif yapılmak istenen World bulunamadı: {world_id}"
            )

        self._active_world_id = world_id

    def get_active(self) -> Optional[World]:
        """
        Aktif World'ü döndürür.

        Aktif World yoksa None döndürür.
        """

        if self._active_world_id is None:
            return None

        return self._worlds.get(
            self._active_world_id
        )

    def has_active(self):
        """
        Aktif bir World olup olmadığını kontrol eder.
        """

        return self._active_world_id is not None

    def get_active_id(self):
        """
        Aktif World ID'sini döndürür.

        Aktif World yoksa None döndürür.
        """

        return self._active_world_id

    def clear_active(self):
        """
        Aktif World seçimini kaldırır.

        World nesnesi silinmez.
        """

        self._active_world_id = None

    def switch(self, world_id):
        """
        Aktif World'ü değiştirir.
        """

        self.set_active(world_id)

    # ========================================================
    # AKTF WORLD ZAMAN YÖNETM
    # ========================================================

    def _require_active_world(self):
        """
        Aktif World yoksa hata verir.

        Manager'ın aktif World gerektiren işlemleri
        için merkezi doğrulama noktasıdır.
        """

        world = self.get_active()

        if world is None:
            raise RuntimeError(
                "Aktif World bulunmamaktadır."
            )

        return world

    def advance_active(self, ticks):
        """
        Aktif World'ün zamanını tick cinsinden ilerletir.
        """

        world = self._require_active_world()

        return world.advance(ticks)

    def advance_active_seconds(self, seconds):
        """
        Aktif World'ün zamanını saniye cinsinden ilerletir.
        """

        world = self._require_active_world()

        return world.advance_seconds(seconds)

    def advance_active_minutes(self, minutes):
        """
        Aktif World'ün zamanını dakika cinsinden ilerletir.
        """

        world = self._require_active_world()

        return world.advance_minutes(minutes)

    def advance_active_hours(self, hours):
        """
        Aktif World'ün zamanını saat cinsinden ilerletir.
        """

        world = self._require_active_world()

        return world.advance_hours(hours)

    def advance_active_days(self, days):
        """
        Aktif World'ün zamanını gün cinsinden ilerletir.
        """

        world = self._require_active_world()

        return world.advance_days(days)

    def pause_active(self):
        """
        Aktif World'ün zamanını durdurur.
        """

        world = self._require_active_world()

        world.pause()

    def resume_active(self):
        """
        Aktif World'ün zamanını yeniden başlatır.
        """

        world = self._require_active_world()

        world.resume()

    def get_active_time(self):
        """
        Aktif World'ün GameTime nesnesini döndürür.
        """

        world = self._require_active_world()

        return world.time

    def get_active_ticks(self):
        """
        Aktif World'ün toplam tick değerini döndürür.
        """

        world = self._require_active_world()

        return world.total_ticks

    def is_active_running(self):
        """
        Aktif World'ün zaman motorunun çalışıp çalışmadığını
        döndürür.
        """

        world = self._require_active_world()

        return world.running

    # ========================================================
    # SORGULAR
    # ========================================================

    def get_by_name(self, name):
        """
        Belirli ada sahip World nesnelerini döndürür.
        """

        return [
            world
            for world in self.get_all()
            if world.name == name
        ]

    def clear(self):
        """
        Tüm World kayıtlarını temizler.

        Aktif World seçimi de temizlenir.
        """

        self._worlds.clear()
        self._active_world_id = None
