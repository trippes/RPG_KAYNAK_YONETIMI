# Aşama 16.2 — Altıgen Runtime'ın Ana Oyun Otoritesi Olması

**Durum:** Kullanıcı entegrasyon sıralamasını onayladı. Teknik mimari geçiş planı hazırlandı; uygulama adımları bu sözleşmeye göre yürütülecek.  
**Dal:** `experiment/map-cleanup`  
**Kapsam:** Altıgen yerel harita + dünya haritası sistemini ana oynanışın tek aktif dünya sistemi yapmak; eski kare sistemi daha sonra tek gizli Paskalya yumurtasına indirgemek.  
**Görsel kabul:** Gerekli değil. Teknik doğrulama otomatik testler, statik analiz, paketleme ve CI ile yapılır.

## 1. Karar ve hedef

Kullanıcı, eski kare harita temizliğinden önce altıgen runtime entegrasyonunun yapılmasını onayladı. Ana oyun açıldığında oyuncu doğrudan altıgen dünyada bulunmalıdır. `H` ile açılan geçici demo/portal akışı kaldırılmalı; altıgen dünya normal oyun akışının kendisi olmalıdır.

Nihai durumda:
- Ana dünya sistemi altıgen axial yerel haritalardan ve `WorldMapDefinition` dünya yerleşiminden oluşur.
- Oyuncu konumu, hareketi, harita geçişleri ve doluluk/çarpışma tek bir otorite tarafından yönetilir.
- NPC'ler, kaynak düğümleri, pazarlar, konteynerler ve dünya nesneleri altıgen harita kimlikleri/konumlarıyla ilişkilendirilir.
- Kayıt/yükleme aynı otoriter altıgen konum durumunu kaydeder ve geri yükler.
- Kare `(x,y)` sistemi altıgen koordinatlarına matematiksel olarak dönüştürülmez. Koordinat türleri ve içerik sözleşmeleri ayrı kalır.
- Eski kare harita sisteminden yalnızca tek, gizli ve ayrı çalışan Paskalya yumurtası haritası kalır.
- Laboratuvar dalı arşiv olarak kalır; bu entegrasyon sırasında değiştirilmez.

## 2. Mevcut koddan doğrulanan durum

### 2.1 İki ayrı konum otoritesi var

- `WorldActor`, `location_id` ve `core.domain.spatial.Position` (kare `x,y`) saklıyor.
- `HexWorldView.enter()`, oyuncu actor kimliğini alıp ayrı bir `HexWorldRuntime` oluşturuyor ve oyuncuyu varsayılan olarak `hex_forest_demo` / `(0,0)` konumuna kaydediyor.
- Hex hareketi `HexWorldRuntime` içindeki `HexMovableEntity.position: EntityPosition` üzerinde gerçekleşiyor.
- `HexWorldView.leave()` bu runtime'ı bırakıyor; actor'ın kare konumu değişmeden kalıyor. Yeniden girişte hex başlangıç konumu yeniden kuruluyor.
- `MainScreen` normal oynanışta kare `MapDefinition`, `WorldMap`, `Position(x,y)`, dört yönlü hareket ve kare harita geçişlerini kullanıyor. `H` yalnızca hex görünümüne geçiş yapıyor.

Bu nedenle sorun bir çizim/renderer değişikliği değildir. Konum ve hareket sahipliği uygulama mimarisinde değiştirilmelidir.

### 2.2 İçerik yükleme ve doğrulama kare haritaya bağlı

- `ContentPackage` hem `map_definitions` (schema v1 kare) hem `hex_map_definitions` (schema v2 axial) taşıyor.
- `content_loader.py`, kare katalog yükleyicisini çağırıyor; hex haritaları ayrıca yüklüyor ve `world.json` ile doğruluyor.
- `populate_opening_content()` ve `_register_opening_content()` başlangıç haritasını kare `map_definitions` içinden seçiyor.
- `_validate_content_references()` NPC, kaynak, pazar ve ticaret partneri referanslarını kare harita kimliği ve kare koordinatlarla doğruluyor.
- NPC kayıtları `location_id + [x,y]`; kaynak düğümleri `location_id + landmark_id`; pazarlar `location_id` ve isteğe bağlı `[x,y]` kullanıyor.
- Quest hedefleri NPC ve kaynak kimliklerine bağlı; koordinatları doğrudan taşımıyor. Bu kimlikler korunmalı.

### 2.4 Mevcut hex içerik, ana gameplay'i taşımaya henüz yeterli değil

İçerik dosyalarının sayısal denetimi şu farkı gösteriyor:

- Kare gameplay tarafında 4 NPC tanımı var; tamamı `village_id` üzerinde kare `[x,y]` konumuyla tanımlı.
- Kare gameplay tarafında 22 kaynak düğümü var; orman ve maden haritalarına, kare landmark ID'lerine bağlanmış.
- Başlangıç pazarı `village_id` ve `innkeeper_mira` NPC'sine bağlı.
- Mevcut axial dünya 7 yerel haritadan oluşuyor.
- Bu 7 hex haritanın yalnızca `hex_forest_demo` dosyasında bir resource landmark bulunuyor. Bu landmark `demo_ore_node` ID'sine bağlı; mevcut 22 kayıtlı kaynak düğümü listesinde bu ID yok. Diğer altı hex haritada landmark bulunmuyor.
- Mevcut hex haritalarında köy başlangıç alanı, dört mevcut NPC'nin yerleşimi, 22 kaynak düğümünün karşılıkları ve mevcut pazar konumu tanımlı değil.

Bu nedenle mevcut hex harita seti, yalnızca runtime bağlantısı yapılarak eski starter gameplay'in yerine geçirilemez. İçerik tarafında köy/başlangıç bölgesi, NPC yerleşimleri, kaynak landmark'ları ve pazarın yeni axial yerleri tasarlanıp doğrulanmalıdır. Eski kare `[x,y]` konumları hex `[q,r]` koordinatlarına otomatik çevrilmeyecek; her yeni hex yerleşimi açık içerik verisi olarak yazılacaktır.

### 2.3 Kayıt/yükleme kare harita kataloğunu yeniden kuruyor

- `ActorSnapshot`, actor için `location_id` ve `Position` kaydediyor.
- `GameApplication.load()`, kayıtlı actor konumlarının aktif kare dünya haritasında bulunmasını ve kare harita sınırlarını doğruluyor.
- Kaynak düğümlerinin `location_id` alanları da kare harita kimliklerine göre kontrol ediliyor.
- Birleştirilmiş kayıt zarfı `GameSaveDocument` ve mevcut kayıt sürümleme/migration hattı üzerinden okunuyor.

Kayıt/yükleme entegrasyonun zorunlu parçasıdır; yalnızca ekrana hex çizmek yeterli değildir.

## 3. Hedef mimari sözleşmesi

### 3.1 Tek konum yazarı

`HexWorldRuntime`, altıgen dünyadaki hareketli varlıkların tek konum ve doluluk otoritesi olacaktır.

- Otoriter yerel konum tipi: `EntityPosition(map_id, LocalHexPosition(q,r))`.
- Haritaların dünya üzerindeki yerleşimi: `WorldHexPosition(q,r)`; bu tip yalnızca harita-harita dünya yerleşimini ifade eder.
- `LocalHexPosition` ile `WorldHexPosition` birbirinin yerine kullanılamaz.
- `HexWorldView` runtime oluşturup yok eden bir yaşam döngüsü sahibi olmayacak; var olan runtime'a bağlanan input/render sunum katmanı olacaktır.
- `WorldActor` ve sosyal NPC kayıtları aynı konumu ikinci kez yazan paralel otoriteler olarak kalmayacak. Actor/NPC kimliği, karakter, envanter, ilişki ve davranış verileri kendi alanlarında kalacak; konum runtime otoritesinden okunacaktır.
- Her entity kimliği için tek kayıt, tek konum yazarı ve tek doluluk kaydı bulunacaktır. Restore işlemi yinelenen kayıt üretmeyecektir.

Bu sözleşme, Core'un genel `World` / `WorldManager` saat ve yaşam döngüsü yapılarını kare harita kodu sanıp silmeyi gerektirmez. Bu genel Core yapıları korunur.

### 3.2 Dünya ekranı ve pencere sistemi

- Ana oyun yüzeyi `HexWorldView` tabanlı altıgen dünya olacaktır.
- `MainScreen` içindeki kare grid çizimi, dört yönlü hareket, kare yol bulma ve kare JSON geçişleri ana oynanış yolundan çıkarılacaktır.
- `H` portal davranışı kaldırılacaktır; altıgen dünyaya geçmek için portal gerekmez.
- `GameWindow` ve `WindowManager` envanter/karakter/görev/harita/üretim/pazar pencerelerinin mevcut pencere davranışını koruyacaktır. Bu aşama pencere sistemini yeniden tasarlamaz.

### 3.3 İçerik sözleşmesi

- `world.json` ve schema v2 hex haritalar ana dünya kataloğunun kaynağı olur.
- Oyuncu başlangıç konumu açıkça paket içeriğinde tanımlanır; `(0,0)` gibi UI içinde sabit kodlanmış başlangıç varsayımı kalmaz.
- NPC içerikleri `map_id` ve axial `[q,r]` konumu kullanır. NPC'ler bu aşamada sabit kalır; otonom hareket veya AI eklenmez.
- Kaynak düğümleri hex haritasındaki landmark kimliğiyle bağlanır. Kaynak miktarı/kapasitesi/yenilenme ve mevcut node kimlikleri korunur.
- Pazar, ilgili NPC kimliği ve hex harita konumu üzerinden tanımlanır. Pazar envanteri, fiyat, stok yenileme ve ticaret kuralları değişmez.
- Quest tanımları NPC/resource kimlikleri üzerinden çalışmaya devam eder; gereksiz koordinat bağımlılığı eklenmez.
- Konteyner ve dünya nesnesi yerleşimleri `EntityPosition` / axial map placement sözleşmesine geçirilir.
- AssetCatalog ve ScenePlacementCatalog mevcut sunum içerik sahipliğini korur. Aynı harita yerleşimi için ikinci bir yazma kaynağı oluşturulmaz.

### 3.4 Kayıt sözleşmesi ve eski kayıtlar

Yeni kayıtlar oyuncu ve altıgen dünyadaki ilgili entity konumlarını axial `EntityPosition` olarak saklamalıdır. Restore, harita tanımlarını, dünya yerleşimini, geçerli hücreleri, entity konumlarını ve doluluk çakışmalarını doğrulamalıdır.

Eski kare kayıtların `location_id + Position(x,y)` alanları otomatik veya genel bir kare→hex koordinat dönüşümüne tabi tutulmayacaktır. Bu dönüşüm kullanıcı tarafından daha önce reddedilen koordinat sistemi karışıklığını doğurur ve konum semantiğini varsaymak olur.

Bu nedenle:
1. Yeni hex kayıt sözleşmesi ve round-trip testleri önce tamamlanır.
2. Mevcut kare kayıtları için açık bir uyumluluk politikası, kayıt örnekleri ve testleri olmadan eski kayıt migration kodu yazılmaz.
3. Eski kayıt verileri hiçbir koşulda sessizce üzerine yazılmaz; mevcut atomik yedekleme/geri alma davranışı korunur.
4. Sekiz kare haritanın kaldırılması, eski kayıtların güvenli biçimde ele alınması ve tek kare Paskalya yumurtası kararının tamamlanmasına bağlıdır.
5. Gerekirse eski kayıtlar için açık, geri alınabilir ve kullanıcıya anlaşılır bir migration/recovery akışı tasarlanır. Bu karar verilmeden eski kare harita JSON dosyaları silinmez.

## 4. Uygulama aşamaları ve teknik kapılar

### 16.2.1 — Konum sözleşmesi ve runtime sahipliği
- Actor kimliği ile konum otoritesinin sınırlarını belirle.
- Hex runtime'ın SessionBundle/GameplayService yaşam döngüsüne nasıl bağlanacağını tanımla.
- Tek konum yazarı, occupancy, statik NPC blocker ve runtime restore kurallarını testlerle sabitle.
- Aynı entity için actor Position ve HexMovableEntity.position gibi iki canlı konum kaynağı kalmadığını kanıtla.

**Kapı:** Mimari karar kaydı, yeni/uyarlanan unit testleri ve mevcut Core kalite testleri başarılı.

### 16.2.2 — Hex içerik paketini ana kaynak yap
- `ContentPackage` içinde hex world/map kataloğunu zorunlu ve açık birincil kaynak yap.
- Oyuncu spawn noktasını paket verisine taşı.
- NPC, resource, market ve trade partner referans doğrulamalarını hex map/landmark kimliklerine geçir.
- Square map tanımlarını geçici olarak ayrı `easter_egg`/legacy katalog sınırında tut; ana gameplay doğrulamasında kullanma.

**Kapı:** İçerik paketi bozuk referansları reddeder; başlangıç paketi kare harita kataloğu olmadan yüklenebilir.

### 16.2.3 — Runtime ve servis entegrasyonu
- Tek HexWorldRuntime örneğini aktif SessionBundle/GameplayService yaşam döngüsüne bağla.
- Player, NPC ve gerekli dünya entity'lerini runtime/occupancy içine kaydet.
- Resource node ↔ hex landmark referansını doğrula.
- Market, konteyner ve dünya nesnesi etkileşimlerini hex konum/komşuluk kurallarıyla çalıştır.
- NPC hareketi, yoldaş AI, otomatik toplama veya yeni ekonomi mekaniği ekleme.

**Kapı:** Etkileşim, çarpışma, occupancy, kaynak toplama, pazar, konteyner ve quest entegrasyon testleri geçer.

### 16.2.4 — Persistence ve legacy kayıt kapısı
- Axial konum snapshot'ı, save schema sürümü ve restore doğrulamasını uygula.
- Harita/entity konumu, occupancy ve runtime tick tutarlılığını round-trip test et.
- Mevcut save migration katmanını inceleyip eski kare kayıtlar için kayıpsız/geri alınabilir politikayı belgeleyip test et.
- Açık migration kararı olmadan kare kayıt konumunu tahmin etme veya sıfırlama.

**Kapı:** Yeni hex save/load round-trip, bozuk/eksik map/entity reddi, backup/recovery ve eski save uyumluluk testleri geçer.

### 16.2.5 — Hex dünya ekranını ana oyun akışına al
- `MainScreen` hex runtime'a bağlanır; portal/temporary enter-leave akışı kaldırılır.
- Hareket, harita sınırı geçişi, seçim, NPC/resource/market/container etkileşimleri hex koordinatlarında çalışır.
- `GameWindow` pencere yönetimi ve ESC menüsü davranışı korunur.
- Renderer sadece runtime snapshot'ını okur; konum güncellemez.

**Kapı:** Otomatik UI/input/render testleri, hareket/transition regresyonları ve Linux/Windows CI geçer. Manuel görsel test istenmez.

### 16.2.6 — Kare sistemin ana oyundan ayrılması
- Ana gameplay kodunda kare `MapDefinition`, `WorldMap`, `Position(x,y)` ve kare geçiş çağrılarını kaldır.
- Kullanılmayan kare loader, validator, test fixture ve release script varsayımlarını bağımlılık kanıtıyla ayır.
- Tek kare Paskalya yumurtası kendi açık kare-map sınırında kalır; axial runtime'a koordinat dönüştürmez.
- Sekiz haritanın kaldırılması ancak save/content/quest/NPC/resource/market/container/test referansları sıfırlandığında yapılır.

**Kapı:** Ana oyun hex-only content package ile açılabilir; tek kare easter egg ayrı yüklenebilir; referans taraması ve tam CI başarılı.

## 5. Test stratejisi

Gerekli otomatik test katmanları:
- Konum otoritesi: entity başına tek konum kaydı, tek occupancy kaydı, tek yazıcı.
- Spatial contracts: `EntityPosition`, `LocalHexPosition`, `WorldHexPosition` tür sınırları.
- Content: başlangıç noktası, NPC, kaynak, market, trade partner, quest giver/target ve landmark referansları.
- Runtime: hareket, engel, occupancy, harita sınırı geçişi, geçiş başarısızlığı ve restore.
- Gameplay integration: konuşma, kaynak toplama, pazar, konteyner, görev hedefi.
- Persistence: save/load round-trip, eski save migration/recovery, bozuk referanslar, backup korunması.
- Packaging: wheel içine gerekli hex content ve yalnızca easter egg için gerekli kare içeriklerin girmesi.
- Platform: GitHub Actions Linux/Python 3.11 ve Windows/Python 3.12.
- Quality: Pytest, compileall, wheel build/install, release verification ve Ruff.

## 6. Kapsam dışı

- Godot veya başka motor geçişi.
- Yeni savaş, diyalog, görev veya ekonomi sistemi.
- NPC otonom hareketi, A*, Dijkstra, companion pathfinding veya yoldaş davranışı.
- Kare koordinatları hex koordinatlarına matematiksel dönüştürme.
- Çok haritalı kare dünya, kare harita editörü veya kare harita üreticisi.
- Ana oyun pencereleri/UI tasarımını yeniden yapmak.
- `main`, `demo_eldoria` veya `experiment/hex-world-laboratory` dallarını değiştirmek.

## 7. Başlangıç durumu ve doğrulama notu

- Onaylı çalışma dalı: `experiment/map-cleanup`.
- Önceki silme denemesi CI'da `world.map_catalog` import hatası verdiği için dosya geri yüklendi. Bu olay, dolaylı import bağımlılıklarının da temizleme öncesi taranması gerektiğini gösterdi.
- Geri yükleme commit'i: `0fb94ee4a2a0eaaa594681f29b435e0c63a8dfbe`.
- Bu commit'in GitHub Actions doğrulaması başlatıldı; sonuç henüz bekleniyor.
- Henüz runtime/content/save entegrasyon kodu değiştirilmedi. Bu belge mimari geçiş sözleşmesidir.
