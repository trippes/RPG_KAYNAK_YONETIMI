# Eldoria — Modüler Yapı ve İnşa Sistemi
## Aşama 2: İnşa Koordinatları ve Yerleştirme Sistemi — Teknik İnceleme Kaydı

- **Durum:** Devam ediyor; koordinat ve saf yerleştirme doğrulama dilimi uygulanmış, gerçek runtime entegrasyonu ve kullanıcı kabulü bekliyor
- **Hedef dal:** `experiment/map-cleanup`
- **Kapsam referansı:** `docs/architecture/90-modular-building-construction-system-roadmap.md`
- **İncelenen kaynak HEAD:** `a8a0332c94fdbaea996399c88c75c12fae4d6b1e`

## 1. Aşama sınırı

Bu aşama inşa uzayı koordinat/value object'lerini, hex dünya ile deterministik dönüşümü, hassas konum/yön/yükseklik ve snap/hizalama kurallarını, ayrıca yerleştirme önizleme/doğrulama ve atomik commit sınırını kapsar.

Zemin/duvar/kapı/pencere runtime'ı, crafting, envanter tüketimi, fizik/navigasyon/render entegrasyonu, save/load ve NPC inşası bu aşamanın kapsamı değildir. Mevcut aktör konumu, entity registry, HexWorldRuntime veya GameplayPlacementCatalog için ikinci bir otorite oluşturulmayacaktır.

## 2. İncelenen mevcut mimari

- `HexWorldRuntime`, map tanımlarını, hareketli entity state'ini, sürekli aktör konumlarını, `HexOccupancyRegistry` ve broadphase spatial index'i yönetir.
- `HexOccupancyRegistry`, `HexOccupant` kayıtlarıyla aktör/entity hücre doluluğunu yönetir. Kayıtlar entity ID, tek hücre konumu ve hareket/occupancy engelleme bayrakları taşır.
- `HexWorldRuntime` içinde yapı parçası yerleşim koleksiyonu, yapı footprint sorgusu veya ortak dünya state revision/CAS API'si bulunmamaktadır.
- `GameplayPlacementCatalog`, içerik paketlerinde NPC/resource/container başlangıç yerleşimlerini tanımlar. `GameplayService` bu kayıtları mevcut canonical spatial binding servisleri üzerinden `HexWorldRuntime`'a bağlar. Bu katalog, canlı yapı yerleşim deposu değildir.
- `StructureGeometryDefinition`, shape_kind, width, depth, height ve explicit `footprint_local_points` taşır. shape_kind açıklayıcı metadata'dır; width/depth şu an placement footprint hesabına katılmaz.
- `core/application/ownership.py` World üyeliğini, `core/application/world_runtime.py` simülasyon zaman/event köprüsünü yönetir. İncelenen bu sınırlar yapı placement state'i veya yapı yerleştirme yetkisi sahibi değildir.

## 3. Uygulanmış koordinat sözleşmeleri

Kaynak: `core/domain/spatial/construction.py`  
Export: `core/domain/spatial/__init__.py`  
Test: `tests/test_spatial/test_construction_coordinates.py`

- `ConstructionPosition`: map-scoped map-local WorldPoint, elevation ve rotation.
- Rotation y-down düzleminde saat yönünde artar ve [0, 360) aralığına normalize edilir.
- `ConstructionSnapPolicy`: x/y world-unit adımları ve açısal adım üzerinden açık, deterministik snap sağlar. Sıfır adım ilgili snap eksenini kapatır; yarım adım eşitlikleri sıfırdan uzağa yuvarlanır.
- `ConstructionSpaceTransform`: tek map ID için axial hex hücre merkezi ile construction position arasında dönüşüm yapar; map ID uyuşmazlığını reddeder.
- Hex size açık parametredir; mevcut runtime'ın 32 world-unit değeri domain sözleşmesine sabitlenmemiştir.
- Kamera, projeksiyon, zoom ve viewport dönüşümleri domain katmanına alınmamıştır.

Bu dilim uygulanmıştır. Aşama 2'nin gerçek runtime entegrasyonunu tek başına sağlamaz.

## 4. Uygulanmış placement preview/validation sözleşmeleri

Kaynak: `application/construction_placement.py`  
Test: `tests/test_spatial/test_construction_placement.py`

- `ConstructionPlacementRequest`: parça kimliği, map-scoped konum, explicit yerel footprint noktaları, aktör kimliği, support ihtiyacı ve permission kararı.
- `ConstructionPlacementSnapshot`: map tanımı, hex size/origin, dolu hücreler, desteklenen hücreler ve state revision girdisi. Mapping verisi immutable hale getirilir.
- `ConstructionPlacementValidator`: noktaları rotation'a göre döndürür, world point → axial hücre dönüşümü yapar; map sınırı, blocked terrain, overlap, support ve permission sonuçlarını ayrı ret nedenleriyle döndürür.
- `ConstructionPlacementResult`: geçerlilik, footprint hücreleri, ret nedenleri ve snapshot revision taşır.
- `ConstructionPlacementService`: preview üretir; commit denemesinde yeni snapshot alıp tekrar doğrular.
- `ConstructionPlacementCommitPort`: revision karşılaştırması ile yerleştirmenin tek transaction içinde yapılmasını zorunlu tutan application port sözleşmesidir.

Uygulanmış doğrulama davranışları: yanlış map, map maskesi dışı footprint hücresi, blocked terrain, snapshot'ta verilen occupied cells ile çakışma, support girdisi, permission girdisi, deterministik rotation ve stale revision ret davranışı.

**Önemli sınır:** Snapshot şu an çağıran tarafından verilir; gerçek `HexWorldRuntime`'dan üretilmez. `occupied_cells` mevcut runtime aktör doluluğuna bağlanmamıştır. Bu nedenle şu anki testler gerçek oyun dünyasındaki oyuncu/NPC/nesne/yapı çakışmasını kanıtlamaz.

## 5. Geometri-footprint semantiği

`ConstructionPlacementRequest.from_part_definition`, `StructureGeometryDefinition.footprint_local_points` değerini placement request'e aktarır. Böylece geometry tanımı ile doğrulama arasında veri bağlantısı vardır.

Ancak mevcut algoritma polygon rasterization yapmaz. Her yerel nokta döndürülüp world point'e taşınır ve tek bir axial hücreye dönüştürülür; sonuç hücrelerin birleşimidir. İki uç nokta arasındaki ara hücreler otomatik doldurulmaz. `shape_kind`, `width` ve `depth` footprint üretmek için kullanılmaz.

Bu nedenle bugünkü semantik **explicit footprint sample points** olarak kabul edilmelidir. İçerik yazarı her işgal edilmesi gereken hex hücreyi temsil eden örnek noktaları açıkça sağlamalıdır. Bu, polygon/solid footprint desteği değildir. Polygon rasterization istenirse ayrı algoritma ve sınır testleriyle tasarlanmalıdır; shape_kind üzerinden örtük dikdörtgen üretimi yapılmamalıdır.

## 6. Gerçek runtime entegrasyonu için mimari karar

En az müdahaleli hedef, yapı yerleşim state'ini mevcut `HexWorldRuntime` authoritative owner'ı içinde yönetmektir:

1. Runtime içinde yapı placement kayıtlarını ve map-scoped footprint sorgusunu tutan bir API tanımlanmalı.
2. Aktör/entity occupancy ile yapı placement kayıtları semantik olarak ayrı kalmalı. `HexOccupancyRegistry` yapı aggregate deposuna dönüştürülmemeli; tek hücrelik aktör hareket kuralları çok hücreli yapı kayıtlarıyla karıştırılmamalı.
3. Placement snapshot üretimi runtime'ın map tanımı, mevcut actor occupancy görünümü, yapı footprint kayıtları ve runtime'a ait monoton state revision üzerinden yapılmalı.
4. Preview snapshot'ı aktör ve yapı çakışmalarını açık kurallarla kapsamalı. Bir actor hücresi ile yapı footprint'i farklı veri sahiplerinden gelse de doğrulama tek tutarlı snapshot üzerinden yapılmalı.
5. Commit işlemi aynı runtime owner içinde revision compare-and-swap + footprint çakışma kontrolü + placement kaydı ekleme işlemlerini tek kritik işlem olarak yürütmeli. Başarısız commit hiçbir kaydı veya revision'ı değiştirmemeli.
6. Her başarılı world mutation revision'ı artırmalı. Revision kapsamı ve artırma kuralları açık olmalı; yalnızca yapı kaydını değil snapshot'ı etkileyen ilgili değişiklikleri de kapsamalı.
7. Bu işlem için bağımsız ikinci bir world/runtime/registry oluşturulmamalı.

Bu tasarım henüz uygulanmış değildir. Runtime eşzamanlılık modeli ve mutation noktaları kod/test üzerinden ayrıca doğrulanmadan thread-safety veya transaction garantisi verilmemelidir.

## 7. Support ve permission sahipliği

Şu an `requires_support` ve `has_permission` request'e doğrudan boolean olarak verilir. Bunlar gerçek support graph/structural owner veya actor/world authorization servisine bağlı değildir. Dolayısıyla mevcut kontroller entegrasyon portu değil, saf doğrulayıcı girdileridir.

Aşama 2 kapsamında bu girdiler için sahte production varsayılanları oluşturulmamalıdır. İlgili gerçek owner bulunup sözleşmesi belirlenmeli; bulunmuyorsa bu koşulların hangi aşamada ve hangi owner tarafından sağlanacağı açıkça belgelenmelidir. Kullanıcı/oyun içi izin ve yapısal destek davranışı bu testlerden kanıtlanmış sayılamaz.

## 8. Test kapsamı ve kalan test işleri

Mevcut `tests/test_spatial/test_construction_placement.py` şu davranışları kapsar:
- Geçerli footprint ve revision sonucu
- Geometry tanımından explicit footprint aktarımı
- Footprint tanımı olmayan parçanın reddi
- Wrong-map, outside-world ve blocked-terrain ayrımı
- Overlap ve unsupported ret nedenleri
- Permission denial
- Deterministik rotation
- Commit sırasında revision guard başarı/ret örnekleri
- Stale preview reddi

Genişletilmesi gereken testler:
- Gerçek runtime snapshot'ının actor occupancy + structure placement verisini tutarlı üretmesi
- Bir ve çok hücreli footprint'in actor, object ve yapı kayıtlarıyla çakışması
- Sınırın tam üzerinde/çok yakınında dönüşüm, negatif ve büyük koordinatlar, farklı hex size/origin
- Rotation açı sınırları ve floating-point toleransı
- Commit yarışında revision değişimi; stale durumda hiçbir placement/revision mutation olmaması
- Aynı footprint'e eşzamanlı iki commit girişiminde yalnızca birinin başarılı olması
- Hatalı/boş/tekrarlı footprint ve map maskesi kenar durumları
- Support ve permission kararlarının gerçek owner adaptörleri üzerinden alınması

Mevcut fake port testleri port sözleşmesini örnekler; gerçek runtime atomikliğini kanıtlamaz.

## 9. CI doğrulaması

İncelenen kaynak HEAD: `a8a0332c94fdbaea996399c88c75c12fae4d6b1e`

- [Core quality — run 46064704936](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/46064704936): tamamlandı, başarılı. Windows ve genel verify işleri başarılı; Ruff ve release-candidate kontrolleri geçti.
- [Eldoria CI — run 46064704952](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/46064704952): tamamlandı, 5/5 job başarılı. Python testleri Windows/Ubuntu 3.11 ve 3.12, Pygame headless smoke ve ilgili render/pipeline kontrolleri geçti.

Bu CI sonuçları ilgili HEAD'deki mevcut kodun workflow kontrollerini geçtiğini gösterir. Gerçek runtime placement entegrasyonu veya kullanıcı kabulü yerine geçmez.

## 10. Aşama 2 çıkış ölçütlerinin güncel durumu

| Ölçüt | Durum | Kanıt / eksik |
|---|---|---|
| Construction coordinate/value object'leri | Uygulandı | construction.py ve coordinate testleri |
| Hex ↔ construction dönüşümü | Uygulandı | ConstructionSpaceTransform testleri |
| Snap ve rotation kuralları | Uygulandı | Coordinate testleri |
| Preview request/result sözleşmesi | Uygulandı | construction_placement.py |
| Map boundary ve blocked terrain doğrulaması | Saf snapshot doğrulayıcıda uygulandı | Gerçek runtime snapshot bağlantısı yok |
| Footprint geometry bağlantısı | Kısmen uygulandı | Explicit sample points aktarılıyor; polygon rasterization yok |
| Actor + structure overlap | Bekliyor | Runtime actor occupancy snapshot'a bağlanmadı; structure kayıtları yok |
| Support/permission owner entegrasyonu | Bekliyor | Şu an boolean request girdileri |
| Authoritative runtime snapshot provider | Bekliyor | HexWorldRuntime adaptörü yok |
| Runtime state revision ve atomik CAS commit | Bekliyor | Runtime revision/structure mutation API'si yok |
| Sınır/hassasiyet/çakışma testlerinin genişletilmesi | Kısmen | Saf validator testleri var; runtime ve edge-case testleri eksik |
| CI | Başarılı | İki workflow da aynı incelenen HEAD'de başarılı |
| Oyun içi manuel kabul | Bekliyor | Gerçek oyun akışında yapı yerleştirme yok |

## 11. Sonuç ve devam sırası

Aşama 2 tamamlanmış veya kullanıcı kabulüne hazır değildir. Aşama 3'e geçilmeyecektir.

Önerilen uygulama sırası:
1. `HexWorldRuntime` için yapı kayıtları ve monoton revision sahibi tasarımını netleştir.
2. Actor occupancy ile structure footprint sorgularını tek snapshot üretiminde birleştir; veri sahipliğini ayrı tut.
3. Runtime-backed snapshot provider ve aynı owner içinde atomic CAS placement commit uygula.
4. Geometry footprint sample-point semantiğini açıkça koru veya polygon rasterization ihtiyacını ayrı karar olarak ele al.
5. Support/permission owner'larını belirle ve adaptörleri bağla.
6. Runtime entegrasyon, concurrency, sınır, dönüşüm ve overlap testlerini ekle.
7. CI'ı yeniden çalıştır; raporu güncelle.
8. Kullanıcı gerçek oyun penceresinde yerleştirme/ret/çakışma akışını kabul etmeden Aşama 2'yi kapatma.

## 12. Değişiklik kaydı

- `core/domain/spatial/construction.py` — construction coordinate value objects
- `core/domain/spatial/__init__.py` — public exports
- `tests/test_spatial/test_construction_coordinates.py` — coordinate/snap tests
- `application/construction_placement.py` — application-level preview/validation and commit port
- `tests/test_spatial/test_construction_placement.py` — placement validation/CAS contract tests
- `reports/90-modular-building-construction-phase-2-placement.md` — this stage record

Bütün kaynak değişiklikleri yalnızca `experiment/map-cleanup` dalında incelenmiştir. Bu rapor Aşama 2'yi kapatmaz ve sonraki aşamayı başlatmaz.


## 10. Runtime entegrasyonu — ilk uygulama dilimi (2026-11-27)

Bu inceleme kaydından sonra `HexWorldRuntime` içine ilk gerçek runtime entegrasyon dilimi eklendi:

- Canlı yapı örnekleri `HexWorldRuntime` tarafından `HexWorldStructurePlacement` kayıtları olarak tutulur; `HexOccupancyRegistry` aktör/entity occupancy sahibi olarak kalır.
- Runtime, tek bir placement snapshot'ında aktör hücrelerini ve yapı footprint hücrelerini birleştirir. Aktör occupancy kayıtları yapı kayıtlarına dönüştürülmez.
- Runtime'ın monoton `state_revision` değeri entity kayıt, kaldırma, etkinlik değişikliği, hücre hareketi, sürekli konum güncellemesi ve başarılı yapı commit'i ile ilerler.
- `commit_if_revision`, beklenen revision kontrolünü, aktörün runtime'da kayıtlı ve aynı haritada olmasını, footprint'in yeniden hesaplanmasını, dünya sınırı/blocked terrain/aktör/yapı çakışma kontrollerini ve yapı kaydını tek kilitli runtime işlemi içinde yapar.
- Başarısız/stale commit yapı kayıtlarını, footprint indeksini veya revision değerini değiştirmez.
- `HexWorldRuntimeOwner.discard_if_empty`, yapı kayıtları varken runtime'ın atılmasını da engeller.
- Yeni test dosyası: `tests/test_application/test_construction_runtime_integration.py`. Aktör+structure snapshot, başarılı commit, stale revision, footprint overlap, kayıtlı olmayan actor ve runtime owner lifecycle senaryolarını kapsar.

### Açık sınırlar

- Support evidence runtime tarafından uydurulmaz. `construction_snapshot(..., supported_cells=...)` çağıran gerçek support owner'ın hücre kanıtını vermesini bekler. Henüz böyle bir production support owner entegrasyonu yoktur.
- Permission şu anda request girdisidir; commit sınırında false karar tekrar reddedilir, ancak gerçek authorization owner henüz bağlanmamıştır.
- Runtime commit, yapının kayıtlarını ve hex footprint indeksini yönetir; henüz rendering, collision broadphase, pathfinding, kapı/duvar davranışı veya save/load entegrasyonu yapmaz.
- Runtime'ın kilidi runtime API'si üzerinden yapılan ilgili mutasyonları seri hale getirir. `occupancy` registry'sine runtime dışından doğrudan mutasyon yapılması desteklenen entegrasyon yolu değildir; bütün dünya değişiklikleri runtime API'sinden geçirilmelidir.
- Gerçek oyun akışından placement service çağrısı ve manuel kabul henüz yapılmadı.

Bu nedenle runtime entegrasyonunun temel storage/snapshot/commit yolu uygulanmış olsa da Aşama 2 tamamlanmış değildir. CI sonuçları ve sonraki entegrasyon kontrolleri beklenir.


## 11. Gerçek zemin desteği entegrasyonu (2026-11-28)

İlk support entegrasyonunda elle verilen `supported_cells` girdisi kaldırıldı. Destek kanıtının kaynağı artık map içeriğinin açık terrain capability tanımıdır:

- `HexMapDefinition.foundation_supporting_terrain_ids`, temel taşıyabilen terrain kimliklerini immutable olarak tutar.
- Map JSON şemasında `foundation_supporting_terrain_ids` alanı tanımlanmıştır. Bilinmeyen terrain ID'leri ve tekrarlar yükleme sırasında reddedilir.
- Alanın bulunmadığı eski/test haritaları güvenli biçimde boş destek kümesi üretir; varsayılan olarak hiçbir terrain taşıyıcı sayılmaz.
- `application/construction_support.py` içindeki `ConstructionSupportService`, map hücrelerinin gerçek `terrain_id` değerlerini okuyarak desteklenen axial hücreleri üretir.
- `HexWorldRuntime.construction_snapshot` bu servisi kullanır. Çağıran artık destek hücresi enjekte edemez.
- `commit_if_revision` aynı runtime snapshot'ını yeniden ürettiği için preview sırasında sağlanan destek kanıtı commit anında da aynı authoritative map verisinden tekrar doğrulanır.
- Geçilebilirlik (`blocked`) ile taşıma kabiliyeti birbirinden ayrıdır. Support servisi blocked flag'ini kullanmaz; yerleştirme validator'ı kendi blocked-terrain kuralını ayrıca uygular.

İçerik verileri:
- `content/movement_test/hex_maps/movement_test_arena.json`: grass, stone ve dirt temel taşıyabilir; water taşıyamaz.
- `content/demo_eldoria/hex_maps/starting_valley.json`: grass, forest_floor, clearing_floor ve rock temel taşıyabilir; water taşıyamaz. Rock'ın blocked olması yerleştirmeyi ayrıca engeller; bu, taşıma kabiliyetiyle geçilebilirliğin farklı kavramlar olduğunu korur.

Test kapsamına runtime'ın destek hücrelerini terrain metadata'dan üretmesi ve metadata bulunmadığında `UNSUPPORTED` ile güvenli ret eklenmiştir. Runtime placement entegrasyon testleri artık `requires_support=True` ile çalışır.

### Kapsam sınırı

Bu, zemin/temel seviyesinde ikili taşıma kabiliyeti kontrolüdür; mühendislik anlamında yük kapasitesi, zemin basıncı, eğim/zemin deformasyonu veya jeoteknik simülasyon değildir. Duvar/kolon/kiriş/kat/çatı üzerinden yük aktarımı, destek zinciri ve yapı stabilitesi ayrıca tasarlanmalıdır. Bunlar Aşama 6 ve ilgili yapı-fizik entegrasyonu kapsamındadır. Mevcut yapı parçalarının destek gereksinimi henüz parça tanımlarından otomatik türetilmiyor; request `requires_support` bayrağıyla açıkça ister.

Bu entegrasyon Aşama 2'yi kapatmaz. CI ve kullanıcı kabulü beklenir.
