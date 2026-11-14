# Aşama 8.6 — Güvenli Kayıt ve Şema Geçişi Tamamlanma Raporu

## Durum

**Uygulama ve otomatik test hazırlığı tamamlandı; CI doğrulaması commit sonrasında yapılacaktır.**

Çalışma yalnızca `demo_eldoria` dalında yürütülmüştür. `main` dalına işlem yapılmamıştır.

Başlangıç HEAD: `114e521ff46a11e3c8aa62c37657c2e8af99d6bd`

## 1. Hedef

Aşama 8.6, gelecekteki Content Editor'ün kullanacağı UI bağımsız güvenli kayıt ve migration altyapısını hazırlamaktır. Editör arayüzü, Save düğmesi veya oyun içi düzenleme modu bu aşamanın kapsamında değildir.

## 2. Eklenen altyapı

Yeni modül: `application/presentation_content_store.py`

`PresentationContentStore` üç operasyon sunar:

- `save_asset_catalog(payload)`
- `save_map_placements(map_id, payload)`
- `migrate_legacy_combined_presentation()`

### Güvenli kayıt

- Kaynak paket geçici bir staging dizinine kopyalanır.
- Aday JSON yalnızca staging kopyasına yazılır.
- JSON UTF-8, deterministik anahtar sırası ve okunabilir girintileme ile serileştirilir.
- NaN/Infinity, string olmayan JSON nesne anahtarları ve desteklenmeyen Python değerleri reddedilir.
- Aday veri normal `load_content_package` hattından geçirilir. Böylece yalnızca tek dosya değil, katalog + bütün placement kayıtları + harita referansları birlikte doğrulanır.
- Başarılı doğrulamadan sonra hedef dosya aynı dizinde oluşturulan geçici dosyadan `os.replace` ile değiştirilir.
- Eski hedef baytları `.bak` dosyasına alınır.
- Yazma/replace hatasında değiştirilmiş dosyalar geri yüklenir; yeni oluşturulan hedefler kaldırılır.
- POSIX sistemlerinde dosya ve dizin fsync uygulanır.
- Paket yazımları mevcut cross-thread/cross-process lock primitive'iyle serileştirilir.

### Migration

Legacy birleşik `presentation_assets.json` içeriği açıkça çağrılan migration ile ayrıştırılır:

- Asset kayıtları `asset_catalog.json` içine taşınır.
- Nesneler `map_id` temelinde `placements/<map_id>.json` dosyalarına gruplanır.
- Her placement kaydından `map_id` çıkarılır; dosya köküne alınır.
- Manifest'e `asset_catalog` ve `map_placements` alanları eklenir.
- Eski birleşik dosya korunur.
- Kaynak paket ve staged çıktı normal yükleyiciyle doğrulanır.
- Tekrar çağrı idempotenttir.
- Yarım kalmış önceki migration'dan kalan byte-identical dosyalar tekrar kullanılabilir; çakışan unmanaged dosyalar reddedilir.
- Manifest en son commit edilir. Böylece yeni kaynak dosyaları tamamlanmadan runtime yeni manifest referanslarını görmez.

Oyun kayıtları için kullanılan `application/migrations.py` ve `GameSaveDocument` sözleşmesine dokunulmamıştır.

## 3. Test kapsamı

Yeni test dosyası: `tests/test_application/test_presentation_content_store.py`

Testler şunları kapsar:

1. Deterministik kayıt ve yeniden yükleme.
2. Önceki içeriğin backup olarak korunması.
3. Yinelenen asset ID nedeniyle geçersiz katalog yazımının reddi.
4. Desteklenmeyen gelecek schema sürümünün reddi.
5. NaN değerinin serileştirme öncesi reddi.
6. Geçersiz harita hücresine placement kaydının reddi.
7. Başarılı placement kaydı ve yeniden yükleme.
8. İstenen map ID ile payload map ID uyuşmazlığı.
9. Manifest path traversal girişiminin reddi.
10. Legacy combined → split migration.
11. Migration tekrarında idempotency.
12. Legacy kaynağın korunması.
13. Yarım kalmış migration'dan kalan byte-identical dosyaların yeniden kullanılması.
14. Çakışan unmanaged split dosyalarının reddi.
15. Bozuk legacy kayıtta manifest/kaynak dosyanın korunması.
16. Çok dosyalı migration sırasında sonraki replace başarısız olduğunda rollback.

## 4. Mimari sınırlar

Değişmeyenler:
- Pygame ve oyun ekranları.
- AssetManager cache davranışı ve görsel fallback.
- Hex/kare harita modelleri.
- HexWorldRuntime, WorldTransform, kamera, hareket, collision, occupancy ve pathfinding.
- Depth sorting ve doğal PNG ağaç sunumu.
- Normal oyun arayüzü.

## 5. Bilinçli sınırlar

Aşama 8.6 yalnızca split asset catalog ve map placement dosyalarını güvenli biçimde kaydeder; genel amaçlı tüm content JSON dosyalarına yazma API'si sunmaz. Legacy migration sadece mevcut, doğrulanmış combined presentation formatını split kaynaklara taşır. UI bağımsız daha geniş servis sözleşmesi Aşama 8.7 kapsamındadır.

## 6. Doğrulama

CI workflow sonuçları henüz bu raporun oluşturulduğu anda alınmamıştır. Commit sonrası Eldoria CI (Windows/Linux Python 3.11/3.12 ve Pygame headless smoke) ile Core Quality (Linux/Windows release-candidate verification) sonuçları ayrıca kontrol edilip bu rapora işlenecektir.

Aşama 8.6, otomatik testler ve CI başarıyla tamamlanmadan kapatılmış sayılmayacaktır.
