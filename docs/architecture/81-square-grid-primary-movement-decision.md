# Eldoria — Kare Izgara Birincil Hareket Mimarisi

**Tarih:** 23 Kasım 2026  
**Durum:** Bağlayıcı mimari karar  
**Hedef dal:** experiment/map-cleanup  
**İlişkili plan:** 79 numaralı iki katmanlı hareket mimarisi planı

## 1. Kararın amacı ve önceliği

Bu belge, iki katmanlı dünya fikrinin kesin yorumunu kayda geçirir. 79 numaralı plandaki kare ızgarayı yalnızca yerel iyileştirme olarak ele alan ve axial A*'ı kalıcı dünya ölçeği rota koridoru/ana yol bulucu olarak tutan önceki öneriler bu kararla geçersiz kılınmıştır.

**Altıgen dünya kanonik dünyadır; üzerine yerleştirilen kare ızgara ise oyuncu ve NPC hareketinin birincil navigasyon uzayıdır.** Kare ızgara, ileride tüm mesafelerde rota graph'ını ve hareket yönlendirmesini taşır. Altıgen graph, kalıcı bir üst katman veya eşit öncelikli alternatif navigasyon sistemi olmayacaktır.

## 2. Katmanların değişmez sorumlulukları

### Katman A — Kanonik altıgen dünya

HexMapDefinition, axial (q, r) hücreleri, geçerli harita maskesi, arazi ve dünya kuralları tek doğruluk kaynağı olmaya devam eder. Kaynaklar, yapılar, bölgeler, görev bağlantıları ve içerik kimliği altıgen dünya verisine bağlı kalır.

### Katman B — Birincil kare hareket ızgarası

Kare ızgara, kanonik altıgen geometriyi örten bağımsız ve türetilmiş bir katmandır. Hücreleri dünya koordinatlarında tanımlanır; her kare hücrenin hangi hex alanlarıyla ne kadar kesiştiği hesaplanır. Navigasyon grafı bu katmanda kurulacaktır.

- Oyuncu ve NPC rota araması aynı kare grid topolojisini kullanır.
- Kare grid A* ve komşuluk maliyetleri birincil yol bulma mekanizmasıdır.
- 8 ve 16 dünya birimi hücre boyutları ölçülerek seçilir; nihai çözünürlük ölçüm olmadan sabitlenmez.
- Kare gridin verisi map geometry girdilerinden türetilir; kayda yazılmaz ve gerektiğinde yeniden kurulur.
- Hex A* yalnızca geçiş döneminde karşılaştırma veya geçici güvenli geri dönüş amacıyla tutulabilir. Nihai mimaride ana rota, global koridor veya kalıcı fallback otoritesi değildir.

### Katman C — Sürekli hareket ve fizik

Aktörün gerçek konumu kesirli WorldPoint(x, y) koordinatında kalır. Kare hücre merkezleri hedef/rota referanslarıdır; oyuncu veya NPC hücre merkezlerine snap edilmez. Hız, displacement, çarpışma çözümü ve runtime commit mevcut sürekli dünya düzleminde çalışır.

Kare grid bir rota hücresinin geçilebilir olduğunu söylese bile gerçek collider hareketi mevcut swept physics çözümünden geçmek zorundadır. Physics son fiziksel doğruluk otoritesi olmaya devam eder.

## 3. Grid yerleşimi ve koordinat sözleşmesi

Kare grid dünya x/y eksenlerine paraleldir. Varsayılan grid origin, (0, 0) koordinatlı kare hücrenin merkezinin dünya (0, 0) noktasında bulunduğu hizalamadır. Origin gerektiğinde açık bir WorldPoint parametresidir; renderer veya aktör konumundan örtük biçimde türetilmez.

SquareGridCoord(x, y) tam sayı hücre kimliğidir. world_point_to_square_grid() dünya noktasının ait olduğu hücreyi; square_grid_to_world_point() hücrenin merkezini döndürür. Hücre sınırı eşitliklerinde sağ ve alt hücre sahibi olur; yarı açık aralık kuralı pozitif ve negatif koordinatlarda deterministiktir.

Dünya noktası → kare grid → dünya noktası dönüşümü, grid hücre merkezleri için kayıpsızdır. Serbest bir dünya noktası dönüşümünde yalnızca hücre kimliği elde edilir; aktörün gerçek dünya noktası hiçbir zaman bu merkezle değiştirilmez.

## 4. Hex–square coverage ve geçilebilirlik

Hücre merkezinin hangi hex'e ait olduğunu bulmak, kare hücrenin tamamının o hex içinde olduğunu kanıtlamaz. Bu nedenle yalnızca merkez örneklemesi yeterli değildir.

Aşama 1 prototipi, pointy-top hex poligonunu kare hücre dikdörtgenine kırparak gerçek kesişim alanını hesaplar. Bir kare hücre:
- geçerli hex birleşiminin tamamı tarafından kaplanıyorsa ve
- kesiştiği hex alanlarının hiçbiri blocked değilse

geometri prototipinde WALKABLE sınıfını alabilir. Harita dışındaki hücreler OUTSIDE, harita kenarını kısmen kesen hücreler PARTIAL, tam kaplı ancak engelli hex alanına temas eden hücreler BLOCKED olur. Birden fazla hex'e düşen kare hücrelerin her hex ile kesişim alanı ayrı tutulur.

WALKABLE sonucu nihai fizik izni değildir. Statik nesneler, gerçek collider yarıçapı, dinamik aktör teması ve swept collision sonraki aşamalarda ayrıca doğrulanır.

## 5. Hareket ve animasyon sözleşmesi

Grid hareket yönü ve rota niyeti oyuncu ile NPC'ler için aynı navigasyon uzayından üretilir. Gerçek hareket uygulandığında animasyon iki bilgiyi birlikte kullanır:
- kare hareket sisteminden gelen yön/niyet;
- physics ve runtime commit sonrasında gerçekten gerçekleşen dünya displacement'ı.

Yürüme/koşma fazı zamana bağlı bağımsız döngü değildir; gerçekleşen mesafe ve stance temasından ilerler. Çarpışma hareketi keserse ayak fazı ve gövde hareketi gerçekleşen displacement'a uyum sağlar. Aktör durduğunda lokomosyon döngüsü durur. Grid hücre geçişi animasyonu sıfırlamaz veya aktörü hücre merkezine taşımaz.

## 6. Navigasyonun aşamalı geçişi

1. Saf kare grid geometri ve coverage prototipi.
2. Türetilmiş grid chunk/cache ve deterministik invalidation.
3. Birincil kare-grid A*: köşe kesme engeli, gerçek diagonal mesafe, hareket profili maliyeti ve fizik doğrulamalı rota segmentleri.
4. Oyuncunun tıklama rotası ve serbest input'u kare grid hareket niyetine bağlanır; continuous physics korunur.
5. NPC devriye, takip, kaçınma ve yoldaş komutları aynı kare grid navigasyon uzayına taşınır.
6. Animasyon grid yön/niyeti ile gerçekleşen displacement ve stance verisine bağlanır.
7. Düşük donanım hedefinde ölçüm, regresyon ve manuel kabul.

Aşama 1 yalnızca geometri ve coverage kodu içerir. Pathfinding, oyuncu/NPC entegrasyonu, collider veya animasyon davranışı değiştirilmez.

## 7. Tasarımın kabul edilmeyen yorumları

- Kare gridin yalnızca hex hücresi içinde yerel bir alt-ızgara olması.
- Hex A*'ın uzun vadede ana global rota koridorunu üretmeye devam etmesi.
- Oyuncu/NPC konumunun grid hücre merkezlerine kilitlenmesi.
- Navigasyon hücre durumunun physics çarpışmasının yerine geçirilmesi.
- Animasyonun gerçek displacement yerine yalnızca zaman sayacıyla ilerlemesi.
- Renderer/Pygame katmanının ikinci bir world/grid koordinat otoritesi kurması.
