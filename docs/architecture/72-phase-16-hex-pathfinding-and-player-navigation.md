# Aşama 16 — Hex Pathfinding ve Oyuncu Navigasyonu

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **A* YOL BULMA, TIKLA-VE-HAREKET ET VE OYUNCU NAVİGASYONU BAĞLANTISI TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**

## 1. Yol bulma sözleşmesi

`application/hex_pathfinding.py` içindeki `HexPathfinder`, schema-v2 axial `HexMapDefinition` üzerinde deterministik A* araması yapar.

- Arama yalnızca mevcut local map'in `valid_cells` maskesi içinde ilerler.
- Axial hex mesafesi sezgisel maliyet olarak kullanılır; her komşu hücreye geçiş maliyeti birdir.
- `MovementProfile` arazi geçiş kurallarını, engelli hücre davranışını ve occupancy istisnalarını belirler.
- Runtime tarafından sağlanan dolu/işgal edilmiş hücreler yol dışında tutulur; occupancy'yi yok sayan profiller bu kısıttan muaftır.
- Geçersiz başlangıç/hedef, erişilemeyen hedef veya yol bulunamaması durumunda arama `None` döndürür.
- Heap girdilerinde sayısal tie-break alanları kullanıldığı için eşit öncelikli düğümler deterministik biçimde sıralanır; eski maliyetli kuyruk girdileri atlanır.

Yol bulma yalnızca rota hesaplar. Kimlik, konum ve occupancy sahipliği `WorldActorRegistry` ile `HexWorldRuntime` sınırlarında kalır.

## 2. Runtime hareketi

`HexWorldRuntime.path_to` mevcut entity'nin hareket profili ve occupancy kayıtlarıyla yol üretir. `move_toward` yalnızca bulunan yolun bir sonraki hücresine hareket eder; hareket, normal runtime doğrulamasından geçirilerek occupancy üzerinde atomik olarak uygulanır.

Hareketi devre dışı bırakılmış veya hareket profili izin vermeyen entity için `MOVEMENT_NOT_ALLOWED` sonucu korunur. Yol bulunamaması bu durumla karıştırılmaz.

`ActorHexBindingService.move_toward` canonical actor kaydını ve aktif dünya kapsamını doğrular; yeni actor kimliği veya ikinci konum kaydı oluşturmaz.

## 3. Pygame navigasyonu

`HexGameplayView` aşağıdaki kullanıcı akışlarını sağlar:

- Fareyle harita panelinde tıklanan ekran koordinatı `WorldTransform.screen_to_axial` ile axial hücreye çevrilir.
- Hedef hücrenin aktif map'in valid-cell maskesinde olması gerekir.
- Geçerli hedef için oyuncu hemen ilk pathfinding adımını atar; kalan adımlar `MOVE_STEP_SECONDS = 0.18` zaman aralığıyla sürdürülür.
- Hedef hücre görsel bir işaretçiyle gösterilir.
- Sağ tık hedefi iptal eder; yön tuşlarıyla manuel hareket otomatik hareket hedefini temizler.
- Oyuncu başka map'e geçerse veya runtime/entity kaydı kaybolursa eski hedef temizlenir.
- Harita geçişleri A* rotasının parçası değildir; yalnızca map üzerinde tanımlanmış aktif geçiş kayıtları üzerinden ayrı transition servisiyle gerçekleşir.

`MainScreen.update(elapsed_seconds)`, `GameWindow.step` içindeki frame süresiyle çağrılır. Böylece otomatik hareket gerçek oyun döngüsüne bağlıdır; sunum katmanı kendi konum veya tick otoritesini oluşturmaz.

## 4. Doğrulama kapsamı

- En kısa yol ve engelli hücre çevresinden alternatif rota.
- Valid-cell maskesi ve movement profile kısıtları.
- Occupancy tarafından işgal edilen hücrelerden kaçınma.
- Pathfinding hareketinin yalnızca bir sonraki hücreye ilerlemesi.
- Hareketi devre dışı entity'nin konumunun değişmemesi ve doğru `MOVEMENT_NOT_ALLOWED` sonucu.
- Actor binding üzerinden pathfinding hareketinde canonical actor kimliğinin korunması.
- Altı axial yönlü manuel hareket ve authored map transition seçimi.
- Fare tıklamasının doğru axial hedefe çevrilmesi.
- Frame update döngüsünün otomatik hareket hedefini ilerletmesi.
- Harita render'ının authoritative entity konumunu değiştirmemesi.

## 5. CI doğrulaması

- Doğrulanan HEAD: `a6f72b33ce1f45f7b8a09c95fa4b250f71967518`
- GitHub Actions: [#44532041598](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44532041598)
- Linux: başarılı — **2.266 test + 235 subtest**.
- Windows: başarılı — **2.266 test + 235 subtest**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 6. Kalan kabul sınırı

Teknik navigasyon hattı ve CI doğrulaması tamamlandı. Bununla birlikte varsayılan `demo_eldoria` package'ına bu çalışma kapsamında axial map veya `world.hex_start` eklenmedi. Bu nedenle gerçek oyun dünyasında tıklayarak hareketin görsel/oynanış kabulü, yeni harita içeriği ve açık oyuncu başlangıç hücresi eklendikten sonra ayrıca yapılmalıdır. Bu rapor, henüz üretilmemiş dünya içeriğini veya manuel oyun testini tamamlanmış saymaz.
