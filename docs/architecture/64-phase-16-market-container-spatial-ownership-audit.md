# Aşama 16 — Market ve Container Spatial Ownership Denetimi

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **TEKNİK DENETİM TAMAMLANDI; MARKET İÇİN NPC ANKORU UYGUN, CONTAINER İÇİN YERLEŞİM SÖZLEŞMESİ BEKLİYOR**  
Önceki dilim: [NPC ve Resource Node Spatial Binding](63-phase-16-npc-resource-spatial-binding.md)

## 1. Market denetimi

### Mevcut domain sözleşmesi

`economy.MarketProfile` şu alanları taşır:

- `market_id`
- `location_id`
- `npc_id`
- `merchant_id`
- `inventory_id`
- stok yenileme ve katalog verileri

`EconomySnapshot` bu alanların tamamını save/load içinde korur. `GameplayService.register_market_profile` mevcut profil karşılaştırmasında `location_id` değerini de kullanır. Ancak market profili kendi axial konumunu veya koordinatını taşımaz.

Market, NPC kimliğiyle zaten ilişkilidir. Bu nedenle market için ikinci bir HexWorldRuntime entity/position kaydı oluşturmak gereksizdir. Market'in mekânsal ankrajı, `MarketProfile.npc_id` üzerinden NPC'nin mevcut Hex spatial entity konumundan türetilebilir.

### Karar

- Market kimliği ve ekonomik state `Economy/Market` içinde kalır.
- Market spatial ankrajı bağlı NPC'nin HexWorldRuntime konumudur.
- `MarketProfile.location_id` mevcut save uyumluluğu için bu aşamada değiştirilmez; axial map ID veya koordinat olarak yorumlanmaz.
- Market için ikinci position veya occupancy kaydı oluşturulmaz.
- Market alışverişinin hex komşuluk/etkileşim mesafesi henüz tanımlı değildir. Mesafe kuralı uydurulmayacak; bu denetim yalnızca mekânsal ankrajı tanımlar.

## 2. Container denetimi

### Mevcut domain sözleşmesi

- `ContainerInstance`, `container_id`, `entity_id` ve `definition_id` taşır.
- `ContainerManager`, nested-container ilişkisini ve inventory custody durumunu ayrı ayrı yönetir.
- `ContainerManager.for_entity(entity_id)`, Core entity ile container capability ilişkisini çözer.
- `SessionBundle`, container entity ID'sinin Core entity registry içinde bulunduğunu ve entity türünün `ESYA` olduğunu doğrular.
- Core entity'nin eski `Position(x,y)` alanı vardır. Bu değer axial koordinat değildir ve HexWorldRuntime konumuna dönüştürülmeyecektir.
- Canonical Core world membership sahibi `WorldMembershipService`'tir. Gelecekte world scope doğrulaması `membership.world_id_for(entity_id)` üzerinden yapılmalıdır; `Entity.world_id` yalnızca eski uyumluluk projeksiyonudur.

### Nested/carried ayrımı

Bir container'ın Hex dünya üzerinde bulunması, yalnızca container capability kaydının bulunmasıyla kanıtlanamaz:

- `ContainerManager.inventory_custody(container_id)` doluysa container bir actor/NPC inventory'sinde taşınıyordur; world placement alamaz.
- `ContainerManager.parent_of(container_id)` doluysa container başka bir container içindedir; ayrıca world placement alamaz.
- Yalnızca bu iki custody ilişkisinin dışında kalan ve Core `WorldMembershipService` içinde aktif dünya üyeliği bulunan container, açık bir world placement kaydıyla haritaya yerleştirilebilir.
- Bu placement için map ID ve axial hücre koordinatı içerik verisinden gelmelidir. Eski Core `Position(x,y)` kullanılmaz.

### Persistence bulgusu

`ContainerSnapshot` şemasında `placements` alanı bulunur. `from_runtime` şu anda bu alanı boş liste üretir. `restore` placement kayıtlarını geri döndürür; `GameApplication.load` ise dolu placement listesi içeren eski kayıtları açıkça reddeder ve kare→hex dönüşümü yapmaz.

Mevcut snapshot doğrulaması placement kayıtlarında benzersiz `object_id`, bilinen container entity referansı ve nested/carried container yasağını denetler. Henüz zorunlu axial alanlar, world ID, map maskesi veya footprint/çarpışma sözleşmesi tanımlı değildir.

### Karar

Bu aşamada ContainerHexBindingService yazılmayacaktır. Önce aşağıdaki açık sözleşme hazırlanmalıdır:

1. World-placed container için typed axial placement record.
2. `entity_id` ile container capability'nin birebir eşleşmesi.
3. `WorldMembershipService` üzerinden world scope doğrulaması.
4. Inventory-held veya nested container için placement yasağı.
5. Map maskesi ve occupancy doğrulaması.
6. Container definition veya placement metadata üzerinden açık fiziksel footprint ve blocking flags.
7. Save/load round-trip ve eski kare placement reddi testleri.

Fiziksel footprint ve blocking davranışı container türü başına tanımlanmadan varsayılan olarak bloklayıcı veya bloklamayan davranış seçilmeyecektir.

## 3. Sonuç ve uygulama sırası

| Sistem | Mekânsal karar | Uygulama durumu |
|---|---|---|
| NPC | NPC'nin kendi axial runtime konumu | Adapter tamamlandı |
| Resource node | Sabit, non-blocking spatial object | Adapter tamamlandı |
| Market | Bağlı NPC'nin konumundan türetilen anchor | Sonraki küçük adapter dilimi |
| Container | Yalnızca world-placed ise ayrı axial placement | Typed placement ve persistence sözleşmesi bekliyor |

Bu denetim hiçbir NPC, market veya container için koordinat üretmez. Mevcut kare `location_id` ve `Position(x,y)` verileri axial koordinata dönüştürülmez.
