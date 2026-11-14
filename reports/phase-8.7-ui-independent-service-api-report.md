# Aşama 8.7 — UI Bağımsız Content Service/API Sözleşmesi

## Durum

**TAMAMLANDI — Servis altyapısı, testler ve CI kalite kapıları başarılı.**

Çalışma yalnızca `demo_eldoria` dalında yürütüldü. `main` dalına işlem yapılmadı.

Son doğrulanan uygulama HEAD'i: `cb694f7a38de69632e6c505cc08617ade509c6ad`

## 1. Hedef ve kapsam

Aşama 8.7'nin hedefi, gelecekteki Content Editor'ün JSON dosyalarını veya renderer iç yapılarını doğrudan yönetmesini önleyecek UI bağımsız uygulama sınırını hazırlamaktır.

Bu aşamada Content Editor arayüzü, Pygame ekranı, fare/klavye etkileşimi, preview penceresi veya oyun içi editör modu oluşturulmadı.

## 2. Eklenen servis

Yeni modül: `application/presentation_content_service.py`

Ana sınıf: `PresentationContentService`

Servis mevcut altyapıyı yeniden kullanır:
- `load_content_package`
- `AssetCatalog`
- `ScenePlacementCatalog`
- `PresentationContentStore`

Paralel katalog, placement veya kayıt modeli oluşturulmadı.

### Okuma ve sorgulama API'si

- `load_package()`
- `load_asset_catalog()`
- `list_assets(category=None)`
- `get_asset(asset_id)`
- `load_map_placements(map_id)`

Her okuma canonical package loader üzerinden güncel paketi tekrar doğrular. Böylece servis geçersiz içeriği eski bir cache üzerinden gizlemez. Bilinmeyen hex map kimliği açık servis hatasıdır.

### Doğrulama API'si

- `validate_content_package()`
- `validate_asset_catalog(draft)`
- `validate_map_placements(map_id, draft)`

Yapılandırılmış sonuç modelleri:
- `ContentValidationResult`
- `ContentValidationIssue`

Hatalı paket veya taslaklar yapılandırılmış hata olarak döner. Eksik/bozuk PNG dosyaları mevcut mimaride olduğu gibi fatal olmayan uyarılar olarak sunulur.

Taslak doğrulaması geçici bir paket kopyası üzerinde, aynı güvenli kayıt ve canonical loader hattı kullanılarak yapılır. Canlı paket dosyaları değiştirilmez; doğrulama sırasında backup üretilmez.

### Kayıt API'si

- `save_asset_catalog(draft)`
- `save_map_placements(map_id, draft)`

Her iki işlem de mevcut `PresentationContentStore` servisine delegasyon yapar. Tam paket doğrulaması, atomik değiştirme, backup ve rollback davranışları korunur. Kayıt sonrasında servis paketi yeniden yükler.

### Migration API'si

- `migration_status()`
- `migrate_legacy_content()`

Durum modeli: `ContentMigrationStatus`

Migration durumu salt okunur biçimde raporlanır. Legacy migration yalnızca açıkça çağrıldığında çalışır; normal okuma sırasında otomatik migration yapılmaz. Şema sürümü mevcut version 1 sözleşmesinden değiştirilmedi.

## 3. Paket dışa aktarımı

Servis ve sonuç modelleri `application` paketinden de erişilebilir hâle getirildi:
- `PresentationContentService`
- `PresentationContentServiceError`
- `ContentValidationIssue`
- `ContentValidationResult`
- `ContentMigrationStatus`

## 4. Test kapsamı

Yeni test dosyası: `tests/test_application/test_presentation_content_service.py`

12 test metodu şu davranışları kapsar:

1. Asset listeleme ve ID ile çözümleme.
2. Bilinen haritanın placement kayıtlarını okuma.
3. Bilinmeyen map ID reddi.
4. PNG sorunlarının warning olarak raporlanması.
5. Geçerli asset taslağının canlı dosyaya dokunmadan doğrulanması.
6. Geçersiz asset taslağının yapılandırılmış hatayla reddi.
7. Geçerli placement taslağının canlı dosyaya dokunmadan doğrulanması.
8. Geçersiz placement taslağının reddi ve kaynak dosyanın korunması.
9. Asset kaydının güvenli store üzerinden yapılması ve yeni sonucun okunması.
10. Split migration durumunun salt okunur raporlanması.
11. Legacy migration'ın açık çağrıyla yapılması ve durumun güncellenmesi.
12. Geçersiz paketin yapılandırılmış sonuçla raporlanması.

## 5. Mimari sınırlar

Değişmeyenler:
- Pygame ekranları ve oyun arayüzü.
- AssetManager cache ve görsel fallback davranışı.
- Renderer, depth sorting ve doğal PNG sunumu.
- Hex/kare harita modelleri, geometri, hareket, kamera, collision ve pathfinding.
- Harita geçişleri ve normal oyun HUD'ı.

Yeni servis Pygame veya ekran sınıflarına bağımlı değildir; mouse/keyboard event almaz ve çizim yapmaz.

Mimari belge: `docs/architecture/49-presentation-content-service-api.md`

## 6. CI doğrulaması

Son uygulama commit'i `cb694f7a38de69632e6c505cc08617ade509c6ad` için:

**Eldoria CI — SUCCESS**
Run: `43596267421`

- Ubuntu Python 3.11: 1.457 test geçti.
- Ubuntu Python 3.12: 1.457 test geçti.
- Windows Python 3.11: 1.457 test geçti.
- Windows Python 3.12: 1.457 test geçti.
- Pygame headless smoke: SUCCESS.

**Core quality — SUCCESS**
Run: `43596267420`

- Linux release-candidate verification: SUCCESS.
- Windows release-candidate verification: SUCCESS.
- Wheel build, isolated install, content package verification ve application smoke adımları geçti.

CI bağlantıları:
- https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43596267421
- https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43596267420

### CI sırasında bulunan ve giderilen test sorunu

İlk test commit'inde `get_asset` testi, fixture'da bulunmayan `flora.tree.oak` kimliğini kullanıyordu. Gerçek katalogdaki kimlik `flora.tree.test` olduğundan Ubuntu Python 3.11/3.12 testleri başarısız oldu.

Test, gerçek katalog kimliğini kullanacak şekilde düzeltildi. Üretim kodunda veya içerik dosyalarında değişiklik gerekmedi. Düzeltme sonrası son uygulama HEAD'i üzerinde dört test matrisi ve iki kalite workflow'u başarılı tamamlandı.

## 7. Teslimatlar

- `application/presentation_content_service.py`
- `tests/test_application/test_presentation_content_service.py`
- `docs/architecture/49-presentation-content-service-api.md`
- `application/__init__.py` servis dışa aktarımı

Aşama 8.7'nin servis/API kabul ölçütleri ve CI kalite kapıları karşılanmıştır. Content Editor arayüzü bilinçli olarak kapsam dışında bırakılmıştır.
