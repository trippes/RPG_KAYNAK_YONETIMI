# Aşama 5 — Gövde Modeli, Çarpışma ve Fizik Teknik Mimari Planı

> Belge türü: Ayrıntılı teknik mimari, API sözleşmeleri ve uygulama planı  
> Proje: Eldoria — Hex World Laboratory  
> Çalışma dalı: experiment/hex-world-laboratory  
> Durum: TASLAK — KULLANICI TEKNİK ONAYI BEKLİYOR  
> Tarih: 16 Kasım 2026  
> Ön koşullar: Aşama 4 kapalı; Aşama 5 Genel Planı kullanıcı tarafından onaylandı.  
> Kod durumu: Bu belgeyle kod değişikliği yapılmaz.

---

## 1. Teknik hedef

Aşama 5 sonunda hareketli bir aktör, mevcut WorldPoint konumundan hareket etmeye devam ederken fiziksel gövdesiyle statik hex/nesne engellerine çarpmalı; engelin içine girmeden durmalı veya temas yüzeyine paralel kaymalıdır.

Fizik çekirdeği Pygame'den bağımsız olmalı, mevcut geometry/world/movement API'lerini yeniden yazmamalı, 60 TPS hareket sözleşmesini korumalı ve gerçek hex polygon/kenar geometrisini nihai doğruluk kaynağı yapmalıdır.

## 2. Mevcut kod tabanından doğrulanan sözleşmeler

Aşağıdaki dosyalar çalışma dalının mevcut HEAD'i üzerinde incelenmiştir:

| Dosya / API | Mevcut gerçek | Aşama 5 kararı |
|---|---|---|
| geometry/coordinates.py — WorldPoint | Sonlu x/y değerli immutable sürekli dünya noktası | Yetkili dünya konumu olarak korunur |
| geometry/layout.py — HexLayout | Orientation, circumradius ve origin | Hex şekli ve ölçeğinin kaynağı |
| geometry/polygon.py — hex_corners / hex_polygon / hex_edges | Altı köşe ve altı kenarı dünya koordinatında üretir | Hex engel sınırları buradan alınır |
| geometry/transforms.py — world_to_axial | Dünya noktasını mevcut hex sözleşmesiyle çözer | Hücre aday sorgusunda kullanılır |
| world/cell.py — HexCellData | terrain_id, is_walkable, has_obstacle | Hücre düzeyindeki engel işaretini sağlar |
| world/runtime.py — HexWorldRuntime | is_walkable ve has_obstacle sparse override işlemleri | Çalışma zamanı hücre engeli durumu okunur |
| world/map_registry.py / world/world.py | Kayıtlı ve yüklü harita ayrımı | Fizik yalnızca aktif/yüklü harita bağlamında çalışır |
| movement/state.py — MovementState | WorldPoint, Vector2 velocity, MovementMode | Hareket state'iyle uyum korunur |
| movement/integrator.py — MovementIntegrator | Sabit süreli hareket adımı | Çarpışma öncesi önerilen hareketi üretir |
| simulation/movement_system.py — MovementSystem | Ardışık tick doğrulaması, 60 TPS ve state commit | Mevcut davranış geriye dönük korunur |
| world/movement_context.py | Pozisyondan hücre çözümleme; harita yüklemez | Fizik kendi kopya hex dönüşümünü yazmaz |

Mevcut geometry/polygon.py yalnızca hex köşelerini ve kenarlarını üretir; genel amaçlı polygon çarpışma motoru değildir. Aşama 5 bu farkı koruyarak fiziksel geometri işlemlerini physics katmanında tanımlar.

## 3. Bağlayıcı mimari kararlar

### 3.1 Yetkili konum

- WorldPoint, aktörün sürekli dünya konumunun tek doğruluk kaynağıdır.
- AxialCoord yalnızca hücre/topoloji adresidir.
- Ekran pikseli veya sprite konumu fiziksel state olamaz.
- Çarpışma çözümü WorldPoint üzerinde sonuç üretir; hücre merkezine snap yapamaz.

### 3.2 İlk collider kapsamı

İlk uygulamada gereksiz genel amaçlı fizik motoru kurulmayacaktır.

- Hareketli oyuncu için varsayılan collider: daire.
- Hücre engeli için geometri: gerçek hex polygon.
- Nesne engelleri için ilk destek: daire ve dışbükey polygon.
- Collider API'si ileride capsule gibi şekiller eklenebilecek biçimde ayrıştırılır; capsule ilk sürüm zorunluluğu değildir.
- İçbükey nesne geometrisi ilk sürümde doğrudan kabul edilmez. Gerekirse önceden dışbükey parçalara ayrılmış bileşenler olarak tanımlanır.
- Sprite boyutu collider boyutu olarak varsayılmaz. Ağaç sprite'ının tamamı değil, gövde/temas alanı çarpışma şeklidir.

Bu kapsam daire-daire, daire-polygon ve polygon-polygon temel sorgularına izin verir. İlk oyuncu hareket yolu daire collider üzerinden yürütülür; diğer kombinasyonlar test edilmiş ortak geometri API'si olarak sunulur.

### 3.3 Zemin ankrajı ve yükseklik

- ActorBodyTransform, aktörün ground_anchor WorldPoint değerini taşır.
- Collider merkezi, ground_anchor + collider local_offset ile hesaplanır.
- Görsel sprite pivotu ayrı bir render adaptörünün sorumluluğudur.
- body_height pozitif yükseklik tanımıdır; bu aşamada 2D zemin düzlemi çarpışma hesabına dikey eksen eklemez.
- Katman örtüşmesi, y-sort ve kamera derinliği sonraki aşamaların sorumluluğudur.
- Fizik çekirdeği Pygame Surface veya sprite nesnesi saklamaz.

### 3.4 Hex engel kaynağı

- HexCellData.has_obstacle veya etkin runtime override true ise hücrenin gerçek hex polygonu statik engel olarak sunulabilir.
- is_walkable false tek başına fiziksel duvar anlamına gelmez; geçilebilirlik kuralı ile fiziksel engel geometrisi ayrı kavramlardır. Bu aşamada fiziksel engel oluşturmak için açık obstacle kaydı veya has_obstacle işareti gerekir.
- Nesneye özel ağaç/kaya collider'ları hücre verisinin içine gömülmez; map/world kapsamlı statik obstacle kayıtları olarak tanımlanır.
- Aynı fiziksel engel hem hücre polygonu hem nesne collider'ı olarak iki kez eklenirse çifte temas oluşabileceğinden kayıt kimliği ve sahiplik kuralı zorunludur.
- Runtime hücre durumu okunurken HexWorldRuntime iç sözlüklerine erişilmez; public view/runtime API'si üzerinden etkin durum alınır.

### 3.5 Harita sınırı

- Fizik bağlamı tek bir kayıtlı ve yüklü MapId ile çalışır; kendi başına harita yüklemez.
- İlk demo ve kabul senaryolarında harita sınırı kapalı/katı sınırdır: haritada bulunmayan komşu hücreye geçiş engellenir ve sınır gerçek hex kenarlarından üretilir.
- BoundaryPolicy açık bir ayardır; OPEN seçeneği sınırdan çıkışa izin verebilir. Varsayılan demo davranışı BLOCKED olur.
- Kayıtlı ama yüklenmemiş başka bir harita, otomatik olarak engel veya geçiş hedefi sayılmaz. Haritalar arası transfer bu aşama dışıdır.

### 3.6 Zaman ve hareket entegrasyonu

- Simülasyon tick hızı 60 TPS; tick süresi 1/60 saniyedir.
- Her tick'te önce hareket integratörü önerilen konumu hesaplar, sonra fizik çözümü bu hareketi sınırlar, en son state commit edilir.
- Mevcut MovementSystem davranışı korunur; fizik çekirdeği MovementSystem'in içine Pygame bağımlılığı veya özel çarpışma mantığı sokmaz.
- Çarpışmalı yürütüm için simulation/physics sınırında ayrı CollisionAwareMovementSystem veya eşdeğer orchestrator oluşturulur. Tick sırası ve state commit tek yerde tutulur; MovementSystem ile çifte tick ilerletme yapılmaz.
- Normal, running ve stealth modlarının hız çarpanları hareket integratöründen gelir; fizik çözümü hız moduna özel dallanmaz.
- Aynı tick numarası iki kez işlenemez; tick atlanamaz.

## 4. Hedef katman ve bağımlılık düzeni

Application / Demo Orchestrator  
→ Collision-Aware Movement Orchestrator  
→ MovementIntegrator + PhysicsWorld  
→ Broadphase Index  
→ Narrowphase Geometry  
→ Contact Manifold  
→ Collision Solver  
→ Resolved WorldPoint / MovementState

Bağımlılık kuralları:

1. geometry saf matematik olarak kalır; Pygame import etmez.
2. physics geometry tiplerini kullanabilir; geometry world, movement veya Pygame'e bağımlı olamaz.
3. physics doğrudan sprite, Surface, kamera veya ekran koordinatı bilmez.
4. physics dünya sorgusu için tanımlı read-only obstacle provider/context kullanır; HexWorldRuntime iç depolamasına erişmez.
5. movement çekirdeği physics uygulama ayrıntılarını import etmez.
6. simulation/application orchestrator movement ve physics adımlarını sırayla birleştirir.
7. diagnostics fizik state'ini değiştiremez.
8. döngüsel import yasaktır.

## 5. Önerilen paket ve dosya düzeni

Mevcut klasör ağacına göre yeni modüller aşağıdaki gibi önerilir. İsimler uygulama öncesi son kez gerçek ağaçla karşılaştırılacaktır.

- physics/shapes.py — CircleShape, ConvexPolygonShape.
- physics/body.py — BodyDefinition, ActorBodyTransform.
- physics/obstacle.py — ObstacleId, ObstacleDefinition.
- physics/contacts.py — Contact, ContactManifold.
- physics/broadphase.py — AABB ve aday toplama.
- physics/narrowphase.py — kesin şekil temas sorguları.
- physics/collision_world.py — statik engel sorgusu ve boundary policy.
- physics/solver.py — nüfuz düzeltme ve kayma.
- physics/continuous.py — swept circle / time of impact.
- physics/config.py — toleranslar ve çözüm sınırları.
- simulation/collision_movement_system.py — tick ve hareket/fizik orkestrasyonu.
- diagnostics/collision_snapshot.py — salt okunur debug verisi.

Test modülleri:

- tests/unit/test_physics_shapes.py
- tests/unit/test_physics_body.py
- tests/unit/test_physics_contacts.py
- tests/unit/test_physics_broadphase.py
- tests/unit/test_physics_narrowphase.py
- tests/unit/test_physics_solver.py
- tests/unit/test_physics_continuous.py
- tests/unit/test_physics_boundaries.py
- tests/integration/test_collision_movement_ticks.py
- tests/integration/test_collision_world_hex_obstacles.py
- tests/integration/test_collision_movement_modes.py
- tests/integration/test_collision_map_boundaries.py

Bu dosya ağacı öneridir; var olan modüllerle çakışma görülürse önce gerekçeli değişiklik önerilir. Sırf bu şemaya uymak için mevcut modüller taşınmaz veya yeniden adlandırılmaz.

## 6. Temel veri sözleşmeleri

### 6.1 Collider shape

Shape sözleşmesi en az şunları sağlamalıdır:

- Açık shape kind / tip ayrımı.
- Yerel koordinattaki geometrinin doğrulanması.
- WorldPoint transform ile dünya geometrisine dönüşüm.
- Dünya AABB'si.
- Sonlu koordinat ve pozitif boyut doğrulaması.

İlk somut şekiller:

- CircleShape(radius): radius sonlu ve sıfırdan büyük.
- ConvexPolygonShape(vertices): en az üç farklı, sonlu, sıralı köşe; sıfır alan ve kendi kendini kesen polygon reddedilir; ilk sürüm dışbükeylik doğrulanır.

Hex hücre polygonları doğrudan mevcut hex_polygon API'sinden alınır ve immutable polygon temsiline dönüştürülür. Geometri köşeleri yeniden hesaplanmaz.

### 6.2 BodyDefinition

Önerilen immutable alanlar:

- body_id: kararlı aktör kimliği.
- collider: doğrulanmış shape.
- local_offset: ground anchor'a göre collider merkezi/şekil offset'i.
- body_height: sıfırdan büyük yükseklik tanımı.
- enabled: fizik simülasyonuna katılım durumu.

BodyDefinition görsel sprite veya Pygame nesnesi taşımaz.

### 6.3 ActorBodyTransform

Önerilen alanlar:

- ground_anchor: WorldPoint.
- rotation: ilk sürümde 2D dönüş gereksinimi yoksa sabit/0; polygon engellerin yönelimi gerekiyorsa açık dönüşüm değeri.
- collider_world_shape: body local shape + transform sonucu.

Daire collider rotasyondan etkilenmez. İlk oyuncu prototipinde dönüş açısı kullanılmayabilir; API gereksiz dönüş matematiğiyle genişletilmez.

### 6.4 ObstacleDefinition

Önerilen immutable alanlar:

- obstacle_id: map kapsamı içinde benzersiz kimlik.
- map_id: engelin ait olduğu harita.
- shape: daire veya dışbükey polygon.
- position: WorldPoint.
- collision_layer / mask: ilk sürüm tek varsayılan katmanla başlayabilir; gerçek ihtiyaç olmadan karmaşık filtre matrisi kurulmaz.
- source_cell: hex hücre kaynaklı engeller için opsiyonel CellAddress.

### 6.5 Contact

Her temas sonucu en az:

- obstacle_id / cell address gibi kararlı kaynak kimliği.
- contact_point: WorldPoint.
- normal: normalize edilmiş Vector2; normal engelden aktöre doğru yönlenir.
- penetration_depth: negatif olmayan sonlu değer.
- time_of_impact: yalnız swept collision sonuçlarında 0..1 aralığı.
- contact kind / source türü.

Birden fazla temas, deterministik sıralanmış ContactManifold olarak sunulur. Aynı geometri ve aynı girdi, aynı temas sırasını üretmelidir.

## 7. Geometri ve çarpışma algoritmaları

### 7.1 Broadphase

Broadphase'in amacı kesin temas bulmak değil, dar bir aday kümesi üretmektir.

- Aktörün mevcut collider AABB'si ve hareket süpürme AABB'si hesaplanır.
- AABB ile kesişebilecek hücre/engel kayıtları aday listesine alınır.
- Hex tabanlı sorguda world_to_axial ve komşu hücre sorgusu kullanılabilir; sınır durumunda aday kaybetmemek için sorgu muhafazakâr olmalıdır.
- Adayların AABB örtüşmesi yalnızca eleme/aday toplama ölçütüdür.
- Adaylar kararlı kimlik/adres sırasına göre deterministik sıralanır.
- Tüm haritalar veya bütün dünya engelleri her tick taranmaz; yalnız aktif/yüklü harita ve hareketin etkileyebileceği yerel alan sorgulanır.

İlk sürümde küçük demo haritası için doğrudan hücre komşuluğu taraması kabul edilebilir. Ölçüm gerektirmeden karmaşık dinamik AABB ağacı kurulmaz. Engel sayısı arttığında aynı provider arayüzü mekânsal indeksle değiştirilebilir.

### 7.2 Narrowphase

İlk zorunlu sorgular:

1. Circle-Circle.
2. Circle-ConvexPolygon.
3. ConvexPolygon-ConvexPolygon (ortak geometri API'si ve testleri için).

Circle-Polygon için en yakın nokta/kenar ve köşe durumları doğru ele alınmalıdır. Polygon-Polygon için Separating Axis Theorem (SAT) kullanılabilir. Temas normalinin yönü, nüfuz derinliği ve temas noktası tutarlı olmalıdır.

Narrowphase AABB örtüşmesini temas kabul edemez. Kenar temasında tolerans politikası açık ve test edilmiş olmalıdır.

### 7.3 Temas toleransı

- Dünya birimi HexLayout.radius ile aynı ölçek sistemindedir.
- Geometrik epsilon sabit piksel değeri olarak gömülmez; physics config içinde dünya ölçeğine uygun biçimde tanımlanır.
- Tolerans, collider radius ve hex radius ile kıyaslanabilir aralıkta olmalı; aşırı büyük değer geçitleri kapatmamalıdır.
- Tolerans testleri tam temas, çok küçük boşluk, çok küçük nüfuz ve büyük koordinat senaryolarını kapsar.
- Mevcut geometry tolerance API'si incelenir; aynı amaç için ikinci ve çelişkili tolerans sistemi yaratılmaz.

## 8. Çarpışma çözüm modeli

### 8.1 İlk çözüm stratejisi

İlk sürüm için frictionless kinematic character collision seçilir:

1. Hareket integratörü istenen yeni konumu üretir.
2. Broadphase olası engelleri toplar.
3. Narrowphase gerçek temasları hesaplar.
4. Nüfuz varsa aktör engelden dışarı doğru minimum güvenli düzeltme alır.
5. Hareket vektörünün temas normaline doğru içeri yönelen bileşeni kaldırılır.
6. Temas yüzeyine paralel bileşen korunur; böylece duvar boyunca kayma sağlanır.
7. Kalan hareket ve yeni temaslar sınırlı sayıda iterasyonla çözülür.
8. Çözülmüş konum ve velocity tek atomik state commit olarak kaydedilir.

İlk sürümde kütle, momentum, kuvvet, restitution ve fiziksel itiş simülasyonu yoktur. Bu sistem rigid-body solver değil, RPG karakteri için kinematik çarpışma çözümüdür.

### 8.2 Çoklu temas ve köşeler

- ContactManifold kararlı sıralanır.
- Aynı tick içinde birden çok temas sınırlı solver iterasyonuyla ele alınır.
- Çözüm iterasyon sayısı config ile sınırlıdır.
- Her iterasyonda ilerleme yoksa çözüm döngüsü durdurulur ve güvenli son konum korunur.
- Çözüm sonunda kalan penetrasyon tolerans üstündeyse diagnostics/test başarısızlığı üretilir.
- Köşe durumları tek normal varsayımıyla çözülmez; bağımsız temas kısıtları birlikte değerlendirilir.

### 8.3 Duvar boyunca kayma

Hareketin normal bileşeni çıkarılır, teğetsel bileşen korunur. Oyuncu duvara çapraz yürümeye çalıştığında duvarın içine ilerlemez; duvar boyunca kayar. İki duvarın oluşturduğu köşede çözüm, aktörü köşenin içine itmemeli veya titreşimli ileri-geri düzeltme üretmemelidir.

### 8.4 Determinizm

- Engeller ve temaslar kararlı kimlik sırasıyla işlenir.
- Aynı başlangıç state, aynı tick girdileri ve aynı engel verisi aynı sonucu üretir.
- Sözlük iterasyon sırasına bağlı davranış kabul edilmez.
- Rastgele çözüm sırası veya zaman tabanlı fizik davranışı kullanılmaz.

## 9. Sürekli çarpışma / tunneling

Discrete collision yalnızca tick sonundaki konumu kontrol ederse aktör tek tick'te ince engelin öbür tarafına geçebilir.

İlk uygulama daire oyuncu collider'ı için swept circle yaklaşımını temel alır:

- Başlangıç collider konumu ile hedef konum arasındaki süpürme alanı hesaplanır.
- Engelin polygon kenarları ve köşeleri için ilk temas zamanı (time of impact) bulunur.
- En erken geçerli temas seçilir.
- Aktör temas anına taşınır; kalan hareket temas normali boyunca kaydırılarak devam ettirilir.
- Aynı tick'te yeni temas oluşursa sınırlı sayıda impact iteration uygulanır.
- Maksimum iterasyon aşılırsa güvenli temas konumunda kalınır; engelin içinden geçmeye izin verilmez.

Test matrisi:
- Normal hız, koşma hızı ve gizlilik hızı.
- Çok küçük engel ve ince duvar.
- Tek tick'te collider çapından büyük hareket.
- Eğik yaklaşma ve köşeye yaklaşma.
- Birbirine yakın iki engel.
- Farklı tick/frame gözlem koşulları.

CCD yalnızca gerçekten gerekli şekil kombinasyonları için uygulanır; polygon-polygon tam dinamik rigid-body CCD bu aşamanın zorunlu kapsamı değildir.

## 10. 60 TPS hareket entegrasyonu

Mevcut MovementSystem ardışık tick numarası ve 1/60 saniye sözleşmesine sahiptir. Çarpışma entegrasyonu bu davranışı gevşetemez.

Önerilen akış:

1. CollisionAwareMovementSystem beklenen tick numarasını doğrular.
2. MovementIntegrator mevcut MovementState ve MovementIntent ile önerilen hareket state'ini hesaplar.
3. PhysicsWorld bu tick'in hareket süpürmesini çözer.
4. Çözülmüş WorldPoint, velocity ve mode içeren yeni immutable MovementState oluşturulur.
5. Hesaplama başarılıysa state ve sonraki tick numarası birlikte commit edilir.
6. Hata durumunda önceki state ve tick numarası değişmeden kalır.

Mevcut MovementSystem testleri ve API'si korunur. Çarpışma katmanı eski hareket sisteminin state'ini dışarıdan değiştirerek veya ikinci kez tick ilerleterek entegre edilmez.

## 11. Alt aşama teknik planı ve kapıları

### 5.1 — Fiziksel gövde ve collider sözleşmeleri

İşler:
- Shape, CircleShape ve ConvexPolygonShape immutable modelleri.
- BodyDefinition ve ActorBodyTransform.
- Geçersiz radius, nokta, alan, köşe sırası ve finite değer doğrulamaları.
- Sprite/Pygame bağımsızlığı.

Testler:
- Geçerli/geçersiz collider yapımı.
- Daire ve polygon transform.
- Degenerate ve self-intersecting polygon reddi.
- BodyDefinition immutability.
- Pygame import edilmeden paket testi.

Kapı: Gövde ve shape sözleşmeleri test edilmiş; geometri ve render sorumlulukları ayrılmış olmalı.

### 5.2 — Zemin ankrajı ve gövde yerleşimi

İşler:
- Ground anchor ve collider local offset.
- Body height alanının anlamı ve doğrulaması.
- Sprite pivotu ile fiziksel gövde merkezi ayrımı.
- ActorBodyTransform'tan dünya collider geometrisi üretimi.

Testler:
- Offset sıfır ve sıfır dışı konumlar.
- Farklı gövde boyları.
- Anchor sabitken sprite/pivot temsili değişiminin fizik state'ini etkilememesi.
- Negatif/NaN/sonsuz yükseklik reddi.

Kapı: Authoritative fizik konumu ground anchor sözleşmesine bağlı; görsel pivot fiziği değiştirmiyor olmalı.

### 5.3 — Hex ve nesne engel geometrisi

İşler:
- HexCellData.has_obstacle ve etkin runtime durumundan hücre engeli üretimi.
- Mevcut hex_polygon/hex_edges kullanımı.
- ObstacleDefinition, kararlı ID ve map kapsamı.
- Nesneye özel circle/convex polygon engelleri.
- BoundaryPolicy BLOCKED/OPEN.

Testler:
- Flat-top ve pointy-top hex köşe/kenar doğruluğu.
- Aynı hücrede yinelenen engel kaydının engellenmesi.
- Runtime obstacle açma/kapatma.
- Yüklenmemiş haritaya erişimin reddi; otomatik yükleme olmaması.
- Kapalı/açık sınır politikası.

Kapı: Fizik dünyası doğru harita ve gerçek geometriye dayalı, kararlı obstacle kümesi sunmalı.

### 5.4 — Broadphase ve narrowphase

İşler:
- AABB yardımcıları ve muhafazakâr aday toplama.
- Circle-Circle, Circle-Polygon ve Polygon-Polygon sorguları.
- Contact ve ContactManifold.
- Temas normali, temas noktası ve nüfuz derinliği sözleşmesi.

Testler:
- AABB kesişiyor fakat şekiller temas etmiyor örnekleri.
- Kenar/köşe temasları.
- İçeride, dışarıda ve teğet durumları.
- Normal yönü ve nüfuz derinliği.
- Aday toplama yanlış negatif üretmemeli.
- Flat-top/pointy-top engeller.

Kapı: Broadphase yalnız aday üretir; narrowphase gerçek geometriye göre doğru temas sonucunu verir.

### 5.5 — Temas çözümü ve kayma

İşler:
- Minimum penetration correction.
- Temas normaline giren hareket bileşenini kaldırma.
- Duvar boyunca kayma.
- Deterministik çoklu temas çözümü.
- Iterasyon ve tolerans sınırları.

Testler:
- Tek duvara dik ve eğik yaklaşma.
- Duvara paralel hareket.
- 90 derece ve dar açılı köşe.
- İki/üç eşzamanlı temas.
- Bitişik hex engeller.
- Jitter, köşe kilidi, geriye fırlama ve sonsuz döngü kontrolleri.

Kapı: Aktör engel içinde kalmamalı; teğetsel hareket korunmalı ve çözüm sınırlı sürede bitmeli.

### 5.6 — Sürekli çarpışma ve tunneling

İşler:
- Swept AABB broadphase.
- Daire-polygon swept collision / time of impact.
- Temas sonrası kalan hareketin kaydırılması.
- Maksimum impact iteration ve güvenli fallback.

Testler:
- Bir tick'te ince engeli aşabilecek hız.
- Normal/run/stealth hızları.
- Kenar ve köşe çarpışmaları.
- Ardışık engeller.
- Farklı hareket mesafeleri ve başlangıç konumları.

Kapı: Test kapsamındaki hız ve frame-time koşullarında engel geçişi/tunneling oluşmamalı.

### 5.7 — Entegrasyon ve teknik doğrulama

İşler:
- CollisionAwareMovementSystem.
- 60 TPS ardışık tick ve atomik state commit.
- MovementMode hız profillerinin korunması.
- Collision snapshot/debug verisinin üretimi; yalnızca veri modeli, nihai görsel overlay değil.
- Bütün test ve mimari doğrulamaların çalıştırılması.

Testler:
- Hareket + dünya + fizik uçtan uca testleri.
- 60 TPS tick tekrarı/atlama reddi.
- Hata durumunda state/tick rollback.
- Geçilebilir hücre, fiziksel engel ve harita sınırı ayrımı.
- Pygame bağımsız tüm çekirdek testleri.
- Önceki geometri/dünya/hareket regresyonları.

Kapı: Tüm alt sistemler teknik olarak birlikte çalışmalı; otomatik kabul paketi ve rapor girdileri hazır olmalı.

## 12. Test ve CI stratejisi

Her alt aşamada önce ilgili hedefli pytest testleri, sonra gerekli regresyon grupları çalıştırılır. 5.7 sonunda laboratuvarın tüm pytest paketi ve mimari kontrolleri çalıştırılır.

CI:
- GitHub Actions Linux.
- GitHub Actions Windows.
- Core Quality workflow.
- Bağımsız paket import ve Pygame'siz çekirdek testleri.

Görsel testler alt aşama CI'sine zorunlu kılınmaz. Nihai masaüstü görsel kabul, 5.1–5.7 tamamlandıktan sonra kullanıcı bilgisayarında yapılır.

Her raporda komut, gerçek sonuç, test sayısı, CI run kimliği ve başarısızlık/uyarı bilgisi kaydedilir. Sonuç görülmeden başarı varsayılmaz.

## 13. Performans doğrulama planı

Hedef donanım düşük seviye kabul edildiğinden erken optimizasyon yerine ölçüm uygulanır.

Ölçülecek senaryolar:
- 1 aktör / az sayıda engel.
- 10 aktör / orta engel sayısı.
- 100 aktör / yoğun engel sayısı.
- 1000 aktör / stres senaryosu.
- Dar geçit ve çoklu temas yoğunluğu.
- Broadphase aday sayısı ile narrowphase test sayısı.
- Solver iterasyonu ve CCD impact sayısı.

60 TPS tick bütçesi 16.67 ms'dir; bunun tamamı fizik için ayrılamaz. Fizik alt bütçesi benchmark sonuçları ve toplam demo yükü görülmeden sabit bir sayı olarak uydurulmayacaktır. Benchmark ortamı, Python sürümü, tekrar sayısı, ortalama ve üst yüzdelik süre raporlanır. Laboratuvar runner ölçümü kullanıcının i3/4 GB bilgisayarındaki FPS garantisi sayılmaz.

## 14. Hata ve risk politikası

| Risk | Önlem |
|---|---|
| AABB'nin gerçek temas sanılması | Narrowphase zorunlu; false-positive/false-negative testleri |
| Hex kenarlarının yeniden hesaplanması | Mevcut hex_polygon/hex_edges API'sini kullanmak |
| Sprite'ın tamamının collider yapılması | Ground anchor ve object-specific collider |
| Köşede jitter veya sonsuz döngü | Deterministik manifold, tolerans ve iteration sınırı |
| Yüksek hızda tunneling | Swept circle / time-of-impact |
| Her tick tüm haritanın taranması | Yerel broadphase aday sorgusu |
| Runtime iç verisine doğrudan erişim | Public provider/view sözleşmesi |
| MovementSystem tick sözleşmesinin bozulması | Ayrı collision-aware orchestrator ve tick regresyonları |
| Fizik katmanının Pygame'e bağlanması | Architecture boundary testleri |
| Gereksiz rigid-body motoru karmaşıklığı | Kinematik karakter çarpışmasıyla sınırlı ilk sürüm |

## 15. Kapsam dışı teknik işler

- Kuvvet, kütle, momentum, restitution ve genel rigid-body simülasyonu.
- İlk sürümde capsule collider zorunluluğu.
- Dinamik-dinamik aktör itişmesi ve kalabalık çözümü.
- Tam fizik materyali/friction sistemi.
- Kamera, y-sort, sprite animasyonu ve nihai collider debug çizimi.
- Pathfinding, NPC AI, etkileşim ve ana oyun entegrasyonu.
- Ağ/multiplayer deterministik fizik.

Bu ihtiyaçlardan biri zorunlu hâle gelirse uygulama sırasında sessizce eklenmez; kapsam ve performans etkisi kullanıcıya sunulur.

## 16. Aşama sonu teslimatları

- Physics/collision çekirdeği ve testleri.
- Collision-aware movement entegrasyonu.
- Tek hücre, bitişik engel, dar geçit, duvar ve köşe senaryo haritaları.
- Otomatik test ve CI kanıtları.
- Benchmark ve bilinen sınırlar raporu.
- Nihai görsel kabul kontrol listesi ve kullanıcı sonuçları.
- reports/PHASE-05-CLOSURE-REPORT.md.

---

Bu belge teknik mimari önerisini ve uygulama kapılarını tanımlar. Kullanıcı teknik planı açıkça onaylamadan 5.1 kodlamasına başlanamaz. Her alt aşamanın tamamlanması, sonraki alt aşamaya otomatik onay anlamına gelmez.
