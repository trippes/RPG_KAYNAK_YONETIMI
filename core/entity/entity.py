from datetime import datetime

from core.entity.entity_id import EntityIDGenerator
from core.entity.entity_state import EntityState
from core.entity.entity_type import EntityType
from core.entity.position import Position


class Entity:
    """
    Oyundaki tüm varlıkların temel sınıfı.
    """

    _id_generator = EntityIDGenerator()

    def __init__(
        self,
        entity_type,
        name,
        entity_id=None,
        position=None
    ):
        if not EntityType.is_valid(entity_type):
            raise ValueError(
                f"Geçersiz Entity türü: {entity_type}"
            )

        if entity_id is None:
            entity_id = self._id_generator.generate()

        if position is None:
            position = Position()

        if not isinstance(position, Position):
            raise TypeError(
                "position bir Position nesnesi olmalıdır."
            )

        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name

        self.created_at = datetime.now()
        self.state = EntityState()
        self.position = position

        # Çekirdek 1.7.2:
        # Entity'nin bağlı olduğu World.
        # Başlangıçta Entity herhangi bir World'e bağlı değildir.
        self._world_id = None

    # ========================================================
    # WORLD LŞKS
    # ========================================================

    @property
    def world_id(self):
        """
        Entity'nin bağlı olduğu World ID'sini döndürür.
        """
        return self._world_id

    def has_world(self):
        """
        Entity'nin bir World'e bağlı olup olmadığını döndürür.
        """
        return self._world_id is not None

    def assign_world(self, world_id):
        """
        Entity'yi bir World'e bağlar.

        Entity zaten bir World'e bağlıysa tekrar bağlanamaz.
        """

        if not isinstance(world_id, str):
            raise TypeError(
                "world_id metin olmalıdır."
            )

        if not world_id.strip():
            raise ValueError(
                "world_id boş olamaz."
            )

        if self._world_id is not None:
            raise ValueError(
                "Entity zaten bir World'e bağlı."
            )

        self._world_id = world_id

    def remove_from_world(self):
        """
        Entity'nin World bağlantısını kaldırır.
        """

        self._world_id = None

    # ========================================================
    # DURUM
    # ========================================================

    def activate(self):
        """Entity'yi aktif hale getirir."""
        self.state.activate()

    def deactivate(self):
        """Entity'yi pasif hale getirir."""
        self.state.deactivate()

    def kill(self):
        """Entity'yi ölü hale getirir."""
        self.state.kill()

    def revive(self):
        """Entity'yi tekrar canlı ve aktif hale getirir."""
        self.state.revive()

    def is_active(self):
        """Entity'nin aktif olup olmadığını döndürür."""
        return self.state.is_active()

    def is_alive(self):
        """Entity'nin canlı olup olmadığını döndürür."""
        return self.state.is_alive()

    def get_status(self):
        """Entity'nin mevcut durumunu döndürür."""
        return self.state.get_status()

    def get_state(self):
        """Entity'nin mevcut durum bilgisini döndürür."""
        return self.state.get_state()

    def get_history(self):
        """Entity'nin durum geçmişini döndürür."""
        return self.state.get_history()

    def get_previous_status(self):
        """Entity'nin önceki durumunu döndürür."""
        return self.state.get_previous_status()

    def get_history_length(self):
        """Entity durum geçmişindeki kayıt sayısını döndürür."""
        return self.state.get_history_length()

    def has_status(self, status):
        """Entity'nin geçmişinde belirtilen durumun olup olmadığını döndürür."""
        return self.state.has_status(status)

    # ========================================================
    # BLG
    # ========================================================

    def get_info(self):
        """Entity'nin temel bilgilerini döndürür."""
        return {
            "id": self.entity_id,
            "tur": self.entity_type,
            "ad": self.name,
            "olusturma_zamani": self.created_at,
            "durum": self.state.get_state(),
            "konum": self.position.to_dict(),
            "world_id": self.world_id,
        }
