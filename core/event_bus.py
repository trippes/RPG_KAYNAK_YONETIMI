"""
RPG Kaynak Yönetimi
Çekirdek 1.6 - Olay Veri Yolu

Olayların ilgili işleyicilere dağıtılmasını ve olay kuyruğunun
işlenmesini sağlar.
"""

from core.events import Event, EventQueue
from core.event_handler import EventHandler
from core.compatibility.usage import record_usage


class EventBus:
    """Olayların abonelere dağıtılmasını yöneten merkezi sistemdir."""

    def __init__(self):
        record_usage("core.event_bus.EventBus")
        self._handlerlar = {}

    def subscribe(self, handler):
        """Bir olay işleyicisini sisteme abone eder."""

        if not isinstance(handler, EventHandler):
            raise TypeError(
                "Yalnızca EventHandler nesneleri abone edilebilir."
            )

        if handler.event_type not in self._handlerlar:
            self._handlerlar[handler.event_type] = []

        if handler not in self._handlerlar[handler.event_type]:
            self._handlerlar[handler.event_type].append(handler)

    def unsubscribe(self, handler):
        """Bir olay işleyicisinin aboneliğini kaldırır."""

        if not isinstance(handler, EventHandler):
            raise TypeError(
                "Yalnızca EventHandler nesnelerinin aboneliği kaldırılabilir."
            )

        handlerlar = self._handlerlar.get(
            handler.event_type,
            []
        )

        if handler in handlerlar:
            handlerlar.remove(handler)

        if not handlerlar and handler.event_type in self._handlerlar:
            del self._handlerlar[handler.event_type]

    def publish(self, event):
        """Bir olayı ilgili tüm işleyicilere dağıtır."""

        if not isinstance(event, Event):
            raise TypeError(
                "Yalnızca Event nesneleri yayınlanabilir."
            )

        handlerlar = list(
            self._handlerlar.get(
                event.tur,
                []
            )
        )

        islenen_sayi = 0

        for handler in handlerlar:
            if handler.handle(event):
                islenen_sayi += 1

        return islenen_sayi

    def dispatch_queue(self, queue):
        """
        Olay kuyruğundaki tüm olayları sırayla işler.

        şlenen olay sayısını ve çağrılan handler sayısını döndürür.
        """

        if not isinstance(queue, EventQueue):
            raise TypeError(
                "Yalnızca EventQueue nesneleri işlenebilir."
            )

        islenen_olay_sayisi = 0
        islenen_handler_sayisi = 0

        while not queue.bos_mu():
            event = queue.al()

            if event is None:
                break

            islenen_handler_sayisi += self.publish(
                event
            )

            islenen_olay_sayisi += 1

        return (
            islenen_olay_sayisi,
            islenen_handler_sayisi
        )

    def handler_sayisi(self, event_type=None):
        """Kayıtlı işleyici sayısını döndürür."""

        if event_type is not None:
            return len(
                self._handlerlar.get(
                    event_type,
                    []
                )
            )

        return sum(
            len(handlerlar)
            for handlerlar in self._handlerlar.values()
        )

    def temizle(self):
        """Tüm abonelikleri kaldırır."""

        self._handlerlar.clear()
