# Aşama 15.1 — Gerçekleşen Mimari Denetim Raporu

> Tarih: 19 Kasım 2026  
> Denetim dalı: experiment/hex-world-laboratory  
> Denetim başlangıç HEAD'i: 16708c32eefdb2c314403a5d68b0109af9e66058  
> Salt okunur karşılaştırma dalı: demo_eldoria  
> Karşılaştırma HEAD'i: 7d53d431d5c3639fd95d273de9043b64483a5125  
> Durum: TAMAMLANDI — teknik plan girdisi  
> Kod değişikliği: Yapılmadı

## 1. Denetim kapsamı ve yöntemi

Denetim GitHub üzerindeki gerçek dosya ağacı, kaynak dosyalar, şema belgeleri, Aşama 14 kapanış raporu, laboratuvar genel planı ve demo_eldoria dalındaki mevcut içerik/dünya/render altyapısı üzerinden yürütüldü. Laboratuvar dalı yazılabilir çalışma alanı olarak; demo_eldoria yalnızca salt okunur karşılaştırma kaynağı olarak kullanıldı.

Laboratuvarda incelenen alanlar:
- src/hex_world_lab/geometry, world, movement, physics, spatial, camera, entities, interaction, simulation, rendering, environment, content ve application paketleri.
- pyproject.toml, README.md, ARCHITECTURE_SPECIFICATION.md, DEVELOPMENT_RULES.md, test/kabul sözleşmesi ve JSON şema belgeleri.
- Aşama 8–14 karar ve kapanış kayıtları.

Ana oyunda incelenen alanlar:
- application/content_loader.py, content_pack.py, presentation_content_service.py, presentation_content_store.py, hex_map_definition.py, hex_world_runtime.py ve world_object_placement.py.
- core/domain/spatial, core/application/world_runtime.py, game_ui/world_transform.py, game_ui/renderer.py ve game_ui/world_rendering.
- content/demo_eldoria, mevcut içerik paketi, asset catalog ve map placement belgeleri.
- pyproject.toml, requirements dosyaları ve içerik mimarisi belgeleri.

Bu rapor, incelenen dosyalara dayalı mimari fotoğrafı ve entegrasyon risklerini kaydeder; henüz tüm modüllerin satır satır kod incelemesi veya entegrasyon uygulaması değildir.

## 2. Laboratuvarın gerçekleşen mimarisi

### 2.1 Çekirdek ve sunum sınırı

Laboratuvar src/hex_world_lab altında bağımsız bir Python paketi olarak düzenlenmiştir. Geometri, dünya modeli, hareket, fizik, spatial, entity ve simülasyon sorumlulukları ayrı paketlerdedir. Pygame bağımlılığı özellikle input/pygame_keyboard.py, rendering/pygame_world_renderer.py, rendering/procedural/canvas.py ve rendering/procedural/document_renderer.py dosyalarında görünür.

simulation/tick_coordinator.py Pygame'den bağımsızdır. Sabit tick içindeki hareket, hücre takibi ve entity/spatial eşitleme sırasını koordine eder. rendering/snapshot.py immutable render snapshot tiplerini taşır; renderer bu snapshot'ı okur. Bu, Aşama 10'da kabul edilen simülasyon/render ayrımının kaynak kodundaki karşılığıdır.

### 2.2 Kamera ve mevcut görsel dönüşüm

camera/transform.py world-to-screen ve screen-to-world dönüşümünü viewport merkezi, kamera merkezi ve tekdüze zoom ile uygular; matematiksel dünya Y ekseni ekran koordinatına dönüştürülürken bir kez çevrilir. İncelenen uygulama izometrik/elevation projeksiyonu değildir. Laboratuvarın mevcut kamera/render altyapısı hedeflenen izometrik 2.5D görünüm için temel sunum katmanı sağlar; izometrik projeksiyon, yükseklik/elevation katmanı, gelişmiş ışıklandırma ve animasyon yeteneklerinin mevcut olduğu varsayılamaz.

### 2.3 İçerik veri altyapısı

Aşama 14'teki içerik modeli Pygame'den bağımsızdır:
- VisualDocument, çizim katmanları, primitive'ler, palette token'ları ve anchor bilgisi.
- ContentDefinition ve ContentLibrary, tekrar kullanılabilir içerik tanımlarını kararlı kimliklerle saklar.
- ContentPlacement ve MapContentDocument, map-local içerik örneklerini world-space x/y konumlarıyla tanımlar.
- Content Library JSON v1 ve Map Content JSON v1 strict doğrulama ve deterministik serileştirme sağlar.
- Pygame renderer ve rendering/content_adapters.py, içerik tanımlarını Surface/environment scene/physics adaptörlerine dönüştürür.

Görsel geometri collider üretmez. Collider yalnızca açıkça tanımlanmışsa fizik adaptörüne aktarılır. JSON v1'de rotation/scale bulunmaz. Masaüstü Content Editor GUI'si yoktur.

### 2.4 Paketleme ve test yapısı

Laboratuvar src layout kullanır; pyproject.toml setuptools build backend, Python >=3.11, pygame>=2.6,<3, opsiyonel pytest ve Ruff bağımlılıklarını tanımlar. Tek modül girişi python -m hex_world_lab şeklindedir. Testler unit, integration, acceptance ve stress gruplarına ayrılmıştır.

Aşama 14 kapanış kanıtında laboratuvar CI 881 test, Linux Core Quality 2.344 test ve Windows Core Quality başarıyla tamamlanmıştır. Bunlar kapanış raporunda kayıtlı referans sonuçlarıdır; bu mimari denetim sırasında yeni test çalıştırıldığı anlamına gelmez.

## 3. Ana oyunla önemli örtüşmeler ve farklılıklar

### 3.1 Dünya ve hareket

Ana oyunda application/hex_map_definition.py, application/hex_world_runtime.py, core/domain/spatial ve core/application/world_runtime.py altında zaten hex harita, discrete LocalHexPosition/EntityPosition, occupancy ve hex hareket/pathfinding altyapısı vardır. Ana oyunun game_ui/world_transform.py dosyası axial hücre, world-pixel ve screen-pixel dönüşümlerini kamera/zoom ile birleştirir.

Laboratuvar ise sürekli WorldPoint fiziksel konumu, ayrı axial hücre adresi, fiziksel collider, spatial index ve sabit tick orkestrasyonu üzerine kuruludur. Bu iki model eş anlamlı değildir. Özellikle ana oyunun hücre tabanlı entity pozisyonu ile laboratuvarın kesirli world-space konumu doğrudan cast/kopya ile birleştirilmemelidir; açık bir adaptör ve geçiş politikası gerekir.

### 3.2 Rendering

Ana oyunda game_ui/renderer.py, game_ui/world_rendering/terrain_renderer.py, depth_sorter.py, scene_object.py, karakter renderer/animation ve tree atlas/rig dosyaları mevcuttur. Laboratuvarda PygameWorldRenderer, immutable WorldRenderSnapshot, SpriteVisual ground anchor/depth bilgisi ve prosedürel Surface üretimi bulunur.

İki renderer aynı işlevin basitçe değiştirilebilir sürümleri değildir. Ana oyun mevcut sanat/asset ve karakter sunumunu korurken laboratuvarın world snapshot, camera transform ve çevresel içerik adaptörleriyle nasıl konuşacağı ayrı tasarlanmalıdır.

### 3.3 İçerik altyapısı — kritik çift sistem riski

Ana oyunda Aşama 8 kapsamında zaten UI-bağımsız bir içerik hattı geliştirilmiştir:
- AssetCatalog / asset metadata ve kaynak görsel yolları.
- ScenePlacementCatalog / map-scoped axial placement.
- application.content_loader.load_content_package.
- PresentationContentStore: staged package validation, atomik yazma, backup ve rollback.
- PresentationContentService: UI/Pygame bağımsız okuma, doğrulama, kaydetme ve migration facade.

Laboratuvar Aşama 14'te farklı fakat tamamlayıcı bir model geliştirmiştir:
- Vektör tabanlı VisualDocument ve primitive/layer/style/palette modeli.
- ContentLibrary / ContentDefinition.
- World-space ContentPlacement / MapContentDocument.
- Content Library JSON v1 / Map Content JSON v1.
- Pygame Surface renderer ve açık collider adaptörü.

Bunlar aynı şema değildir. Ana oyundaki asset kataloğu raster asset, normalize anchor, depth/collision/placement metadata ve axial map placement sözleşmesine sahiptir. Laboratuvarın v1 içerik modeli vector drawing document ve world-space placement kullanır. Aşama 16'da iki hattı paralel ve kontrolsüz biçimde yaşatmak veya birini diğerine otomatik dönüştürmek kabul edilemez. Önce ortak kavramlar, kayıp dönüşüm alanları ve tek otorite seçimi tanımlanmalıdır. Var olan PresentationContentService/Store yetenekleri atılmamalı veya ikinci bir editör backend'i varsayılan olarak oluşturulmamalıdır.

## 4. Bağımlılık uyumluluğu riski

Her iki pyproject.toml da Python >=3.11 ve setuptools>=68 kullanır. Ancak laboratuvar runtime bağımlılığı pygame>=2.6,<3, ana oyun bağımlılığı pygame-ce>=2.5 olarak tanımlıdır. Her iki dağıtım da Python kodunda import pygame ad alanını sağlar. Pygame-CE kurulum rehberi, pygame kuruluysa önce kaldırılmasını ve ardından pygame-ce kurulmasını söyler; bu iki dağıtım aynı sanal ortamda birlikte kurulacak bağımsız paketler gibi ele alınmamalıdır.

Bu nedenle tek bir ortak runtime ortamı veya ortak lock dosyası Aşama 15'te varsayılmayacaktır. Aşama 16 öncesinde ayrı sanal ortam, tek dağıtımda uzlaşma veya başka bir paket sınırı seçenekleri kanıtla değerlendirilmelidir. Aşama 15 mevcut bağımlılıkları değiştirmez.

## 5. Entegrasyon öncesi görsel kapsam değerlendirmesi

Mevcut kamera dönüşümü translation + uniform zoom temellidir. Renderer Pygame Surface ve primitive çizimi yapar; prosedürel içerik profilleri ve cache mevcuttur. Bu, gelecekteki izometrik 2.5D dünya görünümünün doğrudan tamamlandığı anlamına gelmez. İzometrik projeksiyon, yükseklik katmanı, depth/occlusion politikasının nihai dünya ölçeğinde doğrulanması, karakter animasyon/asset pipeline birleşimi ve Content Editor GUI ayrı tasarım/uygulama işleri olarak kalır.

Pygame mevcut karar doğrultusunda korunur. Motor değişimi bu raporun önerisi değildir.

## 6. Öncelikli riskler

| ID | Risk | Öncelik | Aşama 15 karşılığı |
|---|---|---:|---|
| R15-01 | pygame / pygame-ce dağıtım çakışması ve ortak ortam kararı | Kritik | 15.5'te seçenek ve kanıt; çözüm A16 ön koşulu |
| R15-02 | İki farklı içerik/placement sözleşmesinin paralel otoriteye dönüşmesi | Kritik | 15.3–15.4 veri eşleştirme ve tek otorite kararı |
| R15-03 | Discrete EntityPosition ile continuous WorldPoint arasında kayıplı geçiş | Yüksek | 15.3–15.4 adaptör ve dönüşüm sözleşmesi |
| R15-04 | İki renderer/camera hattının sorumluluk çakışması | Yüksek | 15.4 dosya eşleştirmesi ve A16 dilimleme |
| R15-05 | Ana oyun paketindeki dosya/asset yollarının dağıtımda bulunabilirliği | Yüksek | 15.5 paketleme ve temiz kurulum kontrolü |
| R15-06 | İzometrik 2.5D hedefin mevcut affine kamera/render ile karıştırılması | Orta | 15.8 kapsam ve sonraki aşama önerisi |

## 7. Sonuç

Laboratuvar, geometri/hareket/fizik/spatial/entity/simulation/render/content katmanlarında test edilmiş ve ayrı paketlenmiş bir teknik temel sunmaktadır. Ancak ana oyunda hex runtime, renderer, asset catalog, placement catalog ve UI-bağımsız content service/store zaten bulunduğundan entegrasyon bir klasör kopyalama işi değildir. En büyük iki entegrasyon kapısı pygame dağıtımının uzlaştırılması ve iki içerik veri hattının kayıpsız/tek otoriteli bir sözleşmeye bağlanmasıdır.

Denetim kararı: Aşama 15 teknik planını hazırlamak için yeterli kanıt toplandı. Entegrasyonun kendisi henüz hazır ilan edilmemiştir; bu karar 15.2–15.8 çıktıları ve kullanıcı kabulinden sonra verilecektir.

## 8. Referanslar

Depo kaynakları:
- experiments/hex_world_laboratory/reports/PHASE-14-CLOSURE-REPORT.md
- experiments/hex_world_laboratory/docs/CONTENT_DATA_API.md
- experiments/hex_world_laboratory/docs/content/CONTENT_LIBRARY_JSON_SCHEMA_V1.md
- experiments/hex_world_laboratory/docs/content/MAP_CONTENT_JSON_SCHEMA_V1.md
- experiments/hex_world_laboratory/src/hex_world_lab/camera/transform.py
- experiments/hex_world_laboratory/src/hex_world_lab/rendering/snapshot.py
- experiments/hex_world_laboratory/src/hex_world_lab/rendering/content_adapters.py
- demo_eldoria: application/presentation_content_service.py
- demo_eldoria: application/presentation_content_store.py
- demo_eldoria: application/hex_world_runtime.py
- demo_eldoria: game_ui/world_transform.py
- demo_eldoria: game_ui/world_rendering/depth_sorter.py
- demo_eldoria: reports/phase-8-content-editor-foundation-plan.md
- demo_eldoria: docs/architecture/44-content-pipeline-audit.md
- demo_eldoria: docs/architecture/45-presentation-content-separation.md
- demo_eldoria: docs/architecture/47-content-validation-and-safe-loading.md
- demo_eldoria: docs/architecture/48-presentation-content-safe-persistence.md
- demo_eldoria: docs/architecture/49-presentation-content-service-api.md

Context7 ile başvurulan teknik belgeler:
- Pygame display, event ve Surface: https://www.pygame.org/docs/ref/display.html ; https://www.pygame.org/docs/ref/event.html ; https://www.pygame.org/docs/ref/surface.html
- Pygame-CE kurulum ve dağıtım çakışması: https://github.com/pygame-community/pygame-ce/wiki/Installing-pygame-ce
- Pygame-CE import namespace: https://github.com/pygame-community/pygame-ce
- Setuptools pyproject config: https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html
- Setuptools src-layout package discovery: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html

Sınır: Bu rapor denetim anındaki kaynak ve belge durumunu kaydeder. Herhangi bir ana oyun dosyası değiştirilmemiş, kod aktarılmamış ve test çalıştırılmamıştır.
