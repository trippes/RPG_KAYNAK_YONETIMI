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
- `ActorView` kimlik/oynanış görünümü ile spatial görünümü birbirinden ayırır.
- Kare sisteme ihtiyaç duyan mevcut kod, geçiş boyunca açıkça adlandırılmış legacy kare-konum adaptöründen yararlanabilir. Bu adaptör yalnızca kare modunda etkin olabilir.
- Hex modunda aynı actor için legacy kare konumunu güncel konum gibi sunmak yasaktır.
- Bu geçiş tamamlanana kadar eski kare API'leri kaldırılmaz; fakat hex actor için ikinci bir canlı konum kaynağı olarak kullanılamaz.

### Test kapısı

- Actor kimliği, karakter ve envanter bağları konum değişiminden bağımsız kalır.
- Actor faaliyet yaşam döngüsü spatial refaktörden etkilenmez.
- Hex modundaki actor kimliği için legacy kare konum okuma/yazma girişimleri açıkça reddedilir veya yalnızca uyumluluk sınırında izole edilir.
- Actor silme/yeniden yükleme davranışında kimlik ve ilişkiler korunur.

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
- Aynı actor için `WorldActor.position` ve `HexMovableEntity.position` eşzamanlı, bağımsız ve yazılabilir iki konum kaynağı olarak kalamaz.

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

## Şu anki başlangıç noktası

- `HexWorldRuntimeOwner` runtime örneğini oturum boyunca korur.
- `WorldActor` hâlâ `location_id` ve kare `Position` taşır.
- `HexWorldRuntime` oyuncunun axial konumunu ayrı tutar.
- Dolayısıyla mevcut kod yalnızca runtime yaşam döngüsünü oturumlaştırmıştır; tek konum otoritesi henüz sağlanmamıştır.

**Bir sonraki uygulama işi:** Katman 1'in gerçek tüketicilerini ve snapshot/restore etkilerini testlerle haritalandırıp actor kimliğini spatial konumdan ayıran geriye uyumlu, hex actor için çift konum yazımını engelleyen kod değişikliğini yapmak.
