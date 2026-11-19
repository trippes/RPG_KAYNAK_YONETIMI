# Aşama 16 — Teknik Aktarım Uygulama İlerleme Kaydı

**Tarih:** 2026-11-19  
**Çalışma dalı:** `experiment/map-cleanup`  
**Mimari referans:** `reports/phase-16-continuous-world-integration-contract.md`

Bu kayıt, laboratuvar kabiliyetlerinin Eldoria mimarisinde yerel olarak uygulanması sırasında tamamlanan ilk dikey dilimi ve henüz aktarılmayan sorumlulukları ayırır.

## Tamamlanan ilk aktarım dilimi

1. **Yerel sürekli koordinat modeli:** `core.domain.spatial.WorldPoint` ve map-scoped `ContinuousEntityPosition` eklendi. Kanonik eksen +X sağa, +Y aşağı; değerler sonlu ve immutable.
2. **Geometri:** mevcut pointy-top axial dönüşümler korunarak sürekli dünya noktası dönüşümü, fractional axial çözümü, deterministik cube rounding ve önceki hücreyi yalnızca eşit mesafe sınırında koruma eklendi.
3. **Kamera/screen sınırı:** `WorldTransform` sürekli world point ↔ screen dönüşümünü destekliyor.
4. **Runtime sahipliği:** yeni runtime oluşturulmadı. Mevcut `HexWorldRuntime` sürekli konumu tutuyor; hücre pozisyonu/occupancy bu konumla tutarlı türetilmiş görünüm olarak doğrulanıyor. Eski cell-based çağrılar hücre merkezine yerleşerek geriye uyumluluğu koruyor.
5. **Spatial broadphase temeli:** native `AABB` ve map-scoped `UniformGridIndex` eklendi. Mevcut actor ID anahtarı kullanılıyor; index kimlik veya pozisyon otoritesi değil.
6. **Runtime index bağlantısı:** aktör kaydı, hareket, map transfer ve kaldırma sırasında sürekli konum indeksleniyor/güncelleniyor. Runtime sorgusu stabil ID sırasıyla aday döndürüyor.
7. **Persistence:** `HexWorldSnapshot` v2 sürekli x/y kaydediyor. v1 cell-only kayıtlar açıkça hücre merkezine migrate ediliyor; kayıtta olmayan hız/ara hareket uydurulmuyor. Dış `GameSaveDocument` sürümü değiştirilmedi.
8. **Interaction katmanı:** NPC tıklama hedeflemesi `HexGameplayView` hücre taramasından application `HexInteractionService`'e taşındı. Ekran noktası önce world point'e çevriliyor, adaylar spatial index ile bulunuyor; sol tık diyalog ve sağ tık boş menü kabuğu davranışı korunuyor.
9. **Render:** NPC ve oyuncu render konumları mevcutsa runtime'ın sürekli konumunu kullanıyor; render interpolasyonu authoritative runtime state'i değiştirmiyor.
10. **Kimlik bağımlılığı:** `hex_actor_binding.py` içindeki lab EntityId wrap/unwrap kaldırıldı. `WorldActorRegistry` actor ID'si doğrudan kullanılıyor.

## Eklenen/yenilenen test kapsamı

- WorldPoint ve continuous position doğrulaması.
- Y-down axial/world round-trip ve sınır tie-break.
- WorldTransform continuous screen/world round-trip.
- Uniform grid map scope, AABB exact filtering, update/remove ve deterministik sorgu.
- Runtime continuous position, türetilmiş occupancy, index tutarlılığı, başarısız güncelleme atomikliği.
- Hex-world snapshot v2 round-trip ve v1 cell-only migration.
- Application NPC hedef sorgusu ve aynı hücrede stabil ID tie-break.
- Actor identity wrapper kaldırıldı; mevcut actor registry sahiplik testleri korundu.

**Test durumu:** Bu çalışma oturumunda Python test paketi çalıştırılamadı. GitHub commit status sorgusu da raporlanmış bir CI check döndürmedi. Testler eklendi; başarılı oldukları iddia edilmiyor. Yerel doğrulama zorunludur.

## Henüz aktarılmayan / tamamlanmamış kabiliyetler

1. Laboratuvar movement intent, mode, state ve integrator davranışlarının ana oyunun canonical simulation tick'ine bağlanması.
2. Gerçek movement speed/config değerlerinin doğrulanması; mevcut Eldoria'da onaylı world-unit/s değeri bulunmadan değer atanmayacak.
3. Native physics body/shape, static hex collision geometry, broadphase/narrowphase, continuous sweep ve solver aktarımı.
4. Player radius 8 dışında NPC/prop collider ölçülerinin belirlenmesi; henüz onay yok.
5. Dinamik çarpışma indeksinin gerçek collider bounds ile beslenmesi. Şu anki runtime grid actor merkez noktalarını interaction/konum adayı olarak indeksler; fiziksel gövde broadphase'i değildir.
6. Etkileşim profile/range/tag/priority sözleşmesinin tam aktarımı. Mevcut click davranışı korunmuştur; yeni etkileşim davranışı eklenmemiştir.
7. `hex_world_geometry_bridge.py`, `hex_physics_bridge.py` ve kalan tüm lab import tüketicilerinin native Eldoria karşılıklarıyla değiştirilmesi.
8. `pyproject.toml` içindeki `hex_world_lab*` package discovery'nin kaldırılması. Bu adım tüm runtime ve test import'ları sıfırlanana kadar yapılmayacak.

## Koruma notları

- `experiment/map-cleanup` dışında dal değiştirilmedi.
- `main`, `demo_eldoria` veya laboratuvar dalına yazılmadı.
- Laboratuvar kaynak dosyaları ana oyuna kopyalanmadı.
- Yeni oyun içeriği veya oynanış özelliği eklenmedi.
- Save migration açık ve sürümlüdür; dış save schema v3 korunmuştur.

**Sonuç:** İlk yerel dikey dilim uygulandı; teknik aktarım tamamlanmış değildir. Sıradaki ana iş, native fizik ve sabit tick movement pipeline'ıdır. Lab paketini kaldırma aşamasına henüz gelinmemiştir.
