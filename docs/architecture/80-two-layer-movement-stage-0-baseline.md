# Eldoria — İki Katmanlı Hareket Mimarisi: Aşama 0 Baseline ve Mevcut Sözleşmeler

**Tarih:** 23 Kasım 2026  
**Hedef dal:** `experiment/map-cleanup`  
**Denetlenen HEAD:** `af979dda3d35eecabe03efe88017909996899952`  
**Kapsam:** Aşama 0 — baseline ve sahiplik sözleşmelerinin doğrulanması  
**Durum:** Tamamlandı; oyun davranışında kod değişikliği yapılmadı.

---

## 1. Aşama 0 sonucu

Bu rapor, 79 numaralı iki katmanlı hareket mimarisi planının uygulanmasından önce, dalın gerçek kod durumunu ve mevcut sözleşmelerini kaydeder.

**Temel sonuç:** Eldoria'da sürekli dünya koordinatında hareket altyapısı mevcuttur. Yeni sistem sıfırdan bir hareket motoru olmayacaktır. Geliştirilmesi gereken ana alan, mevcut sürekli hareket ve fizik hattının bugün hâlâ axial/altıgen graf üzerinde çalışan navigasyonla nasıl birleştirileceğidir.

Aşama 0 sırasında:
- Oyuncu veya NPC hareket kodu değiştirilmedi.
- Fizik, çarpışma, harita, kayıt şeması veya içerik verisi değiştirilmedi.
- Mevcut kaynak zinciri, konum sahipliği, collider ölçüleri, zaman adımları, kayıt sözleşmesi ve CI baseline'ı doğrulandı.
- Uygulama aşamalarında çözülmesi gereken mevcut engeller ayrıca kaydedildi.

## 2. Güncel mimari: doğrulanmış sahiplik sınırları

### 2.1 Kanonik dünya ve konum sahipliği

| Sorumluluk | Güncel sahip | Doğrulanan davranış |
|---|---|---|
| Harita topolojisi ve geçerli alan | `HexMapDefinition` | Axial `(q,r)` hücreleri, `valid_cells`, arazi, engeller, landmark ve geçiş tanımları |
| Aktör kimliği ve sosyal/oyunsal durum | `WorldActorRegistry` / ilgili domain kayıtları | Var olan aktör kimliği uzamsal sisteme yeniden sarılmaz veya kopyalanmaz |
| Aktörün gerçek harita konumu | `HexWorldRuntime` | `ContinuousEntityPosition` içindeki sürekli `WorldPoint(x,y)` tek fiziksel konum kaynağıdır |
| Türetilmiş altıgen hücre sahipliği | `HexWorldRuntime` + `HexOccupancyRegistry` | Sürekli nokta `world_point_to_hex` ile axial hücreye çevrilir; occupancy bu hücreyi indeksler |
| Dinamik uzamsal aday sorgusu | `UniformGridIndex` | Sürekli dünya koordinatındaki collider AABB'lerini broadphase için indeksler; navigasyon grafı değildir |
| Statik çarpışma geometrisi | `HexPhysicsSnapshot` | Harita geometrisinden üretilen engeller ve süpürmeli sürekli çarpışma çözümü |
| Sunum ve input adaptörü | `HexGameplayView` / `GameWindow` | Kamera, giriş, rota niyeti, çizim ve animasyon; kanonik aktör konumunun sahibi değildir |

`HexWorldRuntime.entity()` sürekli konum ile occupancy hücresinin birbiriyle tutarlı olduğunu doğrular. `set_continuous_position()` yeni dünya noktasından axial hücreyi yeniden hesaplar. Aynı hex içinde kalındığında alt-hücre konumu güncellenir; hex sınırı geçildiğinde geçerli harita maskesi, arazi/hareket kuralları ve occupancy kontrol edilir.

Runtime commit sırası önemlidir:
1. Dinamik uzamsal broadphase indeksi yeni collider sınırlarıyla güncellenir.
2. Axial occupancy yeni hücreye taşınır.
3. Occupancy işlemi başarısız olursa broadphase önceki konuma geri alınır.
4. İki türetilmiş kayıt kabul ettikten sonra sürekli konum güncellenir.

Dolayısıyla kare navigasyon ızgarası, `WorldPoint` konumunun veya occupancy'nin ikinci bir sahibi olamaz. Kare hücre merkezine snap yapılmayacaktır.

### 2.2 Oyuncunun mevcut hareket çağrı zinciri

Güncel ana `GameWindow` akışı şu şekildedir:

1. İçerik paketinden oyuncu aktörüne ait `MovementConfig` yüklenir.
2. `FixedStepAccumulator`, frame süresini sınırlı sabit simülasyon adımlarına böler.
3. `ContinuousPlayerMovementController`, `MovementIntent` ve varsa `MovementTarget` alır.
4. `MovementIntegrator`, hız, ivme, yavaşlama ve hedefe yaklaşma durumunu hesaplar.
5. `HexPhysicsSnapshot.resolve_motion()`, önerilen sürekli yer değiştirmeyi statik collider'lara karşı süpürmeli fizik çözümünden geçirir.
6. `DynamicActorCollisionResolver`, oyuncu-NPC fiziksel etkileşimini ve itişleri çözer.
7. Sonuç `HexWorldRuntime.set_continuous_position()` üzerinden commit edilir.
8. Oyuncu konumu commit edilemezse aynı adımda geçici yapılan NPC itişleri geri alınır.

Başlıca kaynaklar:
- `game_ui/game_window.py`
- `application/continuous_player_movement.py`
- `core/domain/movement/integrator.py`
- `application/hex_physics_bridge.py`
- `application/dynamic_actor_collision.py`
- `application/hex_world_runtime.py`

### 2.3 NPC hareket çağrı zinciri

NPC sistemleri aynı sürekli `WorldPoint`, harita fiziği ve runtime commit sözleşmesini kullanır; ancak mevcut kodda oyuncunun `MovementIntegrator` sınıfını ortak biçimde kullanmazlar.

- **Devriye:** `NPCBehaviorSystem`, axial waypoint'ler ve `HexWorldRuntime.path_to()` üzerinden sonraki hex hedefini seçer; hedefe doğru sürekli displacement üretir, statik fizik çözümünden geçirir ve runtime'a commit eder.
- **Kaçınma/kaçış:** `NPCAvoidanceSystem`, kaçış yolunu axial A* ile bulur; sürekli koordinatlarda yerel steering ve NPC ayrışması ekler; displacement'ı fizik çözümünden geçirir.
- **Yoldaş takibi:** `CompanionCommandService`, hedefe giden axial rota üzerinden sürekli konuma doğru hız-zaman adımları uygular.
- **Dinamik aktör çözümü:** `DynamicActorCollisionResolver`, oyuncu-NPC ve NPC-NPC temaslarını fizik gövdeleri üzerinden çözer.

Bu nedenle 79 numaralı planın “oyuncu ve NPC aynı `MovementIntegrator` kullanır” ifadesi **mevcut davranışın tarifi değildir**; bu, ileride NPC entegrasyonu sırasında ele alınacak hedef mimari kararıdır. Beşinci aşamada oyuncu/NPC hareket profillerinin gerçekten ortaklaştırılması veya açıkça farklı tutulması, hız ve ivme davranışı korunarak kararlaştırılmalıdır.

## 3. Navigasyonun bugünkü sınırı

Sürekli hareket mevcut olsa da hedef ve yol üretiminin önemli bölümü hâlâ altıgen grafına bağlıdır:

- `HexPathfinder`, axial komşuluklar üzerinden A* araması yapar.
- `HexWorldRuntime.path_to()` bu yolu kullanır.
- `ClickMoveRouteController`, axial hücre rotasını fizik doğrulamalı waypoint'lere dönüştürür.
- Devriye, kaçınma ve yoldaş takip sistemleri axial hedef/rota hücreleri kullanır.
- `HexPhysicsSnapshot.can_reach_cell()`, axial komşu adımlarının fiziksel geçilebilirliğini kontrol eden doğrulama kapısıdır.

Sonuç olarak gerçek konum kesirli ve süreklidir; fakat rota arama ve hedef seçimi hâlâ hücre merkezleri ve altıgen komşulukları çevresinde kuruludur. İki katmanlı mimarinin çözmesi gereken ana problem budur.

### 3.1 İki farklı “grid” yapısı karıştırılmamalıdır

- `UniformGridIndex`: aktör ve collider AABB'leri için dinamik spatial-hash/broadphase indeksi.
- Gelecekte eklenecek kare navigasyon ızgarası: geçilebilir alan örneklemesi, yerel yol grafı, rota maliyeti ve navigasyon sorguları için türetilmiş veri.

Bunlar farklı veri yapıları, farklı doğruluk sözleşmeleri ve farklı yaşam döngüleridir. Biri diğerinin yerine kullanılamaz.

## 4. Fizik ve geometri sözleşmeleri

### 4.1 Dünya geometrisi

- Harita şeması: `hex_axial`
- Yönelim: `pointy_top`
- Koordinat sistemi: `axial`
- `HexWorldRuntime.HEX_SIZE`: **32 dünya birimi** (merkezden köşeye yarıçap)
- Başlangıç Vadisi içerik haritası: **61 geçerli axial hücre**, q/r sınırları `[-4, 4]`.

Dönüşümler `core/domain/spatial/hex_geometry.py` içinde merkezi olarak tutulur. `axial_to_world_point()`, `world_point_to_fractional_axial()` ve `world_point_to_hex()` aynı geometri sözleşmesini kullanır. Nokta-yukarı hex dönüşüm formülleri renderer veya navigasyon modüllerinde yeniden yazılmamalıdır.

### 4.2 Statik ve dinamik çarpışma

- Oyuncu collider'ı: `CircleShape(8.0)`, yarıçap 8 dünya birimi.
- NPC varsayılan fizik gövdesi: `CircleShape(radius=4.0)`; içerik paketi açıkça başka bir fizik yarıçapı verebilir.
- Statik harita geometrisi: engelli hex hücreleri, yürünemez landmark'lar, kapalı harita sınırı ve içerikten gelen nesne engelleri.
- Hareket çözümü: `resolve_continuous_motion()`, collider displacement'ını süpürerek engel adaylarına karşı çözer.
- Dinamik aktör itişi: mevcut `DynamicActorCollisionResolver` tarafından çözülür.

Oyuncu ve fizik gövdesi etkin NPC'ler normal harita başlangıç/binding akışında `blocks_movement=False` ve `blocks_occupancy=False` ile kaydedilir. NPC binding kodu da fizik gövdesi mevcut olduğunda fizik çarpışmasını gerçek engel kabul eder; böylece iki aktör aynı axial hücreyi paylaşabilirken collider'ları ayrı konumlarda kalabilir. Bu davranış korunmalıdır. Hücre occupancy, fizik collider'ının yerine geçen kaba bir aktör duvarına dönüştürülmemelidir.

### 4.3 Sabit zaman adımı

`FixedStepAccumulator` varsayılan olarak:
- Simülasyon adımı: **1/60 saniye**
- Bir frame için en fazla catch-up adımı: **8**
- Fazla birikmiş tam adımlar sınırlanır/düşürülür; kesirli kalan süre saklanır.

`MovementIntegrator` zaman kaynağına sahip değildir; `delta_seconds` parametresi alır ve hız/ivme hesabını saniye cinsinden yapar. Hareket ve fizik, render FPS'ine göre doğrudan ölçeklenmemelidir.

## 5. Kayıt ve geri yükleme sözleşmesi

- Dış oyun kaydı: `rpg-game-save`, sürüm **3** (`application/save_document.py`).
- İç hex dünya snapshot'ı: `rpg-hex-world`, sürüm **2** (`application/hex_world_persistence.py`).
- Hex dünya kaydı aktör için map ID + axial q/r ve sürekli dünya konumu x/y değerlerini saklar.
- Hex dünya v1 eski kayıt biçimi, v2 okuyucusunda migration/uyumluluk yolundan desteklenir.
- Kare navigasyon ızgarası ve cache'i henüz mevcut değildir; gelecekte de türetilmiş veri olarak bellekte yeniden üretilmelidir. Save schema'ya kare hücre koordinatı eklenmeyecektir.

Sürüm 3 dış kayıt zarfı, sürüm 2 hex dünya snapshot'ı ve map içerik kimliği korunarak yeni navigasyon cache'i kayıtlara dahil edilmemelidir.

## 6. İçerik paketi için mevcut entegrasyon bulgusu

GitHub'daki denetlenen HEAD'de `content/active_package.json`, `demo_eldoria` paketini seçmektedir. Bu paketin `gameplay_rules.json` dosyasında şu an `movement.actors` profili bulunmamaktadır.

`load_movement_configs()`, hareket profili yoksa boş mapping döndürür; hız değeri tahmin etmez. `GameWindow` içindeki normal oyuncu input etkinleştirmesi de oyuncu aktörünün `_movement_configs` içinde bulunmasını şart koşar.

Bu nedenle **denetlenen GitHub içerik paketinde oyuncu hareket profili için açık bir konfigürasyon eksikliği vardır**. Ayrı bir yerel paket veya yerel değişiklik bu durumu değiştirebilir; bu rapor yalnızca denetlenen GitHub HEAD'ini tarif eder.

Aşama 4'e geçilmeden önce:
1. Başlangıç paketinde oyuncu için açık ve içerik kaynaklı `MovementConfig` değerleri tanımlanmalı veya eksik profil için tasarlanmış bir input politikası eklenmelidir.
2. Hız/ivme değerleri ölçüm ve oyun tasarımı kararı olmadan tahmin edilmemelidir.
3. Bu konfigürasyon testlerde ve varsayılan oyun açılışında doğrulanmalıdır.

Bu eksiklik kare grid geometrisini prototiplemeyi engellemez; ancak oyuncu entegrasyonu ve görsel hareket kabulü için bir giriş kapısıdır.

## 7. Test ve CI baseline

Denetlenen HEAD: `af979dda3d35eecabe03efe88017909996899952`.

GitHub Actions sonuçları:

| İş akışı | Sonuç | Kapsam |
|---|---|---|
| Core quality — run `45135586932` | Başarılı | Ubuntu/Windows kalite doğrulaması, Ruff, harita temizliği kontrolü, click-to-move rota benchmark'ı, release doğrulaması |
| Eldoria CI — run `45135587158` | Başarılı | Windows ve Ubuntu üzerinde Python 3.11/3.12 test matrisi; Pygame headless smoke ve izometrik çizim smoke |

Doğrudan incelenen Windows 3.11 ve Ubuntu 3.12 job loglarında:
- `unittest`: **1.577 test** başarılı.
- `pytest`: **2.597 passed**, **319 subtests passed**, **59 warning**.
- Ruff kontrolleri başarılı.
- Diğer iki platform/sürüm matrisi işi de başarılı sonuçlandı.
- Pygame headless başlatma testi başarılı.
- İzometrik render smoke testi başarılı: 15 scene object, 3 gameplay placement ve 3 asset çizildi.

Bu CI sonucu, kodun test ve headless sunum baseline'ını doğrular; gerçek kullanıcı donanımında hareket akıcılığı veya hedef FPS garantisi değildir. Hedef cihaz üzerinde hareket frame-time ölçümü ve görsel kabul daha sonraki aşamada yapılacaktır.

İlgili hareket regresyon dosyaları:
- `tests/test_application/test_continuous_player_movement.py`
- `tests/test_application/test_hex_world_runtime.py`
- `tests/test_application/test_hex_world_persistence.py`
- `tests/test_application/test_hex_world_save_load.py`
- `tests/test_application/test_hex_physics_bridge.py`
- `tests/test_application/test_dynamic_actor_collision.py`
- `tests/test_application/test_npc_behavior_system.py`
- `tests/test_application/test_npc_physics_content.py`
- `tests/test_game_ui/test_hex_gameplay_view.py`
- `tests/test_game_ui/test_movement_input.py`
- `tests/test_hex_world_lab/unit/test_movement_integrator.py`
- `tests/test_hex_world_lab/unit/test_physics_continuous.py`

Mevcut testler alt-hücre sürekli konum, hex sınırı geçişi, engel çözümü, occupancy atomikliği, oyuncu-NPC itişi, hızlanma/yavaşlama, hedefe frenleme ve kayıt/geri yükleme davranışlarını kapsar. Henüz kare grid dönüşümü, kare-grid A*, corner-cutting veya grid cache testi yoktur; bu testler yeni aşamalarla eklenecektir.

## 8. Tarihsel mimari belgeleriyle uzlaştırma

72, 77 ve 78 numaralı belgeler, altıgen hücre hareketi ve görsel enterpolasyonun önceki aşamalarını kaydeden tarihsel belgelerdir. Özellikle 78 numaralı belge, o tarihte oyuncu konumunun hücre adımları ve görsel enterpolasyonla yönetildiği eski durumu anlatır.

Denetlenen güncel HEAD'de ise `ContinuousPlayerMovementController`, `MovementIntegrator`, `HexPhysicsSnapshot.resolve_motion()` ve `HexWorldRuntime.set_continuous_position()` hattı mevcuttur. Bu nedenle eski 78 numaralı rapor güncel kodun tam tarifi olarak kullanılmamalıdır; kronolojik bir önceki aşama kaydıdır. Güncel kaynak kod ve bu baseline raporu, sonraki uygulama için esas alınmalıdır.

## 9. Aşama 0 çıkış kararı ve sonraki adımlar

**Aşama 0 çıkış kriterleri karşılandı:**
- Çalışma dalı/HEAD doğrulandı.
- Sürekli konumun sahibi ve axial occupancy türetme/commit sırası belirlendi.
- Oyuncu hareket, statik fizik, dinamik aktör çarpışması ve runtime commit zinciri belirlendi.
- NPC devriye/kaçınma/yoldaş hareketinin mevcut oyuncu integratöründen farklı olduğu kaydedildi.
- 8 birim oyuncu collider'ı, 32 birim hex yarıçapı, fixed-step ve persistence sözleşmeleri doğrulandı.
- Mevcut CI/test baseline'ı kaydedildi.
- Yeni kare ızgara için bulunmayan test alanları belirlendi.

**Aşama 1'e geçiş kapsamı:** Yalnızca saf geometri prototipi: `WorldPoint ↔ GridCoord` dönüşümü, grid hücresinin hex coverage/sahipliği, harita maskesi ve 8/16 dünya birimi çözünürlük karşılaştırması. Oyuncu/NPC hareket hattına bağlanmayacaktır. Geçilebilirlik sınıflandırması, gerçek collider fiziğinin yerine geçmeyecektir.

**Aşama 4 ön koşulu:** Varsayılan `demo_eldoria` paketinde oyuncu hareket profilinin eksikliği ele alınmalıdır.

**Aşama 5 tasarım kararı:** NPC hareket davranışları ortak `MovementIntegrator` modeline taşınacaksa bu değişim ayrı test ve performans kontrolüyle yapılmalıdır; mevcut davranışın zaten böyle olduğu varsayılmamalıdır.

---

## 10. Teknik dokümantasyon dayanağı

Pygame belgelerinin Context7 üzerinden doğrulanan örnekleri, frame-rate bağımsız hareket için `delta time` ile ölçeklenmiş dünya hareketini ve `Vector2` kullanımını gösterir. Eldoria zaten zaman birimli native movement/physics katmanı kullandığından Pygame sunum katmanı ikinci bir hareket otoritesi kurmamalıdır.

- Pygame ana dokümantasyonundaki delta-time hareket örneği: https://github.com/pygame/pygame/blob/main/docs/reST/index.rst
- Pygame Rect çarpışma yardımcıları: https://github.com/pygame/pygame/blob/main/docs/es/ref/rect.md
- Eldoria süpürmeli sürekli çarpışma çözümü: `core/domain/physics/continuous_solver.py`
