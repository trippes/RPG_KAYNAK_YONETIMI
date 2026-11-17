# Aşama 9 — Ayrıntılı Teknik Mimari Planı

> **Belge türü:** Dosya/API düzeyinde teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Depo:** trippes/RPG_KAYNAK_YONETIMI  
> **Çalışma dalı:** experiment/hex-world-laboratory  
> **Durum:** TEKNİK PLAN HAZIRLANDI — KULLANICI ONAYI BEKLENİYOR  
> **Hazırlanma tarihi:** 17 Kasım 2026  
> **Genel plan:** [PHASE-09-GENERAL-PLAN.md](PHASE-09-GENERAL-PLAN.md)  
> **Planın hazırlandığı HEAD:** 3f64a7030064fd40e25926e28066b45bb95af048  
> **Uygulama durumu:** Başlatılmadı

---

## 1. Teknik karar özeti

Aşama 9, mevcut hex world laboratuvarında henüz bulunmayan ortak entity katmanını oluşturacak; oyuncu, NPC ve kaynak nesnelerini tekil kimlik, harita kapsamı ve sürekli dünya konumu üzerinden temsil edecektir. Mevcut Geometry, World, Movement, Physics, Rendering ve Spatial paketleri yeniden yazılmayacak; yeni entity/interaction katmanı bunların açık API'lerini kullanacaktır.

Ana kararlar:

1. Entity kimliği konumdan bağımsızdır. Kimlik, tür, dünya/harita adresi ve transform ayrı kavramlardır.
2. Sürekli dünya konumu authoritative kaynaktır. Hareketli entity konumu WorldPoint olarak tutulur. Hex koordinatı gerektiğinde world_to_axial() ile türetilir; hareketli entity hücre merkezine zorlanmaz.
3. Hücreye sabit içerik geometri üzerinden yerleştirilir. Statik kaynak/nesne hücre adresinden axial_to_world() ile dünya konumuna dönüştürülür.
4. Görsel anchor, entity transform ve collider ayrıdır. ActorBodyTransform.ground_anchor ile SpriteVisual.ground_anchor aynı entity konumundan beslenir; sprite boyutu fizik gövdesini değiştirmez.
5. Spatial yalnızca aday bulur. Aşama 8'de kabul edilen UniformGrid ve generic Spatial API kullanılabilir. Kesin hedef uygunluğu ve menzil kararı Interaction katmanında yapılır.
6. Hedef seçimi deterministiktir. Harita kapsamı, hedeflenebilirlik, etkileşim türü, menzil ve sabit tie-break sırası açıkça uygulanır.
7. Yoldaşlık, NPC kimliğinden ayrı bir ilişkidir. NPC oyuncuya yoldaş olarak bağlanabilir; komut durumu FOLLOW, WAIT veya RETURN olarak saklanır. İlişki ve komut geçişleri bu aşamada uygulanır; komutlar NPC'yi hareket ettirmez.
8. Harita sınırı korunur. Entity ve Spatial sorguları world/map kimliğiyle sınırlandırılır. Harita unload/remove sırasında entity ve yoldaş referanslarının yaşam döngüsü yönetilir.
9. Pygame yalnızca sunum adaptörüdür. Entity, interaction ve companion domain kuralları Pygame import etmez.
10. Aşama 9 mevcut hareket sistemini genişletmez. Oyuncu hareketi mevcut MovementSystem/CollisionAwareMovementSystem üzerinden sürer. NPC otomatik hareketi, takip AI'sı ve pathfinding bu aşamada yoktur.

## 2. Depo denetiminden doğrulanan mevcut durum

İnceleme, teknik plan hazırlanırken experiment/hex-world-laboratory HEAD üzerinde yapıldı. Uygulama öncesinde HEAD ve hedef dosya SHA'ları yeniden doğrulanacaktır.

### 2.1 Mevcut temel modüller

| Mevcut dosya | Doğrulanan sorumluluk | Aşama 9 kullanımı |
|---|---|---|
| geometry/coordinates.py | AxialCoord, CubeCoord, sürekli WorldPoint değer nesneleri | Entity dünya konumu ve hex adresi |
| geometry/transforms.py | Axial/world dönüşümleri | Hücreye sabit entity yerleşimi ve hit-test |
| geometry/distance.py | hex_distance() | Topolojik etkileşim menzili |
| world/identity.py | WorldId, MapId, CellAddress | Entity world/map kapsamı |
| world/world.py | HexWorld aggregate; map registry/runtime/view sahipliği | Map lifecycle orkestrasyonu |
| world/map_registry.py | Map kayıt, load, unload ve remove işlemleri | Entity kayıtlarının map lifecycle ile eşlenmesi |
| movement/state.py, simulation/movement_system.py | Sürekli konum ve 60 TPS hareket adımları | Oyuncu hareketinin mevcut otoritesi |
| physics/body.py | BodyDefinition, ActorBodyTransform, ground-anchor tabanlı collider dönüşümü | Entity fizik gövdesi adaptasyonu |
| rendering/snapshot.py | SpriteVisual, WorldRenderSnapshot, ColliderVisual | Entity verisinden salt okunur render snapshot üretimi |
| spatial/protocols.py, spatial/grid.py | Generic Bounds2D/SpatialIndex ve UniformGrid | Entity aday sorgusu |
| physics/spatial_adapter.py | Map-scoped ObstacleSpatialIndex | Entity için ayrı adaptör tasarımına örnek |
| application/movement_demo.py | Tek oyunculu/tek haritalı kabul demosu | Çok entity'li test sahnesinin entegrasyon noktası |

### 2.2 Önemli mevcut sınırlar ve eksikler

- src/hex_world_lab/entities/ ve interaction/ dizinleri henüz uygulama modülü içermiyor; yalnızca yer tutucular mevcut.
- Mevcut demo tek oyuncu aktörü etrafında düzenlenmiştir. Entity registry ve çoklu sprite sunumu henüz mevcut değildir.
- HexWorld map lifecycle API'si sunar; entity registry veya entity lifecycle callback'i sunmaz. Lifecycle bağlantısı yeni bir application-level coordinator üzerinden kurulmalıdır. World katmanına entity bağımlılığı eklenmeyecektir.
- WorldRenderSnapshot çoklu SpriteVisual kabul eder; birden fazla entity'nin render'a taşınması için kullanılabilir.
- ActorBodyTransform ground anchor ile fiziksel collider'ı birbirinden ayırır. Bu sözleşme korunacaktır.
- Spatial paketi generic bounds/index API'si sunar. ADR-008'e göre UniformGrid büyük ve uzun ömürlü aday kümeleri için tercih edilen adaptördür; küçük kümelerde doğrusal referans sorgu seçeneği korunabilir.
- WorldPoint matematiksel dünya koordinatıdır; screen/camera koordinatı değildir.
- Entity, interaction veya companion davranışını yönetecek mevcut bir NPC AI/tick sistemi bulunmadığı için Aşama 9 yalnızca kapsam dahilindeki veri/ilişki/query sözleşmelerini ekleyecektir.

## 3. Hedef katman mimarisi

### 3.1 Bağımlılık yönü

~~~mermaid
flowchart TD
    GEO[Geometry: WorldPoint / AxialCoord / transforms]
    WORLD[World: WorldId / MapId / CellAddress / map lifecycle]
    ENTITY[Entities: identity / kind / transform / registry]
    PHYS[Physics: BodyDefinition / ActorBodyTransform]
    RENDER[Rendering: SpriteVisual / WorldRenderSnapshot]
    SPATIAL[Spatial: Bounds2D / UniformGrid]
    EIDX[EntitySpatialIndex adapter]
    INTERACTION[Interaction: range / target query / selection]
    COMPANION[Companions: relationship / command state]
    APP[Application: lifecycle coordinator / demo]
    GEO --> ENTITY
    WORLD --> ENTITY
    ENTITY --> PHYS
    ENTITY --> RENDER
    SPATIAL --> EIDX
    ENTITY --> EIDX
    EIDX --> INTERACTION
    ENTITY --> INTERACTION
    ENTITY --> COMPANION
    COMPANION --> APP
    INTERACTION --> APP
    APP --> RENDER
~~~

Kurallar:

- geometry hiçbir entity, NPC, companion, interaction veya Pygame modülünü import etmez.
- world entity paketini import etmez; world kimliği ve map lifecycle API'si sağlar.
- entities Geometry ve World identity değer nesnelerini kullanabilir; Pygame, Rendering, Interaction ve Physics uygulama koduna bağımlı olmaz.
- spatial generic kalır. Entity türlerini, NPC davranışlarını veya interaction kurallarını bilmez.
- Entity Spatial adapter, Entity ve Spatial API'lerini birleştirir; Physics'in obstacle adapter'ı doğrudan entity index olarak kullanılmaz.
- interaction Entity registry ve entity spatial query API'sini kullanır. Kamera veya Pygame event nesnesi kabul etmez.
- companions entity kimlikleri ve konum snapshot'larıyla ilişki/komut durumunu yönetir; Movement/Physics/Pathfinding çağırmaz.
- Application katmanı map lifecycle, registry, index ve demo akışını koordine eder.
- Renderer yalnızca immutable snapshot tüketir; entity konumunu veya companion durumunu değiştiremez.

## 4. Veri modeli ve sözleşmeler

Aşağıdaki API isimleri uygulama için önerilen sözleşmelerdir. Onay sonrasında kodlama sırasında mevcut stil ve testlerle tutarlı son biçimleri uygulanacaktır.

### 4.1 Entity kimliği ve türü

Önerilen yeni dosyalar:
- entities/identity.py
- entities/kind.py

Önerilen sözleşme:

- EntityId(value: str): Boş olmayan, değişmez ve entity türünden bağımsız kimlik.
- EntityKind(Enum): PLAYER, NPC, RESOURCE.
- Kimlikler registry içinde tekil olmalıdır. Aynı entity ID ikinci kez kaydedilemez.
- Entity ID, map ID veya axial koordinattan türetilmez; entity taşınsa da kimliği değişmez.
- Entity türü değiştirilebilir bir etiket değildir. NPC'nin yoldaş olması onun EntityKind.NPC niteliğini değiştirmez.

### 4.2 World location ve transform

Önerilen dosyalar:
- entities/transform.py
- entities/entity.py

Önerilen değer nesneleri:

~~~python
@dataclass(frozen=True, slots=True)
class EntityLocation:
    world_id: WorldId
    map_id: MapId
    position: WorldPoint

@dataclass(frozen=True, slots=True)
class EntityTransform:
    location: EntityLocation
    rotation_radians: float = 0.0
~~~

Kurallar:

- EntityLocation world ve map kimliğini aynı konum kaydında taşır.
- WorldPoint sonlu, sürekli dünya koordinatıdır.
- rotation_radians sonlu olmalıdır; mevcut fizik transform'u ile aynı açı konvansiyonunu kullanır.
- Hex adresi transform'un yerine geçmez. Gerekli olduğunda ilgili map'in HexLayout değeriyle world_to_axial() çağrılarak türetilir.
- Entity transform değişimi tek bir registry API'si üzerinden yapılır; doğrudan mutable field yazımı yapılmaz.
- Statik/hücreye sabit entity oluşturulurken CellAddress ve map layout doğrulanır; başlangıç WorldPoint değeri axial_to_world() ile türetilir. Hücreye sabitlik politikası entity placement metadata'sında açıkça saklanır; hareketli entity'ler bu politikaya zorlanmaz.
- Entity konumu kamera zoom'u, ekran koordinatı, sprite merkezi veya collider merkezinden hesaplanmaz.

### 4.3 Entity kaydı ve registry

Önerilen dosyalar:
- entities/entity.py
- entities/registry.py
- entities/__init__.py

EntityRecord önerilen alanları:

- entity_id: EntityId
- kind: EntityKind
- transform: EntityTransform
- body: BodyDefinition | None
- interaction_profile: InteractionProfile | None
- is_active: bool

Türe özgü içerik (NPC adı, kaynak türü, can, envanter, üretim verisi vb.) bu ortak kayda kontrolsüz metadata yığını olarak eklenmez. Bu aşama yalnızca ortak varlık sözleşmesini ve test prototipinin ihtiyaç duyduğu minimum tanımlayıcı bilgiyi tutar.

EntityRegistry önerilen API:

- register(entity) -> None
- get(entity_id) -> EntityRecord | None
- require(entity_id) -> EntityRecord
- update_transform(entity_id, transform) -> None
- set_active(entity_id, active) -> None
- remove(entity_id) -> EntityRecord
- entities_for_map(world_id, map_id) -> tuple[EntityRecord, ...]
- all_entities() -> tuple[EntityRecord, ...]

Kurallar:

- Registry tek bir WorldId kapsamındadır.
- Map'e ait kayıt, o world altında kayıtlı map ID'siyle eşleşmelidir.
- Registry dışarıya mutable dictionary veya liste vermez; deterministik tuple snapshot döndürür.
- Silinen entity get/query sonuçlarında görünmez.
- Registry EntityId tekilliğini registry kapsamı içinde uygular.
- EntityRecord immutable tutulur; güncelleme yeni kayıtla atomik değiştirme şeklindedir.
- Registry doğrudan dosya persistence'ı yapmaz.

### 4.4 Harita lifecycle koordinasyonu

Mevcut HexWorld entity lifecycle callback sağlamadığı için yeni dosya:
- application/entity_world_coordinator.py

Önerilen sorumluluk:

- HexWorld, EntityRegistry ve map-scoped EntitySpatialIndex nesnelerini koordine etmek.
- Map load olduğunda o map'e ait aktif entity kayıtlarını spatial index'e eklemek.
- Map unload olduğunda entity kayıtlarını registry'den silmeden map'in aktif spatial index'ini temizlemek; unloaded map entity'lerini aktif sorgulardan çıkarmak.
- Map yeniden load olduğunda map'e ait retained entity kayıtlarını yeniden indekslemek.
- Map remove olduğunda o map'e ait entity kayıtlarını ve onlara bağlı companion ilişkilerini kontrollü biçimde kaldırmak.
- Map lifecycle sırasında yarım güncellenmiş registry/index durumu bırakmamak; işlem başarısızsa değişiklikleri commit etmemek veya güvenli rollback uygulamak.

Bu coordinator dışında HexWorld içine Entity veya Companion import'u eklenmeyecektir.

### 4.5 Foot-anchor ve Physics body binding

Mevcut dosyalar korunur:
- physics/body.py
- rendering/snapshot.py
- rendering/pygame_world_renderer.py

Yeni adaptör önerisi:
- entities/presentation.py veya application seviyesinde entity_presentation.py

Kurallar:

- Entity'nin authoritative konumu ayak/zemin temas noktasıdır.
- ActorBodyTransform(ground_anchor=entity.transform.location.position, rotation_radians=...) fizik gövdesinin world shape'ini üretir.
- Sprite üretimi SpriteVisual.ground_anchor alanına aynı WorldPoint değerini verir.
- Sprite asset'in foot-anchor oranı görsel piksel yerleşimini belirler; entity WorldPoint'i değiştirmez.
- Collider ölçüsü BodyDefinition içindeki shape ile tanımlanır; sprite yüzey boyutundan otomatik türetilmez.
- Body bulunmayan kaynak/etkileşim nesnesi de entity olabilir. Etkileşim yarıçapı collider yerine geçmez.
- Mevcut WorldRenderSnapshot alanları geriye dönük uyumlu biçimde kullanılır; snapshot'a entity registry veya domain nesnesi taşınmaz.

### 4.6 Interaction profili, menzil ve hedef seçimi

Önerilen dosyalar:
- interaction/profile.py
- interaction/range.py
- interaction/target_query.py
- interaction/selection.py
- interaction/__init__.py

InteractionProfile minimum alanları:

- targetable: bool
- interaction_radius: float (dünya birimi; sonlu ve sıfırdan büyük)
- interaction_tags: frozenset[str] (talk, gather, inspect gibi etiketler; oynanış aksiyonu değil)
- Gerekirse selection_priority: int (yüksek değer önce)

Menzil politikası:

- World-distance: Sürekli fiziksel yaklaşma/etkileşim için WorldPoint Euclidean mesafesi kullanılır.
- Hex-distance: Yalnızca kural açıkça hücre adımı tanımlıyorsa hex_distance() kullanılır.
- Kamera zoom'u, viewport, sprite boyutu ve ekran pikseli menzili değiştirmez.
- Kesin menzil testi broadphase'den sonra yapılır; AABB kesişimi tek başına menzilde olma sayılmaz.
- Kaynak node etkileşim yarıçapı ile oyuncu etkileşim menzili ayrı kavramlardır. Kesin karar, tanımlı etkileşim kuralının kullandığı mesafe ve profile göre verilir.

Önerilen API:

- query_targets(origin, map_id, radius, tags=...) -> tuple[TargetCandidate, ...]
- select_target(world_point, map_id, tags=...) -> EntityId | None
- is_in_interaction_range(actor_id, target_id, interaction_kind) -> bool

Deterministik sıralama:

1. Yalnızca aynı world/map kapsamındaki aktif entity'ler.
2. targetable=True ve istenen interaction tag'i olanlar.
3. Kesin dünya/hex menzili koşulunu sağlayanlar.
4. Açıkça tanımlı seçim önceliği.
5. Aynı öncelikte en kısa mesafe.
6. Mesafe eşitse EntityId.value alfabetik artan sıra.

Fare seçimi sınırı:

- Pygame adapter, fare pikselini kamera dönüşümüyle WorldPoint değerine dönüştürür.
- Interaction katmanı yalnızca WorldPoint alır; pygame event, Surface, Rect veya ScreenPoint import etmez.
- Hit-test adayları map-scoped Spatial query ile daraltılır; son geometrik seçim world-space ölçümle yapılır.
- Seçim, konuşma/toplama/saldırı gibi bir aksiyonu kendiliğinden çalıştırmaz.

### 4.7 Entity Spatial adapter

Yeni dosya:
- entities/spatial_index.py

Tasarım:

- Aşama 8 generic SpatialIndex ve UniformGrid kullanılır.
- Physics ObstacleSpatialIndex sınıfı doğrudan entity index olarak kullanılmaz; entity bounds, obstacle shape ve lifecycle farklı sorumluluklardır.
- Her map için ayrı index tutulur. Entity map değiştirirse eski map index kaydı kaldırılır, yeni map index kaydı eklenir.
- Spatial kayıt kimliği EntityId.value olur; kayıt AABB'si entity'nin world-space interaction bounds veya fizik gövdesi bounds'undan üretilir.
- Body varsa world shape AABB'si; body yoksa interaction radius çevresindeki AABB kullanılır. İkisi de yoksa entity spatial/interaction sorgusuna eklenmez.
- Query sonuçları EntityRegistry üzerinden çözülür; kaldırılmış, inactive veya map'i unloaded entity sonuçtan elenir.
- Index yalnızca aday üretir. Kesin hit-test ve interaction menzili Interaction katmanındadır.
- UniformGrid cell size varsayılanı için ADR-008'deki 128 world-unit değeri başlangıç adayıdır; test sahnesi dağılımı benchmark ile doğrulanır. Küçük test kümelerinde linear reference query ile differential test yapılır.
- Update sırası: entity transform doğrulanır → yeni bounds hesaplanır → index update/transfer yapılır → registry transform commit edilir. Hata durumunda önceki registry/index durumu korunur.

### 4.8 Yoldaş ilişki ve komut modeli

Önerilen dosyalar:
- companions/relationship.py
- companions/command.py
- companions/roster.py
- companions/__init__.py

Yoldaşlık, NPC'nin entity türünü veya kimliğini değiştirmez. NPC dünya varlığı olarak registry'de kalır; oyuncu ile ayrı bir ilişki kaydı kurulur.

Önerilen değer nesneleri:

~~~python
class CompanionCommand(Enum):
    FOLLOW = "follow"
    WAIT = "wait"
    RETURN = "return"

@dataclass(frozen=True, slots=True)
class CompanionRelationship:
    player_id: EntityId
    companion_id: EntityId
    command: CompanionCommand
    command_revision: int = 0
    wait_position: WorldPoint | None = None
~~~

Önerilen CompanionRoster API:

- recruit(player_id, npc_id) -> CompanionRelationship
- dismiss(npc_id) -> CompanionRelationship
- issue_command(npc_id, command) -> CompanionRelationship
- get_relationship(npc_id) -> CompanionRelationship | None
- companions_for_player(player_id) -> tuple[CompanionRelationship, ...]
- remove_entity(entity_id) -> None (entity lifecycle ile cascade temizliği)

Kurallar:

- Yalnızca EntityKind.PLAYER bir player owner olabilir.
- Yalnızca EntityKind.NPC yoldaş olarak recruit edilebilir.
- Bir NPC aynı anda en fazla bir oyuncuya bağlı olabilir.
- Bir oyuncunun birden fazla yoldaşı olabilir; bu aşamada üst sınır konulmaz.
- Recruit işlemi, oyuncu ve NPC entity'lerinin aynı world içinde kayıtlı ve aktif olmasını gerektirir. Başlangıç kararı olarak aynı map üzerinde olmaları da gerekir; farklı map'ten recruit/teleport yapılmaz.
- Dismiss, ilişkiyi kaldırır; NPC entity'sini dünyadan silmez.
- FOLLOW: komut kaydı oyuncuyu takip etme niyetini temsil eder.
- WAIT: komut verildiği andaki NPC WorldPoint değeri wait_position olarak yakalanır; sonraki aşamada gerçek bekleme davranışına dayanak olur.
- RETURN: komut, yoldaşın oyuncuya geri dönmesi niyetini temsil eder; hedef oyuncunun güncel konumudur.
- Komut değişiminde command_revision monoton artar; aynı komut tekrar verilirse davranış açık ve test edilebilir olmalıdır.
- Bu aşamada komutlar hareket, hız, pathfinding, teleport veya collision çözümü başlatmaz.
- CompanionRoster MovementSystem, Physics, Pygame veya renderer import etmez.
- Yoldaş ilişkisi NPC'nin haritadaki konumunu, entity ID'sini veya Spatial kaydını tek başına değiştirmez.
- İlişkili entity kaldırılırsa ilişki cascade olarak kaldırılır. Map unload ilişkiyi silmez; entity'ler inactive/unloaded iken ilişki kayıtları korunur. Map remove entity'leri sildiği için ilgili ilişkiler de kaldırılır.
- Player/NPC map geçişi sırasında otomatik takip veya otomatik transfer yapılmaz. İlişki ve son komut durumu korunur; gerçek map geçiş davranışı sonraki yoldaş AI/navigasyon tasarımında ele alınır.

### 4.9 Test sahnesi

Mevcut application/movement_demo.py tek oyunculu kabul sahnesidir. Çok entity'li test için yeni bir application orchestrator veya mevcut demo üzerinde kontrollü genişletme yapılacaktır. Test sahnesi en az:

- 1 PLAYER entity (mevcut hareket sistemiyle kontrol edilir),
- 2 NPC entity (biri yoldaş ilişkisine alınabilir),
- 2 RESOURCE entity (en az biri hücreye sabit),
- Farklı sprite boyutları ve farklı collider/interaction bounds,
- Birden fazla map kimliği için otomatik test fixture'ı,
- Yoldaş recruit/dismiss ve FOLLOW/WAIT/RETURN komut durumlarını gösteren diagnostics

içerecektir.

Bu sahne final sanat veya NPC animasyonu değildir; entity, render anchor, collider, seçim ve yoldaş veri sözleşmelerini doğrulayan teknik prototiptir.

## 5. Dosya düzeyinde uygulama planı

Dosya adları mevcut laboratuvar paket yapısına göre önerilmiştir. Uygulama öncesi kaynak ağacı tekrar doğrulanacak; gereksiz dosya çoğaltılmayacaktır.

| İş paketi | Oluşturulacak / değiştirilecek dosyalar | Sorumluluk |
|---|---|---|
| 9.1 | Yeni kod yok; denetim notları teknik rapora | Mevcut sözleşmeler ve import sınırları |
| 9.2 | entities/identity.py, entities/kind.py, entities/entity.py, entities/registry.py, entities/__init__.py | Entity kimliği, türü, immutable kayıt ve registry |
| 9.3 | entities/transform.py, gerekirse entities/placement.py | World/map/WorldPoint transform ve cell placement |
| 9.4 | entities/presentation.py; mevcut physics/body.py ve rendering/snapshot.py için yalnızca gerekirse uyumlu küçük adaptasyon | Ground anchor, collider ve sprite binding |
| 9.5 | interaction/profile.py, interaction/range.py, interaction/target_query.py, interaction/selection.py, interaction/__init__.py | Menzil, hedef adayları ve deterministik seçim |
| 9.6 | entities/spatial_index.py, application/entity_world_coordinator.py | Map-scoped entity index ve map lifecycle |
| 9.7 | companions/relationship.py, companions/command.py, companions/roster.py, companions/__init__.py | Yoldaş ilişki ve komut durumları |
| 9.8 | application/entity_demo.py veya mevcut demo için sınırlı adaptasyon; gerekli render snapshot üretimi | Player/NPC/resource ve companion prototip sahnesi |
| 9.9 | tests/unit/test_entities_*.py, tests/unit/test_interaction_*.py, tests/unit/test_companions_*.py, tests/integration/test_entity_world_lifecycle.py, tests/integration/test_entity_demo.py, gerekirse benchmark | Unit, integration, regression, performans ve kabul kanıtı |

Mevcut MovementSystem, CollisionAwareMovementSystem, HexWorld, UniformGrid, ActorBodyTransform ve WorldRenderSnapshot public API'leri gerekçe olmadan kırılmayacaktır. Değişiklik gerekirse backward-compatible adapter veya ek alan tercih edilir.

## 6. İş paketlerinin uygulama sırası ve teknik görevleri

### 9.1 — Mevcut sözleşmelerin denetimi

1. Entity/interaction paketlerinin boş iskeletleri ve import sınırları kaydedilir.
2. WorldId/MapId/CellAddress, WorldPoint/AxialCoord ve movement state ilişkisi doğrulanır.
3. ActorBodyTransform ve SpriteVisual ground-anchor eşlemesi doğrulanır.
4. Spatial UniformGrid API'si ve ADR-008 kararı doğrulanır.
5. Map unload/remove davranışı için coordinator entegrasyon noktası belirlenir.
6. Çakışan sorumluluklar ve dosya planı teknik uygulama raporuna kaydedilir.

### 9.2 — Entity kimliği ve yaşam döngüsü

1. EntityId ve EntityKind değer nesneleri uygulanır.
2. Immutable EntityRecord ve map/world doğrulaması eklenir.
3. EntityRegistry tekillik, register/get/require/update/remove ve deterministic snapshot API'lerini sağlar.
4. Duplicate ID, yanlış world, bilinmeyen map, inactive ve remove sonrası query davranışları test edilir.
5. Registry dış mutable storage vermez.

### 9.3 — Position/transform ve map address

1. EntityLocation ve EntityTransform uygulanır.
2. Hareketli entity WorldPoint konumunu kesirli olarak korur.
3. Cell placement helper, CellAddress ve HexLayout doğrulamasıyla world point üretir.
4. World-to-hex dönüşümü türetilmiş query olarak sağlanır; authoritative konum değiştirilmez.
5. Map değişimi tek transaction olarak ele alınır; eski map index kaydı ve yeni map kaydı tutarlı güncellenir.

### 9.4 — Foot-anchor ve physics body binding

1. Entity konumundan ActorBodyTransform üretimi sağlanır.
2. Entity konumundan SpriteVisual üretimi sağlanır.
3. Sprite asset foot-anchor oranı yalnızca çizim yerleşiminde uygulanır.
4. Collider bounds, body transform ve interaction bounds birbirinden ayrı tutulur.
5. Sprite boyutu değişiminin collider/WorldPoint'i değiştirmediği test edilir.

### 9.5 — Interaction range ve target selection

1. InteractionProfile ve interaction tag doğrulamaları eklenir.
2. World distance ve hex distance ayrı stratejiler olarak uygulanır.
3. Spatial aday query ve exact distance/hit-test iki adımda yürütülür.
4. Aynı mesafe/öncelik durumunda EntityId tie-break deterministik sonuç verir.
5. Kamera zoom ve viewport değişimi sonuçları değiştirmez.
6. Selection yalnızca EntityId döndürür; oyun aksiyonu çalıştırmaz.

### 9.6 — Spatial index ve map lifecycle

1. EntitySpatialIndex map başına ayrı UniformGrid tutar.
2. Body bounds veya interaction radius bounds ile entity indexlenir.
3. Transform update, map transfer ve remove işlemleri atomik yapılır.
4. Map unload index'i kapatır/temizler ama retained entity kayıtlarını silmez.
5. Map reload retained kayıtları yeniden indexler.
6. Map remove map entity'lerini ve bağlı companion kayıtlarını temizler.
7. Differential test, index query sonucunu brute-force referansla karşılaştırır; false-negative kabul edilmez.

### 9.7 — Yoldaş ilişki ve komut altyapısı

1. CompanionCommand enum ve CompanionRelationship immutable kaydı uygulanır.
2. CompanionRoster recruit/dismiss/issue_command ve query API'lerini sağlar.
3. Owner/NPC tür doğrulaması ve tek NPC-tek owner kuralı uygulanır.
4. Bir player için birden fazla companion desteklenir.
5. WAIT komutu anlık NPC WorldPoint değerini wait_position alanına alır.
6. FOLLOW ve RETURN komutları niyet/durum olarak kaydedilir; movement intent üretmez.
7. Entity remove ve map remove işlemlerinde ilişkiler tutarlı temizlenir.
8. Komut revision ve aynı komutun tekrar verilme davranışı test edilir.

### 9.8 — Player/NPC/resource prototip sahnesi

1. Player mevcut movement sistemiyle kontrol edilmeye devam eder.
2. NPC'ler sabit test entity'leri olarak yerleştirilir; kendi kendilerine hareket etmez.
3. Kaynak entity'leri hücreye sabit ve/veya sürekli konum örnekleriyle gösterilir.
4. Render snapshot birden fazla sprite ve collider debug girdisi taşır.
5. Fareyle hedef seçimi ve yakın hedef sorgusu test sahnesine bağlanır.
6. Yoldaş recruit/command durumları diagnostics üzerinde gözlenebilir olur; gerçek takip animasyonu veya hareketi gösterilmez.

### 9.9 — Doğrulama ve kabul hazırlığı

1. Unit, integration, architecture boundary ve regression testleri çalıştırılır.
2. Linux ve Windows CI doğrulamaları alınır.
3. Spatial differential/performance testleri raporlanır.
4. Render snapshot ve manuel test sahnesi artifact'leri hazırlanır.
5. Kullanıcı için manuel görsel/işlevsel kabul kontrol listesi hazırlanır.
6. Uygulama/doğrulama raporu yazılır; kullanıcı kabulinden sonra kapanış raporu oluşturulur.

## 7. Test ve doğrulama matrisi

| Alan | Zorunlu testler |
|---|---|
| Entity identity | Boş ID, duplicate ID, farklı kind, stable identity |
| Registry lifecycle | Register/get/update/remove, immutable snapshots, inactive entity |
| World/map scope | Foreign world/map rejection, same axial coordinate across maps, unloaded map exclusion |
| Transform | Fractional WorldPoint preserved, rotation validation, map transfer consistency |
| Cell placement | CellAddress validation, axial_to_world expected point, layout mismatch |
| Anchor/physics | Same ground anchor reaches sprite and body, sprite resize does not change collider |
| Spatial | Insert/update/remove, map isolation, brute-force differential, no false negatives |
| Interaction | World radius, hex radius, tags, targetable false, deterministic tie-break, no action side effects |
| Mouse selection | World-space point after camera conversion, zoom invariance, overlapping targets |
| Companion recruit | PLAYER owner only, NPC companion only, duplicate recruit rejected, one owner per NPC, multiple companions per player |
| Companion commands | FOLLOW/WAIT/RETURN transition, WAIT position snapshot, revision monotonicity, repeated command policy |
| Companion lifecycle | Dismiss preserves NPC, entity remove cascades link, map unload retains dormant relation, map remove clears relation |
| Architecture | No Pygame imports in entities/interaction/companions; no entity imports in world/geometry/spatial |
| Integration | Player + NPC + resource in same map; rendering, selection, spatial and companion data agree |

### 7.1 Differential ve determinism testleri

- EntitySpatialIndex sonuçları aynı map için brute-force AABB adaylarıyla karşılaştırılır.
- Aday listesi sırası stable EntityId sırasına normalize edilir.
- Exact interaction sonucu index ve linear reference yolunda aynı olmalıdır.
- Aynı input/snapshot sırası aynı target ve companion roster sonucunu üretmelidir.
- Map ID farklı entity hiçbir zaman sorgu sonucuna sızmamalıdır.

### 7.2 Performans ölçümü

Aşama 9'un amacı yeni bir Spatial algoritması geliştirmek değildir. Ölçüm, entity adapter maliyetini ve doğru indeks stratejisini doğrular:

- 100 / 1.000 / 10.000 entity aday kümeleri.
- Uniform ve clustered konum dağılımları.
- Index build, query median/p95, update, remove ve memory.
- Linear reference ile karşılaştırma.
- Test sahnesi küçükse linear yolun daha ucuz kalabileceği raporlanır; indeks zorunlu olarak her durumda açılmaz.

### 7.3 CI ve manuel kabul

- Laboratuvarın mevcut Linux ve Windows Core Quality workflow'ları başarılı olmalıdır.
- Tam pytest sonucu ve CI run bağlantıları rapora yazılır.
- Görsel kabulde player/NPC/resource ground anchor hizası, Y-sort, collider debug, mouse target selection, zoom invariance ve yoldaş komut durumları kontrol edilir.
- Kullanıcı manuel kabulini bildirmeden Aşama 9 kapatılmış sayılmaz.

## 8. Kabul kriterleri

Aşama 9 ancak aşağıdakilerin tümü sağlandığında teknik olarak tamamlanmış sayılır:

1. Player, NPC ve resource ortak EntityId/kind/location sözleşmesini kullanır.
2. Hareketli entity WorldPoint konumu hücre merkezine yuvarlanmaz.
3. Cell-anchored entity konumu Geometry dönüşümünden türetilir.
4. Entity, sprite foot-anchor ve collider birbirinden bağımsızdır; aynı ground anchor'da birleşir.
5. Entity ve Spatial query world/map kimliğini korur.
6. Map unload/remove stale index veya dangling companion relationship üretmez.
7. Interaction menzili kamera zoom/viewport değişiminden etkilenmez.
8. Mouse selection ve nearest target sorgusu deterministiktir.
9. Spatial index update/add/remove/map transfer sonrasında brute-force referansla tutarlıdır.
10. NPC oyuncuya yoldaş olarak recruit/dismiss edilebilir.
11. FOLLOW, WAIT ve RETURN komut durumları saklanır, doğrulanır ve test edilir.
12. WAIT komutu verildiği andaki NPC world position snapshot'ı saklanır.
13. Yoldaş komutları bu aşamada hareket üretmez; mevcut NPC konumu kendiliğinden değişmez.
14. Player/NPC/resource prototip sahnesi birlikte çalışır.
15. Unit, integration, regression ve architecture tests başarılıdır.
16. Linux ve Windows CI başarılıdır; benchmark ve görsel test kanıtı raporlanır.
17. Kullanıcı manuel görsel/işlevsel kabulini tamamlar.

## 9. Kapsam dışı ve sonraki aşama bağlantıları

Bu teknik plan genel planın kapsamını genişletmez. Aşağıdakiler Aşama 9 uygulamasına alınmayacaktır:

- NPC'nin periyodik/otonom hareketi, günlük rutinleri, algı ve karar verme.
- Yoldaşın gerçek FOLLOW/WAIT/RETURN hareket davranışı.
- Oyuncu hareketini takip eden yoldaş steering, hız eşleme, mesafe kontrolü ve catch-up.
- A*, Dijkstra veya başka pathfinding/navigation algoritması.
- Engellerin çevresinden dolaşma, kapı/geçit planlama ve formasyon hareketi.
- Yoldaş savaş, savunma, saldırı, görev, envanter, diyalog ve kaynak toplama aksiyonları.
- Kaynak toplama/üretim/ekonomi kuralları.
- Nihai NPC animasyonu, ses ve sanat paketi.
- Çevre sanatı, terrain texture ve dekorasyon.
- Pygame-Godot geçişi.
- main veya demo_eldoria dalında değişiklik.

Sonraki aşama tasarımına bırakılan doğal bağlantılar:
- NPC AI/schedule: NPC'nin kendi günlük davranış ve periyodik hareket kararları.
- Navigation/pathfinding: oyuncu ve yoldaşların engelleri dikkate alarak hedefe ulaşması.
- Companion behavior: FOLLOW/WAIT/RETURN komutlarının gerçek hareket davranışına çevrilmesi; catch-up ve formasyon.
- Interaction gameplay: konuşma, toplama, inceleme ve benzeri gerçek aksiyonların hedef seçimine bağlanması.

## 10. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| Entity katmanının World veya Geometry içine gömülmesi | Katman döngüsü ve test zorluğu | Ayrı entities paketi ve application coordinator |
| WorldPoint ile HexCoord'un tek konum gibi kullanılması | Sürekli hareket hassasiyetinin kaybı | WorldPoint authoritative; hex adresi türetilmiş |
| Sprite ve collider ölçülerinin birbirine bağlanması | Render değişikliğinin fizik davranışını bozması | Ground anchor ortak; sprite/collider ayrı |
| Spatial index'in stale kalması | Hedeflerin kaybolması veya yanlış map'ten gelmesi | Atomik update ve differential test |
| Yoldaş komutlarının erken hareket davranışına dönüşmesi | Aşama 9 kapsamının büyümesi | CompanionRoster yalnızca ilişki/komut state yönetir |
| Map unload/remove sırasında orphan ilişki | Bozuk companion referansları | Coordinator üzerinden lifecycle ve cascade test |
| Çok entity'li demo mevcut tek actor demosunu bozması | Önceki hareket/kamera kabulünün gerilemesi | Ayrı entity demo veya backward-compatible adaptasyon |
| Aşırı genel entity framework tasarımı | Gereksiz soyutlama ve bakım maliyeti | Yalnızca PLAYER/NPC/RESOURCE ortak gereksinimleri |

## 11. Uygulama öncesi karar kapıları

Teknik plan onaylandığında kodlamaya geçmeden önce şu noktalar yeniden doğrulanacaktır:

1. Lab branch HEAD ve hedef dosya SHA'ları.
2. Bu belgede listelenen kaynak dosyaların mevcut içerikleri ve public API'leri.
3. Testlerin gerçek package import sınırları.
4. Map unload/remove sırasında entity kayıtlarını retained/dormant tutma ve map remove'da cascade silme yaklaşımı.
5. Yoldaş recruit için aynı map zorunluluğu ve tek NPC-tek player ilişkisi.
6. WAIT komutunun WorldPoint snapshot semantiği.
7. Entity spatial bounds için body AABB / interaction radius seçimi.

Bu kapılarda genel planla çelişen bir bulgu çıkarsa uygulama durdurulur; önce teknik plan revize edilip yeniden onaya sunulur.

## 12. Onay ve uygulama sırası

1. Kullanıcı bu ayrıntılı teknik mimari planı inceler.
2. Kullanıcı onay verirse 9.1–9.9 uygulaması başlatılır.
3. Uygulama yalnızca experiment/hex-world-laboratory dalında yapılır.
4. Her write öncesi branch HEAD ve hedef dosya SHA doğrulanır; her write sonrası commit/HEAD kontrol edilir.
5. Otomatik test, CI, benchmark ve görsel test kanıtları raporlanır.
6. Kullanıcı manuel kabulini tamamlar.
7. Kullanıcı kabulinden sonra Aşama 9 kapanış raporu ve Master Plan güncellemesi yapılır.

**Sonuç:** Bu plan onaylanmadan Aşama 9 kodlaması başlamaz. Genel plandaki yoldaş kararı korunur: Aşama 9 yoldaş ilişkisini ve FOLLOW/WAIT/RETURN komut altyapısını kurar; gerçek takip ve hareket davranışını sonraki AI/navigasyon aşamaları uygular.
