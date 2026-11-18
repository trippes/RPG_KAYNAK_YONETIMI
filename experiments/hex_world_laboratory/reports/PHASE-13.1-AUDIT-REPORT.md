# Aşama 13.1 — Mevcut Altyapı Denetimi ve Baseline Raporu

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Denetlenen HEAD:** `e3149baa307e81dcb08318a36272b0d163149596`  
> **Durum:** TAMAMLANDI — 13.2 GEOMETRİ/CANVAS SÖZLEŞMESİNE GEÇİŞE HAZIR  
> **Kapsam:** Salt-okunur depo, test, workflow ve Pygame API denetimi. Bu iş paketi kaynak kodu değiştirmemiştir.

## 1. Sonuç özeti

Aşama 12'nin prosedürel görsel üretimi işlevsel ve izole durumdadır; ancak üretim kodu tek bir modülde toplanmış, ortak geometri/canvas/palet/seed/bileşen/profil sözleşmeleri ayrıştırılmamıştır. Mevcut çevresel domain modeli ve renderer entegrasyonu bu ayrıştırma için yeterli sınırları sağlamaktadır.

**13.1 kararı:** Teknik plandaki `rendering/procedural/` hedef paketi korunacaktır. Önce saf geometri ve Pygame'e bağlı canvas sınırı oluşturulacak; sonra mevcut üç profil bu API'ye taşınacaktır. Yeni çim ve çiçek/bitki profilleri, ortak bileşenlerin gerçek tekrar kullanımını kanıtlamak üzere daha sonra eklenecektir.

## 2. İncelenen mevcut kod

| Dosya | Denetim sonucu |
|---|---|
| `src/hex_world_lab/rendering/procedural_environment.py` | Ağaç/kaya/çalı tek modülde; `EnvironmentArtPalette`, `_surface`, `_finish` ve yerel çizim yardımcıları mevcut. 3x supersampling ve `smoothscale` kullanılıyor. |
| `src/hex_world_lab/rendering/environment_assets.py` | Üç Surface üretiliyor; renderer'a SpriteAsset ve normalize anchor ile kaydediliyor. |
| `src/hex_world_lab/rendering/pygame_world_renderer.py` | Sprite asset registry, world bounds culling, kamera ölçekleme ve Y-sort mevcut. Üretim renderer'ın frame çizim yolunda bulunmamalı. |
| `src/hex_world_lab/environment/definition.py` | Immutable domain tanımı; collider açıkça tanımlanıyor, görselden türetilmiyor. |
| `src/hex_world_lab/environment/presentation.py` | Domain → SpriteVisual/EnvironmentDebugVisual ve açık collider → physics adapter sınırı mevcut. |
| `src/hex_world_lab/rendering/snapshot.py` | Renderer'a giden görsel veriler DTO olarak taşınıyor. |
| `tests/unit/test_procedural_environment_art.py` | Raster dosyası yüklenmediği, üç profilin deterministik/alpha destekli olduğu, boyut/silhouette ve palet etkisi test ediliyor. |
| `benchmarks/benchmark_phase_12_environment.py` | Aşama 12 çevresel nesne adapter benchmark'ı mevcut; prosedürel Surface üretim/cache benchmark'ı henüz yok. |
| `scripts/render_phase_12_scenes.py` | Aşama 12 görsel kanıt sahneleri mevcut. |

### Mevcut profil baseline'ı

| Profil | Surface ölçüsü | Anchor (x, y) |
|---|---:|---:|
| Ağaç | 132 × 168 | (0.50, 0.94) |
| Kaya | 66 × 48 | (0.50, 0.92) |
| Çalı | 88 × 58 | (0.50, 0.92) |

Varsayılan palet mevcut `EnvironmentArtPalette` içinde immutable dataclass olarak tanımlıdır. RGB kanalları 0–255 aralığında, bool olmayan tamsayılarla doğrulanır. Ağaç/kaya/çalı çıktıları mevcut testte byte düzeyinde deterministik karşılaştırılır.

## 3. Domain ve renderer sınırları

Aşağıdaki sözleşmeler korunacaktır:

1. `environment/` domain katmanı Pygame Surface veya Pygame çizim API'si bilmeyecek.
2. `EnvironmentalObjectDefinition.collider` tek fiziksel gerçek kaynağı olmaya devam edecek.
3. Profil/palet/seed/canvas değişiklikleri collider, placement, WorldPoint, anchor ve depth metadata değerlerini değiştirmeyecek.
4. `environment_sprite_visuals()` mevcut SpriteVisual DTO üretim yolu korunacak.
5. Y-sort, culling, F3 collider overlay ve F4 environment bounds/debug renderer davranışı korunacak.
6. Sprite Surface üretimi asset kayıt/ön üretim aşamasında yapılacak; render frame'inde profil çizimi veya Surface üretimi olmayacak.

## 4. Pygame API doğrulaması — Context7

Context7 üzerinden resmi Pygame dokümantasyonu incelendi:

- `pygame.draw` polygon, lines, ellipse ve circle fonksiyonları Surface üzerinde doğrudan çizim yapar; çizim primitive'leri renderer adaptöründe kalmalıdır.
- `pygame.SRCALPHA` per-pixel alpha içeren Surface formatı sağlar. Aşama 12'nin transparan Surface yaklaşımı korunabilir.
- Surface pixel erişimi kilitleme/erişim maliyeti taşır; üretim API'si her pikseli Python döngüsüyle düzenlemek yerine Pygame draw primitive'lerini kullanmalıdır.
- `pygame.transform.smoothscale` 24/32-bit Surface üzerinde çalışır; küçültmede alan ortalaması, büyütmede bilinear filtre kullanır. Mevcut 3x supersampling → final küçültme yaklaşımı teknik olarak uygundur.
- `convert_alpha()` display formatına bağlı yeni Surface üretir. Headless üretim/display başlatma bağımlılığı yaratmamak için varsayılan üretim yoluna konulmayacak; ancak ölçümlü blit deneyi gerekçe gösterirse ayrıca değerlendirilebilir.
- Surface nesneleri mutable'dır. Cache uygulanırsa cache'ten dönen Surface'lerin üretimden sonra değiştirilmemesi açık API sözleşmesi ve testlerle korunmalıdır.

Context7 kütüphane kaydı: `/pygame/pygame`.

## 5. Test ve CI baseline'ı

Depo ağacında laboratuvar için:
- 68 unit test dosyası,
- 22 integration test dosyası,
- 3 acceptance test dosyası
bulunuyor. Bunlar dosya sayılarıdır; test fonksiyonu/test case sayısı değildir.

Laboratuvar `pyproject.toml`:
- Python `>=3.11`,
- `pygame>=2.6,<3`,
- `pytest>=8,<9` test extra,
- `python -m pytest -q` test komutuyla uyumlu yapılandırma içeriyor.

`.github/workflows/hex-world-lab-ci.yml`:
- Python 3.12 / Ubuntu,
- SDL dummy video/audio,
- tam laboratuvar Pytest suite'i,
- önceki aşamaların benchmark'ları,
- Phase 12 benchmark ve görsel kanıt üretimi/upload adımlarını içeriyor.

`.github/workflows/core-quality.yml`:
- Linux Python 3.11 ve Windows Python 3.12 doğrulama işleri,
- laboratuvar test paketinin kurulumu,
- release candidate doğrulaması içeriyor.

**Ruff durumu:** Laboratuvar `pyproject.toml` içinde Ruff yapılandırması yok; iki workflow'da da Ruff kurulumu, `ruff check` veya `ruff format --check` adımı yok. Bu nedenle teknik plandaki yeni procedural paket/dokunulan dosyalarla sınırlı, blocking Ruff kalite kapısı yeni bir CI entegrasyonudur. Mevcut tüm depoya toplu lint/format uygulaması yapılmayacaktır.

## 6. 13.2 öncesi netleştirilen kararlar

1. Geometri modülü saf Python olacak; Pygame import etmeyecek.
2. Geometri noktaları/bounds yerel 2D koordinat sisteminde temsil edilecek; WorldPoint veya kamera dönüşümüyle karıştırılmayacak.
3. Canvas modülü Pygame'e bağlı olacak ve mantıksal boyut, supersampling ölçeği ve çıktı Surface boyutunu ayıracak.
4. Canvas başlangıç varsayılanı 3x supersampling olacak; ölçüm/kalite kanıtı olmadan değiştirilmez.
5. SRCALPHA korunacak; display başlatılması Surface üretimi için zorunlu olmayacak.
6. Eski `EnvironmentArtPalette` ve `build_environment_surfaces()` import yolları geçiş süresince facade olarak korunacak.
7. Cache henüz zorunlu değildir. Cache API'si 13.7'de üretim ve hit maliyeti benchmark'ından sonra karara bağlanacaktır.
8. İlk refaktör mevcut üç profilin piksel çıktısını ve ölçülerini korumaya odaklanacak; yeni profil ekleme ayrı alt iş paketidir.

## 7. Risk ve takip

- Mevcut procedural fonksiyonlarda yerel çizim yardımcıları profil içinde tanımlanmıştır. Bunları genel bileşen API'sine taşırken gereksiz soyutlama yapılmamalıdır.
- Mevcut testler çıktının aynı runtime'da deterministik olmasını kanıtlıyor; platformlar arası pixel-perfect eşitliği kanıtlamıyor.
- Renderer her zoom seviyesinde sprite'ı smoothscale ediyor. Aşama 13 cache'i yalnızca prosedürel kaynak Surface üretimini kapsamalı; kamera zoom cache'i ayrı bir optimizasyon konusu olarak kapsam dışı kalmalı.
- Root proje `pygame-ce`, laboratuvar ise `pygame` dağıtımını tanımlıyor. Bu mevcut ayrık ortam düzenidir; Aşama 13 bunu değiştirmeyecek.

## 8. 13.1 kabul durumu

- [x] Lab branch HEAD ve korunan branch'ler kontrol edildi.
- [x] Mevcut procedural çizim, asset registration, domain ve renderer kodu incelendi.
- [x] Mevcut unit/integration/acceptance test kapsamı sayıldı.
- [x] Laboratuvar ve Core Quality workflow'ları incelendi.
- [x] Ruff'ın mevcutta bulunmadığı doğrulandı.
- [x] Context7 resmi Pygame Surface/draw/smoothscale davranışlarıyla teknik sözleşmeyi doğruladı.
- [x] Teknik planın 13.2 başlangıç kararları netleştirildi.
- [ ] Kullanıcı 13.1 denetim sonucunu gözden geçirdi (uygulama devamı için ayrıca durdurma gerekmiyor; teknik plan onayı yürürlükte).

**Sonuç:** Aşama 13.1 denetimi tamamlandı. Sıradaki iş paketi 13.2 — saf geometri ve Pygame canvas sözleşmesinin uygulanmasıdır.
