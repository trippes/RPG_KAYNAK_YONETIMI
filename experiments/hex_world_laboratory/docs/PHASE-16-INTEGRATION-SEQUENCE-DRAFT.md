# Aşama 15.6 — Aşama 16 Entegrasyon Dilimleri ve Geri Dönüş Taslağı

Durum: Taslak öneri; Aşama 16 uygulama onayı değildir.  
Tarih: 19 Kasım 2026.

## 1. Temel yaklaşım

Büyük bir merge veya klasör kopyalama yerine küçük, tek sorumluluklu entegrasyon dilimleri kullanılmalıdır. Her dilim ayrı branch commit'i, CI, test kanıtı ve kullanıcı kabul kapısı taşır. Main mevcut runtime/content davranışı, adapter parity testleri geçmeden devreden çıkarılmaz.

## 2. Önerilen dilim sırası

| Dilim | Hedef | İlk değişiklik alanı | Ön koşul | Kabul kapısı | Geri dönüş |
|---|---|---|---|---|---|
| 0. Runtime/package spike | pygame/pygame-ce, entry point, clean install kararını kanıtla | pyproject, build scripts, isolated smoke fixtures (A16 branch) | Kullanıcı dağıtım kararı | clean venv, Linux/Windows, import/display/asset smoke | Spike branch/commit kaldırılır; main dosyaları etkilenmez |
| 1. Domain/geometry bridge | Axial, layout, world unit, map/world ID mapping | core/domain/spatial adapter package | Tek koordinat ve owner sözleşmesi | roundtrip/property tests, negative/boundary cases | Adapter kaldırılır; Main HexCoord/LocalHexPosition kalır |
| 2. Entity and movement bridge | Continuous movement ve discrete actor model arasında sınır | application adapter/service, test fixtures | Authoritative movement state kararı | deterministic tick, occupancy, collision, map transition tests | Eski HexWorldRuntime yolu varsayılan kalır |
| 3. Spatial/physics bridge | Lab broadphase/continuous collision'i Main occupancy ile ilişkilendir | physics adapter ve opt-in feature flag | Geometry/entity bridge kabulü | brute-force differential, collision regression, performance baseline | Yeni index/solver devre dışı; eski occupancy path |
| 4. Simulation orchestration | Lab tick sequencing'i Main simulation runtime ile bağla | core/simulation adapter/application service | Tick owner ve retry semantics kararı | no double tick/update, deterministic replay, action/time regression | Önceki game loop/runtime orchestration |
| 5. Camera/render bridge | Immutable snapshot'i Main renderer/depth pipeline'a bağla | game_ui/world_rendering adapters | Snapshot schema ve world-pixel mapping | visual screenshot/manual checks, y-sort, anchor, culling, zoom | Mevcut Main renderer/camera |
| 6. Vector content read adapter | VisualDocument'i Surface cache/AssetManager ile sun | game_ui/assets vector adapter | Pygame distribution + anchor/layer/collider mapping | visual golden images, cache lifecycle, asset fallback | Main raster catalog/renderer unchanged |
| 7. Placement/persistence coexistence | Vector source ile Main axial placements için açık ownership | application presentation service adapter; no schema overwrite | Content owner + ID + map conversion decisions | legacy fixtures, staged validation, backup/rollback | Lab content read-only; Main package backup restore |
| 8. Platform/release acceptance | Birleşik kurulum ve mevcut save/content davranışı | packaging/CI/docs | Önceki dilimlerin tamamı | Linux/Windows clean install, tests, performance, visual acceptance | Release candidate tag/branch geri alınır |

## 3. Her dilimin zorunlu çalışma protokolü

1. Önce A16 branch HEAD ve Main korunan branch HEAD'leri kaydedilir.
2. Yalnızca dilimin hedef dosyaları değiştirilir; dosya listesi PR/raporda belirtilir.
3. Önce unit test, sonra adapter contract test, sonra integration/regression test.
4. Main mevcut davranışını doğrulayan parity fixture'ları korunur.
5. CI geçmeden ve kullanıcı görsel/işlevsel kabul vermeden sonraki dilime geçilmez.
6. Veri migration'ı gerekiyorsa migration dry-run ve backup/restore kanıtı ayrıca alınır.
7. Her dilim için geri dönüş commit'i ve açık rollback komutu/işlemi rapora yazılır.

## 4. Veri güvenliği

- Main mevcut save, package, asset catalog ve placement dosyaları kaynak veri olarak korunur.
- İlk vector content entegrasyonu read-only coexistence olmalıdır; iki yönlü sync yok.
- Aynı veri dosyası için iki writer bulunamaz.
- Schema v1/v2 yerinde değiştirilmez. Yeni schema gerekirse yeni sürüm, migration fixture ve rollback.
- Migration'dan önce tüm ilgili content package ve save dosyaları yedeklenir; staged validation başarılı olmadan replace yapılmaz.
- Backup doğrulanmadan destructive cleanup veya legacy format kaldırma yapılmaz.

## 5. Durdurma ölçütleri

Aşağıdakilerden biri görülürse ilgili dilim durdurulur:
- Entity/world/content authoritative owner belirsizliği.
- Coordinate conversion roundtrip veya boundary testi başarısızlığı.
- Mevcut Main save/content fixture'ının okunamaması.
- Pygame distribution/Surface API uyumsuzluğu.
- CI platformlarından birinde import, packaging veya runtime regression.
- Collision false positive/negative veya spatial differential mismatch.
- Snapshot render'ın simulation state'i değiştirmesi.
- Performance baseline'ında gerekçesiz ciddi regresyon.
- Asset provenance veya license gate'in çözülememesi.

## 6. Kullanıcı karar kapıları

A16 başlamadan kullanıcıdan açık onay gerektiren kararlar:
1. Pygame distribution strategy.
2. Continuous/discrete movement authoritative owner.
3. Map/world coordinate and unit conversion.
4. Main renderer mı, Lab renderer mı, yoksa adapter bridge mi sunum sahibi olacak.
5. Vector content ve raster catalog coexistence/ownership modeli.
6. İlk A16 diliminin kapsamı ve rollback noktası.

Bu belge A16 için önerilen yol haritasıdır; kod taşıma, merge veya Main branch değişikliği yetkisi vermez.
