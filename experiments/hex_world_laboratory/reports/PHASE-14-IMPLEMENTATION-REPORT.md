# Aşama 14 — Uygulama ve Otomatik Doğrulama Raporu

**Tarih:** 18 Kasım 2026  
**Durum:** Teknik uygulama ve otomatik doğrulama tamamlandı; kullanıcı masaüstü/görsel kabulü bekleniyor.  
**Çalışma dalı:** `experiment/hex-world-laboratory`  
**Kod doğrulama HEAD:** `25daff476df5f44682eed879458c830ceb735cf4`

## 1. Sonuç

Aşama 14'ün 14.2–14.8 teknik iş paketleri, onaylı teknik plana uygun biçimde laboratuvar dalında uygulandı. Gelecekteki ELDORIA CONTENT EDITOR masaüstü uygulamasının kullanacağı içerik veri modeli, vektör çizim belgesi, içerik kütüphanesi, harita yerleşim belgesi, sürümlü JSON persistence ve runtime adapter temeli hazırlandı.

Editör penceresi, harita düzenleme arayüzü, fareyle yerleştirme/çizim, ana oyun entegrasyonu, rotation/scale ve gameplay sistemleri bu aşamaya alınmadı.

## 2. Uygulanan veri modeli

Yeni `src/hex_world_lab/content/` paketi Pygame ve render katmanından bağımsızdır.

- `VisualDocument`: version 1; mantıksal ölçü, ground/depth anchor, renk tokenları, sıralı katmanlar ve kararlı öğe kimlikleri.
- Primitive öğeler: polygon, ellipse, circle ve polyline.
- `DrawingStyle`: fill/stroke tokenları ve çizgi kalınlığı.
- `ContentDefinition`: kararlı content ID, ad, kategori, visual document, metadata ve opsiyonel açık collider.
- `ContentLibrary`: benzersiz content ID doğrulaması ve referans çözümleme.
- `ContentPlacement`: benzersiz instance ID, content ID ve dünya koordinatı.
- `MapContentDocument`: mevcut `HexMapDefinition` ile içerik yerleşimlerinin immutable birleşimi.
- Placement ekleme, güncelleme ve silme işlemleri yeni belge döndürür; kaynak belgeyi değiştirmez.

## 3. JSON persistence ve şemalar

İki ayrı v1 belge türü eklendi:

- `eldoria_content_library`: `schemas/content-library.v1.schema.json`
- `eldoria_map_document`: `schemas/map-content.v1.schema.json`

Ayrıntılı sözleşmeler:
- [Content Library JSON v1](../docs/content/CONTENT_LIBRARY_JSON_SCHEMA_V1.md)
- [Map Content JSON v1](../docs/content/MAP_CONTENT_JSON_SCHEMA_V1.md)

Codec deterministik JSON üretir. Dosya yükleme duplicate object key ve NaN/Infinity değerlerini reddeder. Unknown/missing alanlar, yinelenen kimlikler, bozuk geometri, bilinmeyen palette tokenları, çözülemeyen content referansları ve desteklenmeyen sürümler doğrulamada reddedilir. Dosya yazımı açık `create` veya `replace` modu ile güvenli geçici dosya/atomik işlem kullanır.

Mevcut MAP JSON v1 ve runtime snapshot v1 şemaları değiştirilmedi; map content yeni bir wrapper belgesidir.

## 4. Vektör profil ve render entegrasyonu

Beş mevcut profil artık VisualDocument kaynak tanımlarıyla üretilir:

- tree
- rock
- bush
- grass
- flower

Mevcut `build_environment_profile(s)` Surface API'leri korunmuştur. Pygame Surface üretimi vector document renderer üzerinden yapılır. Tree/rock/bush için eski kabul edilmiş görsel çıktıyla piksel eşitliği regresyon testi korunur; grass/flower aynı seed için deterministik, farklı seed için farklıdır.

Pygame tarafında:
- alpha Surface üretimi,
- bounded `ProceduralSurfaceCache`,
- içerik kimliğine göre asset registration,
- map content -> environment scene -> sprite visual adapter hattı eklendi.

Collider verisi çizim geometrisinden türetilmez. Circle ve convex polygon collider yalnızca açıkça tanımlanır ve mevcut physics shape'lerine adapter ile çevrilir. Beş built-in profilin collider değeri varsayılan olarak `None`.

## 5. Test ve CI sonuçları

### Hex World Laboratory CI

- Workflow run: [#44396008498](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44396008498)
- Pytest: **881 passed**, 98.15 saniye.
- Ruff lint: başarılı.
- Ruff format check: başarılı.
- Önceki aşamaların benchmark işleri: başarılı.
- Phase 14 vector profile benchmark: başarılı.
- Phase 14 PNG/JSON evidence üretimi ve artifact yüklemesi: başarılı.

### Core Quality

- Workflow run: [#44396007803](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44396007803)
- Linux: **2,344 passed**, 1 uyarı.
- Windows: başarılı.
- Ruff lint ve format: Linux/Windows başarılı.
- Tek uyarı, mevcut Pygame bağımlılığının `pkg_resources` deprecation uyarısıdır; Phase 14 kaynaklı test hatası değildir.

## 6. Phase 14 profil benchmark sonuçları

GitHub Actions Python 3.12 runner üzerinde, profil başına 25 soğuk render ve 25 cache lookup ölçümü:

| Profil | Soğuk render medyanı | Cache lookup medyanı |
|---|---:|---:|
| Tree | 762.731 µs | 0.561 µs |
| Rock | 223.760 µs | 0.551 µs |
| Bush | 168.005 µs | 0.551 µs |
| Grass | 240.842 µs | 0.541 µs |
| Flower | 175.850 µs | 0.551 µs |

Cache sonucu: 5 giriş, 120 hit, 5 miss, tahmini Surface belleği 141,760 byte (yaklaşık 138.4 KiB). Bu ölçümler runner'a özgü gözlemsel medyanlardır; donanımdan bağımsız performans garantisi veya eşik değildir.

## 7. Görsel kanıt

[Phase 14 content validation artifact — ZIP](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44396008498/artifacts/14470961143)

Artifact içeriği:
- `tree.png`, `rock.png`, `bush.png`, `grass.png`, `flower.png`
- `profile-sheet.png`
- `manifest.json`
- `benchmark.json`

Manifest beş profilin ölçü, anchor, katman/öğe sayısı ve entegre map preview içindeki stable ID/placement verisini içerir.

## 8. Mimari sınırlar ve açık kalan kabul

- Content domain doğrudan Pygame, rendering, environment veya physics modüllerini import etmez; runtime adapter ayrı rendering katmanındadır.
- Rotation/scale v1'e alınmadı.
- Desktop ELDORIA CONTENT EDITOR UI ve map-editing interaction yapılmadı.
- Ana oyuna entegrasyon yapılmadı.
- AI, pathfinding, NPC hareketi, gathering/economy, combat/dialogue/quest sistemleri değiştirilmedi.
- `main` ve `demo_eldoria` dallarına commit/merge yapılmadı.

Otomatik teknik doğrulama tamamdır. Resmî Aşama 14 kapanışı için [manuel kabul kontrol listesindeki](../docs/PHASE-14-MANUAL-ACCEPTANCE-CHECKLIST.md) yerel görsel kontrolün kullanıcı tarafından tamamlanması beklenmektedir.
