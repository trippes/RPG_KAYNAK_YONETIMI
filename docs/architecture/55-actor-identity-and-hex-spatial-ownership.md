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

<text></text>
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

## Güncel durum

- Katman 1 tamamlandı ve Linux/Windows CI kapısından geçti.
- Kare konum `WorldActor` dışına çıkarıldı; geçiş dönemi kare tüketicileri `LegacyActorSpatialStore` üzerinden besleniyor.
- Hex modunda kare konum görünürlüğü ve yazımı kapatılıyor; kayıt/yükleme için askıya alınmış durum korunuyor.
- Katman 2 henüz uygulanmadı: `HexWorldRuntime` hâlâ `HexMovableEntity.position` ile `HexOccupant.position` içinde aynı konumu iki ayrı kayıt olarak tutuyor.

**Bir sonraki uygulama işi:** Katman 2'de occupancy kaydını tek konum otoritesi yapmak; entity kataloğunu kimlik/tür/hareket profili/aktiflik verisine indirgemek ve `HexMovableEntity` nesnesini runtime'dan türetilen salt okunur görünüm haline getirmek.
