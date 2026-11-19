# Aşama 16 — İçerik Tabanlı Hex World Başlangıcı

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **EXPLICIT WORLD INITIALIZER VE PYGAME STARTUP BAĞLANTISI TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilim: [Ana Oyun Hex Gameplay View](70-phase-16-main-hex-gameplay-view.md)

## 1. Runtime başlangıç sözleşmesi

Yeni `application/hex_world_initializer.py` mevcut content package üzerinden session-scoped `HexWorldRuntime` başlatır.

Başlangıç için zorunlu veri:
- En az bir schema-v2 axial `HexMapDefinition`.
- Birden fazla map varsa `WorldMapDefinition`.
- `starter_content.json` içindeki açık `world.hex_start = {map_id, q, r}`.
- Aktif Core world ve oluşturulmuş canonical player actor.

Başlangıç hücresi map'in `valid_cells` maskesinde doğrulanır. q/r strict integer'dır. Başlangıç verisi yoksa veya geçersizse runtime kurulmaz. Package'ta axial map yoksa initializer `None` döndürür ve mevcut mapless hazırlık ekranı korunur.

## 2. Session ownership ve rollback

Runtime, `SessionBundle.hex_world_runtime_owner` üzerinden tek örnek olarak oluşturulur. Runtime'ın WorldId'si aktif Core world ile eşleştirilir. Var olan runtime kullanılırken map ID seti, map definitions ve world topology aktif package ile karşılaştırılır; farklı content ile sessizce devam edilmez.

Oyuncu, mevcut `player_actor_id` kullanılarak `ActorHexBindingService` üzerinden başlangıç hücresine kaydedilir. NPC/resource/container placement catalog daha sonra `GameplayService.register_gameplay_placements` üzerinden uygulanır.

Başlatma başarısız olursa yeni eklenen spatial kayıtlar geri alınır. İlk kez oluşturulan runtime boş kaldıysa `HexWorldRuntimeOwner.discard_if_empty` ile session owner'dan kaldırılır. Önceden var olan runtime veya başka entity kayıtları silinmez.

## 3. Ana oyun akışına bağlantı

Character creation tamamlandıktan sonra GameWindow:
1. Gameplay content setup'ını çalıştırır.
2. Player inventory'yi ilk sıradaki actor varsayımıyla değil, canonical `player_actor_id` ile bağlar.
3. `initialize_hex_world` çağırır.
4. Başlatma verisi yoksa veya doğrulama başarısızsa kullanıcıya açık notice gösterir; eski kare haritaya dönmez.

Save load yolunda runtime yeniden oluşturulmaz; mevcut save restore edilen session runtime'ını kullanır.

## 4. Resource node content population

`populate_gameplay_resources`, package `resources.json` kayıtlarından `WorldResourceNode` domain kayıtlarını da oluşturur. Node identity, resource type, quantities, regeneration rate ve gathering duration mevcut resource domain manager'ında kalır. Spatial binding daha sonra aynı node ID'sini HexWorldRuntime'a bağlar.

Aynı setup tekrar çağrılırsa uyumlu mevcut node tekrar eklenmez. Başka world'e ait veya package configuration ile çelişen mevcut node sessizce değiştirilmez; hata yükseltilir. Mevcut node quantity değeri yeniden başlangıç miktarına sıfırlanmaz.

## 5. Veri güvenliği ve kapsam

- Mevcut `demo_eldoria` package'ına harita veya başlangıç koordinatı eklenmedi.
- Kullanıcı tarafından onaylanmamış q/r koordinatı üretilmedi.
- Kare `width/height` alanları axial koordinat olarak yorumlanmadı.
- Lab demo map ve senaryoları ana oyuna taşınmadı.
- Runtime başlangıcı yalnızca package açıkça map ve `hex_start` sağladığında gerçekleşir.

Bu nedenle teknik başlangıç hattı hazırdır; varsayılan demo package hâlâ mapless'tir ve yeni dünya içeriği tasarlanıp eklenene kadar oyun alanı hazırlık ekranında kalır.

## 6. Test kapsamı

- Mapless package runtime oluşturmadan çıkar.
- Axial map varken `hex_start` zorunludur.
- Başlangıç hücresi map maskesinde doğrulanır.
- Geçerli start ile session runtime ve player spatial kaydı kurulur.
- Player binding başarısızlığında boş runtime owner'dan kaldırılır.
- Runtime owner yalnızca boş runtime'ı discard eder; entity içeren runtime'ı reddeder.
- Resource node content setup oluşturur ve tekrarlı setup'ta quantity/state'i sıfırlamaz.
- GameWindow player inventory binding'i canonical player ID kullanır.

## 7. CI doğrulaması

- Doğrulanan HEAD: `800893ca3dc06a054cbc5a150a56aa0a683b3453`
- GitHub Actions: [#44529788834](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44529788834)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.257 test + 235 subtest başarılı**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 8. Sonraki teknik kapı

Sıradaki iş, map transition ve world navigation akışının ana oyun view'ına bağlanması; ardından NPC/resource etkileşimi, click-to-move/pathfinding ve presentation asset/depth pipeline entegrasyonudur.

Canlı dünya içeriği hâlâ eksiktir: yeni axial map dosyaları, world-map topology, player start, NPC/resource/container placements ve görsel asset/placement kayıtları. Bunlar eklenmeden gerçek dünya akışı manuel kabul edilemez.
