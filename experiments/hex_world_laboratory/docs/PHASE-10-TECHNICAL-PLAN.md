# Aşama 10 — Simülasyon Orkestrasyonu ve Dünya Bütünlüğü: Teknik Mimari Planı

> **Belge türü:** Teknik mimari ve uygulama sözleşmesi  
> **Üst belge:** [HEX_WORLD_LAB_MASTER_PLAN.md](HEX_WORLD_LAB_MASTER_PLAN.md)  
> **Genel plan:** [PHASE-10-GENERAL-PLAN.md](PHASE-10-GENERAL-PLAN.md)  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **İncelenen temel commit:** `48d5d94033b6b71409b8c3afc35751face250fcd`  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — 10.1–10.8 UYGULANDI — OTOMATİK TEST/CI BAŞARILI — MANUEL KABUL BEKLENİYOR  
> **Kapsam kararı:** NPC, kaynak ve yoldaş hareketi bu aşamada yoktur.

---

## 1. Teknik hedef

Aşama 10, laboratuvardaki mevcut gerçek zamanlı tick üretimini koruyarak simülasyon sistemlerinin tek bir koordinasyon noktasında, tanımlı ve test edilebilir sırayla çalışmasını sağlayacaktır.

Uygulama aşağıdaki mimari ayrımı kuracaktır:

- **Tick pump:** Gerçek zamanın sabit simülasyon tick'lerine dönüştürülmesi.
- **Simulation tick coordinator:** Her tick içindeki authoritative sistem güncelleme sırasının yürütülmesi.
- **Movement/Physics:** Oyuncunun hareketini ve çarpışma çözümünü gerçekleştiren mevcut sistem.
- **Cell tracker:** Hareketten sonra oyuncunun hex hücre çözümünü güncelleyen mevcut sistem.
- **Entity synchronization:** Kesinleşmiş oyuncu WorldPosition'ını EntityTransform'a aktaran uygulama adaptörü.
- **EntityWorldCoordinator:** Entity registry ve entity spatial index tutarlılığını koruyan mevcut sahip.
- **Camera/Rendering:** Simülasyonun son tamamlanmış durumunu okuyan sunum katmanı.

Temel kural: **Bir simülasyon tick'i tamamlanmadan o tick'in sonucu render veya etkileşim sorgularına tamamlanmış state olarak sunulmaz.**

## 2. İncelenen gerçek kod ve mevcut durum

Teknik plan, laboratuvar dalındaki gerçek dosyalar üzerinden hazırlanmıştır.

| Dosya | Mevcut sorumluluk | Aşama 10 kararı |
|---|---|---|
| `src/hex_world_lab/application/demo_tick_pump.py` | Monotonic clock, 60 TPS accumulator, tick numarası, kare başına en fazla 8 tick, zaman borcu | Korunacak; gerçek zaman/tick üreticisi olmaya devam edecek |
| `src/hex_world_lab/application/movement_demo.py` | MovementSystem, MovementCellTracker, input adaptörü, tick pump, kamera ve render snapshot | Tick işini yeni koordinatöre devredecek; sunum görevlerini koruyacak |
| `src/hex_world_lab/application/entity_demo.py` | Player/NPC/resource kayıtları, etkileşim ve yoldaş menüsü, entity render snapshot | Oyuncu eşitleme callback'ini simülasyona bağlayacak; render içindeki state güncellemesini kaldıracak |
| `src/hex_world_lab/application/entity_world_coordinator.py` | Registry, spatial index, companion ve harita yaşam döngüsü eşgüdümü | Mevcut sahiplik ve geri alma davranışı korunacak |
| `src/hex_world_lab/simulation/collision_aware_movement_system.py` | Oyuncu movement entegrasyonu ve collision çözümü; tick başına tek adım | Tek movement/physics adımı olarak korunacak |
| `src/hex_world_lab/simulation/movement_cell_tracker.py` | WorldPosition → hücre çözümü; başarılı çözümden sonra state commit | Hareketten sonra çağrılacak |
| `src/hex_world_lab/entities/registry.py` | EntityRecord ve transform kayıtlarının authoritative saklanması | Doğrudan render veya demo tarafından güncellenmeyecek; coordinator üzerinden yönetilecek |
| `src/hex_world_lab/entities/spatial_index.py` | Registry state'inden türetilen harita bazlı entity aday indeksi | EntityWorldCoordinator üzerinden güncellenecek |
| `src/hex_world_lab/app.py` | Pygame event/frame loop, pump, kamera ve render çağrıları | Tek laboratuvar giriş noktası olarak korunacak; yalnızca gerekirse entegrasyon düzenlemesi yapılacak |

### 2.1 Doğrulanmış mevcut veri akışı

Şu anda `LabApplication.run()` her frame'de sırasıyla:
1. Pygame olaylarını işler.
2. `MovementDemo.pump()` çağırır.
3. Kamerayı render delta süresiyle günceller.
4. `EntityDemo.render()` çağırır.

`MovementDemo` içindeki tick callback'i `CollisionAwareMovementSystem.step()` ve ardından `MovementCellTracker.update()` çağırır.

`EntityDemo.build_render_snapshot()` ise şu anda `sync_player()` çağrısını render snapshot oluşturulurken yapmaktadır. Bu çağrı `EntityWorldCoordinator.update_transform()` üzerinden registry ve spatial index'i değiştirebilir. Bu, mimari sözleşmedeki render'ın simülasyon state'ini değiştirmemesi kuralına aykırıdır ve Aşama 10'un birincil düzeltmesidir.

### 2.2 Korunacak mevcut garantiler

- `DemoTickPump` sabit 1/60 saniyelik tick üretir.
- Bir pump çağrısı en fazla 8 başarılı tick işler; kalan süre borcu kaybolmaz.
- Başarısız callback'in tick numarası ve zaman borcu pump tarafından tüketilmez; aynı tick yeniden denenir.
- `CollisionAwareMovementSystem.step()` hesaplama başarılı olmadan kendi hareket state/tick ilerlemesini commit etmez.
- `MovementCellTracker.update()` çözüm başarılı olmadan kendi tracker state'ini commit etmez.
- `EntityWorldCoordinator.update_transform()` spatial güncellemesi başarısız olduğunda önceki entity transform'unu geri yüklemeyi dener.
- `EntitySpatialIndex` entity registry'den türetilmiş veridir; bağımsız authoritative konum kaynağı değildir.

## 3. Önerilen mimari

### 3.1 Yeni bileşen

Yeni dosya:

`src/hex_world_lab/simulation/tick_coordinator.py`

Önerilen sınıf:

`SimulationTickCoordinator`

Sorumlulukları:
- Bir tick için input niyetini almak.
- Oyuncu movement/physics adımını bir kez çalıştırmak.
- Başarılı hareketin WorldPosition sonucunu hücre takipçisine aktarmak.
- Varsa entity konum eşitleme callback'ini çağırmak.
- Tick'in tamamlanmasını ve sırasını doğrulamak.
- Bir aşama hata verdiğinde aynı tick'in yeniden çağrılmasını güvenli biçimde sürdürmek.

Bu sınıf:
- Pygame import etmeyecek.
- Saat/monotonic clock okumayacak.
- Render veya kamera çağırmayacak.
- NPC, kaynak veya yoldaş hareketi üretmeyecek.
- EntityRegistry veya EntitySpatialIndex iç yapısını doğrudan değiştirmeyecek.
- EntityWorldCoordinator sınıfını simülasyon paketine bağımlılık olarak almayacak; entity eşitlemesi tiplenmiş bir callback sınırından sağlanacak.

### 3.2 Bileşenin bağımlılıkları

Koordinatörün ihtiyaç duyduğu girdiler:
- Mevcut `CollisionAwareMovementSystem` örneği.
- `MovementIntent` üreten callable/input kaynağı.
- Mevcut `MovementCellTracker`.
- İsteğe bağlı `Callable[[WorldPoint], None]` entity synchronization callback'i.

Entity callback'i ilk aşamada boş olabilir; bu sayede MovementDemo'nun tek başına kullanıldığı mevcut hareket testleri ve önceki laboratuvar davranışı korunur. EntityDemo oluşturulduktan ve player kaydı yapıldıktan sonra callback bir kez bağlanır. Tick başladıktan sonra callback'in değiştirilmesine izin verilmez.

### 3.3 Tick yürütme sırası

Her tick aşağıdaki sırayla yürütülecektir:

| Sıra | İşlem | State sahibi |
|---:|---|---|
| 1 | Tick numarası doğrulanır; input niyeti bir kez okunur | SimulationTickCoordinator / input adaptörü |
| 2 | Oyuncu hareketi ve collision çözümü tek adımda çalışır | CollisionAwareMovementSystem |
| 3 | Son WorldPosition hücre çözümüne aktarılır | MovementCellTracker |
| 4 | Son WorldPosition player EntityTransform'a aktarılır | EntityWorldCoordinator üzerinden callback |
| 5 | EntityWorldCoordinator aynı transform güncellemesinin parçası olarak spatial index'i günceller | EntityWorldCoordinator / EntitySpatialIndex |
| 6 | Tick tamamlandı olarak işaretlenir | SimulationTickCoordinator |

Önemli ayrım: Aşama 10'da ayrı bir PhysicsSystem veya ikinci bir collision adımı oluşturulmayacaktır. `CollisionAwareMovementSystem` zaten movement entegrasyonu ve collision çözümünü aynı tick içinde yürütmektedir. Yeni koordinatör bu iç işleyişi kopyalamaz.

Interaction/target selection, en son tamamen tamamlanmış tick'in entity/spatial state'ini okur. Kamera ve render ise simülasyon tick'inin dışında, frame başına güncellenen sunum işlemleridir.

### 3.4 Tick hatası ve tekrar deneme sözleşmesi

Mevcut `DemoTickPump`, callback hata verdiğinde aynı tick numarasını sonraki pump çağrısında yeniden gönderir. Bu davranış korunmalıdır. Ancak movement adımı başarılı olduktan sonra cell tracker veya entity eşitlemesi hata verirse movement adımını tekrar çalıştırmak ikinci kez hareket üretme veya tick numarası uyuşmazlığı doğurabilir.

Bu nedenle `SimulationTickCoordinator` tick içi ilerlemeyi aşama bazında takip edecektir:
- Tick numarası ve başarılı okunmuş input niyeti saklanır.
- Movement başarılı olduğunda elde edilen MovementState/WorldPosition saklanır.
- Sonraki aşama hata verirse aynı tick yeniden geldiğinde tamamlanmış önceki aşamalar tekrar çalıştırılmaz.
- Cell tracker ve entity eşitleme aşamaları yalnızca tamamlanmamış aşamadan sürdürülür.
- Tick ancak tüm aşamalar başarılı olduğunda tamamlanmış sayılır.
- Başka bir tick numarasıyla devam etme girişimi, bekleyen tick çözülmeden reddedilir.

MovementSystem'in kendi atomik commit davranışı korunur. Cell tracker'ın update işlemi de mevcut tasarımında çözüm başarılı olduktan sonra state commit ettiği için aynı WorldPosition ile tekrar çağrılabilir. Entity eşitlemesinde mevcut EntityWorldCoordinator geri alma davranışı korunacak ve hata enjeksiyon testleriyle doğrulanacaktır.

Bu mekanizma genel amaçlı event bus veya plugin sistemi değildir; yalnızca bu aşamada gereken sabit ve belgeli tick hattıdır.

## 4. Dosya bazında uygulama tasarımı

### 10.1 — Mevcut sözleşmelerin son denetimi

- Yukarıdaki dosyaların güncel branch HEAD'inde tekrar doğrulanması.
- Tick numarası başlangıcı ve `DemoTickPump` ile movement system sayaçlarının aynı başlangıç değerini kullanmasının doğrulanması.
- `MovementDemo` ve `EntityDemo` dışındaki test/diagnostic tüketicilerinin `tick_pump`, `pump()`, `start()`, `state` ve `movement_system` API'lerine bağımlılığının belirlenmesi.
- Hiçbir public test/diagnostic API'sinin gerekçesiz kaldırılmaması.

### 10.2 — SimulationTickCoordinator

- `simulation/tick_coordinator.py` oluşturulacak.
- Tick input, movement, cell tracking ve entity sync aşamalarını sabit sırada yürütecek.
- Beklenen tick numarası ve bekleyen aşama state'i yönetilecek.
- Callback bağlama yalnızca tick başlamadan önce yapılabilecek.
- Koordinatör Pygame ve wall-clock bağımlılığı taşımayacak.
- `simulation/__init__.py` üzerinden kontrollü export yapılacak.

### 10.3 — MovementDemo entegrasyonu

- `MovementDemo` içine `SimulationTickCoordinator` referansı eklenecek.
- Mevcut `DemoTickPump` callback'i doğrudan hareket ve cell tracker kodunu değil, koordinatörü çağıracak.
- `_advance_tick()` ya kaldırılacak ya da yalnızca koordinatöre delege eden ince bir uyumluluk metodu olarak kalacak.
- `MovementDemo.start()`, `pump()`, `tick_pump`, `state`, `diagnostics` ve mevcut hareket API'leri korunacak.
- Tek başına MovementDemo kullanıldığında entity sync aşaması olmadan çalışabilmesi sağlanacak.

### 10.4 — EntityDemo entegrasyonu ve render saflığı

- Player EntityRecord başlangıçta mevcut MovementState konumuyla oluşturulmaya devam edecek.
- EntityDemo, player kaydı ve EntityWorldCoordinator kurulumu tamamlandıktan sonra SimulationTickCoordinator'a tek seferlik entity sync callback'i bağlayacak.
- Callback, tick'in kesinleşmiş WorldPosition değerini alacak; MovementDemo state'ini render sırasında okumayacak.
- Transform değişmediyse gereksiz registry/spatial güncellemesi yapılmayacak.
- `build_render_snapshot()` içindeki `sync_player()` çağrısı kaldırılacak.
- `build_render_snapshot()` ve `render()` player EntityRecord, registry, companion ilişkisi veya spatial index üzerinde authoritative değişiklik yapmayacak.
- Render snapshot, son tamamlanmış tick'te eşitlenmiş EntityRecord verisini okuyacak.
- Action menu gibi sunum/UI geometrisi güncellenebilir; ancak bu, simülasyon/world state değişikliği sayılmayacak.

### 10.5 — Harita ve entity yaşam döngüsü entegrasyonu

- EntityWorldCoordinator'ın mevcut load/unload/remove sorumlulukları korunacak.
- Harita unload edildiğinde entity kayıtları ve yoldaş ilişkileri saklı kalacak; ilgili spatial index devre dışı kalacak.
- Reload sonrasında aktif entity'ler yeniden indekslenecek.
- Harita remove işlemi entity ve companion kayıtlarını temizlemeye devam edecek.
- Player sync callback'i yalnızca player'ın kayıtlı world/map kimliği için geçerli konum güncellemesi yapacak.
- Bu aşama haritalar arası player transferi veya companion teleport davranışı eklemeyecek.
- Yaşam döngüsü değişiklikleri aynı anda tick yürütülmesiyle yarışmayacak; mevcut tek-thread demo akışında tick sınırları arasında uygulanacak.

### 10.6 — Input, etkileşim, kamera ve render sınırları

- Pygame input olayları mevcut adapter üzerinden alınmaya devam edecek.
- Input niyeti her tick için bir kez örneklenecek; bir frame'de birden fazla tick varsa her tick kendi input okumasını yapacak.
- Sağ tık hedef sorgusu ve sol tık seçimi en son tamamlanmış entity/spatial state'i okuyacak.
- Yoldaş komutları mevcut context menu üzerinden roster verisini değiştirebilir; bu komutlar hareket sistemi çağırmayacak.
- Kamera hedefi oyuncunun son movement state'inden okunacak ve render delta ile güncellenecek.
- Render snapshot üretimi yalnızca mevcut world/entity verisini okuyacak.

### 10.7 — Test ve performans doğrulaması

- Koordinatörün unit testleri.
- Tick hata/tekrar deneme testleri.
- MovementDemo ve EntityDemo entegrasyon testleri.
- Render saflığı testleri.
- Harita lifecycle regresyonları.
- Uzun süreli tick ve spatial differential testleri.
- Simülasyon tick maliyeti ve render snapshot maliyetinin ayrı benchmarkları.

### 10.8 — Regresyon, performans ve kabul doğrulaması

- 3.600 tick'lik uzun süreli entity/spatial tutarlılık testi eklendi.
- 30/60/120 render FPS eşdeğerliği ve 60 TPS sabit zaman adımı regresyonları korundu.
- NPC, kaynak ve FOLLOW/WAIT/RETURN komutlarının hareketsizlik garantileri doğrulandı.
- Simülasyon tick maliyeti ile render snapshot maliyeti ayrı ölçüldü.
- Laboratuvar CI, Linux Core Quality ve Windows Core Quality başarılı tamamlandı.
- Görsel test sahneleri ve Phase 10 benchmark raporu artifact olarak yüklendi.
- Manuel kabul kontrol listesi kullanıcı testi için hazırlandı; kullanıcı onayı bekleniyor.

## 5. Test mimarisi ve beklenen testler

### 5.1 Unit testler

Yeni dosya önerisi:
`tests/unit/test_simulation_tick_coordinator.py`

Test senaryoları:
- Tick numarası sıralı ve tekil kabul edilir.
- Yanlış/tekrarlı tick numarası reddedilir.
- Input her tick için bir kez okunur.
- Hareket, cell tracker ve entity sync beklenen sırada çağrılır.
- Entity callback yokken MovementDemo akışı bozulmaz.
- Movement adımı hata verirse tick tamamlanmış sayılmaz.
- Movement tamamlandıktan sonra cell tracker hata verirse tekrar denemede movement ikinci kez çalışmaz.
- Entity sync hata verirse aynı tick yeniden çağrıldığında movement ve başarılı cell tracking tekrar çalışmaz.
- Bekleyen tick tamamlanmadan daha ileri tick kabul edilmez.
- Tick başarıyla tamamlanınca bir sonraki tick kabul edilir.
- Koordinatör Pygame import etmeden kullanılabilir.

### 5.2 Integration testler

Yeni/yenilenecek dosyalar:
- `tests/integration/test_simulation_tick_flow.py`
- `tests/integration/test_entity_demo_render_purity.py`

Test senaryoları:
- DemoTickPump → SimulationTickCoordinator → Movement/Physics → CellTracker → EntityWorldCoordinator → EntitySpatialIndex akışı.
- Bir saniyelik simülasyon süresinde 60 tick tamamlanması.
- 30/60/120 render FPS koşullarında aynı tick/input dizisinin aynı oyuncu konumunu üretmesi.
- Oyuncu hareket ettiğinde aynı tamamlanmış tick sonunda MovementState, EntityTransform ve spatial query sonucu aynı WorldPosition'ı temsil eder.
- Hareketsiz tick'te gereksiz transform/index güncellemesi yapılmaz.
- Render snapshot öncesi ve sonrası player EntityRecord, tüm registry kayıtları, companion ilişkileri ve spatial query sonuçları aynıdır.
- Birden fazla render çağrısı yeni simülasyon tick'i üretmez.
- Render çağrısı player sync callback'ini tetiklemez.
- NPC ve kaynak konumları tick'ler boyunca değişmez.
- FOLLOW/WAIT/RETURN komutları NPC konumunu değiştirmez.
- Right-click hedef menüsü ve left-click seçim son tamamlanmış spatial state üzerinde çalışır.

### 5.3 Mevcut testlerle uyumluluk

Aşağıdaki test aileleri regresyon referansıdır:
- `tests/integration/test_demo_tick_pump.py`
- `tests/integration/test_movement_tick_contract.py`
- `tests/integration/test_movement_demo_render.py`
- `tests/integration/test_entity_world_lifecycle.py`
- `tests/unit/test_movement_system.py`
- `tests/unit/test_collision_aware_movement_system.py`
- `tests/unit/test_movement_cell_tracker.py`
- Entity registry, companion ve spatial index unit testleri.

Mevcut testler yeni mimariye göre güncellenebilir; ancak önceki kabul edilmiş davranışlar korunmalıdır. Test sayısı tek başına başarı ölçütü değildir.

## 6. Zaman adımı ve determinism kararı

Mevcut 60 TPS sabit zaman adımı korunacaktır:
- `TICK_RATE = 60`
- `TICK_DURATION_SECONDS = 1 / 60`
- `MAX_TICKS_PER_PUMP = 8`
- Zaman borcu atılmaz; sonraki pump çağrılarında işlenir.
- MovementSystem'in sabit `TICK_DELTA_SECONDS` sözleşmesi korunur.
- Render FPS simülasyon hızını belirlemez.
- Kamera smoothing ve sunum güncellemesi frame delta kullanabilir; authoritative dünya state'ine yazamaz.

Determinism kabulü şu sınırda tanımlanır: Aynı başlangıç simülasyon state'i, aynı tick numaraları ve aynı sıralı MovementIntent dizisi aynı movement/entity/spatial sonucunu üretmelidir. Pygame event zamanlaması veya gerçek zamanlı clock ölçümü deterministik domain girdisi sayılmaz.

## 7. State sahipliği ve veri akışı

| Veri | Authoritative sahibi | Türetilen/okuyan katman |
|---|---|---|
| Oyuncu WorldPosition | CollisionAwareMovementSystem state | EntityTransform, hücre tracker, kamera, render |
| Oyuncu hex çözümü | MovementCellTracker | Diagnostics/render |
| Player EntityTransform | EntityRegistry; tick callback ile güncellenir | EntitySpatialIndex, interaction, render |
| Entity spatial bounds/index | EntitySpatialIndex | TargetQuery |
| NPC/resource konumu | EntityRegistry | Spatial index, interaction, render |
| Companion relationship/command | CompanionRoster | Context menu ve diagnostics |
| Camera transform | CameraController | Input dönüşümü ve renderer |
| Render snapshot | Snapshot builder tarafından üretilen immutable DTO | Pygame renderer |

EntitySpatialIndex hiçbir zaman bağımsız konum doğruluk kaynağı olmayacaktır. Render snapshot içindeki görsel konumlar authoritative state'in kopyasıdır; geri yazılmaz.

## 8. Kapsam dışı ve açık yasaklar

Aşama 10'da aşağıdakiler uygulanmayacaktır:
- NPC devriyesi, gezinmesi, rastgele veya otonom hareket.
- Yoldaş FOLLOW/WAIT/RETURN gerçek hareketi, takip, bekleme davranış motoru veya geri dönüş rotası.
- Pathfinding, A*, Dijkstra, rota planlama, click-to-move ve engel dolaşma.
- NPC AI, algı, karar, günlük rutin, combat veya dialogue davranışı.
- Kaynakların hareketi, toplanması, üretimi, envantere aktarılması veya ekonomi.
- Player/NPC harita transferi, companion teleport veya formation.
- Yeni fizik motoru veya ikinci collision çözüm katmanı.
- Kamera/render mimarisinin yeniden yazılması.
- Pygame'den Godot'a geçiş.
- Ayrı Aşama 10 launcher'ı. Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak kalır.
- `main` veya `demo_eldoria` dalında herhangi bir değişiklik.

## 9. Uygulama sırası ve değişiklik kontrolü

Önerilen kodlama sırası:
1. Tick coordinator unit testleri ve minimal koordinatör tasarımı.
2. SimulationTickCoordinator uygulaması ve simulation package export'u.
3. MovementDemo entegrasyonu; eski public API regresyonları.
4. EntityDemo callback entegrasyonu; render içindeki sync çağrısının kaldırılması.
5. Entity/spatial tutarlılık ve render purity integration testleri.
6. Harita lifecycle, yoldaş hareketsizlik ve kaynak/NPC hareketsizlik regresyonları.
7. Uzun süreli testler ve benchmarklar.
8. Teknik sözleşme, test raporu, manuel kabul checklist'i ve kapanış belgeleri.

Her iş paketi küçük commitlerle çalışma dalına yazılacaktır. Her GitHub yazımından önce aktif dal HEAD ve hedef dosyanın SHA'sı doğrulanacak; korunan dallara yazılmayacaktır.

## 10. Teknik kabul kapısı

Bu teknik plan kullanıcı tarafından onaylanmış; 10.1–10.8 uygulaması tamamlanmıştır. Bu bölüm, uygulama öncesi onay kapısının tarihsel kaydıdır.

Aşama teknik olarak kabul edilebilmek için:
1. SimulationTickCoordinator sabit ve belgeli sırayı uygular.
2. DemoTickPump mevcut 60 TPS, 8 tick sınırı ve lossless time debt garantilerini korur.
3. Tick tekrar denemesi tamamlanmış alt aşamaları tekrar çalıştırmaz.
4. Aynı input/tick dizisi deterministik sonuç verir.
5. Player MovementState, EntityTransform ve spatial index aynı tamamlanmış tick'i temsil eder.
6. Player entity sync render snapshot veya render sırasında yapılmaz.
7. Render ve snapshot authoritative simülasyon/world state'ini değiştirmez.
8. NPC, kaynak ve yoldaş komutları konum değişikliği üretmez.
9. Harita load/unload/reload/remove yaşam döngüsü Aşama 9 sözleşmesini korur.
10. Mevcut movement, physics, camera, selection ve companion davranışları regresyonsuzdur.
11. Laboratuvar testleri, Linux/Windows Core Quality, benchmark ve görsel artifact adımları başarılıdır.
12. Kullanıcı manuel kabulü tamamlar.

## 11. İlgili mimari belge güncellemesi

`docs/ARCHITECTURE_SPECIFICATION.md` içindeki Simulation ve Movement/Physics veri akışı bölümleri uygulanan tick sırasını ve render sınırını yansıtacak şekilde güncellenmiştir. Belge, hedef mimari ile Aşama 10'da doğrulanmış sözleşmeyi birbirinden ayırır.

---

**Teknik karar özeti:** Mevcut DemoTickPump korunur. Yeni Pygame-bağımsız SimulationTickCoordinator, tick içindeki movement/physics → cell tracking → entity transform/spatial sync sırasını yönetir. Entity sync render snapshot içinden çıkarılır ve simülasyon tick'ine bağlanır. Render son tamamlanmış state'i salt-okunur biçimde görüntüler. NPC, kaynak ve yoldaş hareketi uygulanmaz.


## 12. Uygulama ve doğrulama kaydı

Uygulanan ana dosyalar:
- `src/hex_world_lab/simulation/tick_coordinator.py`
- `src/hex_world_lab/simulation/__init__.py`
- `src/hex_world_lab/application/movement_demo.py`
- `src/hex_world_lab/application/entity_demo.py`
- `tests/unit/test_simulation_tick_coordinator.py`
- `tests/integration/test_simulation_tick_flow.py`
- `tests/integration/test_entity_demo_render_purity.py`
- `tests/integration/test_entity_world_lifecycle.py`
- `benchmarks/benchmark_simulation_tick.py`
- `.github/workflows/hex-world-lab-ci.yml`

Gerçek tick sırası: Input → CollisionAwareMovementSystem (movement + collision) → MovementCellTracker → EntityWorldCoordinator callback (registry + spatial index) → tick completion. DemoTickPump 60 TPS, pump başına en fazla 8 tick ve zaman borcu koruma davranışını sürdürür.

Kod doğrulama commit'i: `d4ce6d8704aa46e0b327f539c72b9a9b0d350c2d`.

- Laboratuvar: 759 test başarılı.
- Core Quality Linux: 2.222 test başarılı; 1 adet `pkg_resources` deprecation uyarısı.
- Core Quality Windows: 2.222 test başarılı.
- Laboratuvar CI: run `44260997907`, başarılı.
- Core Quality: run `44260997901`, başarılı.
- Simülasyon tick ortalaması: 177.5944 µs/tick (120 tick'lik batch ortalaması 21.3113 ms; p95 22.7414 ms).
- Render snapshot ortalaması: 219.3906 µs/snapshot (120 snapshot'lık batch ortalaması 26.3269 ms; p95 26.5093 ms).
- Ölçüm ortamı: GitHub Actions Ubuntu, Python 3.12.16; üç ısınma ve yirmi ölçüm batch'i.
- Kullanıcı manuel görsel/işlevsel kabulü bekleniyor; bu nedenle aşama henüz resmen kapatılmış sayılmaz.
