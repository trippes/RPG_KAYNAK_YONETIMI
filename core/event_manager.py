"""
RPG Kaynak Yönetimi
Çekirdek 1.6 - Olay Yöneticisi

Olay oluşturma, kuyruğa ekleme ve olay kuyruğunu
işletme işlemlerini merkezi olarak yönetir.
"""

from core.events import Event, EventQueue
from core.event_bus import EventBus


class EventManager:
    """Olay sisteminin oluşturma, kuyruğa alma ve dağıtım işlemlerini yönetir."""

    def __init__(self, event_bus=None, event_queue=None):
        if event_bus is not None and not isinstance(event_bus, EventBus):
            raise TypeError(
                "event_bus yalnızca EventBus nesnesi veya None olabilir."
            )

        if event_queue is not None and not isinstance(event_queue, EventQueue):
            raise TypeError(
                "event_queue yalnızca EventQueue nesnesi veya None olabilir."
            )

        self.event_bus = (
            event_bus
            if event_bus is not None
            else EventBus()
        )

        self.event_queue = (
            event_queue
            if event_queue is not None
            else EventQueue()
        )

    def olustur(self, tur, veri=None):
        """Yeni bir Event oluşturur."""

        return Event(
            tur=tur,
            veri=veri
        )

    def ekle(self, tur, veri=None):
        """Yeni olay oluşturur ve kuyruğa ekler."""

        event = self.olustur(
            tur=tur,
            veri=veri
        )

        self.event_queue.ekle(
            event
        )

        return event

    def yayinla(self, event):
        """Bir Event'i doğrudan EventBus üzerinden yayınlar."""

        if not isinstance(event, Event):
            raise TypeError(
                "Yalnızca Event nesneleri yayınlanabilir."
            )

        return self.event_bus.publish(
            event
        )

    def islet(self):
        """Kuyrukta bekleyen tüm olayları işler."""

        return self.event_bus.dispatch_queue(
            self.event_queue
        )

    def bekleyen_sayi(self):
        """Kuyrukta bekleyen olay sayısını döndürür."""

        return self.event_queue.bekleyen_sayi()

    def temizle(self):
        """Bekleyen tüm olayları kuyruktan temizler."""

        self.event_queue.temizle()
