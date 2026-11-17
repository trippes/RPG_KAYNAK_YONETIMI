# Aşama 7 — Render ve Görsel Doğrulama Genel Planı

**Proje:** Eldoria Hex World Laboratory  
**Dal:** `experiment/hex-world-laboratory`  
**Durum:** Kullanıcı tarafından onaylandı; 7.1–7.8 uygulama ve otomatik doğrulama tamamlandı, manuel görsel kabul bekleniyor.

## 1. Amaç

Hex dünya topolojisini, dünya üzerindeki varlıkların konumlarını ve derinlik ilişkilerini geometrik olarak doğru, görsel olarak tutarlı ve performanslı biçimde sunmak. Simülasyon ve geometri çekirdeğinin mevcut davranışı korunacak; çalışmalar render katmanının doğru temsiline odaklanacaktır.

## 2. Kapsam ve çalışma paketleri

### 7.1 — Hex çizim sırası ve görünür alan culling
- Hücre çizim sırası belirlenecek.
- Viewport içinde kalan hücreler konservatif bir görünür alan sorgusuyla seçilecek.
- Kısmen görünen hex'ler korunacak; görünür hücre atlanmayacak.
- Küçük harita ve büyük harita performansı karşılaştırılacak.

### 7.2 — Geometrik debug katmanları
- Hex sınırları, merkezleri ve axial koordinat etiketleri gösterilecek.
- Debug overlay normal render görünümünden ayrı ve açılıp kapatılabilir olacak.

### 7.3 — Sprite foot-anchor
- Sprite görsel pivotu, dünya uzayındaki ground-anchor ile eşleştirilecek.
- Asset başına normalize foot-anchor tanımlanabilecek.
- Görsel pivot fiziksel collider veya simülasyon konumunu değiştirmeyecek.

### 7.4 — Y-sort ve depth
- Dünya nesneleri ve aktör aynı kararlı derinlik sıralama kuralını kullanacak.
- Sıralama ground-anchor Y, layer priority ve stable visual ID ile deterministik olacak.

### 7.5 — Kamera titremesi ve subpixel
- Dünya ve kamera koordinatları float hassasiyetinde tutulacak.
- Yuvarlama yalnızca nihai Pygame raster/blit sınırında yapılacak.
- Kesirli pan ve zoom davranışı otomatik test ve görsel sahnelerle incelenecek.

### 7.6 — Collider debug karşılaştırması
- Oyuncu ve statik nesne collider şekilleri doğrudan fizik sisteminden alınacak.
- Fiziksel şekiller ayrı debug overlay'de çizilecek.
- Sprite ground-anchor, dünya görünümü ve collider hizası karşılaştırılacak.

### 7.7 — Gereksiz çizimlerin elenmesi ve performans
- Görünür olmayan hücre ve nesneler snapshot hazırlama aşamasında elenecek.
- Culling kapalı/açık ölçümleri aynı viewport ve kamera koşullarında karşılaştırılacak.
- Küçük haritada overhead ölçülerek culling eşiği belirlenecek.
- Büyük haritalarda snapshot ve render maliyetindeki kazanç raporlanacak.

### 7.8 — Bütünleşik doğrulama ve kabul
- Alt aşamalar tek render akışında birleştirilecek.
- Otomatik testler, regresyon testleri ve benchmark'lar çalıştırılacak.
- Görsel test sahneleri ve ekran görüntüsü kanıtları üretilecek.
- Manuel masaüstü görsel kabul kullanıcı tarafından tamamlanacak.

## 3. Teknik ilkeler

- Hex geometrisinin tek doğruluk kaynağı geometry core'dur.
- Render girdisi immutable world-space snapshot'tır.
- Bir frame içindeki tüm dünya katmanları aynı kamera transform'unu kullanır.
- Render, culling, sprite yerleşimi ve debug katmanları simülasyon state'ini değiştirmez.
- Fiziksel collider boyutları zoom veya sprite ölçeğine bağlı değildir.
- Performans optimizasyonları ölçümle gerekçelendirilir.
- Aşama 6'da kabul edilen kamera, hareket ve çarpışma davranışları korunur.

## 4. Beklenen çıktılar

1. Render pipeline prototipi.
2. Görünür alan culling algoritması ve performans karşılaştırması.
3. Hex debug ve koordinat görselleştirme katmanları.
4. Sprite foot-anchor ve Y-sort prototipi.
5. Subpixel kamera doğrulama sahneleri.
6. Fiziksel collider debug overlay'i.
7. Otomatik testler ve manuel kabul kontrol listesi.
8. Görsel test sahneleri ve ekran görüntüsü kanıtları.
9. Aşama 7 uygulama/doğrulama raporu.

## 5. Kabul kriterleri

- Hex çizimi geometri çekirdeğiyle aynı parametreleri kullanır.
- Görünür hex hücreleri eksiksiz çizilir.
- Sprite zemine doğru noktadan oturur.
- Y-sort doğru ve deterministik örtüşme üretir.
- Render katmanı simülasyon state'ini değiştirmez.
- Kamera hareketinde belirgin titreme veya konum drift'i bulunmaz.
- Dünya görünümü ile fiziksel collider debug görünümü karşılaştırılabilir.
- Büyük haritalarda culling ölçülebilir fayda sağlar; küçük haritada gereksiz olduğu gösterilirse devre dışı bırakılır.
- Otomatik doğrulama, performans raporu ve kullanıcı görsel kabulü tamamlanır.

## 6. Kapsam dışı

- A* veya başka pathfinding algoritması.
- Click-to-move.
- Hareket ve çarpışma sistemini yeniden tasarlama.
- Kamera çekirdeğini yeniden geliştirme.
- Yeni oyun mekaniği veya simülasyon sistemi.
- Tam animasyon/nihai sanat asset paketi.
- Işık, gölge, shader ve post-processing.
- 3D veya Godot'a geçiş.

Bu genel plan Aşama 7'nin bağlayıcı kapsamıdır. Teknik uygulama ayrıntıları `PHASE-07-TECHNICAL-PLAN.md` belgesinde tanımlanmıştır.
