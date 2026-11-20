# Eldoria — Ana Oyun Mimarisi ve Entegrasyon Sözleşmesi

> **Belge türü:** Bağlayıcı mimari referans / teknik sözleşme  
> **Proje:** Eldoria — RPG Kaynak Yönetimi  
> **Hedef dal:** `experiment/map-cleanup`  
> **Belge yolu:** `docs/architecture/60-eldoria-main-game-architecture-contract.md`  
> **Durum:** KABUL EDİLMİŞ MİMARİ REFERANS — uygulama öncesi teknik kapı  
> **Hazırlanma tarihi:** 20 Kasım 2026  
> **Uygulama durumu:** Bu belge tek başına hiçbir özelliğin uygulanmış veya testlerden geçmiş olduğunu göstermez.

---

## 0. Belgenin bağlayıcılığı ve kullanım şekli

Bu belge, Eldoria'nın karakter oluşturma sonrasında çalışan ana oyun dünyasının mimarisini, sistem sahipliklerini, entegrasyon sınırlarını ve kabul ölçütlerini tanımlar. Bundan sonraki ana oyun geliştirme çalışmalarında kararlar bu sözleşmeye göre verilir.

Belge; eski laboratuvar entegrasyon taslaklarının, tarihsel faz planlarının veya geçici teknik notların otomatik devamı değildir. Çelişki halinde bu belgede tanımlanan güncel kararlar esas alınır. Eski belgeler tarihçe ve teknik kanıt olarak korunabilir; ancak bu sözleşmenin yerine geçmez.

### 0.1. Normatif terimler

- **MUST / ZORUNLU:** Uygulama bu koşulu sağlamadan kabul edilemez.
- **MUST NOT / YASAK:** Bu davranış mimari ihlaldir.
- **SHOULD / ÖNERİLEN:** Güçlü varsayılan karardır; istisna gerekçelendirilmelidir.
- **MAY / İSTEĞE BAĞLI:** İhtiyaç halinde uygulanabilir.
- **Mevcut:** İncelenen temizlik dalında bulunduğu gözlemlenen davranış veya altyapı.
- **Hedef:** Bu sözleşmeyle kararlaştırılan, henüz uygulanmamış veya tamamlandığı kanıtlanmamış davranış.
- **Doğrulanmadı:** Kaynak kodu veya test sonucu ile kanıtlanmamış durum.

Bir modülün laboratuvar dalında bulunması, onun temizlik dalında mevcut olduğu veya ana oyuna entegre edildiği anlamına gelmez. Kod varlığı, çalışma zamanı entegrasyonu ve kabul testi üç ayrı kanıttır.

### 0.2. Değişiklik yönetimi

Bu sözleşmeyi değiştiren her mimari karar:
1. Değişikliğin gerekçesini ve etkilediği sistemleri açıklamalı,
2. Veri sahipliği ve bağımlılık yönünü yeniden değerlendirmeli,
3. Kayıt uyumluluğu ve eski kayıt etkisini belirtmeli,
4. İlgili test ve kabul maddelerini güncellemeli,
5. Belgenin karar geçmişine tarih ve kısa açıklama olarak eklenmelidir.

Bir uygulama PR'ı/commit'i sözleşmeyi sessizce değiştiremez. Mimari değişiklik önce belgede karara bağlanır, sonra kodlanır.

---

## 1. Ürün hedefi ve görsel/oynanış vizyonu

### 1.1. Ana hedef

Karakter oluşturma ekranı tamamlandıktan sonra oyuncu, Eldoria'nın sürekli görünür ana dünya yüzeyine girer. Bu yüzey; Diablo II ve Baldur's Gate II çizgisinde, yukarıdan eğimli/izometrik algı veren, derinlik sıralaması bulunan, çevresel nesnelerle yaşayan bir 2.5D RPG dünyası olmalıdır.

Dünya, karakter veya envanter ekranı açıldığında kaybolmamalıdır. Karakter, envanter, görev, harita, üretim, pazar ve benzeri arayüzler ana dünyanın üzerinde açılan taşınabilir pencereler olarak çalışır.

Görsel hedef yalnızca zemini elmas biçimli çizmek değildir. Oyuncu; araziyi, ağaç gövdelerini ve taçlarını, kayaları, çalıları, kaynakları, NPC'leri, yapıları, gölgeleri ve etkileşim işaretlerini ortak bir dünya koordinatında algılamalıdır. Nesnelerin birbirinin önüne/arkasına geçmesi, oyuncunun ağaç arkasında kalması ve çevresel nesnelerin zemine oturması tutarlı olmalıdır.

### 1.2. Ürün ilkeleri

1. Dünya, ana oyun ekranının kalıcı görsel ve etkileşim yüzeyidir.
2. Oyun simülasyonu, dünya verisi ve çizim birbirinden ayrıdır.
3. Tek bir oyun olgusunun tek bir yetkili veri sahibi bulunur.
4. Klavye hareketi ve fareyle hedefe hareket aynı hareket/fizik otoritesine bağlanır.
5. NPC, kaynak, sandık, kapı ve çevresel dekor aynı şey değildir; davranış ve sahiplikleri ayrılır.
6. Görsel boyut, zemin temas noktası, derinlik alanı ve fizik çarpıştırıcısı ayrı kavramlardır.
7. Ana oyun düşük donanımda çalışabilir kalmalıdır. Gereksiz sürekli hesaplama, büyük yüzey kopyaları ve sınırsız entity taraması yapılmaz.
8. Kaydet/yükle yalnızca görünen ekranı değil, tutarlı oyun durumunu saklar.
9. Yeni içerik eklemek için mümkün olduğunca Python kodu değil, doğrulanan içerik tanımı ve asset kaydı kullanılır.
10. Pygame mevcut ana çalışma ortamıdır. Godot'a geçiş bu sözleşmenin varsayımı değildir.

### 1.3. Kapsam dışı

Bu sözleşme aşağıdakileri ilk teslimatın zorunlu parçası saymaz:
- Ağ çok oyuncululuğu ve sunucu otoritesi,
- Çok iş parçacıklı simülasyon,
- Tam 3D fizik ve serbest kamera,
- Rastgele prosedürel dünya üretiminin tüm araçları,
- Gelişmiş dinamik ışık/gölge editörü,
- Çok karakterli kontrol edilen parti,
- Her NPC için tam günlük rutin ve karmaşık sosyal yapay zekâ,
- Godot veya başka motorla yeniden yazım.

Bunlar ileride ayrıca tasarlanabilir; mevcut sistem sınırlarını bozacak biçimde gizlice eklenemez.

---

## 2. Mimari bağlam ve mevcut başlangıç noktası

### 2.1. Temizlik dalının rolü

Bu sözleşmenin hedefi `experiment/map-cleanup` dalıdır. Bu dal, eski kare harita gameplay ve eski demo/portal akışının kaldırıldığı; axial harita/world altyapısının korunduğu ana oyun tabanıdır.

İnceleme sırasında aşağıdaki ana akış gözlemlenmiştir:

```text
main.py
  -> GameApplication / GameplayService
  -> GameWindow
  -> CharacterCreationScreen
  -> gameplay hazırlığı
  -> initialize_hex_world()
  -> MainScreen
  -> HexGameplayView
```

Gerçek çağrı ayrıntıları ve isimleri kod değişikliklerinden önce yeniden doğrulanmalıdır. Bu şema mimari yönü gösterir; her sınıfın tüm sorumluluklarını tek başına tanımlamaz.

### 2.2. Mevcut altyapıdan korunacak temel

İncelenen temizlik dalında şu altyapılar bulunmaktadır:
- `GameApplication`, `GameplayService` ve oturum/bundle bileşimi,
- `WorldActorRegistry` ve Core world/entity sahiplik modeli,
- `HexWorldRuntime`, `HexMapDefinition`, occupancy ve axial harita modeli,
- `MovementRules`, `HexPathfinder` ve `ActorHexBindingService`,
- `NPCRegistry` ve `NPCSpatialBindingService`,
- `HexWorldSnapshot` ve birleşik save/load akışı,
- `MainScreen`, `GameWindow` ve `WindowManager`,
- içerik paketi ve başlangıç içeriği yükleme sistemi.

Bunlar sıfırdan yazılacak sistemler değildir. Gerekli görülen değişiklikler mevcut sahiplik ve geriye dönük uyumluluk ilkelerine göre yapılır.

### 2.3. Mevcut prototipin sınırları

İnceleme sırasında ana oyun dünya çiziminin henüz hedeflenen nihai izometrik 2.5D sunum olmadığı görülmüştür:
- `world_transform.py` pointy-top axial hücre projeksiyonu yapmaktadır; bağımsız 2:1 izometrik kamera/projeksiyon katmanı değildir.
- `HexGameplayView` terrain, kamera, seçim ve hareket etkileşimini bir araya getiren prototip yüzeyidir.
- Terrain renderer texture kabul edebilse de ana çizim akışında gerçek asset bağlantısı tamamlanmış değildir.
- Karakter/NPC çizimi temel geometrik/prosedürel görünümdedir; nihai sprite/animasyon sunumu değildir.
- Ağaç, kaya, çalı ve bitki asset'lerinin scene placement üzerinden ana render akışına tam bağlandığı doğrulanmamıştır.
- Gelişmiş canopy/foreground occlusion, yükseklik, ışık ve gölge sistemi yoktur.
- NPC fizik gövdelerinin tanımlanmış olması, oyuncu hareket çözümüne dinamik çarpışma engeli olarak katıldıklarını kanıtlamaz.
- Yoldaş komut verilerinin bulunması gerçek takip pathfinding/steering davranışının tamamlandığını kanıtlamaz.

Bu eksikler, sözleşmenin hedef mimari kararlarıdır; mevcut dalın kusursuz çalıştığı iddiası değildir.

---

## 3. Katmanlı mimari

### 3.1. Katmanlar

```text
┌────────────────────────────────────────────────────────────┐
│ Presentation / Pygame UI                                    │
│ MainScreen, WindowManager, renderers, input adapters       │
├────────────────────────────────────────────────────────────┤
│ Application orchestration                                  │
│ GameWindow, GameplayService, initialization, save/load     │
├────────────────────────────────────────────────────────────┤
│ World simulation                                           │
│ HexWorldRuntime, occupancy, movement rules, pathfinding    │
├────────────────────────────────────────────────────────────┤
│ Actor / NPC / gameplay domains                             │
│ WorldActorRegistry, characters, NPCRegistry, quests, items  │
├────────────────────────────────────────────────────────────┤
│ Physics / spatial services                                 │
│ geometry, bodies, broadphase, narrowphase, solver, index   │
├────────────────────────────────────────────────────────────┤
│ Content and persistence                                    │
│ definitions, placements, asset catalog, snapshots, codecs  │
├────────────────────────────────────────────────────────────┤
│ Core                                                       │
│ canonical session, world/entity ownership, tick/events     │
└────────────────────────────────────────────────────────────┘
```

Şema kavramsaldır. Fizik ve spatial servisleri simülasyon katmanının kullandığı bağımsız teknik servislerdir; Core'un yerine geçmez.

### 3.2. Bağımlılık yönü

- Presentation, Application API'lerini ve immutable render snapshot'larını tüketebilir.
- Presentation domain state'ini doğrudan değiştiremez.
- Application, domain servislerini koordine eder ve oturum bileşimini yönetir.
- World simulation, actor/NPC kimliklerinin sahibi değildir; dünya içi konum, harita kuralları ve occupancy ilişkisini yönetir.
- Physics, actor/NPC iş kurallarını bilmez; fizik gövdeleri, şekiller, çarpışma ve hareket çözümü sağlar.
- NPC/character/quest/resource domain'leri fizik veya Pygame import etmez.
- Content loader doğrulanmış tanımları üretir; içerik JSON'u kod çalıştıramaz.
- Persistence, domain sahiplerinden snapshot alır ve doğrulanmış aday state'i geri yükler.
- Core, Pygame, render, asset veya UI pencerelerini bilmez.

### 3.3. Yasak bağımlılıklar

Aşağıdakiler mimari ihlaldir:
- `core` içinden `pygame`, `game_ui`, `rendering` veya asset yükleme çağrısı,
- Domain sınıflarının Pygame Surface/Rect/Vector2 nesnelerini canonical state olarak saklaması,
- Renderer'ın `WorldActorRegistry`, `NPCRegistry` veya `HexWorldRuntime` üzerinde çizim sırasında mutasyon yapması,
- UI pencerelerinin doğrudan save dosyasına yazması,
- Physics modülünün NPC diyalog/quest/relationship davranışını bilmesi,
- Content JSON içinde Python import, eval veya çalıştırılabilir callback,
- Aynı aktörün konumunu birden fazla registry'nin bağımsız biçimde yetkili olarak saklaması.

---

## 4. Veri sahipliği ve canonical state sözleşmesi

Tekil sahiplik, bu mimarinin en önemli kuralıdır. Bir sistemin başka sistemin verisini göstermesi, o verinin sahibi olduğu anlamına gelmez.

| Veri / olgu | Yetkili sahip | Diğer sistemlerin rolü |
|---|---|---|
| Oturum ve canonical entity/world kimliği | Core session / entity repository / membership | Application orchestration |
| Aktör kimliği ve oyun kimliği | `WorldActorRegistry` | UI ve physics kimliği referanslar |
| Karakter istatistikleri ve karakter state'i | Character domain | Actor binding ilişki kurar |
| NPC sosyal ve davranış state'i | `NPCRegistry` / social domain | World ve physics konum bağlantısı sağlar |
| Aktif dünya ve map kimliği | Core world + `HexWorldRuntime` scope | UI aktif dünya bilgisini okur |
| Harita topolojisi, geçilebilirlik tanımı | `HexMapDefinition` | Movement ve renderer okur |
| Dünya içi sürekli konum | Hex world movement/runtime sözleşmesi | Physics sonucu üretir; actor binding aktarır |
| Axial hücre üyeliği | `HexWorldRuntime` / occupancy | Konumdan türetilir ve doğrulanır |
| Fizik gövdesi ve collider | Physics runtime | Actor/world kimliğine bağlanır |
| NPC ilişki, faction, dialogue | Social/NPC domain | UI sunar, quest olayları tüketir |
| Quest progress | Quest domain / quest log | Event ve save snapshot ile bağlanır |
| Inventory ve resource quantities | Resource/inventory domain | UI yalnızca komut gönderir |
| Görsel asset tanımı | Asset catalog/content | Renderer yükler veya cache kullanır |
| Scene placement | Scene/content placement model | Renderer ve interaction adapter tüketir |
| Kamera ve geçici UI state | Presentation | Save kapsamına varsayılan olarak girmez |
| Save document | Persistence/application snapshot | Tekil domain sahiplerinden oluşturulur |

### 4.1. Actor ve NPC sahiplik ayrımı

- `WorldActorRegistry`, dünya aktörlerinin kararlı kimliklerini ve actor-level oyun bağlarını yönetir.
- Character domain karaktere ait nitelik, sınıf, sağlık ve benzeri karakter state'inin sahibidir.
- `NPCRegistry`, NPC'ye özgü sosyal/davranış state'inin sahibidir.
- `HexWorldRuntime`, harita kapsamındaki konum ve occupancy ilişkisinin sahibidir.
- Physics runtime, fizik gövdesi ve fiziksel çözüm state'inin sahibidir.
- `NPCSpatialBindingService` ve `ActorHexBindingService` bu sahipler arasındaki açık adaptörlerdir.

Aynı NPC için registry'ler arasında ayrı ve senkronize edilmesi gereken iki farklı “gerçek konum” oluşturulamaz. Physics hareket sonucu tek bir kabul edilmiş world position olarak runtime'a aktarılır; axial hücre ve occupancy bu konumla tutarlı tutulur.

### 4.2. Kimlik ve scope

Her dünya aktörü dünya kimliğiyle scope edilmelidir. Başka dünyaya ait actor, NPC, container veya resource node aktif runtime'a sessizce eklenemez. World ID uyuşmazlığı açık hata üretmelidir.

Entity/actor ID'leri kararlı ve benzersiz olmalıdır. Render sırası, dictionary sırası veya dosya satırı kimlik olarak kullanılamaz.

---

## 5. Dünya koordinatları, axial topoloji ve izometrik projeksiyon

Bu üç kavram kesin olarak ayrılır. Axial koordinat ile ekran pikseli aynı koordinat sistemi değildir. İzometrik projeksiyon, hex topolojisinin kendisi değildir.

### 5.1. Üç koordinat alanı

1. **Axial map coordinate `HexCoord(q, r)`:** Haritanın altıgen topolojisini, komşuluğu, hücre uzaklığını ve occupancy'yi tanımlar.
2. **Continuous world coordinate `WorldPoint(x, y)`:** Oyuncu, NPC ve fizik gövdelerinin hücreler arasında kesintisiz hareket ettiği dünya düzlemidir.
3. **Screen coordinate `ScreenPoint(sx, sy)`:** Kamera, zoom ve projeksiyon sonrası Pygame ekranındaki piksel koordinatıdır.

Dönüşümler ayrı, test edilebilir fonksiyonlardır:
- `axial_to_world(HexCoord) -> WorldPoint`
- `world_to_axial(WorldPoint, previous_cell?) -> HexCoord`
- `world_to_screen(WorldPoint, CameraState) -> ScreenPoint`
- `screen_to_world(ScreenPoint, CameraState) -> WorldPoint`
- `screen_to_axial(ScreenPoint, CameraState) -> HexCoord` yalnızca yukarıdaki ters dönüşümlerin bileşimi olarak.

Bir dönüşüm diğerinin yerine geçemez.

### 5.2. Sürekli dünya koordinatı

- Hareket ve fizik, piksel koordinatında değil world unit cinsinden çalışır.
- World unit ölçeği renderer'ın tile pixel ölçüsünden bağımsızdır.
- Oyuncu hücre merkezlerine kilitlenmez; hücreler arası sürekli hareket mümkündür.
- Axial hücre, sürekli konumdan türetilen topolojik üyelik bilgisidir.
- Hücre sınırında kararlı seçim için önceki hücreyi tie-break girdisi olarak kullanmak mümkündür.
- Float toleransı ve sınır davranışı açıkça test edilmelidir.
- Harita dışı konum politikası harita/oyun kuralıdır: BLOCK, CLAMP, TRANSITION veya OPEN seçeneklerinden biri açıkça belirlenir. Genel geometri katmanı kendiliğinden politika seçmez.

### 5.3. Axial geometri

- Hex koordinatları immutable value object olmalıdır.
- Altı komşu yön ve karşıt yön deterministik tanımlanmalıdır.
- Mesafe axial/cube matematiğiyle hesaplanır.
- Flat-top/pointy-top geometrik seçimi map schema/renderer konvansiyonunda tek anlamlı olmalıdır.
- Hex polygon ve world/pixel dönüşümleri aynı orientation ve ölçü sözleşmesini kullanmalıdır.
- Masked map hücreleri olmayan koordinatlara erişim doğrulanmalıdır.
- Geometri modülü oyun kimliği, actor registry veya Pygame ekran yaşam döngüsünü bilmez.

### 5.4. İzometrik projeksiyon

Nihai hedef klasik 2:1 izometrik görünümdür. Projeksiyon bağımsız bir presentation bileşenidir. İlk matematiksel referans:

```text
u = world_x - world_y
v = world_x + world_y

screen_x = origin_x + (u * tile_width / 2) * zoom
screen_y = origin_y + (v * tile_height / 2) * zoom
```

Klasik 2:1 görünümde `tile_width / tile_height = 2` oranı başlangıç varsayımıdır. Kamera offset'i ve viewport merkezi ayrıca uygulanır. Bu formül nihai kod API'sini zorunlu kılmaz; dönüşümün matematiksel niyetini tanımlar.

Axial hücre merkezi önce world plane'e dönüştürülür, sonra izometrik ekrana projekte edilir. Axial pixel conversion helper'ı tek başına nihai renderer projeksiyonu olarak kullanılamaz.

### 5.5. Ters dönüşüm ve fare seçimi

- Fare ekran koordinatı önce camera/projection ters dönüşümüyle world coordinate'e çevrilir.
- Ardından world coordinate axial hücreye veya world-space hit-test'e çevrilir.
- Fare tıklamasında hücre seçimi ve entity seçimi ayrı hit-test aşamalarıdır.
- Zoom, kamera hareketi, pencere ölçeklemesi ve viewport clipping ters dönüşümü bozmaz.
- Hücre sınırındaki tıklamalar deterministik sonuç üretir.
- Ekran dışı veya UI penceresi altında kalan tıklamalar dünya etkileşimine sızmaz.

### 5.6. Kamera

Kamera en az:
- world-space position,
- zoom,
- viewport,
- takip hedefi,
- takip smoothing parametresi,
- harita sınırı/limit politikası
taşımalıdır.

Kamera simülasyon konumunu değiştiremez. Kamera follow, player movement'ın yerine geçmez. Zoom sınırları konfigüre edilebilir ve geçersiz değerler reddedilir. Edge scrolling, drag pan ve follow davranışları aynı CameraController üzerinden yürütülür.

---

## 6. Harita ve dünya modeli

### 6.1. Static definition ve runtime state ayrımı

- `HexMapDefinition` değişmez harita tanımıdır: hücreler, topology, terrain türleri, geçilebilirlik tanımları, map metadata ve statik ilişkiler.
- `HexWorldRuntime` aktif oyun oturumunun dünya içi runtime state'ini taşır: konum, occupancy, runtime override ve map-local state.
- Static content definition runtime sırasında mutasyona uğratılamaz.
- Runtime override, tanım dosyasını değiştirmez; snapshot olarak kaydedilir.
- Birden fazla map definition aynı anda paket içinde bulunabilir; aktif map/world scope açıkça belirtilir.

### 6.2. Hücre ve geçilebilirlik

Bir hücrede en az:
- kararlı axial koordinat,
- terrain kimliği,
- geçilebilirlik/terrain movement metadata,
- varsa statik feature/obstacle referansı,
- isteğe bağlı yükseklik/elevation metadata
bulunabilir.

Geçilebilirlik yalnızca renderer'ın terrain adına bakılarak tahmin edilmez. `MovementRules` tek yetkili kural API'sidir. Physics collider ile pathfinding walkability birbiriyle çelişmemelidir:
- Pathfinding geçilebilir dediği hücre fiziksel olarak geçilmez bir statik duvar içeremez.
- Physics boş dediği hücre pathfinding tarafından sebepsiz yere kapatılamaz.
- Dinamik actor occupancy, statik terrain walkability'den ayrı sorgulanır.
- Geçici aktör engeli ile kalıcı harita engeli farklı sonuç kodlarıyla raporlanabilir.

### 6.3. Map transition

Map geçişleri açık tanımlı transition kayıtları üzerinden yapılır. Geçiş:
1. kaynak map ve hedef map kimliklerini doğrular,
2. hedef giriş koordinatını doğrular,
3. actor/world scope'u taşır veya yeniden bağlar,
4. occupancy ve spatial index kayıtlarını günceller,
5. kamera ve render snapshot'ını yeni dünya ile senkronize eder,
6. save/load için tutarlı map kimliğini korur.

Transition yalnızca ekran değişimi değildir. Mevcut başlangıç map'inde transition bulunmaması, sistemin tasarım dışı olduğu anlamına gelmez; içerik hazır olduğunda aynı sözleşme kullanılır.

---

## 7. Hareket, pathfinding ve input sözleşmesi

### 7.1. Tek hareket otoritesi

Klavye hareketi, fareyle hedefe hareket, NPC steering ve yoldaş takip davranışı farklı niyetler üretebilir; fakat hepsi aynı world-space movement/physics pipeline'ından geçer.

UI veya input controller aktörün konumunu doğrudan yazamaz. Input yalnızca `MovementIntent` veya eşdeğer komut üretir.

### 7.2. Hareket niyeti

Movement intent en az:
- actor/entity ID,
- yön veya hedef world position,
- movement mode (walk/run/sneak vb.),
- hız/ivme isteği veya profile referansı,
- kaynak/öncelik,
- intent tick veya geçerlilik aralığı
taşımalıdır.

Bir tick'te çelişen birden fazla intent varsa öncelik kuralı deterministik olmalıdır. Örneğin kullanıcı kontrolü, scripted action ve AI steering arasında açık öncelik bulunur. Öncelik yalnızca event geliş sırasına bağlı olamaz.

### 7.3. Klavye hareketi

- WASD/yön tuşları yön intent'i üretir.
- Normal yürüme, koşma ve gizlenme gibi modlar MovementProfile/MovementConfig ile tanımlanır.
- Tuş basılı tutma frame rate'e bağlı hız üretmez; fixed simulation tick'e göre ilerler.
- Diagonal movement normalize edilir; iki eksende daha hızlı hareket oluşmaz.
- Pause, UI modal durumu veya input focus kaybı oyuncu hareketini durdurur.
- Input state'i pencere odağı kaybolduğunda güvenli biçimde temizlenir.

### 7.4. Click-to-move

- Tıklama hedefi world coordinate ve/veya axial destination olarak çözülür.
- `HexPathfinder` harita topolojisi ve `MovementRules` kullanır.
- Pathfinding bir rota/waypoint üretir; aktörün konumunu doğrudan değiştirmez.
- Her waypoint'e giderken aynı collision-aware movement pipeline kullanılır.
- Dinamik actor engelleri için yeniden rota hesaplama veya steering politikası tanımlanır.
- Hedef geçersiz, erişilemez veya stale ise açık başarısızlık durumu döner.
- Kullanıcı yeni hedef verdiğinde eski rota deterministik biçimde iptal edilir/değiştirilir.

### 7.5. Hareket sonuçları

Movement pipeline sonuçları en az:
- accepted,
- blocked_static,
- blocked_dynamic,
- partial/slide,
- reached_target,
- invalid_target,
- out_of_bounds
gibi ayırt edilebilir sonuçlar üretmelidir. Gerçek enum isimleri uygulama sırasında seçilir; anlamlar kaybolamaz.

---

## 8. Fizik ve spatial query sözleşmesi

### 8.1. Fizik sisteminin kapsamı

Laboratuvar dalında geliştirilen geometri, body, broadphase, narrowphase, contact, solver, continuous collision ve spatial index bileşenleri teknik adaydır. Bunlar ana oyuna topluca veya körlemesine kopyalanmaz; mevcut domain sahipliği ve movement API'lerine adapter ile entegre edilir.

Physics katmanı:
- circle ve convex polygon gibi şekilleri,
- statik ve dinamik body ayrımını,
- broadphase candidate üretimini,
- narrowphase collision/contact üretimini,
- penetration correction ve sliding/response çözümünü,
- swept/continuous collision ihtiyacını,
- spatial index ile yakın nesne sorgusunu
sağlar.

### 8.2. Statik ve dinamik cisimler

**Statik body:** Arazi engeli, sabit kaya, duvar, yapı gibi oyun sırasında kendi başına hareket etmeyen fizik nesnesidir.

**Dinamik body:** Oyuncu, hareketli NPC, itilebilir nesne veya hareket edebilen fizik nesnesidir.

Dinamik body'ler broadphase sorgularında birbirlerinin adayları olmalıdır. Oyuncu hareket çözümü yalnızca statik harita engellerini görüyorsa NPC fizik gövdesi var olsa bile oyuncu-NPC çarpışması tamamlanmış sayılmaz.

### 8.3. Zorunlu fizik davranışları

- Oyuncu statik engellerden geçemez.
- Oyuncu NPC ile çarpışabilir.
- Oyuncu duran/itilebilir NPC'yi fiziksel olarak itebilir; NPC konumu ve occupancy güncellenir.
- NPC-NPC dinamik çarpışması tanımlı olmalıdır.
- Aynı anda çoklu çarpışma deterministik çözülmelidir.
- Hızlı hareket eden aktörlerde tünelleme önlenmelidir.
- Duvar/engel boyunca hareket mümkün olduğunca kayarak devam edebilir.
- Collider ile sprite ölçüsü bağımsızdır.
- Collision correction sonucu harita dışına veya geçersiz hücreye taşma engellenir.

### 8.4. NPC itişi ve kaçınma ayrımı

Bunlar iki farklı yetenektir:
1. **Fiziksel itiş:** Oyuncu NPC'ye çarpar; collision response NPC'yi yer değiştirir.
2. **Davranışsal kaçınma:** NPC, oyuncu veya başka engel yaklaşırken çarpışma gerçekleşmeden önce uygun yöne çekilir.

İlk yetenek tamamlanmadan ikinci davranışın var olduğu iddia edilemez. Kaçınma sistemi fiziksel solver'ın yerine geçmez; intent/steering üretir ve fizik çözümünden geçer.

### 8.5. Spatial index

UniformGrid, Quadtree veya başka index seçimi benchmark ile yapılır. Index:
- canonical actor state'in sahibi değildir,
- yalnızca aday sorgu hızlandırıcısıdır,
- ekleme/çıkarma/konum/yarıçap güncellemelerinde tutarlı kalmalıdır,
- brute-force oracle ile test edilebilir olmalıdır,
- deterministic sonuç sırası gerektiğinde normalize edilmelidir.

Bir entity kaldırıldığında index'te stale kayıt kalmamalıdır. Maksimum collider radius gibi cache'ler yanlış sonuç üretmese bile gereksiz geniş sorgu yaratıyorsa bakım stratejisi belirlenmelidir.

### 8.6. Collision ile occupancy tutarlılığı

Physics çözümü sonrasında:
1. kabul edilen world position belirlenir,
2. world position axial hücreye dönüştürülür,
3. occupancy eski hücreden çıkarılıp yeni hücreye aktarılır,
4. actor/NPC binding ve spatial index güncellenir,
5. world snapshot bu tutarlı durumu görür.

Bu sıra tek bir transaction/tick sınırı içinde tamamlanmalıdır. Render ara durum veya yarım güncellenmiş occupancy okumamalıdır.

---

## 9. NPC, aktör ve yoldaş davranışları

### 9.1. NPC veri ve runtime ayrımı

NPC definition; kimlik, ad, rol, faction, başlangıç ilişkileri, dialogue/quest/merchant referansları ve başlangıç yerleşimi gibi içerik verilerini tanımlar. Runtime ise mevcut konum, ihtiyaç, davranış modu, aktif hedef, patrol progress ve ilişki değişimleri gibi canlı state'i taşır.

NPC role string'i tek başına davranış kodu değildir. Davranış, genel AI/behavior servisleri tarafından uygulanır.

### 9.2. NPC hareketi

NPC hareketi de oyuncu ile aynı:
- movement intent,
- pathfinding/steering,
- physics collision,
- occupancy update,
- render snapshot
zincirini kullanır.

NPC'nin doğrudan `position = target` yaparak duvarlardan geçmesi yasaktır. Teleport yalnızca açık bir gameplay action veya map transition gibi tanımlı işlem olabilir.

### 9.3. Başlangıç davranış seviyeleri

Önerilen uygulama sırası:
1. Statik NPC yerleşimi ve interaction,
2. Basit patrol waypoint hareketi,
3. Collision-aware NPC hareketi,
4. Oyuncu/engel çevresinden kaçınma,
5. Durum/rol tabanlı behavior,
6. İhtiyaçlar ve zaman çizelgesi.

Her seviye önceki davranışları bozmadan eklenmelidir. Tam günlük rutin ilk fizik teslimatı için ön koşul değildir.

### 9.4. Yoldaş komutları

Yoldaş sistemi en az şu kullanıcı komutlarını destekleyecek şekilde tasarlanır:
- **Beni takip et**
- **Burada bekle**

Takip davranışı oyuncuya göre hedef/offset üretir; oyuncunun tam üzerine binmeye çalışmaz. Yoldaşlar dar alanlarda birbirine ve oyuncuya çarpmamalı, sıkışma durumunda yeniden konum/rota çözümü üretmelidir.

Bekleme komutu yoldaşın bekleme konumunu ve komut state'ini kaydeder. Oyuncu uzaklaştı diye bekleme komutu otomatik bozulamaz. Return/rejoin davranışı ileride ayrı komut olarak eklenebilir.

Laboratuvar dalındaki command/relationship/roster modelleri adaydır; gerçek steering/pathfinding ve save bağlantısı ayrıca doğrulanmalıdır.

---

## 10. Etkileşim sistemi

### 10.1. Etkileşim hedefleri

Etkileşim sistemi oyuncu ile dünya nesneleri arasında ortak sorgu sözleşmesi sağlar. Hedefler:
- NPC konuşma,
- kaynak toplama,
- sandık/container açma,
- kapı/portal kullanma,
- yapı/tesis kullanma,
- inceleme,
- görev ve dünya objesi etkileşimleri.

Her hedef türü kendi domain servisinde işlenir. Interaction katmanı yalnızca hedef bulma, mesafe/menzil, seçim ve eylem isteğini yönlendirir.

### 10.2. Target query ve selection

- Önce spatial query ile adaylar bulunur.
- Sonra etkileşim menzili ve görüş/engel kuralı kontrol edilir.
- Birden fazla aday varsa deterministik sıralama uygulanır.
- Fare hover, seçim ve gerçek eylem ayrı durumlardır.
- UI penceresi üzerinde tıklama dünya hedefine aktarılmaz.
- Seçili hedef yoksa action sessizce başka hedefe uygulanmaz.

### 10.3. Komut yönlendirme

Interaction sonucu doğrudan NPC veya resource state'ini değiştirmez; ilgili application/domain API'sine komut gönderir. Örneğin:
- Talk → social/dialogue service,
- Gather → resource/gathering service,
- Open container → container/lock service,
- Quest action → quest service.

Başarı/başarısızlık kullanıcıya UI feedback/toast olarak sunulur; domain sonucu tek kaynaktır.

---

## 11. Görsel dünya ve render pipeline

### 11.1. Renderer'ın rolü

Renderer, simülasyon state'ini değiştirmeden görsel çıktı üretir. Renderer'ın temel girdisi, belirli bir tick'e ait immutable `WorldRenderSnapshot` veya eşdeğer sunum modelidir.

Renderer doğrudan registry'lerden dağınık veri toplayıp çizim sırasında domain çağrıları yapmamalıdır. Snapshot oluşturma sorumluluğu application/simulation adapter katmanındadır.

### 11.2. Render snapshot veri sözleşmesi

Her render item ihtiyaca göre şunları taşıyabilir:
- stable entity/placement ID,
- render kind/type,
- asset veya animation key,
- world position,
- ground anchor,
- depth anchor,
- sprite bounds,
- canopy/occlusion bounds,
- layer/order metadata,
- facing/direction,
- animation state/frame key,
- tint/opacity/visibility flags,
- selection/interaction presentation flags.

Snapshot, domain nesnelerinin mutable referanslarını taşımamalıdır. Gerekli değerler immutable kopya/value object olarak sunulur.

### 11.3. Çizim aşamaları

Önerilen render sırası:
1. viewport ve camera hazırlığı,
2. görünür arazi hücrelerinin culling'i,
3. zemin texture/terrain çizimi,
4. ground decals ve zemin üstü küçük detaylar,
5. dünya nesnelerinin depth sıralaması,
6. karakter/NPC/resource/prop sprite çizimi,
7. foreground canopy/occlusion pass,
8. gölge/ışık ve atmosfer pass'i,
9. selection/interaction overlay,
10. dünya HUD ve UI pencereleri.

Bu sıralama gerçek alpha blending ve occlusion ihtiyacına göre alt pass'lere ayrılabilir. Ancak depth/foreground kuralı tek ve belgeli olmalıdır.

### 11.4. Depth sorting

Tek bir `q` veya `r` değerine göre sıralama nihai 2.5D için yeterli kabul edilmez. Her nesne ground contact/depth anchor üzerinden dünya düzlemindeki derinlik anahtarını üretmelidir.

- Aynı depth key için stable tie-break entity/placement ID kullanılır.
- Sprite'ın üst sınırı depth hesabına dahil edilmez; zemin temas noktası esas alınır.
- Büyük çevre nesnelerinin canopy kısmı ayrı foreground pass'e alınabilir.
- Oyuncu ağaç gövdesinin arkasında/önünde doğru görünmelidir.
- Görsel bounding box, collision shape yerine kullanılamaz.

### 11.5. Occlusion ve canopy

Ağaç gibi uzun nesneler tek sprite olarak çizilse bile mantıksal olarak:
- zemin/roots bölgesi,
- gövde ve alt kısım,
- üst canopy/foreground bölgesi
şeklinde ayrıştırılabilir.

Oyuncu ağacın arkasına geçtiğinde canopy oyuncunun önünde çizilebilir. Oyuncu ağacın önündeyse canopy davranışı seçilen sanat tasarımına göre tutarlı kalır. İlk sürümde sprite splitting veya mask tabanlı yöntemlerden biri seçilebilir; yöntemler karıştırılıp nesne bazında keyfi davranış üretilmez.

### 11.6. Culling

- Kamera viewport'u ve sprite bounds kullanılarak görünmeyen item'lar çizim listesinden çıkarılır.
- Büyük ağaç canopy'si ekran dışındayken gövde ekran içinde olabilir; culling tüm görsel bounds'u dikkate alır.
- Spatial index render culling için aday sağlayabilir; ancak render sırasını belirlemez.
- Culling sonucu gameplay entity silinmez veya simülasyondan çıkarılmaz.
- Culling on/off görsel doğruluk testleri yapılır.

### 11.7. Animasyon

Animasyon zamanı render frame rate'e bağlanamaz. Simulation tick veya ayrı deterministik animation clock kullanılır. Başlangıçta:
- idle,
- walk,
- run,
- attack/hit (combat aşamasında),
- interaction
durumları desteklenebilir.

Sprite frame seçimi actor state/facing ile eşleşir. Animasyon state'i render için türetilen presentation bilgisi olabilir; gameplay açısından önemli animation event'leri simulation tick'te tetiklenmelidir.

### 11.8. Asset ve cache

- Asset catalog asset kimliği, dosya yolu, ölçü/anchor metadata ve opsiyonel varyantları tanımlar.
- Dosya yoksa açık content validation error veya tanımlı placeholder fallback kullanılır.
- Asset yükleme her frame yapılmaz.
- Surface/texture cache presentation katmanında yaşar.
- Cache temizleme ve asset lifecycle açık olmalıdır.
- İçerik paketi asset path'leri paket köküne göre güvenli çözülür; path traversal engellenir.

---

## 12. Environment, prop ve scene placement sözleşmesi

### 12.1. Üç ayrı kavram

1. **Asset definition:** Görselin ne olduğunu ve nasıl çizileceğini tanımlar.
2. **Scene placement:** Belirli bir haritada bu görselin nerede bulunduğunu tanımlar.
3. **Gameplay entity:** O nesnenin oyun kuralı, kimliği, etkileşimi ve persistence state'idir.

Bir ağaç dekor olabilir; odun kaynağıysa ayrıca resource/gameplay entity ilişkisi taşır. Görsel placement tek başına resource node oluşturmaz.

### 12.2. Placement alanları

Scene placement ihtiyaca göre:
- placement ID,
- asset ID,
- map ID,
- world position veya axial anchor,
- rotation,
- scale,
- elevation,
- ground anchor,
- depth anchor,
- render layer,
- visual variation/seed,
- optional gameplay entity reference
taşıyabilir.

Rotation/scale/elevation her ilk teslimat için zorunlu değildir; ancak model bunların gelecekte eklenmesini engellememelidir. Placement XY'den başka bir veri saklamıyorsa bu sınırlama açıkça belirtilmelidir.

### 12.3. Collider bağlantısı

Collider asset görselinden otomatik çıkarılmaz. Collider:
- açık physics shape definition,
- gameplay entity fizik profili,
- veya harita statik obstacle tanımı
üzerinden tanımlanır.

Görsel büyük, collider küçük olabilir. Canopy oyuncunun üzerinden geçilebilirken gövde geçilemez olabilir. Bu nedenle tek sprite rect'i ile collision yapılması yasaktır.

### 12.4. İçerik doğrulama

Loader şu durumları doğrular:
- asset ID var mı,
- map ID var mı,
- placement ID benzersiz mi,
- koordinat harita sınırında mı,
- referans verilen gameplay entity mevcut mu,
- collider tanımı geçerli mi,
- scale/rotation/elevation değerleri aralık içinde mi,
- schema version destekleniyor mu.

Eksik asset veya bozuk placement sessizce yok sayılmaz; validation raporu üretir.

---

## 13. Simülasyon tick ve sistem güncelleme sırası

### 13.1. Fixed timestep

Simülasyon sabit tick ile ilerler. Render frame rate simülasyon hızını belirlemez. Laboratuvar prototipindeki 60 TPS yaklaşımı başlangıç adayıdır; gerçek değer benchmark ve mevcut Core tick sözleşmesiyle uyum doğrulanmadan kesin runtime sabiti olarak kabul edilmez.

Frame başına biriken zaman için üst sınır, max catch-up tick ve pause/resume davranışı tanımlanır. Uzun frame sonrasında sınırsız tick borcu biriktirilmez.

### 13.2. Önerilen tick pipeline

```text
1. Input sampling / command queue
2. Player and scripted movement intents
3. NPC and companion behavior intents
4. Pathfinding / steering updates
5. Physics broadphase candidate generation
6. Narrowphase contacts and continuous collision
7. Physics solve / accepted world positions
8. Hex cell conversion and occupancy synchronization
9. Actor/NPC/spatial binding synchronization
10. Interaction range and world query refresh
11. Domain actions / simulation event publication
12. Immutable render snapshot creation
13. Persistence-safe boundary / diagnostics
```

Bu sıra entegrasyon sırasında gerçek Core scheduler/event lifecycle ile eşleştirilmelidir. Core'un canonical tick'i dışında ikinci bir authoritative game clock oluşturulamaz.

### 13.3. Determinism

Aynı başlangıç snapshot'ı, aynı input/command dizisi ve aynı tick sayısı aynı canonical gameplay state'i üretmelidir. Determinism için:
- entity iteration stable order,
- collision pair stable order,
- random seed explicit,
- tie-break kuralları sabit,
- wall-clock time gameplay kararı için kullanılmaz,
- render frame rate simulation kararına etki etmez.

Floating-point platform farkları için kabul toleransı belirlenir; tam bitwise determinism gerekip gerekmediği test stratejisinde açıkça kararlaştırılır.

### 13.4. Event akışı

Domain olayları ilgili servis tarafından üretilir; event queue/scheduler mevcut Core/Application sözleşmesiyle taşınır. Renderer event tüketerek state değiştirmez. UI olayları gösterir; gameplay sonucu domain state üzerinden okunur.

---

## 14. UI ve ana oyun pencereleri

### 14.1. Kalıcı dünya yüzeyi

`MainScreen` gameplay boyunca ana dünya yüzeyidir. Karakter oluşturma tamamlandığında bu ekran etkinleşir ve inventory/character/quest gibi pencereler açıldığında kapanmaz veya başka bir tam ekran sayfasıyla değiştirilmez.

### 14.2. WindowManager

WindowManager:
- pencere kayıt ve lifecycle,
- z-order,
- focus,
- drag/move,
- resize (desteklenen pencerelerde),
- viewport clipping,
- content origin,
- pointer capture,
- close action
sorumluluklarını taşır.

Her pencerenin açık/kapalı ve geometry state'i UI state'tir; domain state değildir.

### 14.3. Kapatma ve Escape

- Her pencerede görünür mouse ile kullanılabilir kapatma X'i bulunur.
- Escape oyun içi menüyü açar/kapatır; tek başına açık pencereleri kapatma kısayolu değildir.
- Pencere kapatma işlemi yalnızca o pencerenin close action'ını çağırır.
- Modal diyalog/confirm katmanı Escape'i kendi açık sözleşmesine göre tüketebilir; davranış açıkça belirtilir.
- UI input focus dünya hareketini engeller; tuşlar pencereye ve oyuna aynı anda uygulanmaz.

### 14.4. Pencere seti

İlgili oyun akışına göre:
- Character,
- Inventory,
- Quest Log,
- World Map,
- Production,
- Market/Trade,
- Container,
- Dialogue,
- in-game menu
pencereleri açılabilir.

Her ekranın ayrı bir tam ekran GameWindow state'i olması zorunlu değildir. Dünya üstü pencere olarak çalışması ana kuraldır. Tam ekran ayrı mod yalnızca açık ürün kararıyla eklenebilir.

### 14.5. Erişilebilirlik ve feedback

- Mouse ile görünen kontrol,
- klavye navigasyonu,
- belirgin focus state,
- anlaşılır hata/başarı feedback'i,
- okunabilir metin ve ölçeklenebilir UI
sağlanmalıdır.

Toast, domain hatasının yerine geçmez; domain sonucu kullanıcıya sunar.

---

## 15. Persistence ve save/load sözleşmesi

### 15.1. Tek birleşik kayıt otoritesi

Mevcut `GameApplication` save/load ve `GameSaveDocument` bileşimi korunur. Laboratuvar `HexWorld` persistence sistemi ana oyuna ikinci bir bağımsız save formatı/otoritesi olarak eklenemez.

Her domain kendi snapshot'ını üretir; application bunları tek tutarlı belge içinde birleştirir.

### 15.2. Kayıt kapsamı

Oyun ilerledikçe kayıt en az aşağıdakileri kapsamalıdır:
- Core session/world/entity identity ve membership,
- player character ve actor bağları,
- aktif world/map kimliği,
- world-space position ve axial occupancy,
- NPC konumları ve gerekli davranış state'i,
- companion roster ve follow/wait command state,
- inventory, item ve resource miktarları,
- resource node runtime state,
- quest progress ve quest graph progress,
- containers/locks,
- production/economy/social/combat state,
- runtime world overrides ve gerekli simülasyon state'i.

Kamera, pencere konumu ve geçici selection varsayılan olarak save kapsamı dışındadır; ürün kararıyla ayrı user preferences kaydı olabilir.

### 15.3. Snapshot tutarlılığı

Snapshot tek bir güvenli simulation boundary'de oluşturulur. Save sırasında:
- bundle validate edilir,
- aktif world ile HexWorldRuntime world ID eşleşir,
- actor/NPC/resource/container sahiplik referansları doğrulanır,
- occupancy ve world position tutarlılığı kontrol edilir,
- duplicate ID ve bozuk referans reddedilir.

Kısmi veya yarım tick state'i kaydedilemez.

### 15.4. Load atomikliği

Load:
1. dosyayı parse eder,
2. schema/version doğrular,
3. candidate session ve domain state oluşturur,
4. content/map referanslarını doğrular,
5. domain owner ve world scope kontrollerini yapar,
6. snapshot'ları candidate runtime'a restore eder,
7. bütün doğrulamalar başarılıysa candidate'ı aktif holder'a atomik yayımlar.

Hata halinde mevcut çalışan oturum bozulmadan kalır. Kısmi restore yayınlanamaz.

### 15.5. Legacy save politikası

Eski kare harita konumları veya placement verileri axial map state'e otomatik çevrilmez. Mevcut kodun legacy spatial state'i açıkça reddetme yaklaşımı korunur. Bir migration ancak kaynak verinin anlamı, map karşılığı, kayıp riski ve testleri belgelenmişse eklenebilir.

### 15.6. Versiyonlama

Her snapshot schema version taşır. Bilinmeyen gelecek sürüm reddedilir. Desteklenen eski sürümler açık migration fonksiyonlarıyla dönüştürülür. Migration idempotent olmalı veya tek seferlik olduğu açıkça belgelenmelidir.

---

## 16. İçerik paketi ve modlama sözleşmesi

### 16.1. Content data ve gameplay rule ayrımı

Content pack şu verileri tanımlar:
- map definition,
- terrain/feature,
- asset catalog,
- scene placements,
- NPC/character definitions,
- quest/dialogue definitions,
- resource definitions,
- başlangıç konumu ve başlangıç içerik ilişkileri.

Gameplay kuralları Python domain/application kodunda kalır. JSON yalnızca doğrulanan data taşır; çalıştırılabilir kod içermez.

### 16.2. Manifest ve schema

- Paket kimliği ve sürümü manifest'te tanımlanır.
- Map klasörü/harita discovery sözleşmesi mevcut loader ile uyumlu olmalıdır.
- Her yeni veri türü schema version ve validation tanımlar.
- Bilinmeyen zorunlu alan veya unsupported future schema reddedilir.
- Paketler birbirinin runtime state'ini paylaşmaz.
- Asset path çözümü paket kökü dışına çıkamaz.

### 16.3. Yeni içerik ekleme kuralı

Yeni ağaç, kaya, NPC, kaynak veya görev eklemek için mümkün olduğunca:
1. asset catalog/definition ekle,
2. scene placement veya gameplay definition ekle,
3. gerekli domain referanslarını bağla,
4. validation ve fixture testini güncelle.

Yeni içerik için GameWindow, MainScreen veya renderer içine içerik kimliğine özel if/else eklemek yasaktır.

---

## 17. Laboratuvar dalı bileşenleri için entegrasyon karar matrisi

Aşağıdaki kararlar, laboratuvar dalında geliştirilen sistemlerin ana oyuna hangi ilkeyle alınacağını tanımlar. Her entegrasyondan önce laboratuvar HEAD ve ilgili dosyalar yeniden doğrulanır.

| Laboratuvar bileşeni | Karar | Ana oyundaki sınır / gerekçe |
|---|---|---|
| Axial/cube geometry | **Koru ve uyumunu doğrula** | Temizlik dalının HexCoord/map convention ile çakışma kontrolü; tek geometri standardı |
| Continuous movement primitives | **Uyarlayarak entegre et** | ActorHexBindingService ve mevcut movement rules otoritesine bağlanır |
| Movement intent/config/state | **Uyarlayarak entegre et** | Application input ile physics pipeline arasında value/API sözleşmesi |
| Physics shapes/contacts/solver | **Seçerek entegre et** | Mevcut statik map collision ve actor binding ile adapter gerekir |
| Continuous collision | **Benchmark ve testle entegre et** | Hızlı hareket tünellemesini önlemek için |
| UniformGrid/Quadtree | **Ölçerek seç** | Bir veya birden fazla index olabilir; canonical owner değildir |
| Camera controller | **Uyarlayarak entegre et** | Mevcut UI viewport ve bağımsız izometrik projection ile birleştirilir |
| Camera projection/transform | **Yeniden tasarla/ayır** | Axial pixel projection nihai 2:1 iso projection değildir |
| Render snapshot/culling | **Koru ve genişlet** | Domain state'i immutable presentation modeline dönüştürür |
| Pygame renderer | **Uyarlayarak entegre et** | MainScreen/HexGameplayView lifecycle'ına bağlanır; texture/asset/occlusion eksikleri tamamlanır |
| Environment definitions | **Koru ve genişlet** | Asset definition ve scene placement ayrımı |
| Procedural visual documents | **Aday; validation sonrası** | İçerik çizim tanımı; gameplay logic veya collider yerine geçmez |
| EntityRegistry | **Canonical owner olarak alma** | Temizlik dalındaki WorldActorRegistry/NPCRegistry sahipliğini ikame edemez |
| Entity presentation/transform adapters | **Seçerek entegre et** | Presentation/spatial adapter olarak kullanılabilir |
| Interaction profile/range/selection | **Uyarlayarak entegre et** | Mevcut NPC/resource/quest/container domain API'lerine yönlendirilmeli |
| Companion command/roster | **Uyarlayarak entegre et** | Gerçek follow/wait steering ve persistence tamamlanmalı |
| Simulation tick coordinator | **Doğrudan otorite yapma** | Core canonical tick ve Application scheduler ile uyumlu adapter gerekir |
| Content definitions/library | **Uyarlayarak entegre et** | Mevcut ContentPackage/manifest/loader ile tek paket sözleşmesi |
| Lab map/runtime persistence | **Ana save otoritesi yapma** | GameSaveDocument/HexWorldSnapshot tek birleşik save yapısı korunur |

### 17.1. Entegrasyon öncesi kontrol

Her laboratuvar bileşeni için:
- gerçek dosya yolu ve export API,
- bağımlılık/import grafiği,
- Python sürümü ve Pygame CE uyumu,
- mevcut testler ve test kapsamı,
- deterministic davranış,
- mutability/thread assumptions,
- performance benchmark,
- mevcut temizlik dalı API'sine adapter ihtiyacı
kaydedilir.

Laboratuvar kodu ana dala alınmadan önce branch commit SHA sabitlenir. “Laboratuvarda çalışıyordu” tek başına kabul kanıtı değildir.

---

## 18. Dosya ve modül sınırı haritası

Bu tablo kesin dosya listesi değil, mevcut modüllere göre hedef sorumluluk haritasıdır. Uygulama öncesi gerçek repository tree ile dosya düzeyinde eşleştirilir.

| Mevcut alan / örnek dosya | Hedef sorumluluk | Karar |
|---|---|---|
| `main.py` | Entry point ve uygulama başlatma | İnce orchestration; gameplay logic eklenmez |
| `application/game_application.py` | Session, domain orchestration, save/load | Korunur; tek birleşik persistence |
| `application/hex_world_initializer.py` | Başlangıç world/map runtime hazırlığı | Korunur; içerik tabanlı başlangıç |
| `application/hex_actor_binding.py` | Actor ile hex world konum/occupancy adaptörü | Korunur; tek konum otoritesine göre geliştirilir |
| `game_ui/game_window.py` | Pygame loop ve UI lifecycle | Korunur; dünya/pencere ayrımı |
| `game_ui/screens/main_screen.py` | Kalıcı dünya yüzeyi | Korunur ve hedef ana render host'u yapılır |
| `game_ui/window_manager.py` | Dünya üstü UI pencereleri | Korunur; close/focus/input sözleşmesi |
| `game_ui/world_rendering/hex_gameplay_view.py` | Dünya sunum orkestrasyonu | Parçalara ayrılarak geliştirilebilir |
| `game_ui/world_transform.py` | Mevcut axial/pixel helper | Nihai izometrik projection olarak kullanılmaz; adapter/legacy rolü netleştirilir |
| `game_ui/world_rendering/camera.py` | Kamera state/controller | Bağımsız world-space camera API |
| `game_ui/world_rendering/terrain_renderer.py` | Arazi çizimi | Asset catalog ve culling ile bağlanır |
| `game_ui/world_rendering/character_renderer.py` | Actor sprite/animation | Sprite anchor/depth/facing sözleşmesi |
| `game_ui/world_rendering/depth_sorter.py` | Depth ordering | Ground/depth anchor ve stable tie-break |
| `physics/` veya yeni physics paketi | Fizik runtime | Domain'den bağımsız teknik servis |
| `spatial/` veya yeni spatial paketi | Spatial index | Query acceleration; canonical owner değil |
| `content/` | Definitions, assets, placements | Tek manifest/schema loader sözleşmesi |
| `tests/` | Unit/integration/acceptance | Her aşama ile birlikte güncellenir |

Yeni modül açılacaksa var olan aynı sorumluluğu taşıyan modül olup olmadığı önce kontrol edilir. Dosya sayısını artırmak tek başına mimari iyileştirme değildir.

---

## 19. Hata yönetimi, gözlemlenebilirlik ve tanılama

### 19.1. Hata sınıfları

En az şu hata kategorileri ayrılmalıdır:
- invalid content/schema,
- missing asset,
- invalid map/world reference,
- invalid actor binding,
- movement blocked/invalid,
- physics invariant violation,
- occupancy mismatch,
- save validation failure,
- load candidate failure,
- render asset fallback.

Beklenen gameplay başarısızlığı (ör. hedefe ulaşılamaması) exception ile çökme gerektirmeyebilir; ancak teknik invariant ihlali sessizce yutulamaz.

### 19.2. Log ve debug overlay

Geliştirme modunda isteğe bağlı:
- axial grid,
- world coordinate,
- actor collider,
- static/dynamic body,
- broadphase candidates,
- contact normal,
- path waypoint,
- ground/depth anchor,
- camera viewport,
- render culling bounds
gösterilebilir.

Debug overlay gameplay state'i değiştirmez ve release build'de kapatılabilir.

### 19.3. Hata güvenliği

Bir entity'nin render asset'i eksikse oyun, tanımlı placeholder ile devam edebilir; fakat content validation hatası raporlanır. Map definition veya ownership gibi kritik veri bozuksa runtime açılışı reddedilir. Save/load hatası mevcut oturumu yarım bırakmaz.

---

## 20. Performans ve donanım hedefleri

Hedef donanım sınırlı sistemleri de kapsar. İlk optimizasyon hedefi karmaşık efekt değil, istikrarlı simülasyon ve görünür alan çizimidir.

### 20.1. Ölçülecek metrikler

- simulation tick duration (p50/p95/max),
- render frame duration (p50/p95),
- frame rate ve frame-time spike,
- aktif actor/body sayısı,
- broadphase candidate sayısı,
- narrowphase pair sayısı,
- visible/rendered entity sayısı,
- culling ratio,
- asset cache hit/miss,
- snapshot creation duration,
- memory footprint (mümkün olduğunda).

### 20.2. Başlangıç kabul hedefi

Kesin sayısal eşikler benchmark baseline alındıktan sonra belirlenir. İlk hedef:
- küçük başlangıç haritasında sabit tick borcu birikmemesi,
- normal kamera hareketinde belirgin takılma olmaması,
- ekran dışı dekorların çizimden elenmesi,
- her frame tüm dünya entity'lerinin brute-force taranmaması,
- asset dosyalarının her frame yeniden yüklenmemesi,
- düşük donanımda gereksiz full-screen Surface kopyalarından kaçınılması.

10/100/1.000/10.000 entity benchmark senaryoları teknik servislerin ölçek davranışını ölçmek için kullanılabilir; bu sayılar oyunun aynı anda bu kadar aktif NPC çalıştıracağı vaadi değildir.

### 20.3. Optimizasyon ilkesi

Önce doğru ve ölçülebilir mimari, sonra optimizasyon. Premature optimization ile sahiplik veya determinism bozulamaz. Benchmark sonucu olmadan “daha hızlı” iddiası kabul edilmez.

---

## 21. Test ve kabul sözleşmesi

Testlerin var olması, geçtikleri anlamına gelmez. Her aşamada gerçek komut ve sonuç kaydedilir.

### 21.1. Unit test

Zorunlu alanlar:
- axial geometry ve round-trip dönüşümleri,
- world↔screen projection/inverse projection,
- camera transform/zoom/bounds,
- movement normalization ve intent priority,
- pathfinding ve walkability,
- physics shape collision ve solver,
- dynamic body collision ve push,
- spatial index vs brute-force,
- depth sorting stable order,
- placement/schema validation,
- snapshot serialization/restore.

### 21.2. Integration test

- karakter yaratma → MainScreen → HexGameplayView akışı,
- keyboard movement ve click-to-move aynı konum otoritesi,
- physics → axial occupancy → actor binding senkronizasyonu,
- player-NPC collision/push,
- NPC avoidance ve companion follow/wait,
- scene placement → asset renderer,
- interaction → doğru domain service,
- window focus → input routing,
- save → process/runtime restore → aynı world state,
- invalid save → candidate publish edilmemesi.

### 21.3. Görsel kabul testi

Gerçek Pygame penceresi üzerinde aşağıdaki kontroller yapılır:
1. Karakter oluşturma sonrası ana dünya görünür.
2. Kamera oyuncuyu takip eder ve zoom çalışır.
3. Terrain ve hücre sınırları tutarlı görünür.
4. Ağaç/kaya/çalı gibi environment asset'leri doğru anchor ile zemine oturur.
5. Oyuncu ağaç önünden ve arkasından geçtiğinde depth/occlusion doğru görünür.
6. NPC sprite'ları görünür ve zemine oturur.
7. Hareket sırasında sprite/facing/animasyon tutarlıdır.
8. Mouse ile hedef seçimi ve click-to-move doğru çalışır.
9. Pencereler dünyayı kapatmadan açılır, taşınır, odaklanır ve X ile kapanır.
10. Escape in-game menu davranışını uygular; açık pencereleri keyfi kapatmaz.
11. UI penceresi üzerindeki tıklama dünya etkileşimi üretmez.
12. Save/load sonrası aktör ve dünya konumları korunur.

Görsel test ekran görüntüsü/video veya açık test checklist sonucu ile belgelenir. Yalnızca unit test geçmesi izometrik görsel hedefin kabulü değildir.

### 21.4. Regression

Her entegrasyon aşamasında ilgili testlerin yanında tam test suite'i çalıştırılır. Sonuç:
- komut,
- işletim sistemi/Python sürümü,
- test sayısı,
- başarısız test,
- commit SHA
ile raporlanır.

### 21.5. Kabul kapısı

Bir aşama ancak:
- kod değişikliği sözleşmeye uygunsa,
- testler geçtiyse,
- mevcut oyun akışı bozulmadıysa,
- save/load uyumluluğu kontrol edildiyse,
- performans etkisi ölçüldüyse,
- gerekiyorsa görsel kabul yapıldıysa
tamamlandı sayılır.

---

## 22. Uygulama aşamaları ve bağımlılık sırası

Aşamalar aşağıdaki sırada yürütülür. Bir sonraki aşama, önceki aşamanın kabul kapısı kapanmadan başlatılmaz.

### Aşama 0 — Mimari baseline ve dosya eşleştirme
- İki dalın commit SHA'larını sabitle.
- Temizlik dalındaki gerçek dosya ağacını ve mevcut testleri çıkar.
- Laboratuvar bileşenlerini dosya/API/bağımlılık/test bazında eşleştir.
- Korunacak, uyarlanacak, yeniden yazılacak ve kapsam dışı kalacak dosyaları tek tek belirt.
- Bu sözleşmeyle mevcut kod arasındaki fark listesini oluştur.
- Kod değişikliği yapılmaz.

**Çıkış:** Dosya bazlı entegrasyon matrisi ve açık risk listesi.

### Aşama 1 — Koordinat ve izometrik projection temeli
- WorldPoint/HexCoord/ScreenPoint sınırlarını netleştir.
- axial↔world ve world↔screen dönüşümlerini ayır.
- 2:1 izometrik projection, inverse transform, camera ve zoom.
- fare hit-test ve round-trip testleri.

**Çıkış:** Test edilmiş projection/camera; henüz tam environment renderer gerekmiyor.

### Aşama 2 — Arazi ve environment placement
- Terrain renderer'ı gerçek content/asset sistemine bağla.
- Asset catalog ve scene placement validation.
- Ağaç, kaya, çalı ve küçük dekorların çizimi.
- Ground anchor/depth anchor ve culling.
- Collider tanımlarını görselden ayrı bağla.

**Çıkış:** Dekorları ve araziyi olan izometrik dünya; collision doğrulanmış statik engeller.

### Aşama 3 — Oyuncu, NPC ve animasyon
- Sprite renderer ve facing.
- Idle/walk/run animasyonları.
- Ground contact ve depth ordering.
- Canopy/foreground occlusion.
- NPC render snapshot bağlantısı.

**Çıkış:** Oyuncu/NPC görsel olarak çevreyle doğru derinlikte.

### Aşama 4 — Hareket ve fizik entegrasyonu
- Movement intent pipeline.
- Physics body/shape adaptörleri.
- Static/dynamic collision.
- Continuous collision ve sliding.
- Player-NPC itişi.
- occupancy ve spatial index senkronizasyonu.

**Çıkış:** Klavye ve click-to-move aynı fizik otoritesinden geçer; itiş testleri geçer.

### Aşama 5 — NPC davranışı ve yoldaşlar
- NPC pathfinding/steering.
- Patrol.
- Avoidance.
- Companion follow/wait.
- Behavior state persistence.

**Çıkış:** NPC ve yoldaşlar fizik ve harita kuralları içinde hareket eder.

### Aşama 6 — Etkileşim ve gameplay content
- Interaction query/selection.
- NPC dialogue, gather, container, door, structure eylemleri.
- UI feedback/toast.
- Content pack placement/definition ilişkileri.

**Çıkış:** Dünya nesneleri gerçek domain servisleri üzerinden etkileşilebilir.

### Aşama 7 — Birleşik kayıt ve determinism
- Snapshot kapsamını tamamla.
- Candidate restore/atomic publish.
- Save/load regression.
- Tick determinism ve failure injection.

**Çıkış:** Yeniden yükleme sonrası tutarlı dünya ve gameplay state'i.

### Aşama 8 — Görsel/performans kabulü ve release hardening
- Görsel checklist.
- Benchmark.
- Düşük donanım profili.
- Log/debug ve hata senaryoları.
- Dokümantasyon ve release doğrulaması.

**Çıkış:** Ana oyun dikey dilimi kabul edilmiş.

---

## 23. Riskler ve açık teknik kararlar

Aşağıdaki konular uygulama öncesinde veya ilgili aşamada kanıtla karara bağlanmalıdır:

| Risk / karar | Neden önemli | Kapatma yöntemi |
|---|---|---|
| Continuous world position'ın tam sahibi | Actor binding/runtime çift otorite riski | Tek owner API ve invariant test |
| Axial map orientation ile 2:1 projection ilişkisi | Hücre merkezleri ve mouse selection hatası | Matematiksel dönüşüm ve round-trip test |
| Hex hücre collider yaklaşımı | Hex topology ile arbitrary obstacle collision uyumu | Geometry adapter ve collision test |
| Dynamic body solver kapsamı | NPC fizik gövdesi var ama itiş yok olabilir | Player-NPC/NPC-NPC integration test |
| Camera smoothing ve fixed tick | Render jitter veya simülasyon bağımlılığı | Render interpolation ve camera tests |
| Canopy occlusion tekniği | Ağaç arkasında oyuncu çizim hatası | Görsel prototype ve acceptance |
| Asset/placement schema | Eski ContentPackage loader ile çakışma | Schema migration ve fixture tests |
| Physics snapshot lifetime | Eski collider veya stale spatial data | Snapshot lifecycle ve update tests |
| Save schema büyümesi | Eski kayıtların bozulması | Versioned migration/reject tests |
| Düşük donanım performansı | Aşırı draw calls ve candidate pairs | Benchmark baseline |

Bir açık kararın varsayılanı belirsizse uygulayıcı kendi başına yeni mimari icat etmez; karar kaydı açılır ve sözleşme güncellenir.

---

## 24. Güvenlik ve kalite kuralları

- İçerik dosyaları güvenilmeyen veri gibi doğrulanır.
- Dosya yolları paket kökü dışına çıkamaz.
- Bilinmeyen asset/schema hataları görünür raporlanır.
- Deterministic gameplay için global rastgele state kullanılmaz; seed sahipliği belirgindir.
- Runtime registry'lerine duplicate ID kabul edilmez.
- Save dosyası yüklenirken bütün referanslar doğrulanır.
- Pygame Surface nesneleri domain/persistence içine sızmaz.
- Her yeni public API test ve dokümantasyonla gelir.
- Geriye dönük uyumluluk alias'ları yeni kodun bağımlılığı haline getirilmez.
- Kullanılmayan legacy sistemler yalnızca açık temizlik kararıyla kaldırılır; aktif gameplay kodu üzerinde körlemesine silme yapılmaz.

---

## 25. Referanslar ve belge hiyerarşisi

Bu sözleşme ana oyun mimarisinin bağlayıcı referansıdır. İlgili alt belgeler kendi dar alanlarında ayrıntı sağlayabilir; bu sözleşmeyle çelişemez.

Temizlik dalında incelenen ilgili belgeler:
- `docs/architecture/30-master-roadmap.md`
- `docs/architecture/34-content-data-contract.md`
- `docs/architecture/51-map-system-cleanup-general-plan.md`
- `docs/architecture/52-map-system-cleanup-technical-plan.md`
- `docs/architecture/57-legacy-map-system-removal-inventory.md`
- `docs/architecture/58-legacy-map-runtime-dependency-graph.md`
- `docs/content/hex-map-authoring.md`

Kod düzeyinde temel inceleme alanları:
- `main.py`
- `application/game_application.py`
- `application/hex_world_initializer.py`
- `application/hex_actor_binding.py`
- `application/content_pack.py`
- `game_ui/game_window.py`
- `game_ui/screens/main_screen.py`
- `game_ui/screens/character_creation_screen.py`
- `game_ui/window_manager.py`
- `game_ui/world_rendering/hex_gameplay_view.py`
- `game_ui/world_rendering/terrain_renderer.py`
- `game_ui/world_rendering/character_renderer.py`
- `game_ui/world_rendering/camera.py`
- `game_ui/world_rendering/depth_sorter.py`
- `game_ui/world_transform.py`

İlgili test alanları:
- `tests/test_application/test_hex_physics_bridge.py`
- `tests/test_application/test_hex_world_runtime.py`
- `tests/test_application/test_hex_world_initializer.py`
- `tests/test_application/test_hex_world_persistence.py`
- `tests/test_application/test_hex_actor_binding.py`
- `tests/test_application/test_game_application_save.py`
- `tests/test_game_ui/test_hex_gameplay_view.py`
- `tests/test_game_ui/test_world_transform.py`
- `tests/test_game_ui/test_window_manager.py`
- `tests/test_game_ui/test_game_window_rendering.py`
- `tests/test_game_ui/test_hex_terrain_renderer.py`
- `tests/test_game_ui/test_depth_sorter.py`

Bu dosyaların listelenmesi, bu sözleşmenin hazırlanması sırasında testlerin çalıştırıldığı veya geçtiği anlamına gelmez.

---

## 26. Nihai mimari karar özeti

| Konu | Bağlayıcı karar |
|---|---|
| Oyun motoru | Python + Pygame CE |
| Ana dünya | Karakter oluşturma sonrası kalıcı MainScreen |
| UI | Dünya üstü taşınabilir WindowManager pencereleri |
| Dünya topolojisi | Axial hex map |
| Hareket koordinatı | Sürekli world-space |
| Hücre üyeliği | World position'dan axial olarak türetilir |
| Görsel projeksiyon | Bağımsız klasik 2:1 izometrik projection |
| Kamera | World-space camera; simulation state'ten ayrı |
| Kimlik sahipliği | Core / WorldActorRegistry / domain sahipleri |
| NPC state | NPCRegistry/social domain |
| Dünya konum/occupancy | HexWorldRuntime ve açık binding sözleşmesi |
| Fizik | Ayrı teknik servis; statik ve dinamik body |
| NPC itişi | Zorunlu hedef davranış |
| NPC avoidance | İtişten ayrı davranış katmanı |
| Yoldaş | Follow ve wait komutları |
| Renderer | Immutable render snapshot tüketir |
| Depth | Ground/depth anchor ve stable sorting |
| Environment | Asset definition + scene placement + optional gameplay entity |
| Interaction | Query/selection sonrası domain service komutu |
| Simülasyon | Core canonical tick ile uyumlu fixed-step |
| Persistence | Tek birleşik GameSaveDocument/HexWorldSnapshot akışı |
| Content | Versioned, validated, data-driven content pack |
| Entegrasyon | Laboratuvar kodu adapter ve kabul testiyle seçilerek alınır |
| Test | Unit + integration + visual + performance acceptance |

---

## 27. Uygulama öncesi zorunlu kontrol listesi

- [ ] Hedef dalın güncel HEAD SHA'sı kaydedildi.
- [ ] Laboratuvar dalının güncel HEAD SHA'sı kaydedildi.
- [ ] İki dalın dosya bazlı farkı ve ilgili API'leri doğrulandı.
- [ ] Bu sözleşmeyle çelişen eski planlar tarihsel olarak işaretlendi.
- [ ] Her sistemin tekil veri sahibi belirlendi.
- [ ] WorldPoint / HexCoord / ScreenPoint dönüşümleri ayrıştırıldı.
- [ ] Physics adapter sınırı belirlendi.
- [ ] Render snapshot schema'sı belirlendi.
- [ ] Content/placement schema ve loader etkisi belirlendi.
- [ ] Save/load migration/reject politikası doğrulandı.
- [ ] Her aşama için test ve görsel kabul maddeleri eşleştirildi.
- [ ] Kod değişiklikleri ancak bu kontrol ve ilgili aşama onayından sonra başladı.

**Son ilke:** Eldoria'nın ana oyun dünyası; harita, fizik, NPC, görsel sunum ve UI'nin birbirine karıştığı tek bir büyük ekran sınıfı olarak değil, açık veri sahipliği ve test edilebilir sözleşmelerle bağlanan bağımsız sistemler bütünü olarak geliştirilecektir.
