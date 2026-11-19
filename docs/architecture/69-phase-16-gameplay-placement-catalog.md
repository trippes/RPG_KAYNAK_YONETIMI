# Aşama 16 — Axial Gameplay Placement Catalog ve İçerik Bağlantısı

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **TYPED GAMEPLAY PLACEMENT CATALOG VE GAMEPLAYSERVICE BAĞLANTISI TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilimler:
- [HexWorld Snapshot ve Save/Load Entegrasyonu](67-phase-16-hex-world-save-load.md)
- [Container Spatial Placement ve Custody Atomicity](68-phase-16-container-spatial-placement-custody-atomicity.md)

## 1. Presentation placement ile gameplay placement ayrımı

Mevcut `ScenePlacementCatalog` yalnızca görsel sahne nesnelerini yönetir: asset ID, render layer, pixel offset, visual footprint ve collision-box metadata. Bu katalog gameplay actor/resource/container kimliğinin veya occupancy'nin sahibi değildir.

Yeni `application/gameplay_placement_catalog.py` ayrı ve typed bir gameplay placement sözleşmesi sağlar. İki katalog birbirinin yerine kullanılamaz ve aynı entity için iki position owner oluşturmaz.

## 2. Yeni schema

Content package manifest'ine opsiyonel `gameplay_placements` dizin alanı eklendi. Dizin içindeki her JSON dosyası tek bir bilinen axial map'e aittir:

- `schema_version: 1`
- `map_id`
- `placements[]`

Her placement açıkça şunları taşır:
- `domain_id`: NPC ID, resource-node ID veya container ID.
- `kind`: `npc`, `resource_node` veya `container`.
- `q`, `r`: strict integer axial koordinat.
- `blocks_movement`, `blocks_occupancy`: zorunlu boolean davranış metadata'sı.

Catalog yükleyicisi bilinmeyen alanları, eksik alanları, duplicate domain ID'leri, bilinmeyen map ID'lerini, map maskesi dışındaki hücreleri ve hatalı koordinatları reddeder. Resource node placement'ları mevcut resource binding sözleşmesiyle uyumlu olarak non-blocking olmak zorundadır.

Package loader ayrıca NPC placement ID'lerini `npcs.json`, resource placement ID'lerini `resources.json` kayıtlarıyla eşleştirir. Container ID'si runtime'da `ContainerManager` üzerinden çözümlenir; Core entity ID ve world membership kontrolü container binding tarafından yapılır.

## 3. GameplayService composition

Yeni `GameplayService.register_gameplay_placements(catalog)`:

- NPC kayıtlarını `NPCSpatialBindingService` üzerinden,
- Resource node kayıtlarını `ResourceNodeHexBindingService` üzerinden,
- Container kayıtlarını `ContainerHexBindingService` üzerinden

mevcut canonical domain owner'lara bağlar. Konum yalnızca `HexWorldRuntime` içinde tutulur.

Katalog uygulaması tek batch işlemidir. Bir kayıt veya son session validation başarısız olursa bu çağrıda eklenmiş spatial kayıtlar ters sırada kaldırılır; önceden var olan runtime kayıtlarına dokunulmaz. Dönen sonuçlar canonical `HexMovableEntity` görünümleridir.

Yeni `populate_gameplay_placements(service, content_package_path=...)` composition helper'ı, domain owner'lar ve Hex runtime hazırlandıktan sonra package kataloğunu uygulama servisine aktarır. Manifest'te gameplay placement kaydı yoksa boş tuple döner; yeni harita, koordinat veya runtime uydurulmaz.

## 4. İçerik ve veri güvenliği

- Mevcut `demo_eldoria` package manifest'ine yeni gameplay placement directory eklenmedi; package'ta henüz axial maps ve onaylı gameplay placement kayıtları yoktur.
- NPC/resource mevcut içerik tanımları değiştirilmedi.
- Eski kare koordinatlar axial koordinatlara dönüştürülmedi.
- Gameplay placement metadata'sı presentation asset/scene placement dosyalarına yazılmadı.
- Laboratuvar demo haritaları, launcher ve senaryo içerikleri taşınmadı.
- Yeni catalog yalnızca açıkça manifest'te tanımlanırsa yüklenir.

Bu nedenle altyapı hazırdır; gerçek oyun dünyasının NPC/resource/container konumları, kullanıcı tarafından yeni axial haritalar ve başlangıç yerleşimleri tasarlandığında doldurulacaktır.

## 5. Test kapsamı

- Gameplay placement JSON schema ve immutable catalog construction.
- Duplicate domain ID reddi.
- NPC ve resource owner referans doğrulaması.
- Bilinmeyen map ve map maskesi dışı hücre reddi.
- Strict integer q/r ve zorunlu blocking flags.
- Resource node non-blocking kuralı.
- GameplayService üzerinden container placement kayıtlarının uygulanması.
- Batch registration hatasında önceki eklemelerin rollback edilmesi.
- Hex runtime yokken placement uygulamasının reddedilmesi.
- Mevcut boş demo package'ın gameplay placement olmadan yüklenmeye devam etmesi.

## 6. CI doğrulaması

- Doğrulanan HEAD: `8e22621d2f1c08d7fa3b1bb33fdbce164824feff`
- GitHub Actions: [#44528157264](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44528157264)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.243 test + 235 subtest başarılı**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 7. Sonraki teknik kapı

Gameplay placement verisi artık package → catalog → GameplayService → mevcut spatial binding akışına bağlanabilir.

Sıradaki iş, **ana oyun Hex gameplay view** katmanını mevcut Pygame renderer, `WorldTransform`, `HexCamera`, `HexTerrainRenderer`, `HexCharacterRenderer` ve `HexWorldRuntime` ile birleştirmektir. Bu view eski kare runtime'ı geri getirmeyecek; simülasyon konumunu yalnızca HexWorldRuntime'dan okuyacak.

Gerçek oyun alanını açmak için yeni axial map dosyaları, world-map yerleşimi ve oyuncu başlangıç hücresi hâlâ gereklidir. Bunlar tasarlanmadan herhangi bir map veya q/r koordinatı üretmek yasaktır. Ana oyun ekranı, gerekli package verisi yokken açık bir hazırlık durumu gösterebilir; sahte harita veya gizli demo içeriği kullanamaz.
