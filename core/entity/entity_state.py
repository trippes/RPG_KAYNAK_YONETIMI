class EntityState:
    """
    Entity'nin yaşam ve durum bilgisini yöneten sınıf.
    """

    DURUM_AKTIF = "aktif"
    DURUM_PASIF = "pasif"
    DURUM_OLU = "olu"

    GECERLI_DURUMLAR = {
        DURUM_AKTIF,
        DURUM_PASIF,
        DURUM_OLU,
    }

    def __init__(self):
        self.status = self.DURUM_AKTIF
        self.alive = True

        self.history = [
            self.DURUM_AKTIF
        ]

    def set_status(self, status):
        """
        Entity'nin durumunu değiştirir.

        Geçersiz durumlar kabul edilmez.
        Ölü Entity doğrudan aktif veya pasif yapılamaz.
        """

        if status not in self.GECERLI_DURUMLAR:
            raise ValueError(
                f"Geçersiz Entity durumu: {status}"
            )

        if self.status == self.DURUM_OLU:
            if status != self.DURUM_OLU:
                raise ValueError(
                    "Ölü Entity doğrudan aktif veya pasif yapılamaz."
                )

        if status == self.status:
            return

        self.status = status

        if status == self.DURUM_OLU:
            self.alive = False

        elif status in (
            self.DURUM_AKTIF,
            self.DURUM_PASIF,
        ):
            self.alive = True

        self.history.append(status)

    def get_status(self):
        """Entity'nin mevcut durumunu döndürür."""
        return self.status

    def activate(self):
        """Entity'yi aktif hale getirir."""

        if self.status == self.DURUM_OLU:
            raise ValueError(
                "Ölü Entity doğrudan aktif hale getirilemez."
            )

        self.set_status(self.DURUM_AKTIF)

    def deactivate(self):
        """Entity'yi pasif hale getirir."""

        if self.status == self.DURUM_OLU:
            raise ValueError(
                "Ölü Entity doğrudan pasif hale getirilemez."
            )

        self.set_status(self.DURUM_PASIF)

    def kill(self):
        """Entity'yi ölü durumuna geçirir."""
        self.set_status(self.DURUM_OLU)

    def revive(self):
        """Ölü Entity'yi tekrar canlı ve aktif hale getirir."""

        if self.status != self.DURUM_OLU:
            raise ValueError(
                "Canlı Entity diriltilemez."
            )

        self.status = self.DURUM_AKTIF
        self.alive = True

        self.history.append(
            self.DURUM_AKTIF
        )

    def is_active(self):
        """Entity'nin aktif olup olmadığını döndürür."""
        return self.status == self.DURUM_AKTIF

    def is_alive(self):
        """Entity'nin canlı olup olmadığını döndürür."""
        return self.alive

    def get_state(self):
        """Entity'nin mevcut durumunu döndürür."""
        return {
            "durum": self.status,
            "canli": self.alive,
        }

    def get_history(self):
        """Entity'nin durum geçmişinin kopyasını döndürür."""
        return list(self.history)

    def get_previous_status(self):
        """
        Entity'nin mevcut durumundan önceki durumunu döndürür.

        Yalnızca başlangıç durumu varsa None döndürür.
        """

        if len(self.history) < 2:
            return None

        return self.history[-2]

    def get_history_length(self):
        """Entity'nin durum geçmişindeki kayıt sayısını döndürür."""
        return len(self.history)

    def has_status(self, status):
        """
        Entity'nin geçmişinde belirtilen durumun bulunup
        bulunmadığını döndürür.
        """

        if status not in self.GECERLI_DURUMLAR:
            raise ValueError(
                f"Geçersiz Entity durumu: {status}"
            )

        return status in self.history