# Eldoria RPG — Aşama 8.4 Uygulama Raporu
## Konum, Anchor, Scale, Depth, Layer, Collision ve Footprint Sözleşmeleri

| Alan | Değer |
|---|---|
| Depo | trippes/RPG_KAYNAK_YONETIMI |
| Çalışma dalı | demo_eldoria |
| Aşama | 8.4 — Konum ve görsel metadata standartları |
| Referans plan | reports/phase-8-content-editor-foundation-plan.md |
| Son kod/test commit'i | e7ee1995d1ce29eb636446cc3aa466dd21f41ad3 |
| Mimari belge commit'i | 36cab063c523572be04ec082300ee0d36029fa39 |
| Rapor durumu | Uygulama yapıldı; otomatik CI ve kullanıcı kabulü doğrulaması bekliyor |
| Content Editor UI | Geliştirilmedi |

## 1. Amaç ve kapsam

Aşama 8.4'ün amacı, ileride Content Editor tarafından gösterilecek ve değiştirilecek konum/görsel metadata alanlarının birimlerini ve koordinat uzaylarını açık hâle getirmektir.

Uygulama, planın 8.4 bölümündeki şu alanlarla sınırlı tutuldu:
- Anchor ve pivot anlamı.
- Kaynak PNG boyutu ve Draw Scale.
- Placement konum/ofsetleri.
- Depth ve layer sıralaması.
- Collision kutusu ve footprint.
- Geçersiz sayısal/geometrik değerlerin reddedilmesi.

Hex/kare harita simülasyonu, kamera, hareket, occupancy, pathfinding, PNG içerikleri ve renderer davranışı yeniden tasarlanmadı.

## 2. Gerçek koddan doğrulanan mevcut davranış

Uygulama öncesi şu mevcut bileşenler incelendi:
- game_ui/assets/asset_definition.py
- game_ui/assets/placement_catalog.py
- game_ui/world_rendering/scene_object.py
- game_ui/world_rendering/tree_skeleton.py
- game_ui/world_rendering/depth_sorter.py
- game_ui/hex_world_view.py
- content/demo_eldoria/asset_catalog.json
- content/demo_eldoria/placements/hex_forest_demo.json
- tests/test_game_ui/test_asset_catalog_contract.py
- tests/test_game_ui/test_placement_catalog.py
- tests/test_game_ui/test_hex_world_view.py

Önemli mevcut gerçekler:
1. Hex placement `q/r` değerleri integer axial hücre koordinatlarıdır.
2. Placement `offset_x/y` değerleri hücre merkezine eklenir ve kamera zoom'u ile ölçeklenir.
3. Asset anchor değeri normalize [0,1] koordinatlarıdır.
4. Ağaçlarda TreeSkeleton, ground_anchor ve depth_anchor değerlerini ayrı ayrı kullanır.
5. Asset ve placement depth_offset değerleri toplanır.
6. Render sırası önce layer, sonra depth/Y değeri ve deterministik ikincil anahtarlarla kurulur.
7. Collision kutuları mevcut oyuncu hareketinde alt-hücre geometrisi olarak kullanılmaz. Collision metadata'sının bulunması, mevcut HexWorldView kodunda placement'ın q/r hücresine bir occupancy blocker kaydı eklenmesine yeterlidir.
8. Footprint mevcut SceneObjectPlacement modelinde saklanır; mevcut blocker davranışı footprint'i çok hücreli occupancy'ye genişletmez.

Bu nedenle Aşama 8.4'te yeni pivot alanı, hassas collision runtime'ı veya çok hücreli footprint davranışı eklenmedi.

## 3. Uygulanan değişiklikler

### 3.1 game_ui/world_rendering/scene_object.py

- Birim ve koordinat sözleşmesi modül açıklamasında belgelendi.
- `SCENE_LAYERS` ve değiştirilemez `SCENE_LAYER_ORDER` tanımlandı.
- Placement offset ve depth_offset değerleri için finite sayı doğrulaması eklendi.
- q/r değerlerinin boolean değil gerçek integer olması güvence altına alındı.
- Footprint'in pozitif tam sayı map-cell boyutlarından oluşması doğrulandı.
- Collision kutusu x/y/width/height biçiminde finite yerel piksel AABB olarak doğrulandı.
- Collision kutusu mevcutsa genişlik ve yükseklik sıfırdan büyük olmak zorunda.
- SceneObject anchor ve görsel boyut doğrulamaları güçlendirildi.
- SceneObject.depth değerinin world-pixel derinlik çizgisi + world-pixel ince ayar olduğu belgelendi.

Commit: f4f9dd3eb0e65f2c979e8490c6fc5784d102629c

### 3.2 game_ui/assets/asset_definition.py

- Draw Scale teknik sınırları `0.01 <= scale <= 8.0` olarak tanımlandı.
- Anchor değerleri normalize [0,1] aralığında doğrulanıyor ve immutable float çiftine dönüştürülüyor.
- Collision varsayılanı null olabilir; mevcutsa finite yerel piksel AABB ve pozitif alan zorunlu.
- Scale ve depth_offset değerleri doğrulamadan sonra float olarak normalize ediliyor.
- Kaynak PNG boyutlarının 0/0 sentinel davranışı değiştirilmedi.

Commit: 3e3baf455f924d6dc9c756318d547884f58f9909

### 3.3 game_ui/hex_world_view.py

- Katman sırası için dosya içinde tekrarlanan sözlük kaldırıldı.
- Renderer artık SceneObject modülündeki ortak `SCENE_LAYER_ORDER` sözleşmesini kullanıyor.
- Layer/depth/ikincil sıralama algoritmasının davranışı değiştirilmedi.

Commit: 19f69e76f5b81567b6c3213070d62f0021a07e57

### 3.4 Yeni otomatik test

Yeni dosya:
- tests/test_game_ui/test_scene_object_geometry_contract.py

Testler:
- Finite placement offset/depth değerleri.
- Integer axial koordinat ve boolean reddi.
- Pozitif map-cell footprint.
- Collision AABB finite/pozitif alan kuralları.
- Desteklenen layer değerleri.
- Normalize anchor ve visual bounds.
- Görsel boyut ile collision alanının bağımsızlığı.
- Draw Scale alt/üst sınırları.
- Asset collision ve anchor sözleşmeleri.
- Ortak layer sırası.

Commit: e7ee1995d1ce29eb636446cc3aa466dd21f41ad3

## 4. Mimari belge

Yeni belge:
- docs/architecture/46-presentation-geometry-contract.md

Belge; birim tablosunu, anchor/pivot kararını, Draw Scale aralığını, konum/ofset formülünü, collision/footprint mevcut runtime sınırlarını ve layer/depth sıralama sözleşmesini açıklar.

Commit: 36cab063c523572be04ec082300ee0d36029fa39

## 5. Veri ve geriye dönük uyumluluk

- schema_version 1 korundu.
- Mevcut JSON alan adları değiştirilmedi.
- content/demo_eldoria/asset_catalog.json içindeki altı asset kaydı değiştirilmedi.
- İki placement dosyasındaki toplam 14 placement kaydı değiştirilmedi.
- presentation_assets.json legacy okuma yolu korunuyor.
- Kare harita koordinat modeli değiştirilmedi.
- Ağaç PNG'si ve ağaç rig/atlas varsayılan davranışı değiştirilmedi.
- Görsel scale değişimi collision alanını otomatik değiştirmiyor.

## 6. Test ve CI durumu

Bu uygulama oturumunda GitHub dosya/commit işlemleri gerçekleştirildi; Python test komutları doğrudan çalıştırılmadı.

Son kod/test commit'i için GitHub birleşik commit status sorgusu boş status listesi döndürdü. Bu nedenle CI başarılı veya başarısız olarak raporlanmıyor; **CI sonucu henüz doğrulanmış değil**.

Yerel doğrulama için önerilen ilk komut:

```powershell
python -m pytest -q tests/test_game_ui/test_scene_object_geometry_contract.py tests/test_game_ui/test_asset_catalog_contract.py tests/test_game_ui/test_placement_catalog.py tests/test_game_ui/test_hex_world_view.py
```

Ardından tam test ve release kontrolü:

```powershell
python -m pytest -q
python scripts/verify_release.py
```

## 7. Kullanıcı manuel kabulü

Otomatik testler geçtikten sonra mevcut görsel davranışı doğrulamak için:
1. `python main.py --play` ile oyunu aç.
2. H ile hex dünyaya gir.
3. Farklı ağaçların dibinde ve ön/arka taraflarında dolaş; mevcut yaklaşma mesafesi ve depth/Y-sort davranışının değişmediğini kontrol et.
4. Kamera zoom seviyelerini değiştir; sprite, hücre ofseti ve oyuncu konumunun birlikte tutarlı ölçeklendiğini kontrol et.
5. Orman–açıklık geçişini yap.
6. H ile kare dünyaya dön ve kare haritanın çalıştığını doğrula.

Bu kontroller henüz kullanıcı tarafından raporlanmadığı için manuel kabul sonucu beklemededir.

## 8. Korunan sınırlar

- main dalına yazma yapılmadı; tüm dosya yazma işlemleri açıkça demo_eldoria dalına yönlendirildi.
- HexWorldRuntime, WorldTransform, occupancy ve pathfinding değiştirilmedi.
- Kamera, hareket, harita geçişleri ve DepthSorter algoritması değiştirilmedi.
- Kare harita sistemi değiştirilmedi.
- PNG dosyaları değiştirilmedi.
- Content Editor UI, önizleme, sürükle-bırak veya oyun içi editör modu eklenmedi.
- NPC, görev, savaş, ekonomi ve envanter sistemlerine müdahale edilmedi.

## 9. Sonuç ve sonraki kapı

Aşama 8.4'ün metadata sözleşmesi kod ve mimari belge olarak uygulandı. Otomatik testler eklendi. Ancak CI ve kullanıcı manuel kabulü henüz doğrulanmadığından aşama **tamamlandı** olarak işaretlenmemiştir.

Testler ve manuel kabul başarılı olduktan sonra Aşama 8.4 kapatılabilir. Aşama 8.5 — doğrulama ve güvenli yükleme — için ayrıca kullanıcı onayı beklenmelidir.
