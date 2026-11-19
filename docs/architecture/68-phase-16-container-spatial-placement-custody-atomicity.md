# Aşama 16 — Container Spatial Placement ve Custody Atomicity

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **CONTAINER HEX PLACEMENT VE CUSTODY GEÇİŞLERİ TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki sözleşme: [HexWorld Snapshot ve Save/Load Entegrasyonu](67-phase-16-hex-world-save-load.md)

## 1. Amaç ve tekil sahiplik

Container domain state'i `ContainerManager` içinde kalır:

- Container capability, contents inventory, nesting ve inventory custody: `ContainerManager`.
- Core entity kimliği ve dünya üyeliği: Core entity registry ve `WorldMembershipService`.
- World-placed container'ın axial map-local position ve occupancy kaydı: `HexWorldRuntime` / `HexOccupancyRegistry`.
- İşlemler arası koordinasyon: `ContainerHexBindingService`, GameplayService üzerinden sunulur.

Container'ın eski Core `Position(x,y)` alanı okunmaz veya axial koordinata çevrilmez. Container için ikinci bir identity, position veya occupancy owner oluşturulmaz.

## 2. Spatial binding sözleşmesi

Yeni `application/container_hex_binding.py` / `ContainerHexBindingService`:

- World placement yalnızca canonical world membership'i doğrulanmış container entity'leri için yapılır.
- Nested veya inventory custody sahibi container'ın world placement alması reddedilir.
- Spatial kayıt, mevcut Core entity ID'sini aynen kullanır.
- Placement açık `EntityPosition(map_id, LocalHexPosition(q,r))` ve çağıranın sağladığı `blocks_movement` / `blocks_occupancy` değerlerini gerektirir.
- Eski kare konumdan varsayılan axial koordinat, footprint veya blocking davranışı türetilmez.
- Runtime occupancy kaydı eksik ama entity kaydı mevcutsa sessizce onarılmaz; invariant hatası yükseltilir.

## 3. Atomic custody geçişleri

Dört yönlü geçiş uygulandı:

1. World → inventory: spatial entity ve occupancy kaldırılır, sonra inventory custody atanır.
2. World → nested: child'ın spatial kaydı kaldırılır, sonra parent-child ilişkisi kurulur.
3. Inventory → world: custody kaldırılır, açık axial placement ve occupancy kaydı kurulur.
4. Nested → world: parent-child ilişkisi kaldırılır, açık axial placement ve occupancy kaydı kurulur.

Her geçişte session validation ve runtime/domain işlemleri başarısız olursa önceki custody veya spatial state geri yüklenir. Restore edilen world placement, önceki konum, movement profile, active state ve occupancy blocking flags değerlerini korur. Başarısız bir yeni placement girişimi, önceden var olan bir runtime entity kaydını yanlışlıkla silmez.

Hex runtime henüz başlatılmamış eski oturumlarda carry/nest işlemleri mevcut domain davranışını korur; bu yolda olmayan bir Hex konumu üretilmez. Hex runtime yokken world placement talebi açık hata verir.

## 4. GameplayService API

Aşağıdaki işlemler uygulama sınırından sunulur:

- `carry_container`
- `contain_container`
- `transfer_container_custody`
- `place_container_from_inventory`
- `release_nested_container`

Repository taramasında doğrudan `ContainerManager` custody/nesting mutasyonlarının uygulama katmanındaki tek gameplay giriş noktası `GameplayService` olarak doğrulandı; diğer çağrılar binding'in kendi koordinasyon işlemleri veya persistence/domain testleridir. Inventory-to-inventory custody transferi spatial state üretmez; source custody başarısızlıkta geri yüklenir.

## 5. Save/load uyumu

Container custody ve nesting ilişkileri mevcut `ContainerSnapshot` tarafından saklanmaya devam eder. World-placed container konumu, movement profile ve occupancy flags ise `HexWorldSnapshot` içinde saklanır.

Restore sırasında domain-owner validation, carried veya nested container'ın aynı zamanda world placement kaydı taşımasını reddeder. Container placement için ayrı bir mutable position veya ikinci bir save owner eklenmemiştir. Eski `ContainerSnapshot.placements` kayıtları ve kare koordinatları axial konuma dönüştürülmez.

## 6. Test kapsamı

Yeni/ilgili testler şunları kapsar:

- World-placed container'ın carry/nest öncesi occupancy'den kaldırılması.
- Carry ve nesting validation başarısızlığında eski spatial konumun, profile'ın ve blocking flags'in geri yüklenmesi.
- Inventory'den world'e bırakma ve nested container'ı world'e çıkarma.
- İki ters geçişin validation hatasında custody ilişkisini geri yüklemesi.
- GameplayService üzerinden carry → drop ve nest → release akışları.
- Hex runtime başlatılmadan önceki container domain işlemlerinin geriye dönük uyumluluğu.
- World membership, runtime world ve map maskesi doğrulamaları.

## 7. CI doğrulaması

- Doğrulanan HEAD: `8e6cad4d7f4f352c4b8d5913799292eef98415b2`
- GitHub Actions: [#44526817086](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44526817086)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.233 test + 235 subtest başarılı**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 8. Sonraki teknik kapı

Container placement/custody köprüsü tamamlandı. Aşama 16'nın kalan büyük entegrasyon kapıları; axial gameplay placement/content kataloglarının NPC, resource, market ve container kimliklerine bağlanması; ana oyun içerik yükleyicisi ve başlangıç akışının HexWorldRuntime'a geçirilmesi; renderer/input yaşam döngüsünün ana oyun akışına alınması; eski kare harita runtime ve bağımlılıklarının kontrollü temizliğidir.

Bu aşamalar sırasında laboratuvar dalı salt kaynak olarak kalır. Laboratuvar demo haritaları, launcher, senaryolar veya örnek içerik ana oyuna taşınmaz. Kullanıcı tarafından onaylanmamış axial koordinatlar üretilmez; kare kayıtlar sessizce dönüştürülmez.
