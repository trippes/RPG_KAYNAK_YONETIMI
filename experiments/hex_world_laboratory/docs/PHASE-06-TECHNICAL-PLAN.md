# Aşama 6 — Kamera ve Dünya-Ekran Dönüşümü Teknik Mimari Planı

> Belge türü: Ayrıntılı teknik mimari, API sözleşmeleri, bağımlılık şeması ve uygulama/test planı  
> Proje: Eldoria — Hex World Laboratory  
> Çalışma dalı: `experiment/hex-world-laboratory`  
> Durum: TEKNİK TASARIM HAZIR — 6.1 UYGULAMASI BAŞLATILABİLİR  
> Tarih: 17 Kasım 2026  
> Ön koşullar: Aşama 0–5 kapalı; Aşama 6 genel planı kullanıcı tarafından onaylandı.  
> Kod durumu: Bu belge tek başına kod değişikliği içermez.

---

## 1. Teknik hedef ve temel karar

Aşama 6, mevcut sürekli dünya koordinatları ile Pygame viewport'u arasına Pygame bağımsız bir kamera katmanı ekler. Dünya ve fizik sistemleri `WorldPoint` ile çalışmayı sürdürür. Kamera, dünya noktasının ekranda nerede çizileceğini hesaplar; bu dönüşüm simülasyon state'ine geri yazılmaz.

Temel dönüşüm:

- Dünya x ekseni sağa, dünya y ekseni yukarıdır.
- Ekran x ekseni sağa, ekran y ekseni aşağıdır.
- Kamera merkezi `C=(cx, cy)`, viewport boyutu `W×H`, zoom `z>0) olsun.
- Dünya → ekran:
  - `sx = W/2 + (wx - cx) * z`
  - `sy = H/2 - (wy - cy) * z`
- Ekran → dünya:
  - `wx = cx + (sx - W/2) / z`
  - `wy = cy - (sy - H/2) / z`

Y ekseni ters çevrimi yalnızca bu dönüşüm katmanında yapılır. Renderer içinde ikinci bir y-tersleme veya bağımsız kamera hesabı bulunmaz.

İlk sürümde zoom viewport merkezine göre uygulanır; fare imlecinin altındaki dünya noktasını sabit tutan cursor-anchored zoom kapsam dışıdır. Fare tekerleği her adımda zoom'u çarpanla artırır/azaltır.

## 2. Mevcut kod tabanından doğrulanan sözleşmeler

İncelenen mevcut dosyalar:

| Dosya/API | Mevcut sözleşme | Aşama 6 kararı |
|---|---|---|
| `geometry/coordinates.py — WorldPoint` | Immutable, sonlu x/y dünya noktası | Yetkili dünya koordinatı olarak korunur |
| `geometry/coordinates.py — AxialCoord` | Integer q/r hücre adresi | Yalnızca hücre seçimi/topoloji için kullanılır |
| `geometry/layout.py — HexLayout` | Yönelim, circumradius, world origin | Hücre geometrisinin kaynağı |
| `geometry/transforms.py — world_to_axial` | Dünya noktasını mevcut deterministik tie-break ile hücreye çözer | Mouse picking doğrudan bunu çağırır |
| `geometry/polygon.py — hex_polygon` | Hücre köşelerini dünya koordinatında üretir | Render öncesi kamera dönüşümünden geçirilir |
| `movement/state.py — MovementState` | WorldPoint konumu ve hız | Kamera hiçbir alanını değiştiremez |
| `physics` | WorldPoint/world geometry collider'ları | Zoom ve viewport collider verisini etkilemez |
| `application/movement_demo.py` | Sabit merkezli Pygame çizimi, simülasyon orkestrasyonu | Tek dönüşüm kaynağına geçirilecek |
| `application/demo_tick_pump.py` | Sabit 60 TPS tick pompası | Kamera güncellemesi tick pompasına bağlanmaz |
| `tests/unit/test_architecture_boundaries.py` | Geometry/world/movement/physics/simulation Pygame bağımsızlığını korur | Camera da Pygame bağımsız kalır |

Mevcut `geometry/transforms.py` axial/world dönüşümünü zaten sağlar. Aşama 6 bu matematiği kopyalamaz veya değiştirmez.

## 3. Paket ve dosya mimarisi

Yeni/etkilenecek dosyalar:

| Dosya | Sorumluluk |
|---|---|
| `src/hex_world_lab/camera/coordinates.py` | Immutable `ScreenPoint` ve pozitif boyutlu `Viewport` değer nesneleri |
| `src/hex_world_lab/camera/state.py` | Immutable `CameraState`: dünya merkezi ve zoom |
| `src/hex_world_lab/camera/transform.py` | World↔screen dönüşümleri; tek y-ekseni tersleme noktası |
| `src/hex_world_lab/camera/bounds.py` | Dünya AABB sınırları ve viewport-aware kamera merkezi kısıtlaması |
| `src/hex_world_lab/camera/follow.py` | Render delta-time kullanan frame-rate bağımsız takip |
| `src/hex_world_lab/camera/controller.py` | Camera state, viewport, zoom, takip ve bounds orkestrasyonu |
| `src/hex_world_lab/camera/__init__.py` | Desteklenen kamera API dışa aktarımları |
| `src/hex_world_lab/rendering/pygame_world_renderer.py` | Kamera dönüşümü kullanan dünya çizim adaptörü; Pygame bağımlılığı burada kalır |
| `application/movement_demo.py` | Kamera controller, fare seçimi, wheel/resize event ve renderer entegrasyonu |
| `tests/unit/test_camera_*.py` | Kamera çekirdeği birim testleri |
| `tests/integration/test_movement_demo_camera.py` | Demo, render, input ve simülasyon izolasyonu testleri |

Uygulama alt aşamalara göre dar kapsamlı commit'lerle ilerler. Her alt aşamada dosya ağacı ve hedef SHA yeniden doğrulanır; tabloda bulunmayan kapsamlı değişiklikler gerekirse önce etki analizi yapılır.

## 4. API sözleşmeleri

### 4.1 Değer nesneleri

- `ScreenPoint(x: float, y: float)`: viewport içindeki piksel koordinatı; sonlu değer kabul eder.
- `Viewport(width: int, height: int)`: pozitif tam piksel boyutları; bool ve sıfır/negatif değer reddedilir.
- `CameraState(center: WorldPoint, zoom: float = 1.0)`: immutable kamera snapshot'ı; zoom sonlu ve pozitif olmalıdır.
- `WorldBounds(min_x, min_y, max_x, max_y)`: sonlu ve sıralı dünya AABB'si.

Tüm değer nesneleri Pygame import etmez. Ekran koordinatı için `pygame.Vector2` kullanılmaz.

### 4.2 Dönüşüm API'si

`WorldScreenTransform(viewport: Viewport, camera: CameraState)`

- `world_to_screen(point: WorldPoint) -> ScreenPoint`
- `screen_to_world(point: ScreenPoint) -> WorldPoint`

Dönüşümler saf fonksiyondur; girdi nesnelerini değiştirmez. Round-trip testi, kayan nokta toleransı ile `screen_to_world(world_to_screen(p)) ≈ p` koşulunu doğrular.

### 4.3 Kamera controller API'si

`CameraController(viewport, initial_state, zoom_limits, follow_settings, bounds_policy)`

- `resize(viewport) -> None`
- `set_zoom(value) -> None`
- `zoom_by(factor) -> None`
- `set_target(point: WorldPoint | None) -> None`
- `update(delta_seconds: float) -> CameraState`
- `world_to_screen(point) -> ScreenPoint`
- `screen_to_world(point) -> WorldPoint`

Controller kamera state'ini yönetir; MovementState'e veya world runtime'a referans tutmaz. Hedef noktası uygulama katmanından salt okunur snapshot olarak verilir.

### 4.4 Fareyle hücre seçimi

Uygulama adaptörü sırasıyla:
1. Pygame event konumunu `ScreenPoint` olarak alır.
2. Controller'ın `screen_to_world` metodunu çağırır.
3. Sonucu mevcut `world_to_axial(world_point, layout, previous_cell)` fonksiyonuna verir.
4. Seçilen `AxialCoord` yalnızca UI/diagnostic seçim state'inde tutulur.

Harita dışında kalan nokta için `world_to_axial` yine geometrik bir axial adres döndürebilir; uygulama bu adresi aktif `HexMapDefinition.cells` içinde arar. Hücre yoksa seçim `None` olur. Böylece açık dünya hareket politikası, haritada bulunmayan hücreleri varmış gibi seçmez.

## 5. Kamera davranış kararları

### 5.1 İlk zoom aralığı ve input

- Başlangıç zoom: `1.0`.
- İlk güvenli aralık: `0.5–3.0`.
- Fare tekerleği yukarı: `zoom *= 1.1`.
- Fare tekerleği aşağı: `zoom /= 1.1`.
- Sonuç her zaman min/max aralığına clamp edilir.
- Zoom viewport merkezine sabitlenir; oyuncu WorldPoint'i, collider ve dünya geometrisi değişmez.

Bu aralık ilk laboratuvar kabulü içindir; görsel testte kullanılabilirlik sorunu çıkarsa değerler ayrı gerekçeyle güncellenir.

### 5.2 Oyuncu takibi

- Takip hedefi her render frame'inde mevcut oyuncu `WorldPoint` snapshot'ıdır.
- Takip simülasyon tick'ini ilerletmez ve MovementSystem çağırmaz.
- Yumuşatma üstel yaklaşım kullanır: `alpha = 1 - exp(-lambda * dt)`; yeni merkez `current + (target-current)*alpha`.
- Varsayılan takip katsayısı `lambda = 8.0 s⁻¹).
- `dt` negatif/sonlu değilse reddedilir; çok büyük frame aralıklarında `dt` güvenli üst sınıra alınır.
- Takip hedefi yoksa kamera bulunduğu yerde kalır.

### 5.3 Kamera sınırları

- Kamera sınırı, dünya sınırından bağımsız bir sunum politikasıdır.
- Harita bounds, yalnızca yüklü haritanın mevcut hücrelerinin `hex_polygon` köşelerinden world AABB hesaplanarak üretilir; axial q/r min-max yaklaşımı kullanılmaz.
- Kamera clamp'i viewport'un dünya uzayındaki yarı genişlik/yüksekliğini dikkate alır: `half_width = viewport.width/(2*zoom)`, `half_height = viewport.height/(2*zoom)`.
- Bounds viewport'tan küçükse ilgili eksende merkez bounds orta noktasına alınır; ters min/max clamp uygulanmaz.
- Kamera sınır politikası `CLAMP_TO_MAP` veya `UNBOUNDED` olur.
- OPEN/BLOCKED fizik sınır politikası değiştirilmez ve kamera politikasından türetilmez.
- İlk demo varsayılanı `CLAMP_TO_MAP`; unbounded politika test edilebilir ve ileride açık dünya senaryosunda kullanılabilir.

## 6. Render entegrasyonu

- Renderer, `WorldScreenTransform` veya controller'ın dönüşüm API'sini alır.
- Her dünya noktası aynı `world_to_screen` metodundan geçer: hex köşeleri, engel daire merkezleri, polygon köşeleri, ev çizgileri, boundary çizgileri ve oyuncu.
- Daire yarıçapları/çizgi kalınlıkları da zoom ile görsel olarak ölçeklenir; collider geometrisi ölçeklenmez. Piksel çizgi kalınlıkları en az 1 piksel kalır.
- Pencere UI/diagnostic paneli ekran uzayında kalır ve kamera zoom'undan etkilenmez.
- Render yalnızca snapshot okur; MovementState, world runtime, collision geometry veya tick pump üzerinde yazma yapamaz.
- Renderer modülü Pygame import edebilir; camera/geometry/world/movement/physics import edemez.

## 7. Bağımlılık şeması

```text
geometry ───────────────┐
world ──────────────────┤
movement / physics ─────┤   (camera bunlara bağımlı değildir)
                        ▼
application ───────► camera (pure Python)
      │                 │
      └──────────────┬──┘
                     ▼
             rendering (Pygame)
                     ▼
              pygame Surface
```

Bağımlılık yönü:
- Camera yalnızca geometry'nin `WorldPoint` değer nesnesini kullanabilir; world, movement, physics veya Pygame'e bağımlı olamaz.
- Rendering camera ve Pygame'e bağımlı olabilir; simülasyon paketlerine yazma veya doğrudan state sahipliği yoktur.
- Application tüm adaptörleri birleştirir ve simülasyon tick pompasının tek sahibi olmaya devam eder.
- Geometry/world/movement/physics/simulation katmanları camera veya rendering import etmez.

## 8. Alt aşama uygulama sırası ve kapıları

| Alt aşama | Uygulama çıktısı | Zorunlu test kapısı |
|---|---|---|
| 6.1 | ScreenPoint, Viewport ve dönüşüm sözleşmesi; world↔screen matematiği | Değer doğrulama, bilinen örnekler, round-trip, y yönü |
| 6.2 | CameraState, controller, zoom limitleri ve viewport resize | Zoom clamp, geçersiz değer, resize, dönüşüm |
| 6.3 | WorldBounds, map bounds, takip ve clamp/unbounded politikaları | dt bağımsızlığı, bounds küçük/büyük viewport, OPEN/BLOCKED ayrımı |
| 6.4 | Pygame renderer ve fare picking/event entegrasyonu | Tüm çizimlerin hizası, iki hex yönelimi, seçili/boş hücre, render state değişmezliği |
| 6.5 | Tam regresyon, manuel kabul ve CI | Aşama 0–5 tam testleri, Linux/Windows CI, masaüstü kontrol listesi |

Her alt aşama sonunda:
1. hedef dosyaların ve dal HEAD'inin güncel SHA'sı doğrulanır;
2. yalnızca ilgili alt aşamanın kodu ve testleri değiştirilir;
3. test sonuçları kaydedilir;
4. kullanıcıya yerel test komutu ve beklenen sonuç verilir;
5. kullanıcı yerel testleri doğrulamadan sonraki riskli entegrasyon adımına geçilmez.

## 9. Test matrisi

### Birim
- ScreenPoint sonlu değer; Viewport pozitif integer doğrulaması.
- Kamera zoom ve center doğrulaması.
- Her iki dönüşüm yönünde round-trip.
- Dünya merkezi viewport merkezine eşlenir.
- Pozitif dünya y ekran y değerini azaltır.
- Zoom 0.5 ve 3.0 sınırları; sınır dışı zoom clamp.
- Resize sonrası aynı world point yeni viewport merkezine göre doğru hesaplanır.
- Takip farklı frame sürelerinde aynı elapsed time sonunda tolerans dahilinde aynı sonuca yaklaşır.
- Bounds clamp, haritadan küçük viewport, haritadan büyük viewport ve unbounded politika.

### Entegrasyon/regresyon
- Render kamera dönüşümünü kullanır ve simülasyon snapshot'ını değiştirmez.
- Zoom, oyuncu WorldPoint/collider/running speed değerlerini değiştirmez.
- Kamera update tick sayısını değiştirmez; tick rate 60 TPS kalır.
- Hex, obstacle, house, boundary ve actor aynı dönüşümü kullanır.
- Mouse picking kamera pan/zoom/resize sonrası doğru hücreyi bulur.
- Flat-top ve pointy-top yönelimleri desteklenir.
- Harita dışındaki axial adres UI seçiminde geçerli hücre sayılmaz.
- Pencere lifecycle ve mevcut klavye hareket testleri korunur.
- Tüm Aşama 0–5 testleri çalıştırılır.

### Masaüstü kabul
1. Pencere açılış/kapanış.
2. Oyuncu takibi ve yumuşak hareket.
3. Yakınlaştırma/uzaklaştırma sınırları.
4. Fareyle hücre seçimi ve boş alan davranışı.
5. Pencere yeniden boyutlandırma.
6. Harita sınırında kamera clamp davranışı.
7. Oyuncu, hücreler, ağaç, kaya, duvar ve ev hizası.
8. Hareket/çarpışma ve 60 TPS'nin değişmediği.
9. UI tanı panelinin zoom'dan bağımsız kaldığı.

## 10. Kapsam dışı ve riskler

Kapsam dışı: cursor-anchored zoom, kamera rotasyonu, y-sort/depth/occlusion, ışık/gölge/shader/particles, sprite animasyonları, map editor, pathfinding/NPC, ana oyun veya demo_eldoria entegrasyonu, Godot geçişi.

Başlıca riskler:
- Eksen terslemesinin birden fazla yerde yapılması: tek dönüşüm sınıfı ve bilinen koordinat testleriyle önlenir.
- Bounds'un axial q/r aralığından çıkarılması: gerçek hex polygon köşelerinden AABB hesaplanır.
- Zoom'un fiziksel ölçülere sızması: collider ve hareket verileri world-space'te kalır.
- Render frame'inin simülasyon tick'ine bağlanması: kamera update render delta-time alır, tick pump'tan ayrıdır.
- Renderer'ın simülasyon state'ini değiştirmesi: render purity regresyon testleri korunur.

## 11. Aşama 6 kapanış koşulları

Genel plandaki kapanış koşulları aynen geçerlidir. Ayrıca teknik kabul için:
- Camera API'si Pygame bağımsız olmalı.
- Tüm render edilen dünya geometrisi aynı dönüşümden geçmeli.
- Fare picking mevcut geometry tie-break davranışını korumalı.
- Test sonuçları ve CI run kimlikleri kapanış raporunda belirtilmeli.
- Yerel test ve masaüstü kabul sonuçları yalnızca kullanıcı bildirimine dayalıysa bu şekilde etiketlenmeli.

---

Bu belge teknik tasarımın ve alt aşama uygulama kapılarının referansıdır. Uygulama 6.1'den başlar; 6.1 testleri geçmeden 6.2'ye geçilmez.
