# Eldoria RPG — Aşama 8.3 Tamamlanma Raporu
## Metadata ve Harita Yerleşim Verilerinin Ayrıştırılması

| Alan | Değer |
|---|---|
| Depo | trippes/RPG_KAYNAK_YONETIMI |
| Çalışma dalı | demo_eldoria |
| Aşama | 8.3 — Metadata ve yerleşim verilerinin ayrıştırılması |
| Uygulama/test HEAD'i | a4760303bdbe532c53b880012fd0a5d405b7c7c8 |
| Sonuç | Otomatik doğrulama başarılı; manuel kabul kontrolü bekleniyor |
| Content Editor UI | Geliştirilmedi |

## 1. Amaç ve kapsam

Aşama 8.3'ün amacı, tekrar kullanılabilir görsel asset tanımlarıyla harita üzerinde bulunan tekil nesne örneklerini birbirinden ayırmaktır.

Uygulama, Aşama 8'in bağlayıcı planına ve Aşama 8.1 denetiminde belirlenen gerçek mimariye göre yapıldı. Mevcut AssetCatalog, SceneObjectPlacement, ContentPackage ve HexWorldView sorumlulukları korundu; paralel bir runtime veya ikinci bir asset yöneticisi oluşturulmadı.

## 2. Yeni veri düzeni

### 2.1 Asset kataloğu

Yeni kanonik asset dosyası:

content/demo_eldoria/asset_catalog.json

Dosya schema_version 1 ve assets listesi taşır. Harita nesnesi veya placement kaydı içermez. Mevcut 6 asset tanımının tamamı korundu:
- flora.tree.test
- flora.tree.young
- flora.tree.old
- prop.rock.large
- flora.shrub.green
- flora.plant.wildflower

Asset ID, PNG yolu, kaynak ölçü sentinel'i, scale, anchor, collision, placement ve depth metadata değerleri değiştirilmedi.

### 2.2 Harita placement dosyaları

Placement verileri harita başına ayrıldı:
- content/demo_eldoria/placements/hex_forest_demo.json
- content/demo_eldoria/placements/hex_clearing_demo.json

Mevcut 14 nesne kaydı kayıpsız taşındı:
- hex_forest_demo: 12 placement
- hex_clearing_demo: 2 placement

Placement kayıtları asset_id referansı taşır; PNG dosya yolunu veya tekrar kullanılabilir asset metadata'sını taşımaz. map_id her nesneye tekrar yazılmak yerine dosyanın üst düzey alanında tanımlanır.

### 2.3 Paket manifesti

content/demo_eldoria/manifest.json içine iki yeni kaynak bildirimi eklendi:
- asset_catalog: asset_catalog.json
- map_placements: placements

Eski presentation_assets alanı kaldırılmadı. Böylece eski paket okuma yolu ve eski tüketiciler için birleşik JSON dosyası korunmuş oldu.

## 3. Kod değişiklikleri

### Değiştirilen dosyalar
- application/content_loader.py
- content/demo_eldoria/manifest.json
- game_ui/assets/asset_definition.py
- game_ui/hex_world_view.py
- pyproject.toml
- scripts/verify_release.py
- tests/test_application/test_content_loader.py
- tests/test_game_ui/test_hex_world_view.py
- tests/test_game_ui/test_placement_catalog.py

### Eklenen dosyalar
- game_ui/assets/placement_catalog.py
- content/demo_eldoria/asset_catalog.json
- content/demo_eldoria/placements/hex_forest_demo.json
- content/demo_eldoria/placements/hex_clearing_demo.json
- tests/test_game_ui/test_placement_catalog.py
- docs/architecture/45-presentation-content-separation.md

### 3.1 ScenePlacementCatalog

Yeni UI bağımsız ScenePlacementCatalog servisi eklendi.

Sorumlulukları:
- Harita başına placement JSON dosyalarını yüklemek.
- Placement şema sürümünü ve desteklenen alanları kontrol etmek.
- Mevcut SceneObjectPlacement modelini kullanmak.
- Paket genelinde object_id benzersizliğini doğrulamak.
- Her asset_id referansını AssetCatalog ile çözmek.
- Harita bazında placement sorgusu ve tüm placement koleksiyonunu sunmak.
- Placement dosyalarının içerik dizini dışına symlink ile çıkmasını engellemek.
- Yüklenen placement koleksiyonunu değiştirilemez snapshot olarak sunmak.

Servis Pygame, renderer veya ekran sınıflarına bağımlı değildir.

### 3.2 AssetCatalog geriye dönük uyumluluğu

Mevcut AssetCatalog yeni asset-only dosyayı okuyabilir. Yeni katalog biçiminde placement parse edilmez.

Eski presentation_assets.json içinde objects alanı bulunduğunda eski parse davranışı korunur. Böylece eski birleşik dosya kullanan kod ve testler kırılmadan çalışmaya devam eder.

### 3.3 ContentPackage yükleme zinciri

ContentPackage modeline şu alanlar eklendi:
- asset_catalog_path
- map_placements_path

Paket yükleyicisi iki yeni alanın birlikte tanımlanmasını zorunlu tutar. Dosya ve dizin yolları paket kökü içinde çözülür; paket dışına çıkan yollar reddedilir. Asset kataloğunun temel şema biçimi kontrol edilir.

Eski presentation_assets_path alanı aynen korunur.

### 3.4 HexWorldView entegrasyonu

HexWorldView ayrılmış kaynaklar bulunduğunda önce:
1. AssetCatalog yükler.
2. ScenePlacementCatalog yükler.
3. Aynı placement koleksiyonunu blocker kayıtlarında ve sahne çiziminde kullanır.

Yeni ayrılmış kaynaklar bulunmayan eski paketlerde birleşik presentation_assets.json okuma yoluna geri döner.

Görsel depth hesabındaki asset + placement depth_offset toplamı, offset uygulaması, asset scale/anchor kullanımı ve collision fallback davranışı korundu.

## 4. Geriye dönük uyumluluk doğrulaması

presentation_assets.json silinmedi, yeniden adlandırılmadı veya şema değişikliğine uğratılmadı.

Otomatik test, legacy birleşik dosyadaki asset kayıtlarının yeni asset_catalog.json ile aynı olduğunu doğrular. Ayrıca legacy objects listesi ile harita başına ayrılmış placement kayıtları object_id üzerinden karşılaştırılır. Böylece iki veri kümesinin başlangıçta birebir eşdeğer olduğu güvence altına alınır.

Yeni runtime ayrılmış kaynakları önceliklendirir. Eski AssetCatalog.load(presentation_assets.json) çağrısı eski nesne kayıtlarını okuyabilir.

Legacy dosyanın kaldırılması veya yeni servisler tarafından yazılması bu aşamada yapılmadı. İleride yalnızca ayrılmış kaynaklar kanonik yazma hedefi olmalıdır.

## 5. Dağıtım paketi

İlk entegrasyon kontrolü, yeni JSON dosyalarının kaynak depoda bulunmasına rağmen wheel paketine dahil edilmediğini ortaya çıkardı.

Bu nedenle pyproject.toml data-files listesi genişletildi:
- asset_catalog.json
- placements/*.json
- assets/*.png
- assets/*.json

scripts/verify_release.py de güncellendi. İzole kurulan wheel içinden içerik paketi yükleniyor; AssetCatalog ve ScenePlacementCatalog çağrılarıyla 6 asset ve 14 placement kaydının dağıtım paketinde bulunduğu doğrulanıyor.

Bu düzeltme olmadan release kurulumu eksik içerikle sonuçlanabileceği için kapsam içi zorunlu entegrasyon düzeltmesi olarak ele alındı.

## 6. Otomatik test kapsamı

Yeni placement testleri şunları kapsar:
- Ayrılmış asset ve placement dosyalarının birlikte yüklenmesi.
- AssetCatalog içinde placement kaydı bulunmaması.
- Harita başına placement sayılarının korunması.
- Aynı asset'in birden fazla haritada ve birden fazla örnekte kullanılabilmesi.
- Örnek bazlı offset ve collision verilerinin korunması.
- Placement kataloğunun immutable snapshot olması.
- Bilinmeyen asset_id referansının reddedilmesi.
- Farklı harita dosyalarında yinelenen object_id değerinin reddedilmesi.
- Legacy birleşik dosyanın okunabilmesi.
- Legacy ve yeni ayrılmış verilerin birebir eşdeğerliğinin kontrolü.
- HexWorldView'in gerçek demo paketinden ayrılmış kaynakları yüklemesi.

Content package testleri yeni manifest alanlarının yüklenmesini; release doğrulaması ise wheel içindeki gerçek dağıtım dosyalarını kontrol eder.

## 7. CI ve Release Candidate sonuçları

Son uygulama/test HEAD'i:
a4760303bdbe532c53b880012fd0a5d405b7c7c8

### Eldoria CI

Workflow: https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43505158674

| İş | Sonuç |
|---|---|
| Ubuntu / Python 3.11 | Başarılı — 1412 test |
| Ubuntu / Python 3.12 | Başarılı — 1412 test |
| Windows / Python 3.11 | Başarılı — 1412 test |
| Windows / Python 3.12 | Başarılı — 1412 test |
| Pygame headless smoke test | Başarılı |

### Core quality

Workflow: https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43505158822

| İş | Sonuç |
|---|---|
| Linux release-candidate verification | Başarılı |
| Windows release-candidate verification | Başarılı |

Release Candidate doğrulaması wheel oluşturma, izole kurulum, içerik paketini yükleme, ayrılmış asset/placement kaynaklarını okuma, birim testleri, compileall ve application smoke adımlarını içerir.

### CI düzeltme geçmişi

İlk paketleme denemesinde yeni asset ve placement dosyaları wheel içine dahil edilmediği için Core quality başarısız oldu. pyproject.toml data-files tanımları ve release doğrulama betiği düzeltildi.

Placement kataloğunun değiştirilemezliği için eklenen ilk test, frozen dataclass alanı yerine property üzerinden atama yaptığı için Python 3.11'de beklenmeyen TypeError üretti. Model gerçek dataclass field sözleşmesine dönüştürüldü ve test FrozenInstanceError üzerinden düzeltildi. Son HEAD'de tüm Eldoria CI ve Core quality işleri başarılıdır.

## 8. Korunan mimari sınırlar

- Hex axial q/r koordinatları değiştirilmedi.
- Kare harita altyapısı değiştirilmedi.
- HexWorldRuntime veya WorldTransform yeniden yazılmadı.
- Kamera, zoom, hareket, pathfinding ve occupancy algoritmaları değiştirilmedi.
- DepthSorter algoritması değiştirilmedi.
- Ağaç PNG dosyaları değiştirilmedi.
- Ağaç rig/atlas varsayılanı kapalı kaldı.
- Yeni çevre görseli üretilmedi.
- Content Editor UI, harita üzerinde fareyle yerleştirme ve sürükle-bırak geliştirilmedi.
- NPC, görev, savaş, ekonomi ve envanter sistemlerine müdahale edilmedi.

## 9. Manuel kabul testleri

Otomatik testler ve headless smoke test başarılıdır. Bununla birlikte, HexWorldView'in yeni ayrılmış kaynakları gerçek Pygame oturumunda kullandığını doğrulamak için kullanıcı tarafından kısa bir görsel kabul testi gereklidir.

İstenen kontroller:
1. Oyunu normal şekilde başlat ve H ile altıgen dünyaya geç.
2. Orman haritasında ağaç, çalı, kaya ve çiçeklerin görünmeye devam ettiğini kontrol et.
3. Oyuncunun ağaçların önünden ve arkasından geçişinde depth sorting davranışını kontrol et.
4. Doğu sınırından açıklık haritasına, geri dönerek orman haritasına geçişi kontrol et.
5. Kare dünyaya dön ve eski harita görünümünün çalıştığını kontrol et.

Bu kontroller henüz kullanıcı tarafından yapılmadığı için manuel kabul sonucu başarılı olarak işaretlenmemiştir.

## 10. Sonuç

Aşama 8.3 kod, veri ayrıştırması, geriye dönük uyumluluk, wheel paketleme ve otomatik doğrulama bakımından tamamlandı.

Mevcut 6 asset ve 14 placement kaydı ayrıştırıldı. Yeni runtime yolu ayrılmış kaynakları kullanıyor; eski birleşik JSON okuma yolu korunuyor. Dağıtım paketi yeni kaynakları içeriyor ve Release Candidate doğrulaması bunları izole kurulumda okuyabiliyor.

**Aşama 8.3 otomatik doğrulaması başarılıdır. Manuel oyun içi kabul kontrolü kullanıcıdan beklenmektedir.**

Sonraki aşama 8.4 — Konum ve görsel metadata standartlarıdır. Aşama 8.4'e geçiş için kullanıcı onayı beklenmelidir.
