# Eldoria ana oyun uygulaması — Aşama 0 baseline raporu

**Hedef dal:** `experiment/map-cleanup`  
**Baseline commit:** `2b94fa1c3ed1203c740ba947598941a359318e5f`  
**Temizlik dalı tree:** `326b9b03ac70c276c69f92eadff29b82659bd5a9`  
**Laboratuvar dalı HEAD:** `da71a7b88f018c5d267347c1ec220530a3bb854d`  
**Laboratuvar tree:** `e4a3ad9ace512cd532054f2ed5c652cb689d39eb`  
**Referans:** `docs/architecture/60-eldoria-main-game-architecture-contract.md`

Bu rapor, Aşama 0'ın salt okunur başlangıç envanteridir. Branch SHA'ları bu çalışmanın başında sabitlenmiştir. Kodun varlığı, çalışma zamanı bağlantısı veya testlerin geçmesi olarak yorumlanmamıştır.

## 1. Ana oyun akışı ve korunacak sahiplik

| Alan | Gerçek dosya / API | Karar |
|---|---|---|
| Entry point | `main.py` | İnce giriş noktası olarak korunur. |
| Application composition | `application/game_application.py`, `application/gameplay_service.py` | Domain bileşimi ve servis yönlendirmesi korunur. |
| Session/save | `application/session_bundle.py`, `application/save_document.py`, `application/hex_world_persistence.py` | Tek canonical save/restore hattı korunur. |
| World topology | `application/hex_map_definition.py`, `application/hex_world_runtime.py`, `application/hex_occupancy.py` | Harita tanımı, runtime ve occupancy sahipliği korunur. |
| Actor identity | `application/actor_system.py` / `WorldActorRegistry` | Actor kimliği ve oyun yaşam döngüsünün tek sahibi. |
| NPC domain | `npc/`, `application/npc_hex_binding.py` | NPC sosyal/b davranış verisi NPC domain'de; map konumu binding/runtime'da. |
| Movement | `core/domain/movement/`, `application/continuous_player_movement.py`, `application/hex_actor_binding.py` | Native hareket/bağlama API'leri canonical; presentation input sadece intent üretir. |
| Physics | `core/domain/physics/`, `application/hex_physics_bridge.py` | Ana dalın native physics modeli canonical; lab solver kopyalanmaz. |
| Persistent world UI | `game_ui/screens/main_screen.py`, `game_ui/game_window.py`, `game_ui/window_manager.py` | Dünya yüzeyi ve pencere yaşam döngüsü korunur. |
| World presentation | `game_ui/world_rendering/`, `game_ui/world_transform.py` | Mevcut prototip katmanı aşamalı olarak geliştirilir. |
| Content | `application/content_pack.py`, `application/content_loader.py`, `content/demo_eldoria/` | Mevcut manifest ve loader tek content authority olarak kalır. |
| Presentation placements | `game_ui/world_rendering/scene_object.py` | Görsel prop placement ayrı kalır; gameplay entity placement ile birleştirilmez. |
| Gameplay placements | `application/gameplay_placement_catalog.py` | NPC/container/resource gibi domain-owned placement için korunur. |

## 2. Laboratuvar paketleri için karar matrisi

| Laboratuvar alanı | Temizlik dalındaki karşılık | Entegrasyon kararı |
|---|---|---|
| `geometry/` | `core/domain/spatial/` | Core axial/world geometry tek otorite; kopya geometri taşınmaz. |
| `movement/` | `core/domain/movement/` | Intent/integrator ilkeleri incelenir; duplicate movement model eklenmez. |
| `physics/` | `core/domain/physics/`, `application/hex_physics_bridge.py` | Ana dalın native static continuous solver'ı temel; lab dynamic solver davranışı referans alınarak native dynamic solver geliştirilir. |
| `spatial/` | `core/domain/physics/obstacle_index.py`, mevcut spatial testleri | Önce mevcut indeks benchmark edilir; lab index yalnız ölçülebilir kazanım varsa adapter olarak alınır. |
| `camera/` | `game_ui/world_rendering/camera.py` | Mevcut camera korunur; world-space bounds ve iso projection ile test edilir. |
| `rendering/` | `game_ui/world_rendering/` | Lab snapshot/culling fikri uyarlanır; main dalı render API'si ve pygame Surface sahipliği korunur. |
| `environment/` | `game_ui/world_rendering/scene_object.py`, `tree_atlas.py`, `tree_rig_renderer.py` | Mevcut scene placement + asset sistemi genişletilir; lab environment renderer kopyalanmaz. |
| `entities/` | `WorldActorRegistry`, `NPCRegistry`, `HexWorldRuntime` | Lab EntityRegistry canonical owner yapılmaz; yalnız render/query adapter olabilir. |
| `interaction/` | `application/hex_interaction.py`, `GameplayService` | Mevcut domain servisleri korunur; selection yeni gameplay state sahibi olmaz. |
| `companions/` | NPC/social domain ve application servisleri | Komut sözleşmesi uyarlanır; roster kopyası ikinci NPC owner yapılmaz. |
| `simulation/` | `GameApplication`, `GameplayService`, `FixedStepAccumulator` | Tick ve event sahipliği Core/application'da; lab tick coordinator kopyalanmaz. |
| `content/` | `application/content_pack.py`, `scene_object.py`, `GameplayPlacementCatalog` | Mevcut versioned content loader'a adapter ile bağlanır. |

## 3. İlk baseline'da saptanan uygulama farkları

1. `WorldTransform` axial world plane'i viewport'a doğrudan aktarır; bağımsız 2:1 isometric projection/inverse yoktur.
2. Terrain renderer hücre başına organik dairesel stamp çizer; projected hex ground polygon pipeline henüz yoktur.
3. `SceneObjectPlacement` / `SceneObject` veri sözleşmesi vardır; başlangıç content pack'inde placement listesi boş ve render host bağlantısı eksiktir.
4. Tree atlas/rig renderer kodu ve büyük atlas asset'i vardır; ana gameplay view tarafından sahne nesnesi olarak çizildiği kanıtlanmamıştır.
5. Character renderer sprite draw helper içerir; gameplay view'in procedural humanoid çizimi sprite/facing/animation pipeline'a bağlı değildir.
6. Depth sorter axial row/column ile sıralar; continuous ground/depth anchor ve tall canopy occlusion pipeline tamam değildir.
7. Native physics statik engeller ve player continuous motion sunar; NPC gövdelerinin dinamik collision pair'leri olarak player/NPC çözümüne girdiği kanıtlanmamıştır.
8. NPC davranış/companion follow-wait runtime entegrasyonu tamamlanmış değildir.
9. Interaction service mevcut olsa da prop/container/door/structure etkileşimlerinin tamamı world selection'dan domain command'a uçtan uca doğrulanmamıştır.
10. Save hattı hex world state'i kapsar; yeni environment/AI state alanları eklenirse versioned save migration veya açık reject testi gerekir.

## 4. Test ve CI başlangıç kapsamı

Mevcut `.github/workflows/eldoria-ci.yml` Ubuntu/Windows üzerinde Python 3.11/3.12 unit suite ve Ubuntu Pygame dummy-display smoke çalıştırır. `.github/workflows/core-quality.yml` Ruff ve map-cleanup boundary kontrolü uygular. Bu baseline aşamasında hiçbir test komutu çalıştırılmamış; yalnız test dosyalarının ve workflow tanımlarının varlığı incelenmiştir.

Başlangıçta mevcut ilgili test kümeleri:
- `tests/test_game_ui/test_world_transform.py`, `test_hex_gameplay_view.py`, `test_hex_terrain_renderer.py`, `test_depth_sorter.py`
- `tests/test_game_ui/test_scene_object_geometry_contract.py`, `test_placement_catalog.py`, `test_tree_atlas.py`, `test_tree_rig_renderer.py`
- `tests/test_application/test_hex_actor_binding.py`, `test_hex_physics_bridge.py`, `test_npc_hex_binding.py`, `test_continuous_player_movement.py`
- `tests/test_application/test_hex_world_persistence.py`, `test_hex_world_save_load.py`, `test_unified_save_document.py`
- `tests/test_spatial/test_native_continuous_collision.py`, `test_native_collision_solver.py`

## 5. Risk kayıtları

| Risk | Kontrol |
|---|---|
| Projection ile collision/world coordinates karışması | Projection sadece presentation adapter'da kalır; physics API'ye screen coordinate girmez. |
| Click hit-test ve NPC query farklı world point üretmesi | Tek inverse transform üzerinden test edilir. |
| Lab geometry/movement duplicate owner oluşturması | Core spatial/movement modelleri canonical kalır. |
| Environment prop placement ve gameplay placement çakışması | Ayrı schema ve resolver; ortak yalnızca map/anchor referansı. |
| NPC collision ile occupancy çift commit | Dynamic physics çözümü sonrası tek binding transaction. |
| Canopy occlusion'ın tüm sprite'ı gizlemesi | Mask/alpha region bazlı renderer testi ve görsel kabul. |
| Save schema kırılması | Candidate restore, migration/reject ve regression testleri. |
| CI testlerinin gerçek pencereyi kanıtlamaması | Headless smoke yanında kullanıcı makinesinde görsel checklist zorunlu. |

## 6. Aşama 0 sonucu

Dosya ve API eşleştirmesi tamamlandı. Korunacak canonical owners belirlenmiştir. Lab packages are treated as source/reference modules, not as a second runtime. Bu baseline commit kod değişikliği içermez; sonraki commit'lerde aşama aşama uygulama yapılır.
