# Eldoria — Aşama 3.2 Birleşik Hareket Girdisi ve Komut Önceliği Raporu

- **Dal:** `experiment/map-cleanup`
- **Uygulama tabanı:** `f53d699b34c592c4a51d13342bb286f7e9525d5f`
- **Uygulama commit'i:** `51fe2f486e79c043cfa51061ec34a7e7e9af5270`
- **Test düzeltme commit'i:** `2c1d5fba724e7fae6caa7e0735618c4f3fc98938`
- **Tarih:** 21 Kasım 2026
- **Durum:** Tamamlandı

---

## 1. Amaç

Klavye ve fare hareketi tek `MovementIntent`/fixed-step/fizik hattında kalırken, aktif fare rotasının hareket modu klavye adapter'ının o anki moduyla eşleştirildi. Mevcut input önceliği ve focus/pause davranışı kaynak kodu ve hedefli testlerle karakterize edildi.

## 2. Yapılan değişiklikler

### `game_ui/game_window.py`

`_advance_continuous_player_movement()` içinde click-to-move intent'i alınırken yalnızca fare yön vektörü kullanılır; `MovementMode` canlı `PygameMovementInput` intent'inden aktarılır:

- Fare rota yönünü üretir.
- Klavye adapter'ı NORMAL/RUNNING/STEALTH modunun sahibi olmaya devam eder.
- Shift/Alt mod değişikliği bir sonraki fixed step'te fare hareketine de uygulanır.
- Fare hareketi kendi başına koşma veya gizlilik modu açmaz.
- Ortak `ContinuousPlayerMovementController`, integrator, statik collision, dinamik aktör çarpışması ve runtime commit hattı değişmedi.

### Mevcut öncelik ve iptal davranışı

- GameWindow manuel klavye intent'ini fare rotasından önce seçer; manuel hareket aktifse click-to-move iptal edilir.
- `HexGameplayView.handle()` aynı input state'inde altı yönlü manuel eylem gördüğünde mouse-click hedefi işleme dalına girmez ve eski fare hedefini temizler.
- NPC/nesne tıklamaları etkileşim/inceleme akışında kalır; yürüyüş hedefi üretmez.
- Sağ tık mevcut click-to-move hedefini temizler.
- Focus kaybı klavye intent'ini sıfırlar. Mevcut ürün davranışı olarak aktif fare komutu devam eder; bu davranış korunmuştur.
- Pause/resume mevcut fare hedefini korur; pause menüsünde fizik yürütmesi yapılmaz.

## 3. Eklenen ve güncellenen testler

| Dosya | Test | Kanıt |
|---|---|---|
| `tests/test_game_ui/test_game_window_rendering.py` | `test_click_to_move_preserves_current_movement_mode` | Fare yönü korunurken STEALTH modu ortak controller'a aktarılır |
| `tests/test_game_ui/test_game_window_rendering.py` | `test_click_to_move_continues_when_keyboard_focus_is_lost` | Klavye odağı kaybolsa da click-to-move fixed-step yürütmesi sürer |
| `tests/test_game_ui/test_hex_gameplay_view.py` | `test_manual_keyboard_action_cancels_click_goal_and_ignores_same_frame_click` | Manuel yön eylemi eski rotayı iptal eder; aynı frame'deki yeni mouse click yürüyüş komutu olmaz |

Önceki `test_click_to_move_uses_shared_fixed_step_controller_intent` testi, intent nesnesinin kimliğini (`is`) karşılaştırıyordu. Yeni sözleşmede yön ve mod aynı değerde yeni bir `MovementIntent` oluşturduğundan test, nesne değer eşitliğini doğrulayacak şekilde güncellendi. Bu düzeltme uygulama davranışını değiştirmedi.

## 4. Doğrulama

İlk uygulama commit'i `51fe2f4` üzerinde CI, eski testteki nesne kimliği beklentisi nedeniyle başarısız oldu: 2.447 test başarılı, 1 test başarısızdı. Hata test beklentisindeydi. `2c1d5fb` commit'inde test değer eşitliğine çevrildi ve kontroller yeniden çalıştırıldı.

Düzeltilmiş commit `2c1d5fba724e7fae6caa7e0735618c4f3fc98938` için:

| Kontrol | Sonuç |
|---|---|
| Core Quality — Linux verify | Başarılı |
| Core Quality — Windows verify | Başarılı |
| Ruff (Core Quality workflow kapsamı) | Başarılı |
| Eldoria CI — Ubuntu Python 3.11 | Başarılı |
| Eldoria CI — Ubuntu Python 3.12 | Başarılı |
| Eldoria CI — Windows Python 3.11 | Başarılı |
| Eldoria CI — Windows Python 3.12 | Başarılı |
| Pygame headless smoke | Başarılı |
| Eldoria CI Ruff adımı | Başarılı |

- **Core Quality run:** `44880375176`
- **Eldoria CI run:** `44880375186`

## 5. Kapsam koruması

Bu alt aşamada:
- NPC kaçınma/devriye/yoldaş kodu değiştirilmedi.
- NPC orkestrasyon sırası değiştirilmedi.
- Spatial index veya occupancy algoritması değiştirilmedi.
- 60 Hz fixed-step sözleşmesi ve catch-up davranışı değiştirilmedi.
- Collision resolver devre dışı bırakılmadı.
- Fare rota cache'i henüz eklenmedi; bu Aşama 3.3 kapsamıdır.

## 6. Sonuç ve sonraki alt aşamaya devir

**Aşama 3.2 tamamlandı.** Klavye önceliği, focus kaybı davranışı ve fare hareketinde Shift/Alt modlarının uygulanması testlerle doğrulandı. Klavye ve fare aynı ortak fizik hattını kullanmaya devam ediyor.

Sonraki alt aşama 3.3, yalnızca oyuncunun tek aktif click-to-move komutuna ait rota/cursor yaşam döngüsünü ele almalıdır. Aynı hedef için fixed step başına A* tekrarını kaldırırken runtime, map, actor, physics snapshot ve güncel occupancy güvenliği korunmalıdır.
