# Aşama 16 — Ana Oyun Mimari Sahiplik Denetimi

**Tarih:** 2026-11-19  
**Çalışma dalı:** `experiment/map-cleanup`  
**Referans:** `reports/phase-16-laboratory-capability-inventory.md`  
**Amaç:** Laboratuvar kabiliyetlerinin ana oyunda hangi mevcut sınıf/katman tarafından karşılandığını, sorumluluk sınırlarının doğru olup olmadığını ve gerçek boşlukları belirlemek.  
**Kapsam dışı:** Yeni oynanış özelliği, içerik üretimi, demo aktarımı veya bu rapor kapsamında kod değişikliği.

## 1. Yönetici özeti

Ana oyunda laboratuvarla örtüşen önemli mimari sahipler zaten bulunuyor. Bu nedenle entegrasyon için yeni ve paralel bir dünya/aktör/kamera/kayıt sistemi tasarlamak doğru yaklaşım değildir. Mevcut sahipler korunmalı ve laboratuvarın davranışları onların içinde yerel olarak karşılanmalıdır.

Ana mimari sahipler:
- **Geometri ve topoloji:** `core.domain.spatial`
- **Genel aktör kimliği ve gameplay bağları:** `application.actor_system.WorldActorRegistry`
- **Hex konumu, harita geçişi ve occupancy:** `application.hex_world_runtime.HexWorldRuntime` ve `HexOccupancyRegistry`
- **Harita tanımı ve topoloji:** `application.hex_map_definition.HexMapDefinition`, `WorldMapDefinition`
- **Statik fizik haritası:** `application.hex_physics_bridge.HexPhysicsSnapshot`
- **Kamera ve görüntü koordinatları:** `game_ui.world_rendering.camera.HexCamera`, `game_ui.world_transform.WorldTransform`
- **Pygame dünya sunumu:** `game_ui.world_rendering.hex_gameplay_view.HexGameplayView`
- **NPC/Resource/Container domain bağları:** ilgili mevcut registry ve binding servisleri
- **Birleşik kayıt:** `GameSaveDocument`, `HexWorldSnapshot`, `SaveJsonCodec`, `GameSaveFileAdapter`

Bununla birlikte laboratuvarın sürekli dünya konumu, serbest hareket integrasyonu, genel entity spatial index'i ve dünya mesafeli etkileşim hedeflemesi için ana oyunda tam karşılık bulunmuyor. Bazı sorumluluklar şu anda UI veya laboratuvar köprülerinde kalmış.

## 2. Kabiliyet → mevcut mimari sahibi → denetim kararı

| Laboratuvar kabiliyeti | Ana oyundaki mevcut sahip | Bugünkü gerçek sorumluluk | Denetim kararı |
|---|---|---|---|
| Axial koordinat/topoloji | `core.domain.spatial.HexCoord`, `HexDirection` | Hücre koordinatı, komşuluk ve topolojik mesafe | **Korunacak.** Yeni axial model gerekmez. |
| Hex ↔ pixel geometri | `core.domain.spatial.hex_geometry` | Pointy-top hücre merkezi ve pixel/axial dönüşümü | **Genişletilecek.** Sürekli WorldPoint ve sınır tie-break sözleşmesi eksik. |
| Harita-yerel konum | `LocalHexPosition`, `EntityPosition` | Harita ID + ayrık hücre konumu | **Evrimleşecek.** Hücre, sürekli world position yerine yetkili konum olmamalı. |
| Dünya harita topolojisi | `WorldHexPosition`, `WorldMapDefinition` | Haritalar arası axial yerleşim ve geçiş topolojisi | **Korunacak.** Entity'nin dünya içi sürekli konumuyla karıştırılmamalı. |
| Aktör kimliği | `WorldActorRegistry`, `ActorIdentity`, `WorldActor` | Kararlı actor ID, world ID, role, active ve character/inventory bağları | **Korunacak.** Yeni EntityRegistry/ikinci kimlik sistemi kurulmayacak. |
| NPC domain verisi | `NPCRegistry`, `NPCSpatialBindingService` | Sosyal/behavior verisi NPC tarafında; genel kimlik ActorRegistry'de | **Korunacak.** Aynı NPC ID ile bağ devam etmeli. |
| Resource node kimliği/state | `WorldResourceNodeManager`, `ResourceNodeHexBindingService` | Miktar/yenilenme resource manager'da; harita kaydı hex runtime'da | **Korunacak.** Resource manager konum sahibi yapılmamalı. |
| Container kimliği/custody | `ContainerManager`, `WorldMembershipService`, `ContainerHexBindingService` | İçerik/custody container sisteminde; dünya yerleşimi hex runtime'da | **Korunacak.** Legacy square Position kullanılmamalı. |
| Hex entity konumu/occupancy | `HexWorldRuntime`, `HexOccupancyRegistry` | Runtime entity tür/profile/active tutar; occupancy gerçek `EntityPosition` ve hücre indeksini tutar | **Temel sahip korunacak, veri modeli değişecek.** Occupancy hücreden türetilmeli; sürekli world position tek yetkili konum olmalı. |
| Hücre occupancy sorgusu | `HexOccupancyRegistry._by_cell` | Hücre başına entity ID kümeleri; canonical occupant kayıtlarından türetilmiş indeks | **Korunacak ve yeniden tanımlanacak.** Sürekli konumdan türetilen hücre occupancy görünümü olmalı. |
| Genel mekânsal indeks | Tam karşılık yok | `_by_cell` yalnızca hücre lookup; genel AABB/grid/quadtree değil | **Eksik.** Laboratuvar grid/quadtree kabiliyeti mevcut spatial sahipliğe eklenmeli; ayrı entity registry olmamalı. |
| Statik çarpışma geometrisi | `HexPhysicsSnapshot` | Canonical HexMapDefinition'dan statik hex sınır/engel geometrisi üretir | **Sahip doğru, davranış sınırlı.** Statik dünya geometrisi korunmalı; dinamik aktör broadphase ve sürekli hareket eklemlenmeli. |
| Fizik body/shape | `HexPhysicsSnapshot` ve binding parametreleri | Laboratuvar BodyDefinition/CircleShape tipleri doğrudan kullanılıyor | **Yerel domain sahibi eksik.** Onaylı body verileri ana oyuna ait olmalı; NPC/prop ölçüleri varsayılmamalı. |
| Sürekli collision resolution | `HexPhysicsSnapshot.resolve_cell_step` | Kaynak ve hedef hücre merkezleri arasında çarpışma ön kontrolü | **Yalnızca kısmi.** Bu tam serbest hareket çözümü değildir; continuous motion runtime'ı henüz yok. |
| Hareket kuralları | `MovementRules`, `HexWorldRuntime`, `ActorHexBindingService` | Hücre adımı, terrain/profile/occupancy doğrulaması ve commit | **Mevcut kurallar korunacak.** Sürekli hareket bunları hücre geçişi/terrain sorgusu olarak kullanmalı; hareket integratörü bunların yerine geçmemeli. |
| A* / click-to-move | `HexPathfinder`, `HexWorldRuntime.path_to/move_toward` | Hex hücre grafında path bulma ve adım adım ilerleme | **Korunacak.** Pathfinding hedef hücre/rota üretir; fiziksel serbest hareketi kendisi yönetmez. |
| Kamera takip/bounds | `HexCamera` | Takip, edge-scroll, viewport ve dünya sınırlarına clamp | **Korunacak.** Mevcut kamera zaten ana sunum sahibi. |
| Dünya-ekran dönüşümü | `WorldTransform` | Axial→world pixel, world↔screen ve zoom/camera offset | **Genişletilecek.** Sürekli world coordinate API eklenmeli; laboratuvar geometry bridge'e bağımlılık kaldırılmalı. |
| Dünya render orkestrasyonu | `HexGameplayView` | Kamera, transform, terrain/character renderer, input ve geçici görsel hareket | **Sorumluluk daraltılmalı.** View simülasyon/interaction kararlarını üstlenmemeli; render snapshot tüketmeli. |
| NPC hedef seçimi | `HexGameplayView._npc_at_screen_position` | Ekran→axial hücre dönüşümü ve tüm runtime entity'lerini tarama | **Yanlış katman/eksik kabiliyet.** Etkileşim application servisine alınmalı; view yalnızca input ve sonucu yönlendirmeli. |
| Etkileşim menzili/öncelik | Tam karşılık yok | Hücre eşleşmesi dışında dünya mesafeli profil/menzil/öncelik sorgusu yok | **Eksik.** Laboratuvar target query davranışı ana application interaction servisine aktarılmalı. |
| İçerik ve harita tanımı | `ContentPackage`, `load_content_package`, `HexMapDefinition`, `GameplayPlacementCatalog` | Versiyonlu içerik yükleme, harita tanımı ve placement catalog | **Korunacak.** Lab demo content ve ayrı içerik sahipliği taşınmayacak. |
| Render anchor/depth/visibility | `HexCharacterRenderer`, `HexTerrainRenderer`, `DepthSorter` | Mevcut sprite/terrain çizimi ve depth sıralaması | **Genişletilecek.** Lab anchor/snapshot/visibility davranışları mevcut renderer sözleşmelerine uyarlanmalı. |
| Simülasyon tick ve hareket state | `core.simulation`, `core.time.Tick`, `GameSession` | Canonical simulation/tick ve gameplay zaman sahipliği | **Sahip korunacak.** Pygame frame delta doğrudan domain tick sayacı olmamalı; hareket sistemi canonical tick'e bağlanmalı. |
| Birleşik save envelope | `GameSaveDocument` v3 | Core + gameplay ve uygulama snapshot'ları | **Korunacak.** Yeni ayrı save sistemi oluşturulmayacak. |
| Hex dünya save | `HexWorldSnapshot` v1 | Entity `map_id + q/r`, profile, active, occupancy flags, patrol indices | **Genişletilecek.** Sürekli konum/velocity/movement state için açık schema/migration kararı gerekir. |
| JSON codec | `SaveJsonCodec` | Deterministik JSON encode/decode | **Korunacak.** |
| Atomik dosya işlemleri | `GameSaveFileAdapter` | Lock, temp file, fsync, doğrulama, backup ve atomic replace | **Korunacak.** Laboratuvar dosya storage'ı ana oyuna ikinci dosya sistemi olarak eklenmemeli. |

## 3. Mevcut sorumluluk sahiplerinin ayrıntılı değerlendirmesi

### 3.1 Actor kimliği ile spatial konum ayrımı

Mevcut tasarımda `WorldActorRegistry` aktör kimliği ve gameplay bağlantılarının sahibidir. `HexWorldRuntime` ise hex hareket sisteminin spatial kaydını tutar. `HexOccupancyRegistry` gerçek hücre konumunu tutar; runtime entity görünümündeki position occupancy kaydından türetilir.

Bu, kimlik ve konum sorumluluğunu ayırmak bakımından doğru bir temeldir. Ancak runtime içindeki `_HexEntityState` aynı actor ID, kind, profile ve active verisini ikinci bir sözlükte tutar. Bu ikinci kayıt kimlik otoritesi değildir; spatial runtime'ın hareket kabiliyeti state'idir. Bu ayrım korunmalı ve belgelenmeli.

**Hedef:** `WorldActorRegistry` actor kimliğinin; yeni continuous spatial runtime ise dünya konumu, velocity, body transform ve hareket state'inin sahibi olur. Tek actor ID kullanılır. Position iki registry'de kopyalanmaz.

### 3.2 HexWorldRuntime'ın doğru ve yanlış sorumlulukları

Doğru sorumluluklar:
- Harita tanımlarına erişim ve world-map topolojisi.
- Entity'nin hangi map scope'ta bulunduğunu doğrulama.
- Terrain/blocked cell ve profile kurallarını uygulama.
- Occupancy/hücre görünümünü sağlama.
- Map transition ve A* path işlemlerini yürütme.

Sınırlı/evrimleşmesi gereken sorumluluk:
- Bugün entity konumunu `EntityPosition(map_id, LocalHexPosition(q,r))` olarak tutan occupancy'yi yetkili kabul etmesi.
- Hareketi bir hücreden diğerine atomik commit etmesi.

Hedefte sürekli konum, spatial runtime'ın tek authoritative state'i olmalı. Hücre occupancy, mevcut `HexMapDefinition` ve occupancy kuralları üzerinden türetilen sorgu olmalı. `HexPathfinder` hücre grafı üzerinde rota üretmeye devam edebilir; hareketin fiziksel ilerleyişi ayrı continuous movement sistemine ait olmalı.

### 3.3 Fizik sahipliği

`HexPhysicsSnapshot` iyi bir statik harita-fiziği adaptörüdür: canonical Eldoria harita tanımından fizik geometrisi üretir ve statik engeller için indeks tutar. Ancak `resolve_cell_step` kaynak ve hedef hücre merkezleri arasında bir sweep yaparak adımı doğrular. Bu, hareket integrasyonu veya oyuncunun serbestçe world space'te ilerlemesi değildir.

Hedefte:
- Harita sınırları ve statik terrain geometry `HexMapDefinition` kaynaklı olmalı.
- Dinamik body transform ve velocity continuous movement/spatial runtime'da olmalı.
- Broadphase ve narrowphase/solver fizik sorumluluğunda olmalı.
- Body collider boyutları içerik veya açıkça onaylanmış actor tanımından gelmeli.
- Player circle radius 8 world unit kararı korunmalı; NPC/prop collider boyutları belirlenmemeli.

### 3.4 Kamera ve render sahipliği

`HexCamera` ile `WorldTransform` doğru sunum katmanında. Bunlar dünya state'inin sahibi değildir. `HexGameplayView` ise bugün input, NPC hücre seçimi, click-to-move komutu, kamera, görsel interpolasyon ve çizim akışını aynı sınıfta topluyor.

Hedefte `HexGameplayView` Pygame input olaylarını uygulama servislerine yönlendirir ve render snapshot'larını çizer. NPC hedef seçimi ve movement state kararı UI içinde kalmamalı. Render interpolasyonu yalnızca render snapshot'ı üzerinde kalmalı; authoritative world position'ı değiştirmemeli.

### 3.5 Interaction sahipliği

Bugünkü NPC seçimi `HexGameplayView._npc_at_screen_position` içinde ekran koordinatını axial hücreye çevirip `runtime.entities()` listesini tarıyor. Bu, laboratuvarın spatial candidate query + dünya mesafesi + interaction profile + öncelik sıralaması davranışını karşılamıyor.

Hedef sahip:
- Pygame view: tıklama konumunu ve input tipini application interaction service'e iletir.
- `WorldTransform`: screen→world dönüşümü yapar.
- Application interaction service: world position etrafında candidate query, range/profile/priority kontrolü yapar.
- NPC domain/registry: NPC'nin diyalog ve NPC'ye özgü verisini sağlar.
- Mevcut sol tık diyalog akışı korunur. Sağ tık aksiyon menüsü kabuğu boş kalır; aksiyonlar bu aşamada eklenmez.

Yeni servis gereksinimi gerçek bir boşluktur; mevcut UI taramasını daha da büyütmek doğru değildir.

### 3.6 Persistence sahipliği

`GameSaveDocument` v3 uygulamanın birleşik kayıt zarfıdır. `HexWorldSnapshot` v1 hex entity pozisyonu, profile, active, blocking flags ve NPC patrol index'lerini saklar. `ActorSnapshot` actor identity/activity bilgilerini saklar ve güncel snapshot üretiminde legacy square position alanlarını boş bırakır. `SaveJsonCodec` ve `GameSaveFileAdapter` codec ve atomik dosya işlemlerinin sahibidir.

Sürekli konum için yeni bir dosya veya bağımsız lab storage taşınmamalı. `HexWorldSnapshot` sözleşmesi sürümlendirilmeli; continuous world position, gerekli movement state ve gerekiyorsa velocity alanlarının kalıcı olup olmayacağı açıkça belirlenmeli. Geçişte mevcut kayıtların nasıl restore edileceği migration testleriyle tanımlanmalı.

## 4. Gerçek mimari boşluklar

1. **Continuous spatial state:** Ana oyunda `WorldPoint` benzeri sürekli world position ve onun tek yetkili sahibi yok.
2. **Continuous movement:** Intent/mode/config/integrator ve sabit adımlı movement runtime ana oyunda yerel değil.
3. **Dynamic physics:** Statik harita engeli snapshot'ı var; dinamik aktör body spatial index ve tam continuous collision çözümlemesi ana oyun mimarisinde yerel değil.
4. **General spatial index:** Occupancy'nin `_by_cell` indeksi var; genel AABB grid/quadtree ve entity proximity query yok.
5. **Interaction service:** NPC hit-test UI view içinde hücre taramasıyla yapılıyor; world-distance/range/profile/priority sistemi yok.
6. **Entity transform/render snapshot:** Render katmanı cell center ve view interpolation kullanıyor; authoritative continuous transform ve render snapshot sözleşmesi yok.
7. **Persistence extension:** Hex save schema v1 yalnızca map/cell position kaydediyor; continuous transform/movement state yok.

## 5. Mevcut ve korunacak mimari sahiplik haritası

Aşağıdaki sahipler yeni sistemler kurulurken değiştirilmemeli:

- `core.domain.spatial`: axial geometri, hücre kimliği, topolojik mesafe ve movement domain value objects.
- `WorldActorRegistry`: genel aktör kimliği ve gameplay linkleri.
- `NPCRegistry`, `WorldResourceNodeManager`, `ContainerManager`: kendi domain verilerinin tek otoritesi.
- `HexMapDefinition`, `WorldMapDefinition`, `ContentPackage`: harita ve içerik tanımı.
- `HexWorldRuntime`: mevcut hex dünya/harita yaşam döngüsünün evrileceği ana uygulama sahibi.
- `HexOccupancyRegistry`: occupancy sorgusu; hedefte continuous position'dan türetilen hücre görünümü.
- `HexPhysicsSnapshot`: statik map geometry/obstacle üretimi; hedefte ana oyuna ait physics domain tarafından desteklenecek.
- `HexCamera`, `WorldTransform`, `HexGameplayView`: kamera ve Pygame sunum katmanı.
- `GameSaveDocument`, `HexWorldSnapshot`, `SaveJsonCodec`, `GameSaveFileAdapter`: mevcut save sözleşmesi ve dosya sınırı.

## 6. Bağımlılık temizliği sırası

Şu an `application/hex_actor_binding.py`, `application/npc_hex_binding.py`, `application/hex_physics_bridge.py` ve `application/hex_world_geometry_bridge.py` laboratuvar paketini doğrudan import ediyor. `pyproject.toml` paket keşfine `hex_world_lab*` dahil ediyor.

Bunlar hemen kaldırılmamalı. Güvenli sıra:
1. Ana oyunun yerel domain değerlerini ve servis sözleşmelerini oluştur.
2. Her lab importunu yerel karşılığına geçir.
3. Binding tüketicileri, testler ve paketleme doğrulamasını geçir.
4. Ana runtime import grafiğinde `hex_world_lab` kalmadığını doğrula.
5. Ancak sonra paket keşfinden çıkar. Laboratuvarın deney dalı/dizini korunur.

## 7. Uygulama öncesi karar gerektiren noktalar

- Continuous world position için kesin Eldoria value object ve koordinat birimi.
- World coordinate y yönü ve axial↔world dönüşümünün tek sahibi.
- Continuous spatial state'in mevcut `HexWorldRuntime` içinde mi, onun yerel bir alt bileşeninde mi tutulacağı. Ayrı bir ikinci runtime kurulmayacak.
- Canonical simulation tick ile continuous integrator'ın bağlanma noktası.
- NPC/prop body tanımlarının kaynağı; onaylanmamış ölçüler kullanılmayacak.
- Cell occupancy, blocked terrain ve A* path'in continuous actor konumuyla tutarlı türetilmesi.
- `rpg-game-save` v3 ve `rpg-hex-world` v1 için migration/geriye uyumluluk.
- NPC etkileşim sorgusunun application katmanındaki kesin modül sahibi.

## 8. Sonuç

Ana oyunda geometri, kamera, harita, actor kimliği, NPC/resource/container domain bağları, pathfinding ve save sistemi için mevcut sahipler vardır. Bunlar korunmalı ve laboratuvar kabiliyetleri bu sahiplerin sorumlulukları içinde karşılanmalıdır.

En büyük eksiklik, sürekli dünya konumunun ve onunla çalışan hareket/fizik/spatial query mimarisinin ana oyunda authoritative olmamasıdır. En net yanlış katmanlaşma ise NPC hedef seçiminin `HexGameplayView` içinde yapılmasıdır.

Bu raporla kod değişikliği yapılmamıştır. Bir sonraki aşama, bu sahiplik haritasını continuous spatial/movement entegrasyonu için kesin teknik sözleşmeye çevirmek ve ardından küçük, testli aktarım adımlarını başlatmaktır.
