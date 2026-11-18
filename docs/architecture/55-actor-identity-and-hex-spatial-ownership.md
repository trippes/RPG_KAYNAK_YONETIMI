# Actor Kimliği ve Hex Konum Sahipliği Sözleşmesi

**Durum:** Kullanıcı onayladı; üç katman sırasıyla uygulanacak.  
**Dal:** `experiment/map-cleanup`  
**Üst kapsam:** Aşama 16.2.1 — konum sahipliğini tekilleştirme.  
**Görsel kabul:** Gerekli değil. Pytest, Ruff, paketleme ve Linux/Windows CI kullanılacak.

## Amaç

Mevcut modelde `WorldActor` kimlik/oynanış verilerinin yanında kare `location_id + Position(x,y)` konumunu tutuyor. Aynı actor kimliği, `HexWorldRuntime` içinde ayrıca `EntityPosition(map_id, LocalHexPosition(q,r))` ile temsil edilebiliyor. İki kayıt birbirinden bağımsız değişebildiğinden bu durum kalıcı mimari olamaz.

Bu sözleşme üç ayrı katmanı, aşağıdaki sırayla ve ayrı doğrulama kapılarıyla uygular. Kare koordinatları axial koordinatlara dönüştürülmez.

## Katman 1 — Actor kimliği ve oynanış verisi

### Sorumluluk sınırı

Actor kimliğinin ve actor'a bağlı oynanış ilişkilerinin sahibi uygulama oturumundaki actor registry olmaya devam eder.

Bu katmanda korunacak veriler:
- `actor_id`, `world_id`, `role` ve `active`;
- karakter bağlantısı (`character_id`);
- envanter bağlantısı (`inventory_id`);
- faaliyet kimliği ve faaliyet yaşam döngüsü.

Bu veriler spatial konum değildir. Hex geçişinde yeniden yaratılmaz, sıfırlanmaz veya başka bir actor kimliğine taşınmaz.

### Konumdan ayrıştırma

- Nihai modelde `WorldActor` kendi başına harita kimliği veya hücre koordinatı saklamaz.
- `ActorView`, eski kare tüketicileri için registry tarafından oluşturulan geçiş dönemi uyumluluk projeksiyonudur; konumun sahibi değildir.
- Kare konumun gerçek sahibi `LegacyActorSpatialStore` olur. `WorldActor` konum alanı veya konum yazma metodu taşımaz.
- Kare sisteme ihtiyaç duyan mevcut kod, geçiş boyunca registry'nin açık `set_legacy_position` / `legacy_spatial_state` sınırından yararlanabilir. Bu adaptör yalnızca kare modunda görünürdür.
- Hex modunda aynı actor için legacy kare konumunu güncel konum gibi sunmak yasaktır.
- Bu geçiş tamamlanana kadar eski kare API'leri kaldırılmaz; fakat hex actor için ikinci bir canlı konum kaynağı olarak kullanılamaz.

### Test kapısı

- Actor kimliği, karakter ve envanter bağları konum değişiminden bağımsız kalır.
- Actor faaliyet yaşam döngüsü spatial refaktörden etkilenmez.
- Hex modundaki actor kimliği için legacy kare konum okuma/yazma girişimleri açıkça reddedilir veya yalnızca uyumluluk sınırında izole edilir.
- Actor silme/yeniden yükleme davranışında kimlik ve ilişkiler korunur.
- Hex görünümü açıkken snapshot alınsa bile gizlenmiş legacy kare konumu kayıt verisinde korunur; restore edilen oturum kare konumunu kaybetmez.

### Katman 1 uygulama sonucu

- `ActorIdentity` değişmez kimlik nesnesidir; `WorldActor` yalnızca kimlik ve oynanış bağlantılarını tutar.
- `LegacyActorSpatialStore` kare `location_id + Position` bilgisini ayrı saklar.
- `WorldActorRegistry` eski `ActorView` alanlarını store'dan birleştirerek üretir; eski kare ekranlarının geçişi kontrollü sürer.
- Hex görünümüne girerken kare konum askıya alınır; görünümde okunamaz ve yazılamaz. Çıkışta önceki kare konum geri açılır.
- `ActorSnapshot` askıya alınmış kare konumu da serialize eder ve restore sırasında ayrı store'a geri yükler.

**Doğrulama:** Commit `1ce7c99c475d9e5a8130b9dda312e9fdf2017fa6`; GitHub Actions run [#44420129550](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44420129550) — Linux ve Windows başarılı. Linux: 1.473 test + 237 subtest, Ruff, compileall, wheel ve izole kurulum doğrulaması başarılı.

## Katman 2 — HexWorldRuntime tek konum otoritesi

### Sorumluluk sınırı

Hex dünyasında hareketli entity konumunun tek yazarı `HexWorldRuntime` olacaktır.

Otoriter konum:
- `map_id`;
- `LocalHexPosition(q,r)`;
- runtime tarafından yönetilen occupancy/doluluk kaydı.

`WorldHexPosition` yalnızca haritaların dünya üzerindeki yerleşimini ifade eder; hareketli entity'nin yerel konumu yerine kullanılamaz.

### Kurallar

- Bir actor/entity kimliği için tek bir hex spatial kaydı bulunur.
- Hareket, harita geçişi, çarpışma ve doluluk aynı runtime üzerinden yürütülür.
- Renderer ve UI konumu yalnızca okur; konum yazmaz.
- `HexWorldView` runtime sahibi değil, oturum runtime'ına bağlanan sunum/input katmanıdır.
- Runtime oluşturma ve restore işlemleri yarım kayıt veya yinelenen occupancy bırakmaz.
- Runtime'ın oturum ömrü `SessionBundle` ve `GameplayService` üzerinden yönetilir.
- `HexMovableEntity` içindeki konum yalnızca runtime tarafından üretilen salt okunur görünüm olmalıdır; entity kataloğunda ikinci bir yazılabilir konum kopyası tutulamaz.
- Occupancy kaydı, hareketli entity'nin tek otoriter `EntityPosition` kaynağı olmalıdır; tüm hareket ve geçiş sonuçları bu kaynaktan türetilir.

### Test kapısı

- Tek actor kaydı ve tek occupancy kaydı.
- Aynı actor için yinelenen entity kaydı reddedilir.
- Geçersiz harita/hücre ve dolu hücre hareketleri reddedilir.
- Başarısız hareket eski konumu ve occupancy'yi korur.
- Harita geçişi tek işlem olarak tamamlanır; hata halinde kısmi transfer olmaz.
- Oturumdan çıkıp aynı oturuma dönme mevcut runtime ve konumu korur.

### Katman 2 uygulama sonucu

- `HexWorldRuntime` içindeki `_HexEntityState` yalnızca entity kimliği, türü, hareket profili ve aktiflik bilgisini tutar; konum alanı içermez.
- `HexOccupancyRegistry` hareketli entity'nin tek otoriter `EntityPosition` kaynağıdır.
- `HexWorldRuntime.entity()` ve `entities()`, konumu occupancy kaydından türetilen değişmez `HexMovableEntity` görünümleri üretir.
- Normal hareket ve harita geçişi artık ikinci bir entity konum kopyası yazmaz; yalnızca occupancy kaydını günceller.
- Eksik occupancy kaydı veya entity/occupancy tür uyuşmazlığı sessizce kabul edilmez; runtime tutarsızlığı açık hata üretir.
- Geçersiz entity türü/aktiflik bilgisi, occupancy kaydı eklenmeden önce reddedilir; yarım kayıt bırakılmaz.
- Hex runtime'ın oturum içinde korunması ve görünümden çıkıp dönünce konumun sürmesi mevcut owner davranışıyla test edilir.

**Doğrulama:** Commit `92e6132ceb0542c14247f7aa92a6c8993845b2a8`; GitHub Actions run [#44420944142](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44420944142) — Linux ve Windows başarılı. Her iki platformda 1.476 test + 237 subtest; Linux Ruff, compileall, wheel ve izole kurulum doğrulaması başarılı.

**Sınır:** Hex runtime konumu hâlâ oturum içi bellekte tutulur; ana oyun save/load belgesine hex konumunun eklenmesi Katman 3 kayıt/yükleme entegrasyonunda ele alınacaktır.

## Katman 3 — Legacy kare servisleri için uyumluluk sınırı

### Amaç

Kare konuma bağlı sistemleri bir kerede silmek yerine, her bağımlılığı hex sözleşmesine kontrollü taşımak.

### Kurallar

- Her servis bağımlılığı açıkça envanterlenir: hareket, harita geçişi, NPC, kaynak, pazar, konteyner/dünya nesnesi, görev etkileşimi, kayıt/yükleme ve UI.
- Hex modundaki servisler konumu runtime'dan sorgular; `WorldActor` içindeki kare konum alanlarına başvurmaz.
- NPC ve kaynak yerleşimleri axial içerik verisi olarak açıkça tanımlanır. Eski `[x,y]` değerleri otomatik `[q,r]` değerine çevrilmez.
- Kare modunda çalışan eski servisler yalnızca legacy kare katalog ve adaptör sınırında kalır.
- Kare ve hex harita kimlikleri/koordinat tipleri birbirine karıştırılmaz.
- Her servis taşındıkça eski bağımlılığı için regresyon testi eklenir; son tüketici kaldırılmadan legacy adaptör silinmez.
- NPC otonom hareketi, pathfinding, yeni ekonomi veya yeni oynanış davranışı bu geçişin kapsamı değildir.

### Kayıt/yükleme kuralı

Yeni hex kayıtları axial konumu açık biçimde saklar ve restore sırasında harita, hücre ve occupancy tutarlılığını doğrular. Eski kare kayıtlar otomatik dönüştürülmez; silinmez ve sessizce üzerine yazılmaz. Legacy kayıt politikası 16.2.4 kapısında ayrıca tasarlanır. Bu belge tek başına eski kayıt migration'ına izin vermez.

### Test kapısı

- Hex servislerinin kare `Position` ve kare `MapDefinition` bağımlılığı kalmadığı testlerle kanıtlanır.
- İçerik referansları harita/landmark/entity kimlikleri üzerinden doğrulanır.
- Kaynak, pazar, NPC, konteyner, görev etkileşimi ve kayıt/yükleme testleri geçer.
- Legacy kare akışı yalnızca kendi ayrı sınırında çalışır.
- Tam Pytest, Ruff, compileall, wheel doğrulaması ve Linux/Windows CI geçer.

## Uygulama sırası ve değişiklik disiplini

1. Katman 1 tamamlanır ve test kapısı geçmeden Katman 2'ye başlanmaz.
2. Katman 2 tamamlanır ve tek konum/occupancy otoritesi testlerle kanıtlanmadan Katman 3'e başlanmaz.
3. Katman 3 servis servis uygulanır; her servis kendi testleriyle taşınır.
4. Her katman ayrı commit ve ayrı CI doğrulaması alır.
5. Herhangi bir aşamada başarısız CI varsa sonraki katmana geçilmez.
6. `main`, `demo_eldoria` ve `experiment/hex-world-laboratory` değiştirilmeyecek; entegrasyon dalı açık kullanıcı onayı olmadan birleştirilmeyecek.

## Katman 3 — ilk uyumluluk geçişi

- `GameplayService` içindeki konum gerektiren etkileşim, pazar, NPC ticareti, diyalog ve görev teslimi kontrolleri artık `ActorView.location_id` okumuyor; açık `_require_legacy_actor_location` sınırından geçiyor.
- Kare modundaki aktör listeleri konum eşleştirmesini registry'nin legacy spatial store kaydı üzerinden yapıyor.
- `GameApplication` save restore doğrulaması ve kare konum geri yüklemesi `ActorView.location_id/position` alanları yerine registry spatial store kaydını kullanıyor.
- Hex görünümü aktifken legacy konum bulunmadığından kare konum etkileşimi reddediliyor; görünümden çıkışta kare konum geri açılıyor.
- NPC'nin konumu tanımlı değilse mevcut konum-bağımsız diyalog/görev davranışı korunuyor.

**Doğrulama:** Commit `733c23f31258d92e9d4bb260618ef9c9a633eaf4`; GitHub Actions run [#44421720503](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44421720503) — Linux ve Windows başarılı; her iki platformda 1.477 test + 237 subtest. Linux Ruff, compileall, wheel ve izole kurulum doğrulaması başarılı.

## Güncel durum

- Katman 1 tamamlandı; actor kimliği/oynanış verisi ile kare konum sahipliği ayrıldı.
- Katman 2 tamamlandı; hex konumu occupancy kaydı tek başına yönetiyor ve entity görünümü bu kayıttan türetiliyor.
- Katman 3 başladı; servis ve save restore katmanındaki ilk legacy konum bağımlılıkları açık sınıra taşındı.
- UI ekranları hâlâ geçiş dönemi `ActorView` konum projeksiyonunu kullanıyor; bu uyumluluk alanı henüz kaldırılmadı.
- NPC, kaynak, pazar ve konteyner içerikleri hâlâ kare tabanlı konum modelleriyle tanımlı. Hex tarafında NPC/kaynak/market yerleşimleri ve hex başlangıç alanı henüz eksik.
- Hex runtime konumu oturum belleğinde tutuluyor; ana save/load belgesine entegrasyonu henüz yapılmadı.
- Eski kare kayıtlar otomatik dönüştürülmeyecek; migration/recovery politikası ayrıca belirlenecek.

**Bir sonraki uygulama işi:** Kalan UI ve domain tüketicilerini dosya/fonksiyon bazında envanterleyip kare uyumluluk projeksiyonunu servis API'sine taşımak. NPC/kaynak/market için axial yerleşim gerektiren noktalarda koordinat uydurulmayacak; açık içerik verisi ve tasarım kararı beklenecek.
