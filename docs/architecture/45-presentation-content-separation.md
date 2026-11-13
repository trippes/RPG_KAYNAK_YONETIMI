# Aşama 8.3 — Sunum Asset ve Harita Yerleşim Verilerinin Ayrılması

## Durum

Aşama 8.3 kapsamında uygulanmıştır. Bu belge, demo_eldoria içerik paketindeki yeni kanonik veri düzenini ve geriye dönük uyumluluk sınırını açıklar.

## 1. Temel ayrım

Bir asset, tekrar kullanılabilir görsel tanımıdır. Harita placement kaydı ise o asset'in belirli bir haritada bulunan tekil örneğidir.

Asset kataloğu şu sorulara cevap verir:
- Asset'in kararlı asset_id değeri nedir?
- Kaynak PNG'nin göreli yolu nedir?
- Varsayılan scale, anchor, collision, placement katmanı ve depth offset nedir?
- Asset hangi kategori/tür metadata'sına sahiptir?

Placement verisi şu sorulara cevap verir:
- Hangi haritada hangi object_id örneği bulunur?
- Hangi asset_id kullanılır?
- Örnek hangi axial q/r koordinatına ve hücre merkezine göre hangi ofsete yerleşir?
- Örneğe özgü footprint, collision_box, depth_offset, layer ve kind değerleri nelerdir?

Placement kayıtları PNG dosya yolunu veya asset'in tekrar kullanılabilir metadata'sını kopyalamaz.

## 2. Kanonik dosya düzeni

content/demo_eldoria/manifest.json, yeni kaynakları şu anahtarlarla bildirir:

- asset_catalog: asset_catalog.json
- map_placements: placements/

Asset tanımları:

content/demo_eldoria/asset_catalog.json

Bu dosya schema_version: 1 ve assets listesi taşır. objects alanı içermez.

Harita yerleşimleri:

- content/demo_eldoria/placements/hex_forest_demo.json
- content/demo_eldoria/placements/hex_clearing_demo.json

Her placement dosyası schema_version, tek bir map_id ve objects listesi taşır. Her nesne kaydındaki map_id, dosyanın üst düzey map_id değerinden gelir. Böylece her placement kaydında aynı harita kimliği tekrar edilmez.

Mevcut demo verisi ayrıştırılırken 6 asset tanımı ve 14 placement kaydı korunmuştur: orman haritasında 12, açıklık haritasında 2 placement vardır.

## 3. Asset referansı ve örnek bazlı değerler

Her placement asset_id ile katalogdaki bir asset'e bağlanır. Aynı asset birden çok haritada ve aynı haritada birden çok kez kullanılabilir.

Asset varsayılanları katalogda tek yerde tutulur. Placement üzerinde zaten desteklenen yerel alanlar (offset, depth offset, collision box, footprint, layer ve kind) yalnızca o örneğe ait değerleri taşır.

Mevcut tüketici davranışı korunur:
- Görsel ölçek ve anchor asset tanımından gelir.
- Görsel depth değeri asset depth_offset ile placement depth_offset toplamından hesaplanır.
- Placement collision_box tanımlamışsa örnek değeri kullanılır; yoksa blocker kaydı asset collision varsayılanına bakar.
- Placement offset değerleri hücre merkezine göre uygulanır.
- q/r axial koordinatları değişmemiştir.

Bu aşama yeni scale/anchor override alanları veya yeni collision/occupancy davranışı eklemez. Alanların nihai birim ve koordinat sözleşmeleri Aşama 8.4, çapraz doğrulama Aşama 8.5 kapsamındadır.

## 4. Kod sorumlulukları

### AssetCatalog

game_ui/assets/asset_definition.py mevcut AssetCatalog sınıfını korur. Yeni asset-only JSON biçimini yükler; katalog artık yeni placement verisini kendi içine almaz.

Eski presentation_assets.json biçiminde objects listesi bulunduğunda legacy uyumluluk amacıyla mevcut placement parse davranışı sürer. Bu, ikinci bir katalog yaratmak değil, eski dosya biçimini okumaya devam eden geçiş adaptörüdür.

### ScenePlacementCatalog

game_ui/assets/placement_catalog.py harita yerleşimlerini ayrı yükler ve sorgular.

Sorumlulukları:
- Harita başına placement JSON dosyalarını yüklemek.
- Şema sürümünü ve desteklenen alanları kontrol etmek.
- Mevcut SceneObjectPlacement modelini kullanmak.
- Paket genelinde object_id benzersizliğini denetlemek.
- Her asset_id referansını verilen AssetCatalog ile çözmek.
- objects_for_map(map_id) ve tüm placement kayıtlarını sunmak.

Servis Pygame, renderer veya ekran sınıflarına bağımlı değildir. Harita çizimi veya nesne yerleştirme arayüzü içermez.

### ContentPackage ve HexWorldView

application/content_loader.py yeni manifest alanlarını güvenli paket kökü içinde çözer ve ContentPackage üzerinde asset_catalog_path ile map_placements_path sunar. Eski presentation_assets_path alanı korunur.

game_ui/hex_world_view.py yeni kaynaklar mevcutsa önce ayrılmış asset ve placement kaynaklarını yükler. Yeni alanlar bulunmayan eski paketlerde birleşik presentation_assets.json okuma yoluna geri döner.

Hem blocker kayıtları hem sahne çizimi aynı yüklenmiş placement koleksiyonunu kullanır. Hex geometri, occupancy kuralları, depth sorting algoritması veya kamera değiştirilmemiştir.

## 5. Geriye dönük uyumluluk

content/demo_eldoria/presentation_assets.json bu aşamada silinmemiş veya yeniden adlandırılmamıştır. Önceki paket biçimi için legacy okuma girdisi olarak tutulur.

Yeni demo paketi manifesti hem:
- kanonik ayrılmış kaynakları,
- eski tüketiciler için legacy presentation_assets.json yolunu

bildirir. Yeni HexWorldView uygulaması ayrılmış kaynakları önceliklendirir. Eski AssetCatalog.load(presentation_assets.json) çağrısı ise eski objects listesini okumaya devam eder.

Bu geçişte iki veri kümesi içerik bakımından aynı başlangıç durumundan üretilmiştir. Yeni içerik düzenleme servisleri yalnızca ayrılmış kaynaklara yazmalıdır; legacy dosyanın senkronizasyonu gelecekteki kontrollü migration/legacy kaldırma kararına bırakılmıştır. Legacy dosyanın kaldırılması Aşama 8.3'ün hedefi değildir.

## 6. Paketleme

pyproject.toml wheel data-files listesine:
- asset_catalog.json,
- placements/*.json,
- assets/*.png,
- assets/*.json

eklenmiştir.

scripts/verify_release.py, izole kurulmuş wheel içindeki content package'ı yükleyerek 6 asset ve 14 placement kaydının gerçekten dağıtım paketine girdiğini doğrular.

## 7. Kapsam dışı ve sonraki işler

Bu aşamada:
- Content Editor UI geliştirilmedi.
- Harita üzerinde mouse ile yerleştirme/sürükle-bırak yapılmadı.
- PNG dosyaları değiştirilmedi.
- Anchor/pivot/scale/depth/layer/collision/footprint nihai standartları yeniden tanımlanmadı.
- Map ID ve koordinatların map definition ile çapraz doğrulaması eklenmedi.
- Hex/kare harita modelleri birleştirilmedi.
- Kamera, hareket, collision runtime veya depth sorting yeniden yazılmadı.

Birim ve entegrasyon testleri ayrıştırma ve legacy uyumluluğunu doğrular. Map definition çapraz kontrolleri ve bozuk placement verisinin runtime'a ulaşmasını engelleyen genel doğrulama servisi Aşama 8.5 kapsamındadır.
