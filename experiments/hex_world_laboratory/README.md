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

- `F3`: çarpışma/etkileşim tanılamasını açıp kapatır.
- `Esc`: laboratuvar penceresini kapatır.
- NPC üzerinde sağ tık: yoldaş eylem menüsünü açar.

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

**Aşamalar 0–9 tamamlandı ve kullanıcı tarafından kabul edildi.** Sıradaki planlı çalışma Aşama 10 — Simülasyon orkestrasyonu ve dünya bütünlüğüdür. Aşama 10 kodlaması, genel plan, teknik mimari ve kabul ölçütleri hazırlanıp kullanıcı tarafından ayrıca onaylanmadan başlamaz.
