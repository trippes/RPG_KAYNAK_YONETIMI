# Eldoria — Modüler Yapı ve İnşa Sistemi
## Aşama 2: İnşa Koordinatları ve Yerleştirme Sistemi — Çalışma Kaydı

- **Durum:** Devam ediyor; koordinat, footprint tabanlı önizleme/doğrulama ve atomik commit sınırı sözleşmeleri uygulandı; güncel CI doğrulaması bekleniyor
- **Hedef dal:** `experiment/map-cleanup`
- **Kapsam referansı:** `docs/architecture/90-modular-building-construction-system-roadmap.md`
- **Aşama:** 2 — İnşa koordinatları ve yerleştirme sistemi

## 1. Aşama sınırı

Bu aşama yalnızca inşa uzayı koordinat/value object'lerini, hex dünya ile deterministik dönüşümü, hassas konum/yön/yükseklik ve snap/hizalama kurallarını, ayrıca saf yerleştirme önizleme/doğrulama API'sini kapsar.

Zemin/duvar/kapı/pencere runtime'ı, crafting, envanter tüketimi, fizik/navigasyon/render entegrasyonu, save/load ve NPC inşası bu aşamanın kapsamı değildir. Mevcut aktör konumu, entity registry, HexWorldRuntime veya GameplayPlacementCatalog için ikinci bir otorite oluşturulmayacaktır.

## 2. Kaynak incelemesinden doğrulanan mevcut sözleşmeler

- `HexCoord` integer axial hücre/topoloji koordinatıdır.
- `WorldPoint` canonical y-down sürekli dünya düzleminde, world unit cinsinden konumdur.
- `ContinuousEntityPosition` aktörün sürekli konumunu map ID ile ilişkilendirir ve mevcut hareket runtime'ının otoritesidir.
- `HexWorldRuntime.HEX_SIZE` mevcut runtime'da 32 world unit olarak kullanılır.
- `game_ui/world_transform.py` izometrik projeksiyon, kamera, viewport ve zoom işlemlerini sunum katmanında tutar.
- `HexMapDefinition.valid_cells` map-local geçerli hex hücre maskesidir; `blocked` arazi bilgisi hareket/yerleşim kurallarından ayrı ele alınmalıdır.

## 3. İlk uygulama dilimi

Yeni kaynak: `core/domain/spatial/construction.py`

- `ConstructionPosition`: map-scoped map-local world point, mantıksal elevation ve y-down düzleminde clockwise derece cinsinden yönelim.
- `ConstructionSnapPolicy`: x/y world-unit adımları ve açısal adım üzerinden deterministik snap. Sıfır adım ilgili eksende snap'i kapatır; yarım adım eşitlikleri sıfırdan uzağa yuvarlanır.
- `ConstructionSpaceTransform`: tek bir map ID için axial hex hücre merkezi ↔ construction position dönüşümü. Map kimliği uyuşmazlığı reddedilir.

Dışa aktarım: `core/domain/spatial/__init__.py`

Test: `tests/test_spatial/test_construction_coordinates.py`

## 4. Bağlayıcı kararlar

1. Hex dünya kanonik kalır; construction position hex hücreye indirgenmez.
2. Construction position, map ID + mevcut `WorldPoint` + elevation + rotation bileşimidir. Yeni dünya/entity registry veya actor-position sistemi değildir.
3. Construction koordinatları map-local'dır. World-map map placement ve kamera/projeksiyon ofsetleri bu value object'e gömülmez.
4. Hex dönüşümünde hex size açıkça verilir; mevcut 32 world-unit varsayımı domain sözleşmesine sabitlenmez.
5. Rotation derece cinsindendir ve y-down dünya düzleminde saat yönünde artar; değer [0, 360) aralığına normalize edilir.
6. Elevation mantıksal dikey koordinattır; x/y düzlemine, renderer pikseline veya aktör hareketine karıştırılmaz.
7. Snap politikası açıkça çağrılır; global/örtük snap veya kamera zoom'una bağlı grid yoktur.
8. Yerleştirme doğrulama ve atomik commit API'si bu ilk dilimde henüz uygulanmadı. Map maskesi, footprint/geometry, blocked terrain, overlap, support, permission ve stale-state/atomicity kontrolleri için ayrı saf doğrulayıcı tasarımı sonraki Aşama 2 işidir.

## 5. İlk test kapsamı

- Map-scoped position ve rotation normalization
- Geçersiz map ID, point ve non-finite elevation reddi
- Immutable translation/rotation işlemleri
- Deterministik x/y/rotation snapping
- Snap kapatma ve negatif step reddi
- Negatif koordinatlarda half-step davranışı
- Hex merkez ↔ construction position round-trip
- Farklı map ID ile dönüşüm reddi
- Geçersiz hex size/origin reddi

## 6. İkinci uygulama dilimi — yerleştirme önizleme ve doğrulama

Yeni kaynak: `core/domain/spatial/placement.py`

- `ConstructionPlacementRequest`: Parça kimliği, map-scoped konum, yerel footprint noktaları, aktör kimliği, destek ihtiyacı ve yetki kararını taşır.
- `ConstructionPlacementSnapshot`: Değişmez map tanımı, hex ölçüsü/orijini, dolu hücreler, desteklenen hücreler ve state revision girdisini taşır.
- `ConstructionPlacementValidator`: Footprint noktalarını yönelime göre döndürür, world point → axial hücre dönüşümünü deterministik yapar ve dünya sınırı, blocked terrain, overlap, support ve permission kontrollerini ayrı ret nedenleriyle raporlar.
- `ConstructionPlacementResult`: Ghost/preview tüketicisinin kullanabileceği kararlı geçerli/geçersiz sonuç, footprint hücreleri, ret nedenleri ve snapshot revision bilgisini taşır.
- `ConstructionPlacementService`: Preview üretir; commit denemesinde güncel snapshot alıp doğrulamayı yeniden yapar.
- `ConstructionPlacementCommitPort`: Var olan authoritative dünya state'ine bağlanacak adaptör için compare-and-swap sözleşmesidir. Adaptör, revision karşılaştırması ile yerleştirmeyi tek transaction içinde yapmalı; revision uyuşmazlığında hiçbir mutation yapmadan başarısız dönmelidir. Gerçek dünya/runtime adaptörü bu aşamada bağlanmamıştır.

Test: `tests/test_spatial/test_construction_placement.py`

Test kapsamı: geçerli footprint, map uyuşmazlığı, dünya dışı konum, blocked terrain, overlap, support, permission, deterministik yönelim, stale preview ve CAS commit portu davranışı.

## 7. Henüz tamamlanmayan Aşama 2 çıkış ölçütleri

- Footprint-aware map boundary / valid-cell mask validation
- World-outside ve blocked-terrain ret nedenleri
- Yapı-yapı çakışma doğrulaması
- Support ve permission validator ayrımı
- Ghost/preview için geçerli-geçersiz placement sonucu ve kararlı ret nedenleri
- Doğrulama/commit arasında state değişirse stale-state revalidation ve atomik uygulama sınırı
- Coordinate round-trip tolerance ve deterministic placement testlerinin genişletilmesi

Bu nedenle Aşama 2 tamamlanmış veya kabul için hazır sayılmaz. İlk dilim için CI sonuçları geldikten sonra kalan kapsam aynı aşama içinde sürdürülecektir.

## 8. Değişiklik kaydı

- `core/domain/spatial/construction.py` — construction coordinate value objects
- `core/domain/spatial/__init__.py` — public exports
- `tests/test_spatial/test_construction_coordinates.py` — coordinate/snap tests\n- `core/domain/spatial/placement.py` — pure preview/validation and CAS commit boundary\n- `tests/test_spatial/test_construction_placement.py` — placement validation/CAS tests

Bütün değişiklikler yalnızca `experiment/map-cleanup` dalında yapılmıştır. CI doğrulaması tamamlanmadan bu kayıt teknik kabul anlamına gelmez.
