# Eldoria Hex World Laboratory

Eldoria'nın altıgen dünya, hareket, fizik, kamera, render, mekânsal indeks ve entity altyapısını ana oyundan bağımsız geliştirmek ve doğrulamak için kullanılan laboratuvar.

## Çalışma ilkeleri

- Laboratuvar kendi Python paketi, bağımlılıkları, giriş noktası ve test altyapısıyla çalışır.
- Uygulama ve dokümantasyon değişiklikleri yalnızca `experiment/hex-world-laboratory` dalında yapılır.
- `main` ve `demo_eldoria` korunan dallardır; açık kullanıcı izni olmadan bu dallara yazılmaz veya birleştirme yapılmaz.
- Laboratuvar doğrulamaları tamamlanmadan ana oyuna entegrasyon yapılmaz.
- Tek laboratuvar başlatıcısı `python -m hex_world_lab` komutudur. Aşama-özel ikinci başlatıcı kullanılmaz.

## Yetkili belgeler

- [Master Plan ve aşama yol haritası](docs/HEX_WORLD_LAB_MASTER_PLAN.md)
- [Mimari Sözleşme](docs/ARCHITECTURE_SPECIFICATION.md)
- [Geliştirme Kuralları](docs/DEVELOPMENT_RULES.md)
- [Test ve Kabul Ölçütleri](docs/TESTING_AND_ACCEPTANCE_CRITERIA.md)
- [Hex Koordinat Sözleşmesi](docs/HEX_COORDINATE_CONVENTION.md)
- [Harita JSON Şeması v1](docs/MAP_JSON_SCHEMA_V1.md)
- [Runtime Snapshot JSON Şeması v1](docs/RUNTIME_JSON_SCHEMA_V1.md)
- [Spatial İndeks Seçim Kararı — ADR-008](docs/ADR-008-SPATIAL-INDEX-SELECTION.md)

Aşama planlarının ve tarihsel kararların tam dizini Master Plan'dadır. Genel plan, teknik plan ve manuel kabul kontrol listeleri ayrı belgeler olarak korunur; kapanış/doğrulama kayıtları ise mümkün olduğunca tek aşama kapanış raporunda birleştirilir.

## Aşama kapanış raporları

- [Aşama 0 — Temel ve yönetişim](reports/PHASE-00-FOUNDATION-CLOSURE.md)
- [Aşama 1 — Altyapı](reports/PHASE-01-INFRASTRUCTURE-REPORT.md)
- [Aşama 2 — Geometri](reports/PHASE-02-GEOMETRY-REPORT.md)
- [Aşama 3 — Dünya modeli ve persistence](reports/PHASE-03-WORLD-REPORT.md)
- [Aşama 4 — Sürekli hareket](reports/PHASE-04-CLOSURE-REPORT.md)
- [Aşama 4.7 — Hareket modları ve teknik doğrulama](reports/PHASE-04.7-CLOSURE-REPORT.md)
- [Aşama 5 — Gövde, çarpışma ve fizik](reports/PHASE-05-CLOSURE-REPORT.md)
- [Aşama 6 — Kamera ve dünya/ekran dönüşümü](reports/PHASE-06-CLOSURE-REPORT.md)
- [Aşama 7 — Render ve görsel doğrulama](reports/PHASE-07-CLOSURE-REPORT.md)
- [Aşama 8 — Mekânsal indeksleme](reports/PHASE-08-CLOSURE-REPORT.md)
- [Aşama 9 — Varlıklar ve etkileşimler](reports/PHASE-09-CLOSURE-REPORT.md)
- [Aşama 10 — Simülasyon orkestrasyonu](reports/PHASE-10-CLOSURE-REPORT.md)
- [Aşama 11 — Başlangıç ölçüm raporu](reports/PHASE-11-BASELINE-REPORT.md)
- [Aşama 11 — Stres ve regresyon doğrulama raporu](reports/PHASE-11-STRESS-VALIDATION-REPORT.md)
- [Aşama 11 — Kapanış raporu](reports/PHASE-11-CLOSURE-REPORT.md)

Aşama 3.6/3.7 ve Aşama 6–9 alt aşamalarının uygulama, test, CI ve benchmark kanıtları ilgili birleşik kapanış raporlarına taşınmıştır. Silinen eski rapor adları artık kullanılmamalıdır.

## Kurulum (Windows PowerShell)

Laboratuvar dizinine geç:

```powershell
cd experiments/hex_world_laboratory
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Python 3.12 önerilir. Paket Python 3.11 ve üzerini destekleyecek şekilde tanımlanmıştır.

## Çalıştırma

Laboratuvar kök dizininden:

```powershell
python -m hex_world_lab
```

Bu tek giriş noktası güncel Entity kabul sahnesini (oyuncu, NPC, kaynak ve NPC sağ-tık eylem menüsü) başlatır.

- `F3`: collider debug görünümünü açıp kapatır.
- `F4`: çevresel nesne ground/depth anchor, visual/canopy bounds, kimlik ve konum tanılamasını açıp kapatır.
- `Esc`: laboratuvar penceresini kapatır.
- NPC üzerinde sağ tık: yoldaş eylem menüsünü açar.

## Aşama 12 — Çevresel nesneler

- [Aşama 12 genel planı](docs/PHASE-12-GENERAL-PLAN.md)
- [Aşama 12 teknik planı](docs/PHASE-12-TECHNICAL-PLAN.md)
- [Aşama 12 manuel kabul kontrol listesi](docs/PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md)
- [Aşama 12 uygulama, doğrulama ve kapanış raporu](reports/PHASE-12-IMPLEMENTATION-VALIDATION-REPORT.md)
- [Aşama 12 resmî kapanış raporu](reports/PHASE-12-CLOSURE-REPORT.md)
- Ağaç, kaya ve çalı görselleri `rendering/procedural_environment.py` içindeki deterministik Pygame çizicileriyle runtime sırasında üretilir. Hazır PNG/JPG/WebP dosyası yüklenmez.


## Aşama 13 — Genel prosedürel çizim altyapısı

- [Aşama 13 genel planı](docs/PHASE-13-GENERAL-PLAN.md)
- [Aşama 13 teknik planı](docs/PHASE-13-TECHNICAL-PLAN.md)
- [Aşama 13 resmî kapanış raporu](reports/PHASE-13-CLOSURE-REPORT.md)

## Aşama 15 — Nihai mimari ve entegrasyon hazırlığı

- [Aşama 15 genel planı](docs/PHASE-15-GENERAL-PLAN.md)
- [15.1 gerçekleşen mimari denetim raporu](reports/PHASE-15.1-AUDIT-REPORT.md)
- [Ayrıntılı teknik mimari planı](docs/PHASE-15-TECHNICAL-PLAN.md)

15.1 mimari denetimi tamamlandı ve ayrıntılı teknik plan hazırlandı. Teknik plan kullanıcı onayı beklemektedir; 15.2–15.8 uygulaması ve ana oyuna entegrasyon başlamamıştır. main ve demo_eldoria salt okunur korunur.

## Aşama 14 — Content data foundation

- [Aşama 14 genel planı](docs/PHASE-14-GENERAL-PLAN.md)
- [Aşama 14 teknik planı](docs/PHASE-14-TECHNICAL-PLAN.md)
- [Aşama 14 manuel kabul kontrol listesi](docs/PHASE-14-MANUAL-ACCEPTANCE-CHECKLIST.md)
- [Aşama 14 uygulama ve otomatik doğrulama raporu](reports/PHASE-14-IMPLEMENTATION-REPORT.md)
- [Aşama 14 resmî kapanış raporu](reports/PHASE-14-CLOSURE-REPORT.md)
- [Content Data API hazırlık rehberi](docs/CONTENT_DATA_API.md)
- [Content Library JSON v1 sözleşmesi](docs/content/CONTENT_LIBRARY_JSON_SCHEMA_V1.md)
- [Map Content JSON v1 sözleşmesi](docs/content/MAP_CONTENT_JSON_SCHEMA_V1.md)
- [Machine-readable JSON schemas](schemas/)
- [Phase 14 görsel/benchmark artifact'i](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44396008498/artifacts/14470961143)

Aşama 14, gelecekteki ELDORIA CONTENT EDITOR için Pygame'den bağımsız content model, vector VisualDocument, ContentLibrary, MapContentDocument, strict persistence ve runtime adapter altyapısını sağlar. Masaüstü editör ve map editing UI bu aşamanın kapsamı dışındadır.

## Test

```powershell
python -m pytest -q
```

Laboratuvarın tam test paketi ve benchmarkları GitHub Actions laboratuvar iş akışında doğrulanır. Linux ve Windows Core Quality sonuçları da ilgili CI çalıştırmalarından izlenir. Test sayıları geliştirme sırasında değişebileceğinden README içinde sabit bir sayı tutulmaz; güncel sonuçlar ilgili workflow run kayıtlarıdır.

## Mimari sınırlar

- Dünya konumu `WorldPoint` authoritative kalır; axial hex koordinatı gerektiğinde türetilir.
- Hex topolojisi ve fiziksel AABB/spatial sorguları ayrı sözleşmelerdir.
- Spatial broadphase aday toplar; kesin çarpışma/menzil kararını ilgili narrowphase veya interaction katmanı verir.
- Kamera ve render simülasyon state'ini değiştirmez.
- Yoldaş FOLLOW/WAIT/RETURN komutları Aşama 9'da yalnızca niyet/durum olarak kaydedilir; gerçek takip hareketi, steering ve pathfinding değildir.
- Ana oyuna entegrasyon, otonom NPC AI'ı, click-to-move ve çevre sanat paketi ayrı plan/onay gerektirir.

## Güncel durum

**Aşamalar 0–14 tamamlandı ve kullanıcı tarafından kabul edildi. Aşama 15 Genel Planı hazırlandı; kullanıcı onayı bekleniyor. Teknik plan ve uygulama başlamadı.** Aşama 11'in 774 laboratuvar testi, 36.000 tick stres doğrulaması, üç oturumlu performans/bellek ölçümleri ve Linux/Windows CI kontrolleri başarıyla tamamlandı. Aşama 12 prosedürel çizim revizyonu uygulandı ve otomatik doğrulandı: 800 laboratuvar testi, Linux/Windows Core Quality (2.263'er test), üç oturumlu 10/100/1.000 nesne benchmarkı ve beş görsel kanıt başarılı. [Doğrulama raporu](reports/PHASE-12-IMPLEMENTATION-VALIDATION-REPORT.md) ve [CI artifact'i](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44323325450/artifacts/14436541384). Kullanıcı 18 Kasım 2026 tarihinde manuel görsel/işlevsel kabulü verdi. Son ağaç gövdesi ve kaya collider hizalaması F3 görünümünde doğrulanarak kabul edildi; Aşama 12 resmen kapatıldı. [Manuel kabul kontrol listesi](docs/PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md). Aşama 13 de 859/859 test, Ruff, Linux/Windows CI ve kullanıcı görsel kabulinden sonra kapatıldı. Aşama 14'te 881/881 laboratuvar testi, Linux 2.344 test, Windows Core Quality, Ruff, benchmark ve görsel artifact başarılıdır; 19 Kasım 2026 tarihinde kullanıcı görsel kabulinden sonra resmen kapatılmıştır. [Aşama 14 raporu](reports/PHASE-14-IMPLEMENTATION-REPORT.md).
