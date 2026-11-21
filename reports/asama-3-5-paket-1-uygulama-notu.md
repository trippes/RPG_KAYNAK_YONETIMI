# Eldoria RPG — Aşama 3.5 Paket 1 Uygulama ve Test Raporu

**Çalışma dalı:** `experiment/map-cleanup`  
**Mimari referans:** `reports/asama-3-5-serbest-hareket-teknik-mimari-plani.md`  
**Doğrulanan commit:** `5baaa59f54798c0a46699c4a12017c5239a12f3a`  
**Durum:** Uygulama ve CI doğrulaması başarılı.

## 1. Uygulanan kapsam

### Domain hareket modeli
- `MovementConfig` alanlarına `acceleration`, `deceleration` ve `braking_deceleration` eklendi.
- Yeni parametreler sonlu, negatif olmayan ve bool olmayan sayısal değerlerle doğrulanıyor.
- Yeni movement test profilleri için başlangıç tuning değerleri: 180, 240 ve 360 world units/s².
- `MovementTarget` immutable value object olarak eklendi; fiziksel hedef konumunu ve varış toleransını taşır.
- `MovementIntegrator` önceki velocity değerinden ivmelenme, input bırakıldığında yavaşlama ve hedefe yaklaşırken frenleme hesaplar.
- Hedefe yönelik displacement, varış toleransını aşmayacak şekilde sınırlandırılır.
- Domain katmanına Pygame, clock, route controller veya HexWorldRuntime bağımlılığı eklenmedi.

### Controller ve rota entegrasyonu
- `ContinuousPlayerMovementController` kabul edilmiş velocity değerini sonraki fixed step'e taşır.
- Runtime konumu dışarıdan değişmişse önceki velocity devam ettirilmez.
- Başarısız runtime commit sonrasında proposal velocity kabul edilmiş state'e yazılmaz.
- NPC push ve rollback akışı korunmuştur.
- `GameWindow` controller'ı render karesi başına yeniden oluşturmaz; hareket oturumu boyunca korur. Binding, snapshot, body, actor veya config değişince controller yenilenir.
- Click route fiziksel waypoint bilgisini `MovementTarget` olarak aktarır.
- Rota cursor ilerlemesi hex hücre sınırının yanında fiziksel waypoint varışını da dikkate alır.
- Smoothed waypoint ve dönüş noktaları frenleme hedefi olarak korunur.
- Nihai varış adımında hedef metadata'sı tek seferlik tüketilir.

### Fixed-step ve telemetri
- Hareket simülasyonu 60 Hz fixed-step modelini kullanır.
- Kare başına en fazla 8 substep çalıştırılır.
- Fazla tam adımlar atılır, kesirli kalan süre korunur.
- Atılan süre, toplam kayıp süre ve son karedeki substep sayısı izlenebilir.
- Click route metrikleri opt-in performans sayaçlarına bağlanmıştır.

### İçerik
- Gameplay rules doğrulaması ve movement config loader yeni parametreleri destekler.
- `content/movement_test/gameplay_rules.json` hareket profilleri açık tuning değerleriyle güncellendi.
- Demo içerik paketine gereksiz hareket profili eklenmedi.

## 2. Değiştirilen dosyalar

- `core/domain/movement/config.py`
- `core/domain/movement/target.py` (yeni)
- `core/domain/movement/integrator.py`
- `core/domain/movement/__init__.py`
- `application/content_pack.py`
- `application/continuous_player_movement.py`
- `application/click_move_route.py`
- `application/gameplay_step_clock.py`
- `game_ui/game_window.py`
- `game_ui/screens/main_screen.py`
- `game_ui/world_rendering/hex_gameplay_view.py`
- `content/movement_test/gameplay_rules.json`
- `tests/test_application/test_continuous_player_movement.py`
- `tests/test_application/test_click_move_route.py`
- `tests/test_application/test_content_pack.py`
- `tests/test_application/test_gameplay_step_clock.py`
- `tests/test_spatial/test_native_continuous_movement.py`
- `tests/test_game_ui/test_game_window_rendering.py`
- `tests/test_game_ui/test_hex_gameplay_view.py`

## 3. Test ve CI sonuçları

GitHub Actions üzerinde aynı doğrulanan commit için dört platform/sürüm kombinasyonunda testler çalıştırıldı:

| İşletim sistemi | Python | unittest | pytest | Ruff |
|---|---:|---:|---:|---:|
| Ubuntu | 3.11 | Başarılı | Başarılı | Başarılı |
| Ubuntu | 3.12 | Başarılı | Başarılı | Başarılı |
| Windows | 3.11 | Başarılı | Başarılı | Başarılı |
| Windows | 3.12 | Başarılı | Başarılı | Başarılı |

Her kombinasyonda:
- unittest: 1.473 test başarılı.
- pytest: 2.478 test başarılı, 264 subtest başarılı.
- Ruff: All checks passed.
- pytest çıktısında 59 uyarı raporlandı; bunlar mevcut pygame.image.tostring deprecation uyarılarıdır, test başarısızlığı değildir.

Ek doğrulamalar:
- Pygame headless initialization testi başarılı.
- Isometric world ve actor rendering smoke testi başarılı.
- Core quality release-candidate verification Linux ve Windows üzerinde başarılı.
- Legacy map cleanup boundary kontrolü başarılı.

**Eldoria CI:** https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44898414549  
**Core quality:** https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44898414571

## 4. Korunan mimari sınırlar

- `HexWorldRuntime` authoritative konum, occupancy ve spatial index sahibi olarak kaldı.
- Statik collision → dinamik actor collision/NPC push → runtime commit sırası değiştirilmedi.
- NPC push rollback mekanizması korundu.
- Eski kare harita veya legacy demo sistemi eklenmedi.
- Yeni harici dependency eklenmedi.
- Bütün uygulama ve test değişiklikleri yalnızca `experiment/map-cleanup` dalına işlendi.

## 5. Sonuç ve sonraki paket

Aşama 3.5 Paket 1 otomatik test ve kalite kontrollerinden geçti. Bu sonuç kod/test doğrulamasıdır; gerçek oyuncu hissi, farklı hızlarda frenleme, uzun rota takibi ve çarpışma altında görsel davranış için oyun içi manuel kabul testleri ayrıca yapılmalıdır.

**Sonraki teknik paket:** gerçek oyun oturumunda NORMAL/RUNNING/STEALTH geçişleri, klavye yön değiştirme, duvar kayması, NPC itişi ve click-to-move hedef frenlemesinin davranışsal doğrulaması; ölçüm sonuçlarına göre tuning.
