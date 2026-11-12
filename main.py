"""RPG Kaynak Yönetimi için çalıştırılabilir uygulama giriş noktası."""

import sys
from pathlib import Path

from application import GameApplication
from application.runtime_logging import configure_logging
from time_system import random_start_tick


APP_VERSION = "3.0.0rc1"


def oyun_olustur(world_name="Başlangıç Dünyası", width=None, height=None):
    """Varsayılan dünyası oluşturulmuş ve başlatılmış bir oyun döndürür."""

    game = GameApplication.create_default(start_tick=random_start_tick())
    game.dunya_olustur(world_name, width=width, height=height)
    game.baslat()
    return game


def main():
    logger = configure_logging()
    if "--version" in sys.argv:
        print(APP_VERSION)
        return
    content_package_path = None
    if "--content-package" in sys.argv:
        index = sys.argv.index("--content-package")
        if index + 1 >= len(sys.argv):
            raise SystemExit("--content-package için bir paket dizini belirtin.")
        content_package_path = Path(sys.argv[index + 1])
    if "--play" not in sys.argv:
        game = oyun_olustur()
        print(game.bilgi())
        return
    game = oyun_olustur("Başlangıç Vadisi", width=24, height=16)
    from game_ui.starter import create_opening_service
    from game_ui.game_window import launch
    from game_ui import load_backend
    try:
        pygame = load_backend()
    except RuntimeError as error:
        raise SystemExit("Oynatmak için pygame-ce kurulmalı: pip install pygame-ce") from error
    try:
        launch(create_opening_service(game, content_package_path), pygame)
    except Exception as error:
        logger.exception("Interactive game session failed")
        raise SystemExit(f"Oyun başlatılamadı. Ayrıntılar logs/eldoria.log dosyasına yazıldı: {error}") from error


if __name__ == "__main__":
    main()
