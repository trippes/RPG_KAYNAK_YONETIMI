# Aşama 16 — Gameplay Interaction ve Physics Wiring Denetimi

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **DENETİM TAMAMLANDI; İKİ OYUN TASARIMI / CONTENT SÖZLEŞMESİ KAPISI AÇIK**

## 1. Amaç

Hex runtime, axial placement catalog, actor/NPC/resource/container binding, market anchor, persistence, Pygame gameplay view ve pathfinding entegrasyonundan sonra kalan canlı oyun bağlantılarını denetlemek. Bu rapor, altyapı adaptörlerinin varlığını oyuncunun etkileşim akışlarının tamamlandığı şeklinde yorumlamaz.

## 2. Physics bridge — mevcut durum

Aşağıdaki altyapı mevcuttur:

- `HexPhysicsSnapshot`, canonical `HexMapDefinition` üzerinden statik collision geometry üretir.
- `ActorHexBindingService.move_with_physics` ve `move_to_with_physics`, logical/occupancy preflight sonrasında physics doğrulaması yapıp başarılıysa mevcut runtime konumunu commit eder.
- Physics reddinde actor konumu ve occupancy değişmez.
- Snapshot world/map kapsamı ve pointy-top geometry doğrulanır.

Ancak normal Pygame gameplay input akışında bu API henüz kullanılmıyor:

- `HexGameplayView` manuel hareket için `hex_actor_binding.move`, click-to-move için `move_toward` çağırıyor.
- `build_hex_physics_snapshot`, `move_with_physics` ve `move_to_with_physics` için uygulama/gameplay UI çağrı noktası bulunmuyor.
- `GameplayPlacementCatalog` şu an `blocks_movement` ve `blocks_occupancy` alanlarını taşıyor; fiziksel collider şekli/ölçüsü sağlamıyor.
- `BodyDefinition` çağıran katmandan zorunlu olarak isteniyor. Oyuncu veya NPC için canonical body ölçüsü ve şekli tanımlı değil.
- A* pathfinder mantıksal map maskesi, terrain kuralları ve occupancy üzerinden rota üretiyor; statik obstacle snapshot'ına göre edge/path doğrulaması yapmıyor.

### Güvenlik kararı

Bir oyuncu collider yarıçapı, NPC gövde ölçüsü, landmark footprint'i veya collision-box dönüşümü varsayılmayacaktır. Bunlar görsel sprite ölçüsünden türetilmeyecek; presentation footprint fizik gövdesi yerine geçirilmeyecektir.

Physics gameplay bağlantısının tamamlanması için:
1. Actor türü veya content definition düzeyinde typed `BodyDefinition` kaynağı,
2. World object/landmark için açık fiziksel obstacle shape ve transform sözleşmesi,
3. Map başına snapshot lifecycle/cache invalidation kuralı,
4. A* edge validation ile aynı physics kurallarının tutarlı kullanılması

tasarlanıp test edilmelidir.

## 3. NPC ve resource interaction — mevcut durum

Domain/application API'leri korunmuştur:

- `GameplayService.talk_to_npc` mevcut dialogue, actor ve quest mekanizmalarını çalıştırır.
- `GameplayService.start_gathering` mevcut resource activity ve quest progression akışını çalıştırır.
- `NPCSpatialBindingService` ve `ResourceNodeHexBindingService` canonical domain ID'lerini HexWorldRuntime spatial kayıtlarına bağlar.
- Market konumu bağlı NPC'nin güncel spatial position değerinden türetilir.

Bununla birlikte ana Hex gameplay view yalnızca hareket, harita geçişi, zoom ve click-to-move hedefi yönetir. Şu anda:
- Sol tıkla NPC'nin bulunduğu axial hücre seçilir; MainScreen seçilen canonical NPC ID'sini GameWindow'a aktararak mevcut DialogueScreen akışını açar.
- Sağ tıkla aynı NPC ID'sine bağlı, henüz eylem maddesi içermeyen bağlamsal menü kabuğu açılır. Menü içeriği NPC türü/özelliklerine göre daha sonra tanımlanacaktır.
- `InputMapper` içinde gather action (`G`) bulunmasına rağmen HexGameplayView bu aksiyonu kullanmıyor.
- Resource node seçimi, gathering quantity ve etkileşim mesafesi için Hex gameplay UI sözleşmesi bulunmuyor.

### Güvenlik kararı

Yeni NPC etkileşim mesafesi, otomatik yakın NPC seçimi, gather miktarı veya yeni tuş davranışı varsayılmayacaktır. Bunlar kullanıcı tarafından tanımlanması gereken oyun kurallarıdır. Var olan domain servisleri değiştirilmeden kalır; bu rapor yeni demo NPC/resource içeriği veya koordinatı üretmez.

Açık kalan kararlar:
1. Dialogue için aynı hücre, komşu hücre veya farklı bir erişim mesafesi mi geçerli olacak?
2. Resource gathering hedefi nasıl seçilecek ve etkileşim mesafesi ne olacak?
3. G tuşu varsayılan miktar mı başlatacak, miktar penceresi mi açacak, yoksa yalnızca seçili node için mi çalışacak?

## 4. Tamamlanmış entegrasyon ile açık kapıların ayrımı

Tamamlanan ve CI ile doğrulanan altyapı:
- Canonical actor/world identity ve axial spatial ownership.
- Physics snapshot/ön doğrulama API'si (normal player input akışına henüz bağlı değil).
- NPC/resource/container spatial binding.
- Market NPC anchor.
- Container custody geçişlerinde spatial rollback.
- Gameplay placement catalog ve batch registration.
- Hex save/load ve domain owner doğrulaması.
- İçerik tabanlı runtime başlangıcı.
- Ana Pygame Hex view, authored map transition, A* pathfinding ve click-to-move.

Açık kalan oyuncu deneyimi/content kapıları:
- Typed actor body ve statik obstacle metadata'sı ile physics'in gerçek gameplay hareketine bağlanması.
- NPC dialogue seçimi/etkileşim UI'si.
- Resource node seçimi ve gathering UI'si.
- Varsayılan demo package'a yeni axial map, world topology, açık player start ve yeni onaylı gameplay placements eklenmesi.
- Yeni dünya içeriği eklendikten sonra gerçek oyun akışının manuel kabulü.

## 5. Kapsam koruması

- `experiment/hex-world-laboratory` salt kaynak/arşiv dalı olarak kalır.
- `main` ve `demo_eldoria` değiştirilmez.
- Lab demo haritaları, launcher, senaryolar ve demo NPC/resource kayıtları ana oyuna taşınmaz.
- Eski kare koordinatlar axial konum olarak kullanılmaz.
- Varsayımsal body size, interaction range, gather quantity veya başlangıç koordinatı üretilmez.

## 6. Sonuç

Aşama 16'nın mimari ve otomatik doğrulama entegrasyonunda büyük bölümü tamamlanmıştır; ancak normal gameplay physics ve NPC/resource etkileşimleri için gerekli açık sözleşmeler henüz yoktur. Bu iki alan ve yeni axial dünya içeriği tamamlanmadan **“oyuncu açısından tam entegre ve oynanabilir”** kabulü verilmeyecektir.

Önce typed physics/body sözleşmesi ile NPC/resource interaction modelinin tasarım kapıları kapatılmalı; ardından implementation ve Linux/Windows CI doğrulaması yapılmalıdır.
