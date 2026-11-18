# Aşama 12 — Teknik Uygulama ve Doğrulama Planı

> **Belge türü:** Ayrıntılı teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Dayanak:** Kullanıcı tarafından onaylanan `PHASE-12-GENERAL-PLAN.md`  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — PROCEDURAL ÇİZİM YÖNÜNDE REVİZE EDİLDİ  
> **Uygulama durumu:** 12.1–12.8 otomatik uygulama/doğrulama tamamlandı; manuel görsel kabul bekleniyor  
> **Tek laboratuvar başlatıcısı:** `python -m hex_world_lab`

---

## 1. Teknik hedef

Aşama 12, laboratuvarın mevcut hex dünya, render, anchor, fizik/çarpışma ve spatial altyapısını kullanarak görsel dosyasına bağımlı olmayan çevresel nesne sözleşmesi ve Pygame tabanlı prosedürel çizim altyapısı kuracaktır. Ağaç, kaya ve çalı görselleri hazır PNG/JPG dosyaları olarak sahneye yerleştirilmeyecek; Pygame çizim primitifleri ve deterministik geometri kullanılarak kodla üretilecektir.

İlk örnek ağaç olacaktır. Aynı sözleşmenin en az iki farklı çevresel nesne profiliyle (kaya ve çalı) doğrulanması hedeflenir. Nesneler bu aşamada sabit dünya yerleşimleridir; hareketli entity veya oynanış sistemi değildir.

Temel kabul ilkesi:

**Aynı nesne tanımının görsel dosyası değiştiğinde ground anchor, depth anchor, collider ve world placement verileri değişmeden kalabilmelidir.**

Bu belge teknik tasarımı ve önerilen dosya değişikliklerini tanımlar. Teknik planın onaylanması, ayrıca açıkça belirtilmedikçe uygulama izni anlamına gelmez.

## 2. Depo denetiminden çıkan teknik bulgular

İnceleme, Aşama 12 genel planının kaydedildiği `d2a49a8c4a3a554c7806f547435a752c97caf2f2` commit'i üzerindeki gerçek kaynak dosyalarına göre yapılmıştır.

### 2.1 Laboratuvarda mevcut olanlar

| Sorumluluk | Mevcut kaynak |
|---|---|
| Immutable render DTO'ları | `src/hex_world_lab/rendering/snapshot.py` |
| Sprite çizimi ve foot-anchor | `src/hex_world_lab/rendering/pygame_world_renderer.py` |
| Y-sort | Aynı renderer içindeki ortak draw queue |
| Kamera dönüşümü | `camera/WorldScreenTransform` |
| Görünür dünya bölgesi | `rendering/visibility.py` |
| Fiziksel şekiller | `physics/shapes.py` |
| Ground-anchor tabanlı fizik dönüşümü | `physics/body.py` |
| Harita kapsamlı statik engel | `physics/obstacle.py` |
| Engel spatial index | `physics/spatial_adapter.py` |
| Sürekli çarpışma | `simulation/collision_aware_movement_system.py` |
| Test sahnesi | `application/movement_demo.py`, `application/entity_demo.py` |

Mevcut `SpriteAsset` görsel yüzeyi ve normalize foot-anchor değerlerini taşır. `SpriteVisual` dünya ground-anchor noktasını ve ayrı `depth_anchor_y` değerini taşır. Renderer; sprite, daire, çokgen ve oyuncuyu aynı deterministik derinlik kuyruğunda sıralar.

Fizik tarafında `ObstacleDefinition`, `CircleShape` ve `ConvexPolygonShape` zaten görselden bağımsız statik çarpışma tanımlarını destekler. `MovementDemo` içindeki ağaç ve kaya engelleri bugün sabit engel olarak tanımlanmıştır. Bunların çarpışma davranışının korunması gerekir.

### 2.2 Ana oyun tarafında bulunan referanslar

Aynı depo dalında, laboratuvar dışında şu kaynaklar bulunmaktadır:

- `game_ui/world_rendering/tree_skeleton.py`: PNG'den bağımsız normalize ağaç iskeleti, gövde, dal ve yaprak kümesi geometrisi.
- `game_ui/world_rendering/tree_atlas.py`: Ağaç atlası ve manifest doğrulaması.
- `game_ui/world_rendering/tree_rig_renderer.py`: Katmanlı ağaç sprite çizimi.
- `game_ui/world_rendering/scene_object.py`: Görsel boyut, anchor, depth ve collision box sorumluluklarını ayıran sahne nesnesi modeli.
- `docs/architecture/40-tree-skeleton-contract.md` ve `43-articulated-tree-sprite-rig.md`: İlgili mimari sözleşmeler.
- `game_ui/assets/tree_test.png`, `tree_parts_atlas.png` ve `tree_parts_atlas.json`: Ağaç görsel verileri.

Bu kod ve dokümanlar **tasarım referansıdır**. Laboratuvar, `game_ui` Python modüllerini import etmeyecek; ana oyun runtime'ına bağımlı olmayacak ve bu aşamada ana oyun dosyalarını değiştirmeyecektir. Ağaç dallarının rüzgâr animasyonu ve katmanlı rig sistemi bu aşamanın zorunlu kapsamı değildir. İlk prototipte statik, tek sprite ağaç kullanılması önerilir.

### 2.3 Mevcut sınırlamalar

- Laboratuvarın `assets/` dizininde şu anda yalnızca `.gitkeep` bulunmaktadır.
- `SpriteVisual` depth anchor taşır ancak çevresel nesneye ait görsel/canopy bounds veya anchor debug verisi taşımaz.
- Renderer sprite çiziminde foot-anchor kullanır; sprite'lar için mevcut görünürlük culling'i ayrı ve açık bir sözleşme olarak tanımlanmamıştır.
- `MovementDemo` içindeki ağaç/kaya engelleri çarpışma geometrisine dahildir ve snapshot'ta temel daire/çokgen olarak gösterilir.
- Laboratuvarda çevresel nesne tanımı ve yerleşimini birleştiren ayrı bir domain paketi bulunmamaktadır.

Bu nedenle yeni mimari, var olan fizik ve render sistemlerini tekrar yazmak yerine bunlara ince adaptörler eklemelidir.

## 3. Onay için önerilen mimari kararlar

### 3.1 Katman ayrımı

Yeni `environment` paketi Pygame'den bağımsız olacaktır. Domain katmanı yalnızca veri ve geometri sözleşmelerini tanımlar. Pygame Surface yükleme/çizme işleri rendering katmanında kalır.

Önerilen paket:

```text
src/hex_world_lab/
  environment/
    __init__.py
    definition.py
    placement.py
    scene.py
    presentation.py
  rendering/
    snapshot.py
    pygame_world_renderer.py
```

### 3.2 Veri sözleşmeleri

**EnvironmentalObjectDefinition** — yeniden kullanılabilir nesne türü tanımı:

- `definition_id`: benzersiz, boş olmayan tür kimliği.
- `asset_key`: prosedürel çizim profilinin kararlı anahtarı; ör. `tree_oak`, `rock_gray`, `bush_green`. Bu anahtar bir PNG dosyasını zorunlu kılmaz.
- `ground_anchor`: sprite alanı içinde normalize edilmiş (x, y) nokta.
- `depth_anchor`: sprite alanı içinde normalize edilmiş (x, y) nokta.
- `canopy_bounds`: isteğe bağlı normalize dikdörtgen; görsel taç/üst alanını tanımlar.
- `collider`: isteğe bağlı, ground-anchor'a göre yerel dünya birimlerinde `CircleShape` veya `ConvexPolygonShape`.

**EnvironmentalObjectPlacement** — haritadaki tek örnek:

- `instance_id`: harita içindeki benzersiz örnek kimliği.
- `definition_id`: tanım referansı.
- `world_id` ve `map_id`: mevcut `WorldId` / `MapId` tipleri.
- `ground_position`: authoritative `WorldPoint`.
- Bu aşamada nesneler statik olacaktır; runtime hareket, dönüş veya ölçek düzenleme API'si eklenmeyecektir.

**EnvironmentalObjectScene** — bir test sahnesinin tanım ve yerleşim koleksiyonu:

- Tanım kimlikleri ve örnek kimlikleri kendi koleksiyonlarında benzersiz olmalıdır.
- Her placement geçerli bir definition'a başvurmalıdır.
- Tek bir scene yalnızca tek world/map kapsamına ait olmalıdır.
- Dışarıya deterministik, immutable sıralı tuple'lar sunmalıdır.
- Bilinmeyen tanım, yinelenen kimlik veya harita uyuşmazlığı erken ve açık hata üretmelidir.

Bu model; ana oyundaki `SceneObjectPlacement` / `SceneObject` yaklaşımının kavramsal sorumluluk ayrımından yararlanır ancak laboratuvarın kendi tiplerini ve `WorldPoint` / `WorldId` / `MapId` sözleşmelerini kullanır.

### 3.3 Anchor ve geometri kuralları

- **Ground Anchor:** Nesnenin dünyaya bağlandığı tek authoritative noktadır. Sprite'ın normalize görsel anchor'ı bu noktaya oturur.
- **Depth Anchor:** Y-sort için kullanılan ayrı referanstır. Sprite görselinden bağımsız metadata olarak tanımlanır; dünya Y değeri ground position ve sprite yüksekliğinden çözülür.
- **Visual Bounds:** Sprite ölçüsü ve ground anchor üzerinden türetilir. Yalnızca çizim/culling/debug içindir; çarpışma değildir.
- **Canopy Bounds:** Ağaç tacı gibi görsel üst bölgeyi belirtir. Çarpışma veya derinlik kararı vermez.
- **Collider:** Ground Anchor'a göre yerel dünya birimlerinde tanımlanır. PNG boyutundan, alfa sınırlarından veya canopy bounds'tan türetilmez.
- **World Placement:** Nesnenin harita ve dünya koordinatındaki konumudur; kamera dönüşümü bunu değiştiremez.

Normalize anchor/bounds değerleri sonlu ve [0, 1] aralığında olmalıdır. Dikdörtgen pozitif boyutlu olmalı ve normalize görsel alanın dışına taşmamalıdır. Collider koordinatları sonlu olmalı ve desteklenen mevcut fizik şekillerinden biri olmalıdır.

### 3.4 Fizik adaptörü

EnvironmentalObjectScene içindeki collider tanımları, mevcut `ObstacleDefinition` nesnelerine dönüştürülecektir:

- `obstacle_id`, çevresel nesne örneğinin kararlı kimliğinden türetilir.
- `map_id`, placement'ın map kimliğiyle aynı olmalıdır.
- `shape`, tanımdaki yerel collider olarak korunur.
- `position`, placement'ın ground position değeridir.

Böylece mevcut `build_hex_map_collision_geometry`, `CollisionAwareMovementSystem`, narrowphase ve continuous collision kodu kullanılmaya devam eder. Yeni bir collision solver veya paralel fizik sistemi oluşturulmaz.

Ağaç gövdesi için başlangıç collider'ı küçük bir daire veya ince convex polygon olabilir; kesin ölçüler teknik uygulamada mevcut oyuncu collider'ı ve ağaç görseliyle birlikte kalibre edilir. Kaya mevcut polygon engel profilini korur. Çalı, en az bir görsel-only/no-collider profili olarak kullanılarak collider'ın opsiyonel olduğu doğrulanır.

### 3.5 Render adaptörü ve derinlik

EnvironmentalObjectScene, immutable render DTO'larına dönüştürülür. Var olan ortak draw queue korunur:

- Çevresel nesneler `SpriteVisual` olarak snapshot'a eklenir.
- Depth anchor Y değeri sprite'ın ground anchor'ından bağımsız hesaplanır.
- Stable ID eşit depth durumunda deterministik ikincil sıralama sağlar.
- Oyuncu, NPC ve kaynak sprite'larıyla aynı Y-sort kuyruğu kullanılır.
- Render snapshot oluşturma veya çizim authoritative world/entity/physics state değiştirmez.

Anchor metadata'sının tanım katmanında kalması için gerekirse `SpriteVisual` DTO'suna geriye dönük uyumlu normalize sprite anchor alanları eklenecektir. Mevcut actor/NPC/resource sprite davranışı varsayılan değerlerle aynen korunmalıdır.

### 3.6 Görsel sınır ve culling

- Visual bounds, sprite'ın tam çizim dikdörtgenini temsil eder; yalnızca ground anchor noktasına göre culling yapılmaz.
- Kamera görünür bölgesiyle kesişmeyen çevresel sprite'lar çizilmez.
- Culling muhafazakâr olmalıdır: ekranda görünen taç/kenar parçaları yanlışlıkla atılmamalıdır.
- Culling, world position veya scene kayıtlarını değiştiremez.
- İlk prototipte asset ölçeği sabit tutulur; ölçekleme sistemi bu aşamada eklenmez.

### 3.7 Çarpışma görselleştirmesi

Çevresel nesnenin collider'ı normal çizimde temel daire/çokgen olarak görünmeyecek; nesnenin sprite'ı normal görünüm olacaktır. Collider, mevcut collider debug katmanında gösterilmeye devam eder.

Bunun için çevresel nesne obstacle kimlikleri ile environment sprite örnekleri arasında deterministik eşleme yapılır. Aynı obstacle hem sprite hem de debug collider olarak gösterilebilir; normal sahnede collider geometrisi ikinci bir görünür nesne gibi çizilmez.



### 3.8 Prosedürel çizim altyapısı — revize görsel karar

**Temel karar:** Ağaç, kaya, çalı ve ileride oyuncu/NPC gibi görsel öğeler için hazır raster görseli doğrudan sahneye koymak yerine, çizim kodu ile üretilen görsel yüzeyler kullanılacaktır. İlk uygulama Pygame `Surface` üzerine çizim yapan, oyun runtime'ından bağımsız bir renderer paketidir.

Önerilen ayrım:

```text
rendering/
  procedural/
    primitives.py       # yumuşatılmış çizgi, çokgen, elips, gölge yardımcıları
    palette.py          # nesne profillerine ait renk paletleri
    tree_renderer.py    # gövde, kök, dal, yaprak kümeleri
    rock_renderer.py    # çok yüzeyli kaya geometrisi
    bush_renderer.py    # yaprak kümeleri ve hacim
    registry.py         # profil anahtarı -> çizim fonksiyonu
```

- Çizim fonksiyonları deterministik olmalıdır: aynı profil ve parametreler aynı görünümü üretir.
- Çizim, yüksek çözünürlüklü şeffaf ara yüzeyde yapılıp hedef boyuta yumuşak ölçeklenebilir; böylece temel Pygame primitiflerinin sert/pikselli görünümü azaltılır.
- Ağaç; gövde/kök silueti, kalınlığı değişen dallar, farklı tonlarda üst üste binen yaprak kümeleri, ışık ve gölge katmanlarından oluşturulur. Dal eğrileri örneklenmiş Bézier benzeri eğrilerle çizilebilir.
- Kaya; tek düz çokgen yerine ana siluet, ışık alan yüzeyler, gölgeli yüzeyler ve ince kenar vurgularıyla hacim kazanır.
- Çalı; ayrı yaprak kümeleri, renk varyasyonu ve alt gölgeyle oluşturulur.
- Görsel geometri yalnızca sunumdur. Ground anchor, depth anchor, visual/canopy bounds ve collider hâlâ ayrı domain verileridir; çizim sonucu collider üretmez.
- Rastgelelik gerekiyorsa sabit seed veya tanım parametresi kullanılır; render çağrısı sırasında rastgele görünüm değişmez.
- İlk aşamada editör arayüzü yapılmaz. Bununla birlikte çizim fonksiyonları, paletler, geometri ve profil parametreleri ayrık tutulur; ileride Content Editor'ın aynı çizim API'sini parametrelerle çağırabilmesine uygun bir sözleşme korunur.
- Ana oyundaki `game_ui` modülleri import edilmez. Laboratuvar kendi prosedürel çizim sistemine sahip olur.
- Aşama 12'nin görsel kabulü; ağacın harita ölçeğine uygun, katmanlı ve stil bütünlüğü taşıyan bir çevresel nesne gibi görünmesini gerektirir. PNG'nin basitçe küçültülmesi kabul kriteri değildir.

## 4. Dosya bazlı değişiklik planı

Aşağıdaki liste hedeflenen değişiklik alanıdır; uygulama sırasında depo HEAD'i yeniden doğrulanacak ve gerçek kodla uyuşmayan dosya varsayımları uygulanmayacaktır.

### 4.1 Yeni domain dosyaları

| Dosya | Sorumluluk |
|---|---|
| `src/hex_world_lab/environment/definition.py` | Immutable EnvironmentalObjectDefinition ve alan doğrulamaları |
| `src/hex_world_lab/environment/placement.py` | Immutable EnvironmentalObjectPlacement |
| `src/hex_world_lab/environment/scene.py` | Definition/placement bütünlüğü, map kapsamı ve deterministik koleksiyon |
| `src/hex_world_lab/environment/presentation.py` | Environment nesnesinden SpriteVisual, ObstacleDefinition ve debug DTO dönüşümleri |
| `src/hex_world_lab/environment/__init__.py` | Açık public API |

### 4.2 Mevcut laboratuvar dosyaları

| Dosya | Planlanan değişiklik |
|---|---|
| `rendering/snapshot.py` | Gerekirse anchor override ve environment debug DTO alanları; eski kurucularla geriye uyum |
| `rendering/pygame_world_renderer.py` | Sprite anchor override, tam visual-bounds culling ve environment debug çizimi |
| `rendering/__init__.py` | Yeni DTO/export'ların açık dışa aktarımı |
| `application/movement_demo.py` | Mevcut ağaç/kaya sabit obstacle tanımlarını environment scene kaynaklı üretime bağlama; ev duvarlarını değiştirmeme |
| `application/entity_demo.py` | Environment sprite'larını ve debug DTO'larını mevcut snapshot'a ekleme; entity davranışlarını koruma |
| `app.py` | Yalnızca gerekli debug kısayolunu bağlama; tek başlatıcıyı ve mevcut F3 collider davranışını koruma |
| `tests/...` | Aşağıdaki birim, entegrasyon ve kabul testleri |

### 4.3 Asset kullanımı

İlk ağaç prototipi için depoda mevcut olan `content/demo_eldoria/assets/tree_test.png` statik görseli veri varlığı olarak değerlendirilecektir. Ana oyunun `game_ui` Python modülleri veya renderer sınıfları import edilmeyecektir.

Ağaç atlası ve articulated rig, teknik referans olarak kalır; Aşama 12'nin ilk kabul hedefi için katmanlı animasyon zorunlu değildir. Kaya ve çalı için ilk doğrulama görselleri laboratuvar içinde basit, deterministik Pygame yüzeyleriyle üretilebilir; bu placeholder görseller fizik geometrisinin kaynağı olamaz.

Asset yolu uygulamada çalışma dizinine körlemesine bağlanmayacak; laboratuvarın tek launcher'ı ve CI çalışma diziniyle uyumlu, açıkça test edilen bir asset-root çözümü kullanılacaktır. Eksik/bozuk zorunlu ağaç görseli sessizce farklı bir asset'e dönüştürülmeyecek; anlaşılır hata üretilecektir.

## 5. Test ve doğrulama planı

### 5.1 Birim testleri

Yeni test dosyaları:

- `tests/unit/test_environment_object_definition.py`
- `tests/unit/test_environment_object_placement.py`
- `tests/unit/test_environment_object_scene.py`
- `tests/unit/test_environment_object_presentation.py`

Test edilecek invariant'lar:

1. Boş/tekrarlı kimlik, bozuk anchor, NaN/sonsuz değer, normalize alan dışına taşan bounds ve geçersiz collider reddedilir.
2. Definition ve placement immutable davranır.
3. Placement yanlış world/map veya olmayan definition'a bağlanamaz.
4. Scene sıralaması giriş sırasından bağımsız ve deterministiktir.
5. Görsel anchor ve depth anchor birbirinden bağımsızdır.
6. Görsel boyut veya asset değişimi collider geometrisini değiştirmez.
7. Collider'sız nesne geçerli biçimde temsil edilebilir.
8. Collider dönüşümü mevcut ObstacleDefinition ile birebir uyumludur.

### 5.2 Render testleri

- Ground anchor, sprite'ın normalize anchor noktasına tam oturur.
- Depth anchor'a göre ağaç oyuncunun önünde/arkasında doğru sıralanır.
- Eşit depth değerlerinde stable ID sıralaması deterministiktir.
- Görsel sınırın bir kısmı viewport'ta kaldığında sprite çizilir.
- Tamamen viewport dışında kalan sprite culling edilir.
- Zoom ve kamera hareketi anchor/geometry ilişkisini bozmaz.
- Render snapshot ve renderer authoritative simulation state'i değiştirmez.
- Mevcut actor, NPC, resource sprite testleri geriye dönük geçer.

### 5.3 Fizik ve entegrasyon testleri

- Ağaç collider'ı oyuncuyu gövde bölgesinde durdurur.
- Ağaç tacının görsel alanı tek başına çarpışma oluşturmaz.
- Kaya polygon collider'ı mevcut continuous collision davranışıyla çalışır.
- Çalı gibi collider'sız nesne oyuncu hareketini engellemez.
- Collider debug overlay gerçek world collider geometrisiyle eşleşir.
- Kamera zoom/offset değişikliği çarpışma sonucunu değiştirmez.
- Çevresel nesne obstacle ID'leri benzersiz ve map-scoped kalır.
- Eski house wall, hex boundary ve mevcut obstacle regresyonları korunur.

### 5.4 Kabul sahnesi

Laboratuvarın tek başlatıcısıyla açılan mevcut test sahnesine şu statik nesneler eklenir:

- En az bir ağaç.
- En az bir kaya.
- En az bir çalı.
- Oyuncu ve mevcut NPC/resource örnekleri.

Sahne şu durumları görsel olarak gösterebilmelidir:

- Oyuncunun ağacın önünden geçmesi.
- Oyuncunun ağacın arkasından geçmesi.
- Ağacın gövdesi ile taç alanının görsel olarak ayrılması.
- Kaya çarpışması ve çalının çarpışmasız olması.
- F3 collider debug görünümü.
- Yeni environment debug görünümünde ground anchor, depth anchor, visual bounds ve canopy bounds.

Önerilen debug kısayolu F4'tür. Mevcut F3 davranışı değiştirilmez. Debug overlay kapalıyken normal oyun görünümünde yardımcı çizgiler görünmez.

## 6. Performans ve regresyon ölçümleri

- Var olan Aşama 11 tick, render snapshot ve spatial benchmarkları tekrar çalıştırılır.
- Çevresel nesne sayısı için 10 / 100 / 1.000 instance profilleri eklenir.
- Snapshot üretim maliyeti, render süresi ve görünür/elenen sprite sayısı ölçülür.
- Culling açık/kapalı karşılaştırması aynı deterministik sahnede yapılır.
- Collider'ların mevcut broadphase/narrowphase yoluna etkisi raporlanır.
- En az üç bağımsız ölçüm oturumu alınır; medyan, P95 ve P99 raporlanır.
- Ölçüm sonuçları donanım/runner bilgisiyle sunulur; Aşama 11 değerleri mutlak eşik olarak kullanılmaz.

Performans testi, gereksiz genel amaçlı ECS, yeni spatial index veya ayrı render batching sistemi eklemek için gerekçe sayılmaz. Darboğaz ölçülmeden mimari genişletilmez.

## 7. Aşama 12 iş paketlerinin teknik karşılığı

### 12.1 — Mevcut altyapı denetimi
Bu teknik planın kaynak incelemesi başlangıç denetimidir. Uygulama öncesinde HEAD değişmişse ilgili dosyalar yeniden okunur; mevcut testler ve asset path davranışı yerel CI gerçekliğiyle teyit edilir.

### 12.2 — Ortak nesne sözleşmesi
Environment domain tipleri, doğrulamalar, immutable scene koleksiyonu ve physics/render adaptörleri eklenir. Pygame import sınırı test edilir.

### 12.3 — Ağaç prototipi
Mevcut statik ağaç görseli veri varlığı olarak yüklenir. Ground/depth anchor, canopy bounds ve gövde collider'ı tanımlanır. İlk görsel hizalama testleri hazırlanır. Rüzgâr animasyonu ve articulated rig zorunlu değildir.

### 12.4 — Depth sorting
Ağaç, kaya, çalı, oyuncu ve mevcut entity sprite'ları ortak draw queue'da test edilir. Y-sort ground/depth anchor kullanır; sprite'ın üst kenarı veya görsel merkezinden sıralama yapılmaz.

### 12.5 — Çarpışma ayrımı
Tree trunk ve rock collider'ları mevcut ObstacleDefinition yoluna bağlanır. Canopy/visual bounds collider'a dönüştürülmez. Mevcut hareket ve çarpışma API'si korunur.

### 12.6 — Genişletilebilirlik
Kaya ve çalı profilleri aynı definition/placement/scene sözleşmesini kullanır. Tür başına renderer veya fizik alt sınıfı oluşturulmaz.

### 12.7 — Debug
F4 ile anchor, depth line, visual/canopy bounds çizilir. F3 collider debug bağımsız ve geriye uyumlu kalır.

### 12.8 — Bütünleşik doğrulama
Birim, entegrasyon, kabul ve stres testleri; benchmark; Linux/Windows Core Quality; Laboratuvar CI; görsel manuel kabul ve kapanış raporu tamamlanır.

## 8. Kapsam ve mimari koruma kuralları

- Yalnızca `experiment/hex-world-laboratory` dalı değiştirilebilir.
- `main` ve `demo_eldoria` dallarına yazılmaz; merge yapılmaz.
- Ana oyunun `game_ui` runtime kodu laboratuvara bağımlılık yapılmaz.
- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak kalır.
- NPC, kaynak ve yoldaş hareketi eklenmez.
- Companion FOLLOW/WAIT/RETURN yalnızca mevcut komut niyeti olarak kalır.
- Pathfinding, A*, Dijkstra, click-to-move, AI, gathering/economy, combat, quest ve dialogue eklenmez.
- Godot geçişi ve ana oyuna entegrasyon yapılmaz.
- Save/persistence şeması bu aşamada değiştirilmez.
- Yeni generic abstraction yalnızca en az üç profilin gerçek ortak ihtiyacıyla gerekçelendirilir.
- Render ve debug katmanı authoritative simulation state'i değiştiremez.

## 9. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Görsel ölçüler fizik davranışını belirler | Collider ayrı yerel dünya geometrisi olarak tanımlanır |
| Ground anchor ve depth anchor karışır | Ayrı alanlar ve bağımsız testler |
| Ağaç tacı oyuncuyu engeller | Yalnızca trunk collider fizik otoritesidir |
| Sprite culling kenarları keser | Tam visual bounds ve muhafazakâr kesişim |
| Mevcut Y-sort bozulur | Ortak draw queue ve actor/entity regresyon testleri |
| Main-game modülleri lab'a sızar | Pygame bağımsız domain testi ve import sınırı |
| Asset yolu CI'da bozulur | Launcher-root ve CI ortamında asset loading testi |
| Mevcut obstacle'lar iki kez çizilir | Environment obstacle ID ↔ sprite eşlemesi; normal/debug çizim ayrımı |
| Aşırı mimari büyüme | Üç nesne profiliyle sınırlı, statik ve persistence'sız ilk sürüm |

## 10. Beklenen teslimatlar

1. `environment` domain paketi ve public API.
2. Ağaç/kaya/çalı örneklerini içeren deterministik kabul sahnesi.
3. Sprite anchor, depth sorting ve bounds culling entegrasyonu.
4. Görsel ve fizik geometrisi ayrımının doğrulanması.
5. F3 collider ve F4 environment debug overlay.
6. Birim, entegrasyon, kabul ve performans testleri.
7. Linux/Windows CI sonuçları ve benchmark artifact'leri.
8. `reports/PHASE-12-CLOSURE-REPORT.md`.
9. `docs/PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md`.

## 11. Kabul ölçütleri

Aşama 12 ancak aşağıdaki koşulların tamamı sağlandığında kapatılabilir:

- Üç farklı çevresel nesne profili aynı ortak sözleşmeyle temsil edilir.
- Asset değişimi world placement, ground/depth anchor ve collider verisini değiştirmez.
- Ağaç gövdesi çarpışır; canopy tek başına çarpışmaz.
- Kaya collider'ı doğru çalışır; collider'sız çalı hareketi engellemez.
- Y-sort oyuncu ve çevresel nesneler arasında doğru ve deterministiktir.
- Visual bounds culling false-negative üretmez.
- Debug overlay tüm anchor/bounds/collider alanlarını doğru gösterir.
- Render/snapshot authoritative state'i değiştirmez.
- Mevcut laboratuvar testleri ve yeni testler geçer.
- Linux ve Windows CI başarılıdır.
- Performans sonuçları raporlanır ve kabul edilebilir regresyon bulunmaz.
- Kullanıcı manuel görsel kabul kontrollerini tamamlar.
- Kapanış raporu ve ana plan bağlantıları güncellenir.

## 12. Onay kapısı

Bu belge kullanıcı tarafından teknik olarak onaylanmış ve uygulama için ayrıca açık talimat verilmiştir. 12.1–12.8 uygulaması, otomatik testler, üç oturumlu performans ölçümleri, görsel kanıt üretimi ve Linux/Windows CI tamamlanmıştır. Aşama 12'nin resmen kapatılması için kullanıcı manuel görsel kabul kontrol listesini tamamlamalıdır. Herhangi bir kapsam değişikliği veya ana mimari sözleşmeden sapma önce raporlanır ve onaylanır.

---

**Sonuç:** Aşama 12, mevcut render ve fizik sistemlerini yeniden yazmadan; görsel, anchor, derinlik, collider ve dünya yerleşimini açık veri sözleşmeleriyle ayıran küçük ve test edilebilir bir çevresel nesne katmanı kuracaktır.
