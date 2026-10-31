"""
RPG Kaynak Yönetimi
Çekirdek 1.6 - Olay şleyici

Olaylara karşılık çalıştırılacak işleyici yapısını tanımlar.
"""


from core.events import Event


class EventHandler:
    """Bir olay için çalıştırılabilecek işleyiciyi temsil eder."""

    def __init__(self, event_type, callback):
        if not isinstance(event_type, str):
            raise TypeError(
                "Olay türü metin olmalıdır."
            )

        if not event_type.strip():
            raise ValueError(
                "Olay türü boş olamaz."
            )

        if not callable(callback):
            raise TypeError(
                "şleyici çağrılabilir olmalıdır."
            )

        self.event_type = event_type
        self.callback = callback

    def handle(self, event):
        """Verilen olayı işleyiciye gönderir."""

        if not isinstance(event, Event):
            raise TypeError(
                "Yalnızca Event nesneleri işlenebilir."
            )

        if event.tur != self.event_type:
            return False

        self.callback(event)

        return True

    def __repr__(self):
        return (
            f"EventHandler("
            f"event_type={self.event_type!r}, "
            f"callback={self.callback!r}"
            f")"
        )
