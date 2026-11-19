"""Temporary mapless gameplay surface while the replacement hex world is integrated."""


class MainScreen:
    """Keep the gameplay window shell alive without the retired square-map runtime."""

    def __init__(self, service):
        self.service = service
        self.message = "Yeni dünya haritası hazırlanıyor."

    def update(self, _elapsed_seconds=0.0):
        return None

    def handle(self, _state):
        return None

    def render(self, renderer):
        panel = renderer.pg.Rect(
            24, 96, max(1, renderer.width - 48), max(1, renderer.height - 120)
        )
        renderer.panel(panel, (19, 26, 38), (62, 78, 101))
        renderer.text("ELDORIA", 48, 140)
        renderer.text(self.message, 48, 196)
        renderer.text(
            "Eski kare harita sistemi devreden çıkarıldı. Yeni altıgen dünya "
            "entegrasyonundan sonra oyun alanı yeniden açılacak.",
            48, 236,
        )
