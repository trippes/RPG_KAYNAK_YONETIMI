"""RPG Kaynak Yönetimi için çalıştırılabilir uygulama giriş noktası."""

import sys

from application import GameApplication
from application.runtime_logging import configure_logging


APP_VERSION = "3.0.0rc1"


def oyun_olustur(world_name="Başlangıç Dünyası", width=None, height=None):
    """Varsayılan dünyası oluşturulmuş ve başlatılmış bir oyun döndürür."""

    game = GameApplication.create_default()
    game.dunya_olustur(world_name, width=width, height=height)
    game.baslat()
    return game


def main():
    logger = configure_logging()
    if "--version" in sys.argv:
        print(APP_VERSION)
        return
    if "--play" not in sys.argv:
        game = oyun_olustur()
        print(game.bilgi())
        return
    game = oyun_olustur("Başlangıç Vadisi", width=24, height=16)
    from pygame.demo import create_demo_service
    from pygame.game_window import launch
    from pygame import load_backend
    try:
        pygame = load_backend()
    except RuntimeError as error:
        raise SystemExit("Oynatmak için pygame kurulmalı: pip install pygame") from error
    try:
        launch(create_demo_service(game), pygame)
    except Exception as error:
        logger.exception("Interactive game session failed")
        raise SystemExit(f"Oyun başlatılamadı. Ayrıntılar logs/eldoria.log dosyasına yazıldı: {error}") from error


if __name__ == "__main__":
    main()
