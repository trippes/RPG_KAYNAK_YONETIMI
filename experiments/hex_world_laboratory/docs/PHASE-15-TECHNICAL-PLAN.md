# Aşama 15 — Ayrıntılı Teknik Mimari Planı

> Belge türü: Uygulama öncesi teknik mimari plan  
> Proje: Eldoria — Kaynak Yönetimi RPG  
> Çalışma dalı: experiment/hex-world-laboratory  
> Salt okunur karşılaştırma dalı: demo_eldoria  
> Plan tarihi: 19 Kasım 2026  
> Ön koşul: Aşama 0–14 kapalı; Aşama 15.1 denetimi tamamlandı  
> Durum: TEKNİK PLAN HAZIR — KULLANICI ONAYI BEKLİYOR  
> Uygulama: 15.2–15.8 başlamadı

## 1. Teknik amaç ve başarı tanımı

Aşama 15, laboratuvarda doğrulanan dünya altyapısını ana Eldoria oyununa taşımak için gerekli mimari, veri, paketleme, dosya eşleştirme, test ve geri dönüş sözleşmelerini tamamlar. Aşama 15 bir kod entegrasyonu veya görsel geliştirme aşaması değildir.

Başarı, “laboratuvar kodunu ana oyuna kopyalayabiliriz” demek değildir. Başarı; her sorumluluğun mevcut ana oyun karşılığını, laboratuvardaki doğrulanmış davranışı, aradaki veri dönüşümünü, bağımlılık etkisini, test kanıtını ve geri dönüş yolunu açıkça gösterebilmektir.

Aşama 15 sonunda verilecek karar: Entegrasyon için HAZIR / KOŞULLU HAZIR / HAZIR DEĞİL. Bu karar kanıtla gerekçelendirilecek ve kullanıcı kabuline sunulacaktır. Aşama 16 otomatik başlamaz.

## 2. Bağlayıcı sınırlar

- Yazma işlemleri yalnızca experiment/hex-world-laboratory dalında yapılır.
- main ve demo_eldoria yalnızca okunur; dosya değiştirme, commit, cherry-pick, merge veya kod kopyalama yoktur.
- Pygame mevcut motor/çizim kararı olarak korunur. Godot veya başka motora geçiş planlanmaz.
- Aşama 14 Content Data API ve JSON v1 sözleşmeleri korunur; geriye dönük uyumluluk sessizce bozulmaz.
- Yeni oynanış özelliği, yeni çizim profili, editör GUI'si, izometrik kamera veya geniş çaplı refaktör yapılmaz.
- Kanıtlanmayan mimari karar kesinleştirilmez. Gerekirse açık karar / A16 ön koşulu olarak kaydedilir.
- Her belge, öneri ile kabul edilmiş karar ve gerçekleşmiş uygulamayı birbirinden ayırır.

## 3. 15.1 denetiminden devralınan gerçek durum

15.1 denetim raporu: ../reports/PHASE-15.1-AUDIT-REPORT.md.

### 3.1 Laboratuvar mimarisi

Laboratuvar src/hex_world_lab altında Geometry, World, Movement, Physics, Spatial, Camera, Rendering, Entities, Interaction, Simulation, Environment ve Content paketlerine ayrılmıştır. Simulation tick koordinatörü Pygame bağımsızdır. Render snapshot immutable veri taşır. Pygame bağımlılığı input, renderer ve Surface/canvas adaptörlerinde yoğunlaşır.

### 3.2 İçerik altyapısı

Aşama 14'te hazır olan temel:
- Pygame bağımsız VisualDocument, primitive/layer/style/palette/anchor modeli.
- ContentDefinition, ContentLibrary, ContentPlacement, MapContentDocument.
- Content Library JSON v1 ve Map Content JSON v1.
- Strict validation, deterministic serialization ve explicit collider modeli.
- Pygame Surface renderer, bounded cache ve environment/physics adapter.

Henüz bulunmayan: masaüstü Content Editor GUI, harita üzerinde fareyle çizim/yerleştirme, rotation/scale v1 desteği, animasyon ve 3D model hattı.

Ana oyunda ise ayrı bir içerik altyapısı zaten vardır: AssetCatalog, ScenePlacementCatalog, PresentationContentService ve PresentationContentStore. Bu sistem PNG asset metadata'sı, axial placement, güvenli staged validation, atomik kayıt, backup/rollback ve UI-bağımsız servis API'si sağlar. Aşama 15'in görevi iki sistemi hemen birleştirmek değil; kavramsal eşleştirmeyi, veri kayıplarını ve tek otorite sınırını belirlemektir.

### 3.3 Kritik teknik riskler

1. Laboratuvar pygame>=2.6,<3, ana oyun pygame-ce>=2.5 kullanıyor. Her ikisi import pygame sağlar; Pygame-CE kurulum belgesi aynı ortamda dağıtım çakışmasını önlemek için pygame'in kaldırılmasını ister. Ortak ortam kararı açık kalmalıdır.
2. Ana oyun hex varlıklarını ağırlıklı olarak discrete EntityPosition/LocalHexPosition ile; laboratuvar hareketi continuous WorldPoint ile ifade eder.
3. Ana oyun renderer/depth-sort/asset hattı ile laboratuvar snapshot/Surface renderer hattı doğrudan aynı API değildir.
4. Ana oyun içerik sistemi axial map placement ve raster asset metadata; laboratuvar sistemi vector VisualDocument ve world-space placement kullanır.
5. Laboratuvar kamera dönüşümü translation + uniform zoom'dur; izometrik/elevation projeksiyonu olarak değerlendirilmemelidir.

## 4. İş paketleri ve teknik yürütme

### 15.2 — ADR ve mimari karar envanteri

Amaç: Kod ve kapanış raporlarında gerçekleşen kararları tek bir izlenebilir karar tablosunda toplamak.

İncelenecek kayıtlar:
- docs/decisions/ADR-001-HEX-ORIENTATION-SUPPORT.md
- docs/decisions/ADR-002-COORDINATE-AND-SCALE.md
- docs/decisions/ADR-003-ROUNDING-AND-TOLERANCE.md
- docs/ADR-008-SPATIAL-INDEX-SELECTION.md
- Aşama 4–14 kapanış raporlarındaki açıkça kabul edilmiş kararlar.

Yöntem:
1. Her ADR'nin durumunu ve kod/test karşılığını doğrula.
2. Kararları GEÇERLİ, UYGULAMAYLA GÜNCELLENMİŞ, ESKİ/GEÇERSİZ veya AÇIK olarak sınıflandır.
3. Kamera/render, WorldPoint/entity, simulation tick, spatial ve content sözleşmelerine etkisini kaydet.
4. Eski kararları silme; gerekirse yeni ADR veya supersedes kaydı öner.
5. Kullanıcı onayı gerektiren yeni kararları açık karar listesinde tut.

Çıktı: docs/PHASE-15-ADR-STATUS.md — ADR envanteri, kanıt bağlantıları, açık kararlar ve A16 blokajları.

Kabul: Her kritik kararın kaynak dosya/test/rapor bağlantısı bulunur; çelişkiler sessizce kapatılmaz.

### 15.3 — API, veri sahipliği ve sürüm sözleşmeleri

Amaç: Hangi modülün hangi veriyi ürettiğini, kimin authoritative state sahibi olduğunu ve katmanlar arası veri akışını belgelemek.

İş adımları:
1. Public API adaylarını __init__.py export'ları, gerçek import kullanımı ve testlerle doğrula; her sınıfı public API ilan etme.
2. Aşağıdaki alanlar için producer → owner → consumer akışını çiz:
   - AxialCoord / WorldPoint / ScreenPoint.
   - HexMapDefinition / MapRegistry / World runtime.
   - MovementIntent → collision-aware movement → cell tracker → EntityWorldCoordinator → spatial index.
   - Immutable WorldRenderSnapshot → Camera transform → Pygame renderer.
   - VisualDocument → ContentDefinition → ContentLibrary.
   - MapContentDocument / ContentPlacement → validation → persistence → environment scene → Surface asset registration.
3. MAP JSON v1, runtime snapshot v1, Content Library JSON v1 ve Map Content JSON v1 sözleşmelerini tek uyumluluk tablosunda karşılaştır.
4. ID kapsamı, referans çözümleme, map/world kimliği, collider bağımsızlığı, hata davranışı, unsupported-version davranışı ve deterministic serialization koşullarını kaydet.
5. Pygame bağımsız domain API'leri ile Pygame gerektiren adaptörleri ayır.

Öngörülen belgeler:
- docs/PHASE-15-API-CATALOG.md
- docs/PHASE-15-DATA-FLOW.md
- docs/PHASE-15-DATA-COMPATIBILITY.md

Kabul: Her veri için tek authoritative owner, doğrulanabilir producer/consumer zinciri ve şema sürümü açıkça belirtilmiş olmalı.

### 15.4 — Laboratuvar / demo_eldoria dosya ve sorumluluk eşleştirmesi

Amaç: Ana oyundaki mevcut sistemleri yok saymadan, laboratuvar bileşenlerinin hangi noktada doğrudan kullanılabileceğini veya adaptasyon gerektirdiğini belirlemek.

İlk eşleştirme hipotezi — 15.1'de görülen gerçek dosya aileleri:

| Laboratuvar alanı | Ana oyun karşılığı | İlk sınıflandırma |
|---|---|---|
| geometry/* | core/domain/spatial/*, hex geometry | Uyarlama/karşılaştırma; koordinat tipleri birebir varsayılmaz |
| world/* | application/hex_map_definition.py, hex_world_runtime.py, world/* | Yeniden tasarım/adaptör; discrete ve continuous state farkı |
| movement/*, physics/* | application/hex_movement_rules.py, hex_occupancy.py, hex_pathfinding.py, core/domain/spatial | Davranış eşleştirmesi ve kontrollü adaptör |
| spatial/*, entities/* | core/entity/*, core/application/entity_repository.py, hex_occupancy.py | Kısmi örtüşme; lifecycle ve authoritative state analizi |
| simulation/* | core/simulation/*, application/hex_world_runtime.py, application/gameplay_service.py | Orkestrasyon eşleştirmesi |
| camera/* | game_ui/camera.py, game_ui/world_transform.py, game_ui/world_rendering/camera.py | Adaptör/yerine geçme kararı açık |
| rendering/*, environment/* | game_ui/renderer.py, game_ui/world_rendering/*, game_ui/assets/* | Görsel pipeline entegrasyonu; doğrudan kopya değil |
| content/*, content persistence | game_ui/assets/*, application/content_loader.py, presentation_content_service.py, presentation_content_store.py, content/demo_eldoria/* | Veri sözleşmesi köprüsü; iki sistemin birleştirilmesi ayrı karar |
| Lab app.py / __main__.py | Ana main.py, application/game_application.py, game_ui/starter.py | Laboratuvar launcher'ı aktarılmaz |

Her satır nihai raporda beş durumdan biriyle işaretlenecek: DOĞRUDAN KULLAN, ADAPTÖRLE KULLAN, YENİDEN YAZ, ANA OYUNDA MEVCUT/KORU, KAPSAM DIŞI. Her satırda gerçek dosyalar, bağımlılık, veri dönüşümü, test ve risk bulunacak.

Özel içerik incelemesi:
- Ana oyunun AssetCatalog / ScenePlacementCatalog / PresentationContentService / PresentationContentStore API'si korunarak incelenecek.
- Laboratuvar VisualDocument vektör kaynaklarının ana oyun asset pipeline'ına nasıl kayıt edileceği seçenek olarak değerlendirilecek.
- World-space placement → axial map placement dönüşümünde offset, anchor, depth, layer, footprint ve collider kaybı olup olmadığı gösterilecek.
- Var olan PNG asset'ler ve içerik paketleri korunacak; otomatik toplu migration yapılmayacak.

Çıktı: reports/PHASE-15-INTEGRATION-MAPPING.md.

Kabul: Her önemli modül ve içerik formatı için hedef dosya/sorumluluk, karar durumu ve test gereksinimi gösterilmiş olmalı.

### 15.5 — Python/Pygame bağımlılık, paketleme ve lisans denetimi

Amaç: İki projenin tek çalışma zamanı ve dağıtım paketinde buluşması için gerekli koşulları kanıtlamak.

Mevcut metadata:
- Lab: Python >=3.11, setuptools >=68, pygame>=2.6,<3, pytest ve Ruff extras, src layout.
- Demo: Python >=3.11, setuptools >=68, pygame-ce>=2.5, root-layout package discovery, main:main console entry point ve game_ui/assets/*.png package data.

İş adımları:
1. Runtime, test, kalite ve build bağımlılıklarını iki pyproject/requirements dosyası arasında karşılaştır.
2. Pygame ve Pygame-CE sürümlerini aynı temiz sanal ortama birlikte kurmayı varsayma. Ayrı venv, tek dağıtımda standardizasyon ve izole paket sınırı seçeneklerini karşılaştır; seçimi A16 öncesi kullanıcı onayına bırak.
3. Pygame Surface, display, event ve drawing API kullanımlarını iki dağıtımın dokümantasyonuyla karşılaştır; yalnızca import adının aynı olmasını binary/behavioral uyumluluk kanıtı sayma.
4. src layout ile root package discovery, import isimleri, console/module entry point, package-data ve content dosyalarının kurulu pakette bulunabilirliğini kontrol et.
5. Üçüncü taraf lisanslarını gerçek dağıtım metadata'sından doğrula; lisansı doğrulanamayan asset veya bağımlılığı risk olarak kaydet.
6. Temiz ortam kurulum/build/wheel/sdist deneme komutlarını tanımla. Bu aşamada bağımlılık sürümü veya paket metadata'sı değiştirme.

Çıktı: reports/PHASE-15-DEPENDENCY-AND-LICENSE-AUDIT.md.

Kabul: Python, SDL/Pygame dağıtımı, paket import/asset yolu ve lisans durumu açık; çözülemeyenler A16 blokajı olarak yazılmış olmalı.

### 15.6 — Entegrasyon dilimleri ve geri dönüş tasarımı

Amaç: Aşama 16 için küçük, test edilebilir ve geri alınabilir entegrasyon sırası önermek.

Önerilen sıra (henüz onaylanmış uygulama sırası değildir):
1. Paket/çalıştırma izolasyonu: tek runtime bağımlılığı, entry point ve kaynak dosya erişimi kararı.
2. Hex/world model adaptörü: map ID, axial cell ve continuous WorldPoint sahipliği; discrete entity state geçiş politikası.
3. Movement/physics/spatial: collision-aware movement ve broadphase davranışının ana oyun entity lifecycle/occupancy sistemiyle birlikte çalışması.
4. Simulation orchestration: tick sahipliği, mevcut game loop ve gameplay service entegrasyonu; çift tick/çift update engeli.
5. Camera/render: world snapshot, camera transform, existing renderer/depth sorter ve asset cache arasında adaptör.
6. Content pipeline: mevcut asset catalog ve safe store korunarak vector VisualDocument kaynaklarının kontrollü sunulması; placement/anchor/depth/collider dönüşümünün kayıpsızlığı.
7. Persistence/compatibility: mevcut kayıtlar ve MAP/content şemaları korunarak migration veya coexistence.
8. Platform/visual acceptance: Windows/Linux, temiz kurulum, kayıt/yükleme ve görsel regresyon.

Her dilim için ön koşul, değişecek dosyalar, eklenen adaptör, veri sahibi, test seti, performans kontrolü, geri dönüş commit noktası ve durdurma ölçütü tanımlanacak.

Geri dönüş ilkeleri:
- A16'da tek seferde büyük merge yapılmaz.
- Eski ve yeni veri kaynağı aynı anda yazılacaksa tek yazıcı/otorite açıkça belirlenir.
- JSON şemaları kullanıcı onayı olmadan yerinde değiştirilmez; gerekiyorsa yeni sürüm ve explicit migration.
- Her dilim ayrı commit/CI ve kabul kapısı taşır.
- Geri dönüşte mevcut content/save dosyaları korunur; yedeklenmemiş veri migration'ı yapılmaz.

Çıktı: docs/PHASE-16-INTEGRATION-SEQUENCE-DRAFT.md.

### 15.7 — Test, regresyon ve kabul matrisi

Amaç: Laboratuvar doğruluğu ile ana oyun davranışının entegrasyon sırasında kaybolmadığını gösterecek ölçülebilir kontrolleri belirlemek.

Test katmanları:

| Alan | Otomatik doğrulama | Manuel/görsel kabul |
|---|---|---|
| Geometri | axial/world dönüşüm, sınır tie-break, flat/pointy, negatif koordinat | hücre ve kamera hizası |
| Movement/physics | hız, çarpışma, duvar kayması, yüksek hız, deterministik tick | karakterin engel çevresindeki hareketi |
| Spatial/entity | brute-force differential, lifecycle, stale/duplicate entry | entity/NPC/resource konum ve seçim |
| Simulation | sabit tick sırası, retry, render purity | oyun akışında takılma/çift hareket olmaması |
| Camera/render | world-screen roundtrip, snapshot immutability, culling | zoom, pan, y-sort, foot-anchor, collider overlay |
| Content | JSON schema v1 roundtrip, strict reject, ref resolution, deterministic output | profil önizleme, yerleşim/anchor/collider hizası |
| Persistence | create/replace, invalid input no-write, backup/rollback, legacy fixtures | eski kayıt ve paketlerin açılması |
| Packaging | clean install, import smoke, wheel/sdist içerik kontrolü | Windows ve Linux başlatma |
| Performance | tick/render/query/memory benchmark karşılaştırması | hedef donanımda akıcılık |

Referans bazları:
- Aşama 14 kapanış raporundaki 881/881 laboratuvar testi ve Linux 2.344 / Windows Core Quality sonuçları tarihsel referanstır.
- Entegrasyon başlamadan güncel lab ve demo CI sonuçları commit SHA ile yeniden alınmalıdır.
- Benchmarklarda aynı donanım/runner, Python ve yük profili kullanılmadıkça mutlak karşılaştırma yapılmaz.

Çıktı: docs/PHASE-15-TEST-AND-ACCEPTANCE-MATRIX.md.

Kabul: Her kritik entegrasyon riski en az bir otomatik test ve gerekiyorsa manuel kabul adımına bağlanmış olmalı.

### 15.8 — Nihai hazırlık kararı

Amaç: 15.2–15.7 çıktılarının tutarlı olup olmadığını değerlendirip Aşama 16 için karar paketi sunmak.

İş adımları:
1. Dosya eşleştirmesi, API sözleşmesi, bağımlılık matrisi ve test matrisi çapraz kontrol edilir.
2. Kritik riskler engel / koşullu risk / kabul edilmiş risk olarak sınıflandırılır.
3. Her koşul için sorumlu aşama, kanıt ve tamamlanma ölçütü belirlenir.
4. A16 kapsamı, ilk dilimi, dosya sınırları ve kullanıcı onayı gerektiren kararlar yazılır.
5. Entegrasyon hazırlık kararı HAZIR / KOŞULLU HAZIR / HAZIR DEĞİL olarak verilir.

Çıktılar:
- reports/PHASE-15-READINESS-DECISION.md
- Güncellenmiş Master Plan ve README.
- Aşama 15 kapanış raporu (yalnızca bütün kabul kapıları tamamlandıktan sonra).

## 5. Teknik belge ve dosya teslim listesi

Aşama 15 uygulama onayından sonra oluşturulması/güncellenmesi planlanan belgeler:

| Dosya | Amaç |
|---|---|
| reports/PHASE-15.1-AUDIT-REPORT.md | Gerçekleşen mimari denetim kanıtı — hazır |
| docs/PHASE-15-ADR-STATUS.md | ADR ve açık karar envanteri |
| docs/PHASE-15-API-CATALOG.md | Doğrulanmış public API ve modül sınırları |
| docs/PHASE-15-DATA-FLOW.md | State sahipliği ve veri akışları |
| docs/PHASE-15-DATA-COMPATIBILITY.md | MAP/runtime/content JSON sürüm uyumluluğu |
| reports/PHASE-15-INTEGRATION-MAPPING.md | Lab ↔ demo dosya/sorumluluk eşleştirmesi |
| reports/PHASE-15-DEPENDENCY-AND-LICENSE-AUDIT.md | Python/Pygame/package/license matrisi |
| docs/PHASE-16-INTEGRATION-SEQUENCE-DRAFT.md | Dilimlenmiş entegrasyon ve rollback taslağı |
| docs/PHASE-15-TEST-AND-ACCEPTANCE-MATRIX.md | Otomatik/manual kabul matrisi |
| reports/PHASE-15-READINESS-DECISION.md | Nihai hazırlık kararı |
| reports/PHASE-15-CLOSURE-REPORT.md | Kullanıcı kabulinden sonra resmî kapanış |

Bu listede hazır olarak belirtilmeyen dosyalar henüz oluşturulmamıştır. Aşama 15 teknik planı onaylanmadan bu belgelerin üretimine devam edilmeyecektir.

## 6. CI, kalite ve kanıt protokolü

- Dokümantasyon değişiklikleri kod testlerinin yerine geçmez.
- 15.2–15.8 sırasında kod değişikliği yapılmadığı sürece test sonucu uydurulmaz; yalnızca ilgili mevcut CI kanıtlarına referans verilir.
- Son hazırlık kararından önce laboratuvarın güncel HEAD'i üzerinde Hex World Lab CI ve Core Quality workflow sonuçları alınır.
- demo_eldoria CI sonuçları salt okunur karşılaştırma kanıtı olarak kaydedilir; bu dalda workflow veya kod değişikliği yapılmaz.
- Her CI kaydı workflow URL'si, commit SHA, platform, test sayısı ve sonuç ile raporlanır.
- Test/CI başarısızlığı varsa HAZIR kararı verilemez; neden ve blokaj raporlanır.

## 7. Dal ve commit güvenliği

Her yazma işleminden önce:
1. experiment/hex-world-laboratory HEAD doğrulanır.
2. Hedef dosyanın mevcut SHA'sı veya dosyanın yokluğu doğrulanır.
3. Yazma isteğinde branch adı açıkça experiment/hex-world-laboratory verilir.
4. Dönen commit SHA yeni branch HEAD'iyle karşılaştırılır.
5. main ve demo_eldoria HEAD'leri değişmediği doğrulanır.

Beklenmeyen HEAD veya dosya içeriği görülürse yazma durdurulur. Merge, rebase, reset, cherry-pick veya korunan dala yazma bu aşamanın parçası değildir.

## 8. Riskler ve açık kararlar

| ID | Konu | Risk/karar | Çözüm kapısı |
|---|---|---|---|
| R15-01 | pygame / pygame-ce | Aynı import namespace; aynı venv'de dağıtım çakışması riski | 15.5 analiz, A16 ön koşulu |
| R15-02 | İki içerik sistemi | Raster asset/axial placement ile vector/world placement aynı şema değil | 15.3–15.4 eşleştirme |
| R15-03 | WorldPoint / EntityPosition | Continuous ve discrete state'in authoritative owner'ı belirsiz bırakılmamalı | 15.3 sözleşmesi |
| R15-04 | Renderer/camera | İki farklı sunum hattı; doğrudan değiştirilebilir değil | 15.4 ve A16 adapter tasarımı |
| R15-05 | Packaging/assets | Kurulu dağıtımda içerik ve görsel dosyaları eksik kalabilir | 15.5 clean-install kontrolü |
| R15-06 | İzometrik 2.5D | Mevcut affine kamera nihai izometrik projeksiyon değildir | A15 rapor/gelecek aşama kapsamı |

## 9. Aşama 15 kabul kapıları

Aşama 15 ancak aşağıdakilerin tamamı sağlanırsa kapatılır:
1. 15.2 ADR envanteri ve açık kararlar kanıtlıdır.
2. 15.3 API, state owner, dataflow ve schema uyumluluğu belgelenmiştir.
3. 15.4 lab/demo dosya eşleştirmesi gerçek kaynak dosyalara dayalıdır.
4. 15.5 Python/Pygame, build, package-data ve lisans uyumluluğu değerlendirilmiştir.
5. 15.6 A16 sırası, dosya sınırları ve rollback planı tanımlanmıştır.
6. 15.7 otomatik test, CI, manuel görsel kabul ve performans matrisi hazırdır.
7. 15.8 kritik engeller ve hazırlık kararı açıkça sunulmuştur.
8. Güncel laboratuvar CI/Core Quality kanıtları kaydedilmiştir.
9. Kullanıcı masaüstü/manuel kabul kontrolünü tamamlayıp nihai paketi onaylamıştır.

Teknik plan onayı, 15.2–15.8 belgelerinin hazırlanmasına izin verir; ana oyuna kod aktarımı veya Aşama 16 uygulama izni vermez.

## 10. Context7 teknik kaynakları

Aşağıdaki güncel teknik belgeler Pygame/Pygame-CE API sınırları ve Python paketleme sözleşmeleri için kullanılmıştır:
- Pygame display: https://www.pygame.org/docs/ref/display.html
- Pygame event queue: https://www.pygame.org/docs/ref/event.html
- Pygame Surface / alpha / blit: https://www.pygame.org/docs/ref/surface.html
- Pygame-CE kurulum ve pygame dağıtımıyla çakışma uyarısı: https://github.com/pygame-community/pygame-ce/wiki/Installing-pygame-ce
- Pygame-CE README ve import namespace: https://github.com/pygame-community/pygame-ce
- Setuptools pyproject config: https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html
- Setuptools src-layout package discovery: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html

Nihai sınır: Bu teknik plan bir uygulama izni değildir. Kullanıcının bu belgeyi açıkça onaylamasından sonra 15.2–15.8 dokümantasyon/denetim işleri başlatılabilir. Aşama 16 için ayrıca plan ve açık onay gerekir.
