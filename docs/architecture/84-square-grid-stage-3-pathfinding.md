# Eldoria — Aşama 3 Kare Izgara A* Navigasyonu

**Tarih:** 23 Kasım 2026  
**Hedef dal:** `experiment/map-cleanup`  
**Aşama:** 3 — Kare navigasyon A*  
**Durum:** İlk uygulama paketi; gameplay entegrasyonu yapılmadı.

## 1. Kapsam

Bu aşama, Aşama 1 coverage geometrisi ve Aşama 2 chunk cache üzerinde kare-grid A* aramasını ekler. Kare grid, tüm mesafelerde oyuncu ve NPC navigasyonunun birincil graph'ı olma kararını uygular.

Bu aşamada oyuncu input'u, NPC steering, kamera, renderer, fizik motoru, animasyon ve save/load değiştirilmez. Aktör konumu hâlâ sürekli `WorldPoint` olarak kalır; pathfinder yalnızca hücre koordinatlarından oluşan rota önerir.

## 2. Graph ve maliyet

- Sekiz komşuluk kullanılır.
- Cardinal adım maliyeti 1; diagonal adım maliyeti √2 hücre birimidir.
- Diagonal kenar, iki ortogonal komşu hücrenin de geçilebilir olmasını gerektirir; corner-cutting yasaktır.
- A* heuristic'i octile distance ve graph içindeki en düşük pozitif terrain multiplier kullanır; bu nedenle admissible kalır.
- Terrain maliyeti, geçişin iki ucundaki terrain çarpanlarının ortalamasıyla simetrik hesaplanır.
- Bir kare hücre birden fazla hex arazi poligonunu kesiyorsa terrain izni için bütün terrain ID'leri izinli olmalı; maliyet için en yüksek terrain çarpanı kullanılır.
- Eşit maliyetli rotalarda heap tie-break koordinat sırası deterministik sonuç üretir.
- Dinamik occupancy ayrı `blocked_cells` girdisiyle uygulanır; `ignores_occupancy` yalnızca bu dinamik engelleri yok sayar.
- Mevcut `MovementProfile` içindeki `can_traverse_blocked_cells` yeteneği korunur; bu yetenek fiziksel çarpışmayı devre dışı bırakmaz.

## 3. Hareket profili ve fizik

`SquareGridNavigationProfile`, mevcut `MovementProfile` yeteneklerini korur ve ayrıca collider yarıçapı alır. Oyuncu için mevcut 8 birim, NPC için içerik/aktör tanımında açıkça verilen collider yarıçapı kullanılmalıdır; tahminî değer atanmaz.

Collider yarıçapı, kare coverage maskesinde muhafazakâr bir clearance prefilter uygular. Kapsama dışı, partial veya profile göre geçilemeyen hücreler engel kabul edilir. Dinamik occupancy de collider clearance hesabına katılır. Bu filtre gerçek fizik çözümünün yerine geçmez.

`make_physics_edge_validator(snapshot, body)`, mevcut `HexPhysicsSnapshot.resolve_motion()` sistemini kullanarak kare-grid hücre merkezleri arasındaki her kenarı gerçek collider ile önceden doğrulayan callback üretir. Segmentin tamamı istenen displacement'ı uygulayamıyorsa kenar reddedilir.

Gameplay rotası üretiminde bu fizik doğrulayıcı kullanılmalıdır. Callback verilmeden çalışan aramalar graph prototipi/test amaçlıdır; fiziksel güvenli rota garantisi vermez. Dinamik aktör çarpışmaları ayrıca runtime occupancy/physics katmanında ele alınır.

## 4. Sürekli hareket ve waypoint sözleşmesi

Pathfinder sonucu `SquareGridCoord` tuple'ıdır. Hücre merkezleri yalnızca waypoint referanslarıdır. Oyuncu veya NPC koordinatını hücre merkezine snap etmez. Sonraki entegrasyon aşamasında gerçek sürekli başlangıç konumundan ilk waypoint'e geçiş ve hedefin tam dünya koordinatına yaklaşma ayrı fizik doğrulamasıyla yapılacaktır.

Rota smoothing bu aşamada yoktur. Fizik snapshot tarafından doğrulanmamış waypoint segmentleri kısaltılamaz veya atlanamaz. Axial A* kalıcı ana navigasyon katmanı olarak kullanılmayacaktır.

## 5. Görüntüleme ve dünya işleme ile uyum

Kabul edilen görsel hedef 1920×1080 (16:9 Full HD) çözünürlüktür. Bu çözünürlük kamera görüş alanı ve kare-grid çözünürlüğüyle aynı kavram değildir; kamera zoom'u çözünürlükten bağımsız kontrol edilecektir. Daha düşük çözünürlük profilleri performans doğrulamasında ayrıca değerlendirilecektir.

Görüş alanı öncelikli işleme kararı sonraki kamera/render entegrasyon aşamalarında uygulanacaktır:
- Görünen alanın çizimi ve gerekli verileri en yüksek önceliğe sahip olur.
- Ekranın hemen dışındaki chunk'lar önceden ve düşük öncelikle hazırlanır.
- Uzak chunk'lar ihtiyaç oldukça üretilir; tüm dünya her karede işlenmez.
- Navigasyon, render ve NPC simülasyonu ayrı güncelleme önceliklerine sahip olur.
- Ekran dışındaki NPC ve dünya olayları tamamen durdurulmaz; uygun uzak simülasyon sıklığı sonraki aşamalarda belirlenir.

Bu aşamada kamera, renderer, çözünürlük modu veya dünya simülasyonu kodu değiştirilmemiştir.

## 6. Çözünürlük ve performans

8 ve 16 dünya-birimi grid çözünürlükleri açık tutulur; bu aşamada nihai seçim yapılmaz. Benchmark her iki çözünürlükte coverage üretim süresini, A* p50/p95 arama süresini, erişilebilir rota sayısını ve en uzun rota uzunluğunu raporlar. 1920×1080 kamera hedefi pathfinder graph çözünürlüğünü belirlemez; render görüş alanı ile navigasyon çözünürlüğü ayrı ayarlardır.

Komut:

```powershell
python scripts/benchmark_square_grid_pathfinding.py
```

GitHub Actions ayrıca aynı benchmark'ı Ubuntu/Python 3.12 üzerinde çalıştırıp JSON artifact olarak saklar. Hosted runner ölçümleri yalnızca karşılaştırma içindir; son kabul hedef düşük donanımlı yerel bilgisayarda yapılmalıdır.

## 7. Test kapısı

- cardinal ve diagonal rota;
- corner-cutting engeli ve iki ortogonal hücre şartı;
- blocked, partial, outside hücre reddi;
- allowed terrain ve weighted terrain route;
- collider clearance prefilter;
- physics edge validator retleri ve alternatif rota;
- mevcut blocked-cell traversal yeteneği;
- deterministik tie-break;
- negatif koordinatlar;
- invalid start/goal, disabled movement ve dynamic occupancy;
- 8/16 grid benchmark;
- mevcut hex movement, physics, persistence ve cache regresyon testleri.

**Çıkış kuralı:** Kare A* doğru ve deterministik çalışmalı; fizik edge validator mevcut snapshot'a bağlanabilmeli. Player/NPC entegrasyonu sonraki aşamalardadır.
