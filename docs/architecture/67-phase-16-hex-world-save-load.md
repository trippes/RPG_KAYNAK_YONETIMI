# Aşama 16 — HexWorld Snapshot ve Save/Load Entegrasyonu

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **HEX WORLD SNAPSHOT, DIŞ SAVE ŞEMASI V3 VE GAMEAPPLICATION RESTORE TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**

## 1. Mimari sınır

HexWorldRuntime canlı map-local konum ve occupancy'nin tek sahibidir. Save snapshot yalnızca bu state'in serileştirilebilir kopyasıdır; ikinci bir runtime veya konum yöneticisi değildir.

Snapshot şunları saklar:
- canonical `WorldId`
- entity ID ve runtime kind (`player`, `npc`, `object`)
- `map_id` ve axial `q/r`
- MovementProfile
- entity active durumu
- occupancy `blocks_movement` ve `blocks_occupancy` bayrakları
- NPC patrol index değerleri

Map definition, world-map layout, statik collision geometry, kamera ve renderer state'i save içine kopyalanmaz. Bunlar aktif content package'den yeniden yüklenir veya türetilir.

## 2. Yeni snapshot sözleşmesi

Yeni `application/hex_world_persistence.py`:

- `rpg-hex-world` schema, version 1.
- Immutable `HexWorldEntityRecord` ve `HexWorldSnapshot`.
- Strict JSON alan/koordinat/profile doğrulaması; q/r için bool veya float kabul edilmez.
- Duplicate entity ve patrol kayıtları reddedilir.
- Patrol progress yalnızca snapshot içindeki NPC entity'lerine bağlanabilir.
- Unscoped runtime snapshot alınamaz.
- Runtime entity/occupancy registry tutarsızsa snapshot alınamaz.
- Restore yalnızca aynı WorldId'ye bağlı ve boş runtime'a yapılabilir.
- Map maskesi, blocked-cell ve occupancy kuralları restore öncesi/işlem sırasında doğrulanır.
- Restore işlemi bir kayıt başarısız olursa daha önce eklenen entity'leri geri alır; yarım runtime bırakmaz.

`HexWorldRuntime` artık patrol progress'i salt okunur sunar ve restore sırasında kontrollü biçimde geri alabilir.

## 3. Domain owner doğrulaması

`HexWorldSnapshot.validate_domain_owners` restore ve save öncesi her spatial ID'nin gerçek domain sahibi olduğunu doğrular:

- `player` → aynı world'e bağlı `WorldActorRegistry` kaydı.
- `npc` → aynı world'e bağlı actor kaydı ve `NPCRegistry` kaydı.
- `object` → aynı world'e ait `WorldResourceNodeManager` kaydı veya world membership'i doğrulanmış bir container Core entity.

Container için ek olarak:
- canonical world membership `WorldMembershipService.world_id_for(entity_id)` üzerinden doğrulanır.
- inventory custody veya nested parent ilişkisi varsa world placement reddedilir.
- Eski Core `Position(x,y)` alanı okunmaz veya axial koordinata dönüştürülmez.

Bilinmeyen spatial object, başka world'e ait actor/resource/container veya domain sahibi bulunmayan entity save/load sınırından geçemez.

## 4. Dış save schema v3

`GameSaveDocument` schema sürümü 2'den 3'e yükseltildi.

- Yeni `hex_world` alanı opsiyoneldir.
- İçerik `rpg-hex-world` v1 snapshot'ıdır.
- v2 save migration yalnızca `hex_world: null` ekler.
- v0/v1 migration zinciri v3'e ulaşır.
- Eski save'lerdeki kare koordinatlar dönüştürülmez.
- Hex runtime hiç başlatılmamışsa save'de `hex_world` bölümü bulunmaz; mevcut save akışı korunur.

`docs/architecture/24-unified-persistence.md` schema v3 ve restore sırasını yansıtacak şekilde güncellendi.

## 5. GameApplication entegrasyonu

### Save

- Runtime mevcutsa active Core world ile runtime WorldId eşleşmesi zorunludur.
- Snapshot alınır ve domain-owner validation çalıştırılır.
- Yalnızca doğrulamadan sonra `GameSaveDocument` oluşturulur ve atomik save adapter'ına verilir.

### Load

- Yeni candidate SessionBundle ve Core session restore edilir.
- Gameplay, NPC, actor, resource node ve container domain kayıtları candidate üzerinde hazırlanır.
- Hex snapshot varsa aktif content package axial map definitions sağlamalıdır.
- Snapshot WorldId ve domain owner kayıtları doğrulanır.
- Candidate için yeni `HexWorldRuntime` oluşturulur ve snapshot atomik biçimde geri yüklenir.
- Her şey başarılı olduktan sonra candidate `SessionHolder.publish` ile yayımlanır.

Herhangi bir hata önceki aktif bundle/runtime'ı değiştirmez. Hex snapshot bulunan save, map definitions içermeyen content package ile yüklenmez; eski kare harita verisinden otomatik map üretilmez.

## 6. Container sınırı

Container için ayrı bir mutable position owner oluşturulmadı. HexWorldSnapshot, yalnızca mevcut Core world membership'i bulunan, inventory custody ve nested parent ilişkisi olmayan container entity'lerinin runtime spatial kaydını koruyabilir.

Container için içerik/placement üretimi, fiziksel footprint ve blocking flags sağlayan bir placement adapter henüz eklenmedi. `ContainerSnapshot.placements` legacy listesi boş kalır; dolu legacy placement listeleri mevcut load sınırında reddedilir.

## 7. Test ve CI doğrulaması

- Doğrulanan kod commit'i: `2dc6b3cebb15cff07fa6e46a2fd484de7b8560c0`
- GitHub Actions: [#44518854227](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44518854227)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.213 test + 235 subtest başarılı**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

Testler snapshot JSON round-trip, axial coordinate strictness, domain owner doğrulaması, world mismatch, blocked/mask cells, occupancy rollback, patrol progress, GameApplication save/load ve başarısız load'da candidate publication'ın yapılmamasını kapsar.

## 8. Sonraki teknik kapı

Container placement adapter'ı; typed axial placement record, tek hücre/çok hücre footprint kararı, zorunlu blocking metadata ve custody transition'larıyla tasarlanacaktır. Bundan sonra save/load içinde world-placed container ile carried/nested container ayrımı uçtan uca test edilecektir. Bu kararlar tamamlanmadan container konumu veya footprint varsayımı üretilmeyecektir.
