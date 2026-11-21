# Eldoria — Aşama 3.4 Waypoint Takibi ve Güvenli Smoothing Kapanış Raporu

- **Dal:** `experiment/map-cleanup`
- **Önceki route-cache commit'i:** `10e4d20634e14fc80a2f786015d2700e6c0be0ef`
- **Uygulama commit'i:** `62bc84b7ad41ba5ec0e4492f0591018990e66e60`
- **Tarih:** 21 Kasım 2026
- **Durum:** Tamamlandı

---

## 1. Uygulama

Aşama 3.3'te eklenen route cursor ve immutable waypoint dizisi üzerine, yalnızca güvenliği kanıtlanabilen tek ara waypoint'lik collinear smoothing eklendi.

`ClickMoveRouteController._smoothed_waypoint()` şu koşulların tamamı sağlanırsa `cursor + 2` hücresini hedef olarak seçer:

1. Mevcut → sonraki ve sonraki → aday hücre axial farkları aynı olmalı. Böylece dönüş/köşe waypoint'i atlanmaz.
2. İkinci edge güncel map mask kontrolünden geçmeli.
3. İkinci edge güncel occupancy kontrolünden geçmeli (profil occupancy ignore etmiyorsa).
4. Her iki statik edge, A* route planı sırasında aynı immutable `HexPhysicsSnapshot.can_reach_cell()` edge validator'ıyla doğrulanmış olmalı.
5. Mevcut continuous runtime konumundan aday waypoint'e `HexPhysicsSnapshot.resolve_motion()` ile swept collision ön kontrolü yapılmalı.

Swept-clearance kanıtı route cursor segmenti için cache'lenir. Oyuncu kanıtlanan doğrusal segment üzerinde kaldığı sürece aynı statik swept test tekrar çalıştırılmaz; oyuncu segmentten saparsa test yeniden yapılır. Mutable occupancy ise her fixed step'te kontrol edilir.

Herhangi bir API bulunmaz, exception oluşur veya güvenlik kontrolü başarısız olursa controller hemen sonraki waypoint'e geri döner. Smoothing bir ara waypoint'ten fazlasını atlamaz.

Gerçek hareket yine mevcut collision resolver ve `HexWorldRuntime.set_continuous_position()` hattından geçer. Ön kontrol yalnızca smoothing kararını verir; authoritative konum/occupancy commit'i yapmaz. A* planında statik edge validation, fixed-step sırasında mutable occupancy kontrolü ve route segmenti başına cached swept-clearance birlikte kullanılır.

## 2. Eklenen testler

`tests/test_application/test_click_move_route.py` dosyasına dört yeni regresyon testi eklendi:

- `test_collinear_waypoint_is_merged_after_clear_swept_collision_check`
- `test_smoothing_falls_back_to_next_waypoint_when_sweep_hits_collision`
- `test_smoothing_never_merges_a_turning_waypoint`
- `test_smoothing_checks_dynamic_occupancy_of_second_edge`

Böylece doğrusal rotada bir waypoint azaltılırken dönüş noktalarının, dinamik occupancy engellerinin ve swept collision güvenliğinin korunduğu kanıtlandı.

## 3. Doğrulama

Uygulama commit'i `62bc84b7ad41ba5ec0e4492f0591018990e66e60` için:

| Kontrol | Sonuç |
|---|---|
| Pytest — Ubuntu Python 3.11 | **2.466 passed** |
| Pytest — Ubuntu Python 3.12 | **2.466 passed** |
| Pytest — Windows Python 3.11 | **2.466 passed** |
| Pytest — Windows Python 3.12 | **2.466 passed** |
| Ruff — Core Quality kapsamı | Başarılı |
| Core Quality — Linux verify | Başarılı |
| Core Quality — Windows verify | Başarılı |
| Pygame headless smoke | Başarılı |
| Aşama 2 NPC spatial benchmark | Başarılı |

- **Eldoria CI run:** `44881564513`
- **Core Quality run:** `44881564488`
- **NPC spatial benchmark run:** `44881564546`

NPC benchmark'ın başarılı olması Aşama 2 optimizasyonlarının bu değişikliklerle bozulmadığına dair ek doğrulamadır. Oyuncu click-to-move metrikleri NPC benchmark sonuçlarına dahil edilmemiştir.

## 4. Sonuç ve sınırlar

**Aşama 3.4 tamamlandı.** Waypoint cursor takibi, collinear ara waypoint birleştirmesi, dönüş noktalarını koruma, güncel occupancy doğrulaması ve swept static collision ön kontrolü uygulandı.

Bu smoothing bilinçli olarak sınırlıdır. Genel line-of-sight smoothing, çoklu waypoint atlama veya köşeleri kesen optimizasyon uygulanmadı.

Aşama 3.5'te hedefe yaklaşma/durma davranışı ayrıca değerlendirilecektir. Mevcut `MovementIntegrator` hızlanma/frenleme sağlamadığı için bu aşama, gerçek durma hassasiyetinin mevcut fizik bağımlılığıyla kanıtlanıp kanıtlanamayacağını belirlemelidir.
