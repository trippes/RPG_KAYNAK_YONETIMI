# Eldoria — Aşama 3.3 Aktif Click-to-Move Rota Cache Kapanış Raporu

- **Dal:** `experiment/map-cleanup`
- **Uygulama başlangıç commit'i:** `228da552728df2bcdff6d8d66595b8c919998994`
- **Rota cache ilk commit'i:** `d8625de5cda6920eff1a9039fc79758cc7f3092b`
- **Düzeltilmiş uygulama commit'i:** `cf574b029ea4ba57ce6f95e545430ede9130aabe`
- **Sabit fixed-step entegrasyon testi:** `2c5c36c2de40c758d58c9ba5e779b1fd331170ea`
- **Test fixture düzeltmesi:** `01e05abcc2f22e8811974d9ab54e1733b80b6156`
- **Tarih:** 21 Kasım 2026
- **Durum:** Tamamlandı

---

## 1. Amaç ve sonuç

Aynı aktif fare hedefi için her fixed physics step'te yeniden `HexWorldRuntime.path_to()` çağrılması kaldırıldı. Oyuncunun tek aktif click-to-move komutu artık route hücreleri ve cursor ile saklanıyor. Yeni rota yalnızca yeni komut veya doğrulanmış invalidation/replan durumunda hesaplanıyor.

**Ana kabul kanıtı:** Bir render karesinde dört fixed physics step çalıştırıldığında aynı fare hedefi için path query sayısı 1, cache hit sayısı 3 olarak doğrulandı.

## 2. Mimari değişiklikler

### Yeni modül: `application/click_move_route.py`

`ClickMoveRouteController` yalnızca tek oyuncunun aktif click-to-move rotasını yönetir. Genel amaçlı path cache veya NPC cache'i değildir.

Aktif route state:
- Runtime nesne kimliği
- Actor ID
- Map ID
- Hedef axial hücre
- Immutable physics snapshot kimliği
- Oyuncu body tanımı
- Immutable waypoint hücre dizisi
- Route cursor

Controller mutable entity view saklamaz. Oyuncu hücresi ve continuous position her çağrıda `HexWorldRuntime.entity()` üzerinden yeniden okunur. Continuous position varsa entity view içinden, test/uyumluluk adapter'larında yoksa runtime continuous-position API'sinden alınır.

### `game_ui/world_rendering/hex_gameplay_view.py`

- Click-to-move hedefi artık route controller'a devredilir.
- Aynı map ve aynı hedefe yeniden tıklama aktif rotayı korur.
- Yeni hedef eski rotayı iptal eder ve yeni komut başlatır.
- Manuel klavye hareketi, sağ tık ve NPC/nesne etkileşimi eski rotayı temizler.
- Route başarısız/blocked/arrived durumuna gelince view hedef state'ini temizler.
- Runtime veya physics map uyuşmazlığında komut güvenli biçimde sonlandırılır.

## 3. Cache ve invalidation sözleşmesi

### Cache hit

Aynı runtime, actor, map, hedef, physics snapshot ve body ile devam eden komutta route hücreleri yeniden kullanılır. Oyuncunun güncel runtime hücresi route suffix içinde bulunuyorsa cursor ileri taşınır. Bu sırada A* tekrar çalıştırılmaz.

### Cache miss / replan

Aşağıdaki durumlar mevcut rotayı geçersiz kılar ve kontrollü yeni path query üretir:

- Runtime nesnesinin değişmesi (save/load veya runtime replacement dahil)
- Actor ID veya map değişikliği
- Yeni hedef
- Physics snapshot veya player body değişikliği
- Oyuncunun authoritative runtime hücresinin kalan route suffix'inde bulunmaması
- Sonraki hücrenin güncel occupancy veya statik collision kontrolünden geçememesi

Yeni hedefte eski komut iptal edilir. Runtime/snapshot değişikliği, rota sapması veya edge invalidation ise mevcut komut için replan üretir.

### Dinamik ve statik güvenlik

Route planı oluşturulurken `runtime.path_to()` çağrısına immutable physics snapshot üzerinden `edge_validator` verilir; A* rotasındaki her edge statik collision kontrolünden geçer. Snapshot/body kimliği aktif route state'e bağlanır ve değiştiğinde rota invalid edilir.

Her fixed step'te:
1. Sıradaki hücrenin map mask içinde olduğu doğrulanır.
2. Oyuncu occupancy ignore etmiyorsa güncel occupancy üzerinden sıradaki hücreye giriş izni kontrol edilir.
3. Statik edge sonucu yeniden hesaplanmaz; aynı immutable snapshot ile path planında doğrulanmış sonuç kullanılır.

Bu ayrım statik collision güvenliğini korurken her fixed step'te aynı collision solver çağrılarının tekrarlanmasını önler. Collinear smoothing'in swept static collision kanıtı route cursor segmenti için bir kez hesaplanır ve oyuncu kanıtlanan segment üzerinde kaldığı sürece kullanılır. Oyuncu segmentten saparsa kanıt yeniden hesaplanır.

Gerçek hareket yine `ContinuousPlayerMovementController`, statik collision resolver, dynamic actor collision resolver ve `HexWorldRuntime.set_continuous_position()` üzerinden commit edilir. Cache, runtime'ın occupancy/konum sahipliğini devralmaz.

### Replan sınırı

Bir `intent()` çağrısında en fazla bir replan yapılır. Replan sonrasında yeni ilk edge de geçersizse controller komutu blocked/failed durumunda sonlandırır. Sınırsız replan döngüsü yoktur.

## 4. Ölçüm sayaçları

Controller `metrics_snapshot()` ile aşağıdaki oyuncu click-to-move sayaçlarını sunar:

- `player_click_path_queries`
- `player_click_route_cache_hits`
- `player_click_route_cache_misses`
- `player_click_route_replans`
- `player_click_route_invalidations`
- `player_click_route_blocked_steps`
- `player_click_route_waypoints_total`
- `player_click_route_arrivals`
- `player_click_route_failures`

`timing_enabled=True` olduğunda path planning ve route arrival süreleri toplanır; p50/p95/p99 değerleri `metrics_snapshot()` üzerinden alınır. Zaman ölçümü varsayılan olarak kapalıdır; sayaçlar varsayılan durumda da kullanılabilir.

Path planning süresi `runtime.path_to()` çağrısını kapsar; dolayısıyla occupancy blocked-cell üretimi ve A* aramasını birlikte ölçer. Bu sayaçlar NPC kaçınma pathfinding metriğinden ayrıdır.

## 5. Eklenen testler

### `tests/test_application/test_click_move_route.py`

12 yeni test:
- Aynı aktif hedefin fixed step çağrılarında tek A* sorgusu üretmesi
- Yeni hedefin eski rotayı değiştirmesi
- Runtime replacement invalidation
- Güncel occupancy engelinde alternatif rota
- Replan başarısızlığında güvenli durma
- Authoritative oyuncu konumu rotadan saptığında replan
- Statik collision edge invalidation
- Hedef hücre/merkez toleransında varış
- RUNNING/STEALTH modunun route intent'inde korunması
- Physics snapshot değişiminde replan
- İsteğe bağlı path/arrival percentile ölçümü
- Tek fixed step'te yalnızca bir replan yapılması

### `tests/test_game_ui/test_hex_gameplay_view.py`

- Tekrarlanan click-move intent çağrılarında route cache kullanımı
- Bir render karesinde dört fixed physics step çalıştırıldığında bir path query ve üç cache hit

## 6. CI ve kalite doğrulaması

Düzeltilmiş son test commit'i `01e05abcc2f22e8811974d9ab54e1733b80b6156` için:

| Kontrol | Sonuç |
|---|---|
| Pytest — Ubuntu Python 3.11 | **2.462 passed** |
| Pytest — Ubuntu Python 3.12 | **2.462 passed** |
| Pytest — Windows Python 3.11 | **2.462 passed** |
| Pytest — Windows Python 3.12 | **2.462 passed** |
| Ruff — Core Quality kapsamı | Başarılı |
| Core Quality — Linux verify | Başarılı |
| Core Quality — Windows verify | Başarılı |
| Pygame headless smoke | Başarılı |

- **Eldoria CI run:** `44881177857`
- **Core Quality run:** `44881177885`

İlk CI döngülerinde iki test/kalite sorunu bulundu ve düzeltildi:
- View'da artık kullanılmayan `Vector2` import'u kaldırıldı; yeni route modülü ve test dosyası Core Quality Ruff listesine eklendi.
- Cache hit sayımı yalnızca önceden oluşturulmuş rotanın yeniden kullanıldığı adımlarda artırılacak şekilde düzeltildi.
- Çoklu fixed-step entegrasyon testindeki `MovementConfig` fixture'ına zorunlu `max_speed` değeri eklendi.

Son commit'te bütün zorunlu matrisler başarılıdır. `NPC spatial benchmark` workflow'u da rota cache uygulama commit'inde başarılı tamamlandı; Aşama 2 NPC optimizasyon kapsamına kod değişikliği yapılmadı.

## 7. Bilinen sınırlar ve sonraki aşamaya devir

- Waypoint cursor takibi ve güvenli sonraki-edge doğrulaması tamamlandı.
- Bu aşamada waypoint smoothing uygulanmadı. Swept collision/supercover kanıtı olmadan waypoint atlamak veya köşeleri kesen doğrusal birleştirme yapmak güvenli kabul edilmedi. Aşama 3.4'te yalnızca kanıtlanabilir collinear smoothing değerlendirilebilir.
- Arrival tolerance 0.5 dünya birimidir. Ancak `MovementIntegrator` ivmelenme/frenleme sağlamaz. Yüksek hızda hedef merkezini aşma ve salınım riski için bu tolerans tek başına tam bir frenleme çözümü değildir. Aşama 3.5'te bu bağımlılık açıkça ele alınmalıdır.
- Timing metrics isteğe bağlıdır. Aşama 3.6 benchmark'ı `timing_enabled=True` ile 1/10/100 hücre rotalarında çalıştırılmalıdır.
- Oyuncu click-to-move metrikleri NPC kaçınma p95 değerleriyle birleştirilmemelidir.

**Sonuç:** Aşama 3.3 tamamlandı. Aynı aktif hedef için fixed-step başına A* tekrarı kaldırıldı; runtime, occupancy ve collision güvenliği korunarak rota cache, cursor, invalidation, kontrollü replan ve ölçüm sayaçları eklendi.
