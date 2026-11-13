# Eldoria — Aşama 8.1 İçerik Altyapısı Teknik Denetimi

| Alan | Değer |
|---|---|
| Depo | `trippes/RPG_KAYNAK_YONETIMI` |
| Denetim dalı | `demo_eldoria` |
| Denetim anındaki dal HEAD | `858bfa97f9c14a14960f209630af01c3ae4a2865` |
| Denetlenen aşama | 8.1 — Mevcut içerik altyapısının teknik denetimi |
| Sonuç | Denetim tamamlandı; 8.2 için onay bekleniyor |
| Kod/veri şeması değişikliği | Yapılmadı |

## 1. Denetim kapsamı ve depo doğrulaması

GitHub dal sorgusunda `demo_eldoria` dalı doğrulandı. Aşama 7 kapanış commit'i `120d9fa922769c88930dd82598c287f6e3381fd5` ile dal karşılaştırıldığında `demo_eldoria` dalının bu commit'ten üç commit ileride olduğu ve eklenen belgelerin Aşama 7 kapanış raporu ile Aşama 8 teknik planı olduğu görüldü. Dal HEAD'i `858bfa97f9c14a14960f209630af01c3ae4a2865` olarak doğrulandı.

Aşağıdaki belgeler doğrudan `demo_eldoria` ref'i üzerinden okundu:

- `reports/phase-8-content-editor-foundation-plan.md`
- `reports/phase-7-completion-report.md`
- `docs/architecture/39-phase-7-natural-world-architecture.md`

Aşama 8 planı bağlayıcı referans olarak kabul edildi. Denetim sırasında `main` dalına hiçbir yazma işlemi yapılmadı. Bu aşamada uygulama kodu, test veya mevcut içerik dosyaları değiştirilmedi.

## 2. İncelenen gerçek dosyalar

### Mimari ve plan belgeleri
- `reports/phase-8-content-editor-foundation-plan.md`
- `reports/phase-7-completion-report.md`
- `docs/architecture/39-phase-7-natural-world-architecture.md`

### İçerik paketi ve metadata
- `content/demo_eldoria/manifest.json`
- `content/demo_eldoria/presentation_assets.json`
- `content/demo_eldoria/maps/hex_forest_demo.json`
- `content/demo_eldoria/maps/hex_clearing_demo.json`
- `content/demo_eldoria/assets/tree_parts_atlas.json`
- `content/demo_eldoria/assets/tree_test.png`
- `content/demo_eldoria/assets/tree_parts_atlas.png`

### Uygulama ve renderer
- `application/content_loader.py`
- `game_ui/assets/asset_definition.py`
- `game_ui/assets/asset_manager.py`
- `game_ui/world_rendering/scene_object.py`
- `game_ui/world_rendering/depth_sorter.py`
- `game_ui/hex_world_view.py`
- `pyproject.toml`

### Test
- `tests/test_game_ui/test_phase_7_visual_presentation.py`

Bu liste, bu denetimde doğrudan içerikleri alınarak incelenen dosyalardır; deponun tüm dosya ağacının eksiksiz envanteri olduğu iddia edilmemektedir.

## 3. Mevcut mimarinin özeti

Yeni bir Asset Catalog veya AssetManager oluşturulmasına gerek yoktur. Mevcut sistemin ana sorumlulukları şöyledir:

- `AssetDefinition`: Bir görsel varlığın kimliğini, göreli dosya yolunu, kaynak boyut tercihini, çizim ölçeğini, normalize anchor değerini, varsayılan collision verisini, depth offset ve placement/terrain metadata'sını taşır.
- `AssetCatalog`: `asset_definition.py` içinde tanımlıdır. JSON katalog dosyasını okur, asset kayıtlarını doğrular, asset ID ile sorgu sağlar, katalog köküne göre dosya yolu çözer ve haritaya göre placement listesi döndürür. Aynı sınıf şu anda `objects` yerleşimlerini de belleğinde tutar.
- `AssetManager`: Pygame görsellerini ihtiyaç oldukça yükler ve asset anahtarına göre bellekte önbelleğe alır. Görsel dönüştürme (`convert_alpha` / `convert`) yükleme sırasında yapılır. Pygame'e bağımlı tek mevcut katman budur.
- `SceneObjectPlacement`: Bir haritadaki tekil nesne örneğini tanımlar. Hex koordinatları `q/r`, yerel ofsetler, footprint, instance collision box, depth offset, layer ve kind alanlarını taşır.
- `SceneObject` / `SceneObjectRenderer`: Dünya konumundaki görsel nesneyi temsil eder, görsel sınırları hesaplar, görünürlük kontrolü yapar ve ölçeklenmiş görseli ayrı bir cache içinde tutarak çizer.
- `DepthSorter`: Derinlik anahtarına ve isteğe bağlı stabil ikincil anahtara göre sıralama yapar.
- `ContentPackage` / `load_content_package`: Paket manifestini, veri JSON dosyalarını, kare harita kataloglarını, hex haritaları ve dünya haritasını yükler. Presentation catalog için burada yalnızca temel JSON/koleksiyon/sürüm kontrolü yapılır; ayrıntılı asset/placement parse işlemi `AssetCatalog.load` içindedir.

## 4. Mevcut içerik yükleme zinciri

### 4.1 PNG'den ekrana

```text
content/demo_eldoria/manifest.json
        |
        v
application.content_loader.load_content_package()
        |
        +--> presentation_assets yolu ve temel JSON şema kontrolü
        |
        v
HexWorldView._load_presentation_assets()
        |
        v
AssetCatalog.load(presentation_assets.json)
        |
        +--> AssetDefinition kayıtları
        +--> SceneObjectPlacement kayıtları
        +--> asset_id referans kontrolü
        |
        v
AssetCatalog.resolve_path(asset_id)
        |
        v
AssetManager.load_image(asset_id, path, alpha=True)
        |
        v
SceneObject / SceneObjectRenderer
        |
        +--> kaynak PNG boyutu
        +--> asset.scale ile görsel ölçü
        +--> anchor ile blit konumu
        +--> görünürlük/culling
        +--> ölçekli yüzey cache'i
        |
        v
Ekrana çizim
```

Yükleme tembeldir. Katalog metadata'sı hex dünya görünümü ilk çizim/yükleme akışında açılır; PNG, dosya mevcutsa ve ilgili nesne çizilecekse AssetManager tarafından yüklenir. Eksik veya açılamayan sahne görsellerinde `HexWorldView` prosedürel siluet fallback'i kullanır. Bu fallback mevcut davranıştır ve kaldırılmamalıdır.

### 4.2 JSON placement kaydından renderer'a

```text
presentation_assets.json -> objects[]
        |
        v
AssetCatalog.load()
        |
        +--> SceneObjectPlacement
        +--> asset_id katalogda var mı?
        |
        v
AssetCatalog.objects_for_map(map_id)
        |
        v
HexWorldView.render() -> drawable list
        |
        v
_draw_placed_scene_object()
        |
        +--> asset metadata çözümleme
        +--> q/r hücre merkezi + offset_x/offset_y
        +--> SceneObject oluşturma
        +--> SceneObjectRenderer
        |
        v
DepthSorter.sort_by_depth()
        |
        v
Renderer
```

Not: Gerçek metot adı `_draw_placed_scene_object` şeklindedir. Diyagramdaki akış bu metoda karşılık gelir.

## 5. Metadata alanlarının gerçek anlamı ve tüketicileri

| Alan | Mevcut anlam / birim | Üretildiği yer | Tüketildiği yer |
|---|---|---|---|
| `asset_id` | Katalog genelinde asset anahtarı | presentation JSON | AssetCatalog, AssetManager cache anahtarı, placement referansı |
| `path` | Katalog dosyasının bulunduğu dizine göre göreli yol | presentation JSON | AssetCatalog.resolve_path, AssetManager |
| `width/height` | Kaynak piksel boyutu; ikisi de 0 ise PNG'den alınır | presentation JSON | HexWorldView görsel boyutu hesabı |
| `scale` | Pozitif çizim çarpanı; PNG dosyasını değiştirmez | presentation JSON | Görsel genişlik/yükseklik hesabı, tree debug |
| `anchor` | Normalize (0..1) sprite referansı | presentation JSON | SceneObject anchor ve SceneObjectRenderer blit konumu |
| `pivot` | Temel AssetDefinition içinde ayrı alan değil; yalnızca ağaç atlası rig katmanlarında mevcut | tree atlas manifesti | TreeRigRenderer; rig varsayılan olarak kapalı |
| `depth_offset` | Görsel derinliğe eklenen sayısal ince ayar | asset ve placement JSON | _scene_object_depth_y / SceneObject.depth |
| `placement` | Asset'in sunum/terrain yerleşim sınıfı: underlay, ground, canopy, overlay | asset JSON | Terrain texture katmanı; sahne nesnesinin layer alanıyla aynı şey değil |
| `layer` | Placement örneğinin çizim katmanı | objects[] | drawable depth anahtarı |
| `collision` | Asset varsayılan x/y/width/height kutusu; mevcut bloklayıcı kaydında varlık/yokluk olarak kullanılıyor | asset JSON | _register_scene_object_blockers |
| `collision_box` | Placement örneği için x/y/width/height kutusu | objects[] | SceneObject verisi ve bloklayıcı varlık kontrolü |
| `footprint` | Pozitif tamsayı ikilisi; mevcut kodda SceneObject/Placement üzerinde taşınıyor | objects[] | Veri doğrulaması ve SceneObject; çok hücreli rezervasyon şu an uygulanmıyor |
| `q/r` | Hex axial hücre koordinatı | objects[] | LocalHexPosition, harita hücre sorgusu ve drawable konumu |
| `offset_x/y` | Hücre merkezine göre yerel ekran/dünya sunum ofseti; zoom ile çarpılır | objects[] | _draw_placed_scene_object |
| `map_id` | Placement'ın hedef harita kimliği | objects[] | objects_for_map ve harita tanımı sorguları |
| `kind` | Fallback çizim türünü seçmeye yarayan semantik etiket | objects[] | Prosedürel fallback dalı |

### 5.1 Anchor ve pivot

Temel sprite akışında anchor normalize koordinattır. Örneğin `[0.5, 1.0]`, yatay merkez ve görselin alt kenarını referans alır. Renderer, bu referans noktasından görselin sol üst konumunu hesaplar.

Temel asset modelinde bağımsız bir `pivot` alanı yoktur. Pivot yalnızca `tree_parts_atlas.json` içindeki rig layer kayıtlarında bulunur. Ağaç rig çizimi `HexWorldView._tree_rig_enabled = False` nedeniyle varsayılan olarak kapalıdır. Bu nedenle temel asset anchor'ı ile atlas rig pivot'u aynı alanmış gibi birleştirilmemelidir.

Ağaçlar için mevcut çizim yolunda `DEFAULT_TREE_SKELETON.ground_anchor` asset anchor'ının önüne geçebilir. Bu özel durum korunmalı ve 8.4 sözleşmesinde açıkça belirtilmelidir.

### 5.2 Scale ve kaynak boyutu

Mevcut demo varlıklarının `width` ve `height` değerleri 0'dır. `AssetDefinition` bu durumu açıkça “kaynak görsel boyutunu kullan” sentinel değeri olarak kabul eder; iki boyut birlikte 0 olmalıdır. Renderer kaynak PNG'nin gerçek ölçüsünü okur, ardından `asset.scale` ile görsel ölçüsünü hesaplar. Sonraki zoom çarpanı çizim aşamasında uygulanır.

Dolayısıyla 0 değerleri şimdilik geçerli legacy sözleşmedir. 8.2/8.4'te sessizce pozitif değere çevrilmemeli; yeni şemada daha açık bir kaynak boyutu kuralına geçilecekse migration ve geriye dönük uyumlulukla ele alınmalıdır.

### 5.3 Depth ve layer

Sahne nesneleri için layer sırası `underlay < ground < canopy < overlay` olarak çözülür. Nesne derinliği çoğunlukla ekran/dünya Y referansından gelir; ağaçlarda iskeletin depth referansı kullanılır. Asset ve placement depth offset değerleri bu referansa eklenir. Eşit derinlikte stabil sıralama için axial koordinat, drawable türü ve nesne kimliği ikincil anahtar olarak kullanılır.

Oyuncu–ağaç ön/arka sıralama davranışı Aşama 7 manuel kabul testinde başarılıdır. Aşama 8 bu sıralama algoritmasını yeniden tasarlamamalıdır.

## 6. Placement, collision ve footprint davranışının sınırları

- `SceneObjectPlacement` yalnızca axial `q/r` koordinatını temsil eder. Şu anki presentation placement örnekleri `hex_forest_demo` ve `hex_clearing_demo` haritalarına aittir.
- Hex haritalar `content/demo_eldoria/maps/*.json` altında `schema_version: 2` ve `hex_axial` geometri bildirimiyle tanımlanır.
- `ContentPackage` yükleyicisi kare harita tanımlarını `world.map_catalog` üzerinden, hex haritaları ise `load_hex_map_definition` üzerinden ayrı modellerle yükler. Bu ayrım korunmalıdır.
- `AssetCatalog.load` placement'ın `asset_id` değerinin katalogda bulunmasını denetler; ancak `map_id` değerinin gerçekten paketteki bir haritaya ait olduğunu veya `q/r` hücresinin o haritada geçerli olduğunu katalog aşamasında doğrulamaz.
- `HexWorldView.render` yalnızca aktif haritanın placement kayıtlarını çizer; geçersiz hücreye ait kayıtlar drawable listesine eklenmez.
- `_register_scene_object_blockers`, placement'ın kendi `collision_box` alanı veya asset'in `collision` alanı varsa placement hücresine bir `HexOccupant` kaydeder. Mevcut hareket modeli bu aşamada tam piksel kutusu değil, tek hücre doluluğu kullanır.
- Collision kutusunun gerçek dikdörtgen geometrisi mevcut occupancy/pathfinding motoruna aktarılmaz. Bu nedenle collision verisinin ayrıntılı geometrisi şu an tam fiziksel çarpışma davranışı üretmez.
- `footprint` pozitif tamsayı çifti olarak doğrulanır ve nesne modelinde taşınır; çok hücreli bloklama/rezervasyon davranışı mevcut kodda uygulanmaz.
- Asset collision ile placement collision_box arasında veri önceliği/override çözümlemesi merkezi bir resolver olarak mevcut değildir. Bloklayıcı kaydı için “placement kutusu var mı veya asset kutusu var mı” kontrolü yapılır; çizim nesnesine ise placement collision_box aktarılır.

Bu durumlar Aşama 8'in metadata sözleşmesi açısından önemlidir; fakat Aşama 8 kapsamında occupancy, collision veya pathfinding motorunun yeniden yazılmasını gerektirmez.

## 7. PNG dosyaları ve eksik içerik tespiti

`presentation_assets.json` altı asset kaydı içerir. Üç ağaç asset'i aynı `assets/tree_test.png` kaynağını farklı ölçek ve collision varsayılanlarıyla kullanır.

Bu denetimde GitHub dosya sorgusuyla:
- `content/demo_eldoria/assets/tree_test.png` bulundu.
- `content/demo_eldoria/assets/tree_parts_atlas.png` bulundu.
- `content/demo_eldoria/assets/rock_large.png` bulunamadı (404).
- `content/demo_eldoria/assets/shrub_green.png` bulunamadı (404).
- `content/demo_eldoria/assets/wildflower.png` bulunamadı (404).

Bu üç eksik PNG için mevcut renderer prosedürel fallback kullanabilecek şekilde tasarlanmıştır. Eksik dosyalar mevcut demo içeriğinde bilinçli fallback mi yoksa tamamlanmamış içerik mi, bu denetim tek başına belirleyemez. 8.2'de doğrulama sonucu hata/uyarı seviyeleri ayrıştırılırken bu üç kayıt için mevcut fallback davranışı korunmalıdır. Bu denetim sırasında görsel dosyalar değiştirilmemiştir.

Ağaç atlası manifesti ve PNG'si ayrı bir alt sistemdir. Atlas yüklemesi yalnızca `_tree_rig_enabled` açık olduğunda denenir. Varsayılan tek PNG ağaç çizimi korunmalıdır.

## 8. Mevcut doğrulama ve test kapsamı

### AssetCatalog / AssetDefinition doğrulamaları
Mevcut `AssetDefinition`:
- Boş asset ID ve path'i reddeder.
- Boyutların pozitif tamsayı olmasını veya ikisinin birlikte 0 olmasını kabul eder.
- Scale değerinin sonlu ve pozitif olmasını zorunlu tutar.
- Anchor'ın iki normalize ve sonlu sayı olmasını zorunlu tutar.
- Collision tuple uzunluğunu, sayısal türlerini ve negatif genişlik/yüksekliği kontrol eder.
- Depth offset'in sonlu olmasını zorunlu tutar.
- Terrain type değerlerini ve placement enum değerlerini denetler.

Mevcut `AssetCatalog.load`:
- JSON okuma ve schema_version=1 kontrolü yapar.
- assets/objects koleksiyonlarının liste olmasını zorunlu tutar.
- Yinelenen asset ID'yi reddeder.
- Asset path çözümlemesinde katalog kökü dışına çıkışı engeller.
- Yinelenen object ID'yi reddeder.
- Bilinmeyen asset ID referansını reddeder.

### Tespit edilen doğrulama boşlukları
- Katalog asset path'inin varlığını veya gerçek PNG formatını `AssetCatalog.load` sırasında doğrulamaz.
- `available()` yalnızca dosya varlığını kontrol eder; PNG'nin açılabilirliğini/formatını kontrol etmez.
- `AssetDefinition.collision` içindeki sayısal değerler için sonluluk kontrolü yoktur; NaN/Infinity gibi değerler ek doğrulama gerektirir.
- Collision kutusunda sıfır genişlik/yükseklik kabul edilir; bunun geçerli “noktasal/etkisiz collision” mı yoksa reddedilmesi gereken geometri mi olduğu henüz sözleşmeye bağlanmamıştır.
- `SceneObjectPlacement` offset ve depth değerlerinde sonluluk kontrolü yapar; collision_box sayılarında sonluluk kontrolü yapmaz.
- Placement map referansı ve axial hücre geçerliliği katalog yüklemesinde doğrulanmaz.
- Footprint yalnızca pozitif tamsayı ikilisi olarak doğrulanır; harita geometrisiyle ilişkisi kontrol edilmez.
- `AssetCatalog.assets` dışarıya değiştirilebilir dict olarak sunulur; katalog nesnesi bütünüyle immutable değildir.
- `AssetManager` cache anahtarı yalnızca asset key'dir; aynı key'in farklı path/alpha parametresiyle tekrar istenmesi mevcut cache girdisini kullanır. Şu anki tekil katalog kullanımı için kabul edilebilir; editör servislerinde cache yaşam döngüsü açıkça tanımlanmalıdır.
- `AssetManager.load_image` kendi içinde hata/diagnostic modeli sunmaz; çağıran katmanlar exception yakalar.
- `application.content_loader` presentation catalog için yalnızca temel kök tip, sürüm ve liste kontrolleri yapar; ayrıntılı doğrulama daha sonra HexWorldView içinde yapılır. Bu iki aşamalı sınır açık bir servis doğrulama sözleşmesi değildir.

### İncelenen mevcut test
`tests/test_game_ui/test_phase_7_visual_presentation.py`:
- Kataloğun en az altı asset ve orman haritasında en az on placement sunduğunu doğrular.
- Anchor uzunluğunu ve pozitif scale'i kontrol eder.
- Bazı placement kayıtlarında collision_box bulunup bazılarında bulunmadığını ve footprint pozitifliğini kontrol eder.
- DepthSorter için stabil ikincil sıralamayı doğrular.
- Hex terrain renderer'ın geometri yardımcılarını koruduğunu kontrol eder.

Bu test, normal katalog yüklemesini ve temel metadata davranışını doğrular. Bozuk JSON, eksik PNG, yinelenen ID, path traversal, bilinmeyen map referansı, NaN collision ve schema migration gibi Aşama 8 kabul senaryolarını kapsamaz. Bu denetimde testler çalıştırılmamıştır; kod veya veri değiştirilmediği için yalnızca kaynak ve test kapsamı incelenmiştir. CI durum sorgusunda bu HEAD için bağlı status kaydı dönmemiştir; bu sonuç başarılı CI olarak yorumlanmamalıdır.

## 9. Risk ve etki değerlendirmesi

| Öncelik | Bulgu | Etki | Önerilen ele alış |
|---|---|---|---|
| Yüksek | Asset ve placement aynı JSON ve aynı AssetCatalog içinde | Veri sorumlulukları karışık; editör için bağımsız kayıt zor | 8.3'te en düşük riskli ayrıştırma; legacy adapter |
| Yüksek | PNG varlığı/formatı katalog yüklemesinde doğrulanmıyor | Eksik dosyalar yalnızca çizim anında fallback'e düşüyor | 8.2'de kaynak doğrulaması ve kontrollü warning/error sonucu |
| Yüksek | Placement map/cell referansları doğrulanmıyor | Geçersiz placement sessizce çizim dışı kalabilir | 8.2/8.5'te map definition ile çapraz doğrulama |
| Orta | Collision sonluluk ve geometri sözleşmesi eksik | NaN/Infinity veya sıfır alan belirsizliği | 8.4/8.5'te alan bazlı geometri doğrulaması |
| Orta | Footprint taşınıyor ama çok hücreli davranış yok | Metadata beklentisi runtime davranışıyla karıştırılabilir | 8.4'te anlamını “yerleşim/simülasyon footprint'i” olarak ayır; runtime kapsamını genişletme |
| Orta | Anchor ile pivot ayrımı temel modelde yok | Gelecekte farklı dönüşüm/zemin teması ihtiyaçları belirsiz | 8.4'te anchor ve pivot kavramlarını ayrı tanımla; mevcut anchor'ı geriye uyumlu tut |
| Orta | AssetManager cache yaşam döngüsü yalnızca key bazlı | Reload/path değişimi sonrası stale cache riski | 8.2'de cache invalidation/clear sözleşmesini test et |
| Düşük | Katalog public dict mutable | Bellek içi taslak ve runtime verisi istemeden değişebilir | 8.2'de read-only görünüm değerlendirmesi; mevcut tüketicileri bozmadan |

## 10. Aşama 8 planı hakkında karar

Aşama 8 teknik planında kapsam veya sıra değişikliği gerekmiyor. 8.1'in ortaya çıkardığı bulgular, planın 8.2–8.5 alt aşamalarını doğruluyor.

Uygulama ayrıntısı olarak aşağıdaki hususlar 8.2/8.3/8.4 iş listesine eklenmelidir; bunlar planın hedefini değiştirmez:

1. `AssetCatalog` yeni bir sınıf olarak çoğaltılmamalı; mevcut sınıf güçlendirilmeli.
2. `AssetManager` yeniden yazılmamalı; mevcut cache ve Pygame adapter rolü korunmalı.
3. `presentation_assets.json` için legacy okuma/adapter yolu korunmalı; placement ayrımı tek seferde kırıcı yapılmamalı.
4. Katalog dosya yolu güvenliği ile kaynak dosya varlığı/PNG decode doğrulaması ayrı kontroller olmalı.
5. Map referansı ve koordinat geçerliliği katalogdan sonra, map definition bilgisine sahip içerik doğrulama katmanında yapılmalı.
6. `width=0,height=0` kaynak boyut sentinel'i mevcut içerikler için korunmalı; yeni açık şema kararı migration ile yapılmalı.
7. Temel sprite anchor'ı normalize zemin/pivot referansı olarak korunmalı; atlas rig pivot'u ayrı kalmalı.
8. Asset collision varsayılanı ve placement collision override çözümlemesi tek yerde yapılmalı; ancak bu veri sözleşmesi mevcut hücre tabanlı occupancy sistemini değiştirmemeli.
9. Footprint metadata'sı ile gerçek hücre rezervasyonu ayrıştırılmalı; çok hücreli rezervasyon bu aşamada eklenmemeli.
10. Kare harita ve hex harita koordinatları farklı modeller olarak kalmalı. Mevcut presentation placement modeli axial q/r ile sınırlı; kare harita için aynı modele zorla dönüşüm yapılmamalı.

## 11. Aşama 8.2 için uygulanabilir teknik adımlar

1. `AssetCatalog` mevcut API'sini ve tüketicilerini sabitleyen testleri ekle.
2. Asset ID normalize/benzersizlik kuralını belirle; mevcut ID değerlerini değiştirme.
3. `resolve_path` güvenliğini mutlak yol, `..`, symlink ve katalog kökü dışına kaçış testleriyle sabitle.
4. PNG doğrulamasını Pygame'den bağımsız dosya/format kontrolü ve gerektiğinde kontrollü decode katmanı olarak tasarla; AssetCatalog'ı UI bağımlı yapma.
5. Eksik dosya için katalog doğrulama sonucu ile runtime fallback davranışını ayır. Mevcut prosedürel fallback'i kaldırma.
6. Kaynak PNG ölçülerini gerçek dosyadan okuma ve width/height=0 legacy davranışını test et.
7. `AssetManager` cache reuse, clear ve yükleme hatası davranışlarını test et; cache API'sini gereksiz yere değiştirme.
8. `AssetCatalog.assets` erişimini salt okunur sunma seçeneğini tüketici analiziyle değerlendir.
9. 8.2 sonunda sadece katalog sözleşmesi ve asset dosyası doğrulamasını tamamla; placement dosya ayrımını 8.3'e bırak.
10. Bu adımların her biri için birim testleri ekle ve ilgili testleri çalıştırmadan 8.3'e geçme.

## 12. Korunacak sınırlar

- `HexWorldRuntime`, axial geometri, `WorldTransform`, kamera, zoom, hareket, pathfinding ve harita geçişleri değiştirilmeyecek.
- Kare harita yükleme ve çalışma modeli korunacak.
- Oyuncu–ağaç depth sorting davranışı korunacak.
- Ağaç rig/atlas varsayılan kapalı kalacak; doğal tek PNG çizimi korunacak.
- Yeni PNG veya görsel üretimi yapılmayacak.
- Content Editor UI, harita üzerinde mouse ile yerleştirme, sürükle-bırak ve preview penceresi geliştirilmeyecek.

## 13. Denetim sonucu

**Aşama 8.1 teknik denetimi tamamlandı.** Mevcut mimarinin gerçek dosya ve sınıfları belirlendi; PNG ve placement yükleme zincirleri çıkarıldı; metadata tüketicileri ve doğrulama boşlukları kaydedildi. Veri modeli veya runtime değiştirilmedi.

**Sonraki işlem yalnızca kullanıcı onayından sonra Aşama 8.2'ye başlamaktır.**
