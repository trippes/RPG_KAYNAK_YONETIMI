# Aşama 15.8 — Nihai Entegrasyon Hazırlık Kararı

Tarih: 19 Kasım 2026  
Değerlendirme kapsamı: 15.1–15.7  
Karar durumu: **KOŞULLU HAZIR — YALNIZCA AŞAMA 16 PLANLAMASI İÇİN**  
Aşama 16 kod entegrasyonu: **HAZIR DEĞİL / AYRI ONAY VE ÖN KOŞULLAR GEREKİR**

## 1. Yönetici özeti

Laboratuvar Aşama 0–14 boyunca geometri, sürekli hareket, fizik, spatial, entity, simulation, rendering ve vector content katmanlarında bağımsız ve test edilmiş bir temel oluşturdu. Ana oyunda ise hex map runtime, hücre tabanlı movement/occupancy, renderer/depth sorter, raster AssetCatalog/ScenePlacementCatalog ve güvenli PresentationContentService/Store zaten bulunuyor.

Bu nedenle doğru entegrasyon stratejisi mevcut Main altyapısını silmek veya laboratuvarı topluca kopyalamak değildir. Mevcut Main sorumlulukları korunmalı; Lab'ın yeni yetenekleri küçük ve açık adapter sınırlarıyla kazandırılmalıdır.

Mimari karşılaştırma ve A16 taslak planını hazırlamak için yeterli kanıt vardır. Ancak paket dağıtımı, hareket state authority, koordinat dönüşümü ve content ownership kararları henüz çözülmemiştir. Bunlar kod entegrasyonunun ön koşuludur.

## 2. Hazırlık ölçütleri

| Ölçüt | Sonuç | Kanıt / açıklama |
|---|---|---|
| Gerçek mimari ve modül sınırları | TAMAM | 15.1 denetim raporu ve API kataloğu |
| ADR ve açık karar envanteri | TAMAM | PHASE-15-ADR-STATUS.md |
| API ve authoritative state akışı | TAMAM | PHASE-15-API-CATALOG.md, PHASE-15-DATA-FLOW.md |
| Schema/version compatibility | TAMAM — KRİTİK FARKLAR KAYITLI | PHASE-15-DATA-COMPATIBILITY.md |
| Lab/Main dosya eşleştirmesi | TAMAM | PHASE-15-INTEGRATION-MAPPING.md |
| Dependency/package/license audit | TAMAM — LİSANS/DAĞITIM BLOKAJLARI VAR | PHASE-15-DEPENDENCY-AND-LICENSE-AUDIT.md |
| A16 dilim ve rollback taslağı | TAMAM | PHASE-16-INTEGRATION-SEQUENCE-DRAFT.md |
| Test ve kabul matrisi | TAMAM | PHASE-15-TEST-AND-ACCEPTANCE-MATRIX.md |
| Güncel Lab CI/Core Quality | SON A15 HEAD ÜZERİNDE YENİDEN DOĞRULANMALI | Önceki A15 docs HEAD run'ları in progress idi; A15 final HEAD sonuçları kapanıştan önce alınmalı |
| Kullanıcı doküman/manual kabulü | BEKLİYOR | PHASE-15-MANUAL-ACCEPTANCE-CHECKLIST.md |

## 3. A16 öncesi kritik blokajlar

### B15-01 — Pygame dağıtım kararı
Lab pygame>=2.6,<3, Main pygame-ce>=2.5 kullanıyor. Aynı pygame import namespace'i ve kurulum çakışması riski var. Tek dağıtım standardizasyonu veya Pygame bağımsız çekirdek + ayrı adaptör sınırı kararlaştırılmalı. Temiz ortamda Linux/Windows smoke testleri zorunlu.

### B15-02 — Authoritative movement state
Lab continuous WorldPoint, Main EntityPosition(map_id, LocalHexPosition) kullanıyor. Aynı oyuncu/actor için iki bağımsız authoritative hareket kaynağı oluşturulamaz. Sürekli alt-hücre konumunun Main gameplay/save modeline nasıl bağlanacağı açıkça tasarlanmalı.

### B15-03 — Coordinate and map identity bridge
Lab WorldId/MapId, axial cell ve world units; Main map-local axial, world-level map topology ve presentation pixels kullanıyor. Map ID, origin, Y ekseni, scale, layout ve cell boundary dönüşümleri adapter contract olarak testlenmeli.

### B15-04 — Content ownership and migration
Main raster asset/axial placement pipeline ve safe persistence korunmalı. Lab vector definitions/world placements ayrı sözleşme. İlk dilim read-only coexistence olabilir; yazma/migration için tek writer, ID mapping, collider fidelity ve backup/rollback şart.

### B15-05 — Renderer/camera ownership
Main renderer, WorldTransform, HexCamera ve DepthSorter zaten var. Lab snapshot renderer bunların yerine doğrudan konamaz. Tek render entry point ve adapter contract belirlenmeli. Mevcut affine camera isometric/elevation projection değildir.

### B15-06 — License and provenance
Repo root'unda LICENSE/COPYING/NOTICE dosyası görülmedi; raster asset catalog metadata'sında source/license provenance alanı yok. Üçüncü taraf bağımlılık ve asset dağıtım hakları kanıtlanmadan release dağıtımı onaylanamaz.

## 4. Risk sınıfları

| Risk | Sınıf | Yönetim |
|---|---|---|
| Pygame/pygame-ce environment conflict | BLOCKER | A16 package spike ve kullanıcı seçimi |
| Continuous/discrete dual authority | BLOCKER | Movement ownership ADR + adapter tests |
| Content dual writer/schema loss | BLOCKER | Read-only coexistence; migration gate |
| Coordinate/unit mismatch | BLOCKER | Explicit conversion contract + property tests |
| Renderer duplication | HIGH | Main renderer korunur; adapter spike |
| Package data missing after wheel install | HIGH | Wheel/sdist smoke |
| Asset license unknown | RELEASE BLOCKER | Provenance/notice audit |
| Isometric 2.5D target not yet implemented | ACCEPTED SCOPE GAP | Ayrı görsel aşama; A15/A16'ya gizlice eklenmez |

## 5. A16 için önerilen ilk adım

İlk A16 dilimi yalnızca package/runtime spike ve kararları kanıtlama kapsamıyla sınırlı tutulmalıdır:
1. Lab ve Main temiz sanal ortamlarında mevcut kurulumları doğrula.
2. pygame/pygame-ce dağıtım seçeneklerini ayrı ortamda karşılaştır.
3. Pygame bağımsız Lab domain paketlerinin import grafiğini ve Main ile çakışmayan adapter yüzeyini belirle.
4. Wheel/sdist içinde gerekli content/assets dosyalarını doğrula.
5. Sonuçları kullanıcıya sun; movement/content/render entegrasyonuna başlamadan ayrıca onay al.

Bu ilk dilim dahi A16 için ayrı genel/teknik plan ve açık kullanıcı onayı gerektirir.

## 6. Nihai karar

**KOŞULLU HAZIR — A16 PLANLAMASI İÇİN.**

A15 dokümantasyon ve mimari hazırlık çıktıları tamamlanmıştır. Ancak A16 kod entegrasyonu için yukarıdaki blokajlar çözülmeden ve kullanıcı kararları alınmadan entegrasyon yapılmamalıdır. A16 otomatik başlamaz.

A15'in resmî kapanışı için:
- Son A15 HEAD üzerindeki Lab CI ve Core Quality sonuçları başarılı olmalı.
- Kullanıcı manuel kabul kontrol listesini tamamlamalı.
- Kullanıcı Aşama 15 kapanışını açıkça onaylamalı.

Bu rapor A16 kod değişikliğine yetki vermez.
