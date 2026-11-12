# Eldoria — Aşama 4: Altıgen Hareket, Yol Bulma ve Harita Geçiş Runtime'ı

**Durum:** Aşama 4 tamamlandı. Linux Python 3.11 ve Windows Python 3.12 release-candidate doğrulamaları başarılıdır. Son kod commit'i: `a5d593e439bd88e558ad8540fbb90f9c3ca421df`. Her iki platformda da 1.310 test ve 222 subtest başarılıdır.  
**Dal:** `demo_eldoria`  
**Kapsam:** schema-v2 axial hex map'ler. Kare harita hareketi bu aşamada değiştirilmez.

## 1. Katman sözleşmesi

- `core.domain.spatial`: immutable `EntityPosition`, `MovementProfile`, `MovementRequest`, `MovementResult` ve hata nedenleri.
- `application.hex_movement_rules`: saf, yan etkisiz tek hücrelik hareket doğrulaması.
- `application.hex_occupancy`: map-scoped varlık yerleşimi, occupancy ve movement blocking.
- `application.hex_pathfinding`: deterministik A* yerel harita yolu.
- `application.hex_world_runtime`: oyuncu, NPC ve taşınabilir nesnelerin çalışma zamanı konumu.
- `application.hex_transition_service`: JSON'da tanımlanmış aktif çıkışın başka yerel haritaya uygulanması.

Eski `application.movement`, `world.movement` ve kare harita aktör akışı bağımsız kalır.

## 2. Hareket kuralları

Bir yerel hareket:
1. Kaynak map kimliğini ve kaynak hücrenin `valid_cells` içinde olduğunu doğrular.
2. Hedefin aynı map içinde ve `valid_cells` maskesinde olduğunu doğrular.
3. Hedefin tam bir axial komşu olduğunu doğrular.
4. Hareket profilinin izin verdiğini, hedef hücrenin engelli olmadığını ve arazi kısıtını denetler.
5. Başarısızlıkta kaynak konumunu değiştirmez.

Altı yönün tek doğruluk kaynağı `HexDirection` enum'udur. Sabit feet, hız, süre veya fiziksel mesafe kuralı eklenmez.

## 3. Occupancy ve çarpışma

`HexOccupant` iki bağımsız bayrak taşır:
- `blocks_movement`: A* aramasında hücreyi geçiş engeli yapar.
- `blocks_occupancy`: başka varlığın aynı hücreye yerleşmesini engeller.

Hareket profili `ignores_occupancy=True` olduğunda varlık occupancy engellerini
yok sayabilir; bu istisna arazi, valid_cells, engel ve komşuluk doğrulamasını
atlamaz. Varlık yine registry'de tutulur. A* yolunda her ara hücre ayrı bir
hareket hedefi olduğundan, movement veya occupancy bloklayan kayıtlar yol
hücresi olarak dışlanır.

Hareket ve harita geçişi önce hedefi doğrular, sonra occupancy kaydını ve entity konumunu tek uygulama adımında günceller. Başarısız işlemde kaynak konum ve occupancy kaydı korunur.

## 4. Yol bulma

`HexPathfinder.find_path` altı komşulu axial graph üzerinde A* kullanır. Heuristic, `HexCoord.distance_to` topolojik hex adımıdır. Yol:
- `valid_cells` dışına çıkmaz,
- engelli ve movement-blocking hücreleri atlar,
- MovementProfile arazi/engel kurallarını uygular,
- occupancy engellerini dikkate alır; `ignores_occupancy` profili bunları yok sayar,
- deterministik eşitlik sıralaması kullanır.

Dönüş değeri başlangıç ve hedef hücrelerini içeren immutable tuple'dır; yol yoksa `None` döner. Hareket runtime'ı otomatik olarak tüm yolu yürütmez; `move_toward` yalnızca ilk adımı uygular.

## 5. Varlık türleri

- **Oyuncu:** altı yönde komşu hücreye doğrudan hareket ve hedefe doğru ilk yol adımı.
- **NPC:** hedefe yaklaşma, tehditten uzaklaşma, belirlenmiş hücreler arasında devriye. Tüm hedefler ve adımlar map maskesi ve occupancy tarafından sınırlandırılır.
- **Taşınabilir nesne:** varsayılan olarak hareket edemez; açık bir `MovementProfile` verilirse aynı hareket/çarpışma kurallarını kullanır.

Bu API Pygame input veya görsel animasyon bağlamaz.

## 6. Haritalar arası geçiş

`HexMapTransitionService` yalnızca kaynak hücrede bulunan varlığın ilgili aktif `HexMapTransition` kaydını çalıştırır. Hedef harita ve hedef giriş hücreleri doğrulanır; dolu veya engelli giriş hücresi atlanarak ilk uygun hedef seçilir. Hiçbir hedef uygun değilse varlık kaynak haritada kalır.

Runtime'a `WorldMapDefinition` verildiğinde dünya yerleşimleri ve aktif geçişlerin Stage 3 doğrulamaları tekrar uygulanır. Aktif runtime geçişi için dünya topolojisi zorunludur. Geçiş kayıtlarının tek veri kaynağı yerel harita JSON'udur. Tek yönlü ve çift yönlü geçiş ayrımı korunur.

Demo içerik artık iki gerçek yerel haritadan oluşur: `hex_forest_demo` dünya axial koordinatı (0, 0), `hex_clearing_demo` (1, 0). İki haritanın giriş/çıkış hücreleri ve yönleri ters eşleşen aktif `bidirectional` kayıtlarla birbirine bağlanır.

## 7. Aşama 4 kabul testleri

- Altı axial yönde oyuncu hareketi.
- Maskenin dışına, engelli hücreye ve uygunsuz araziye hareketin reddi.
- Hareket izni olmayan veya pasif varlığın hareket edememesi.
- Aynı hücreye çarpışma ve başarısız harekette atomik konum koruması.
- Movement blocking ile occupancy blocking ayrımı.
- A* en kısa yol, alternatif koridor, engel, arazi, occupancy ve ulaşılamayan hedef testleri.
- NPC yaklaşma, kaçınma ve devriye davranışı.
- Taşınabilir nesnenin açık profil olmadan hareket edememesi.
- Aktif/pasif, eksik hedef, yanlış kaynak ve dolu giriş hücresi harita geçiş testleri.
- Mevcut kare harita testleri ve mimari sınır testlerinin değişmeden geçmesi.
- Linux Python 3.11 ve Windows Python 3.12 release-candidate doğrulaması.

## 8. Kapsam dışı

Renderer, kamera, Pygame input/animasyon, save schema/migration, kare haritaları axial'e dönüştürme, fiziksel feet/mesafe/hız, combat movement points ve Stage 5 kaynak/NPC simülasyon entegrasyonu bu aşamada yapılmaz.

## 9. Aşama 4 kapanış raporu

| Alt aşama | Sonuç |
|---|---|
| 4.1 — Ortak hareket domain sözleşmeleri ve saf kurallar | Tamamlandı |
| 4.2 — Altı yönlü axial komşuluk, hücre geçerliliği ve A* | Tamamlandı |
| 4.3 — Occupancy, çarpışma ve atomik konum güncellemesi | Tamamlandı |
| 4.4 — Oyuncu hareket runtime'ı | Tamamlandı |
| 4.5 — NPC yaklaşma, kaçınma, devriye ve sınır davranışları | Tamamlandı |
| 4.6 — Profil kontrollü taşınabilir nesne hareketi | Tamamlandı |
| 4.7 — Dünya topolojisine bağlı haritalar arası geçiş runtime'ı ve reciprocal demo içeriği | Tamamlandı |

Release-candidate workflow: [Linux ve Windows doğrulama sonucu](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43305169877).

Aşama 4 sonunda demo axial dünya iki gerçek yerel haritaya sahiptir. Orman ve açıklık haritaları aktif, karşılıklı ve ters hücre/yön eşleşmeli geçişlerle bağlanmıştır. Dokuz mevcut schema-v1 kare harita korunmuştur. Renderer, kamera, save migration, fiziksel feet/hız kuralları ve Stage 5 entegrasyonu kapsam dışında kalmıştır.
