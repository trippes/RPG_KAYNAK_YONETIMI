# ADR-003 — Hücre seçimi, sınır davranışı ve sayısal tolerans

- Durum: KABUL EDİLDİ — kullanıcı kararıyla
- Tarih: 2026-11-15
- Aşama: 2

## Bağlam
Dünya koordinatındaki bir nokta axial hücreye dönüştürülürken, iki veya üç hücreye eşit uzaklıkta olan sınır noktaları ortaya çıkabilir. Karakter hareket ederken tam sınırda önceki hücresini kaybetmemelidir.

## Karar
1. Nokta için geometrik olarak en yakın hücre seçilir.
2. Nokta iki hücrenin tam sınırındaysa ve önceki hücre bu eşit uzaklıktaki hücrelerden biriyse önceki hücre korunur.
3. Önceki hücre en yakın hücrelerden biri değilse, en yakın hücre seçilir.
4. Önceki hücre bilgisi verilmemişse deterministik cube rounding kullanılır.
5. Cube rounding'de yarım değerler half-up yuvarlanır; düzeltme eşitliğinde q, r, s sırası yedek deterministik önceliktir.
6. Mutlak ve göreli sayısal toleranslar 1e-9'dur. Tolerans yalnızca sayısal eşitliği değerlendirmek içindir; sınırdan gerçekten geçişi engellemez.

## Hareket açısından beklenen davranış
- Karakter A hücresinden B hücresine ilerlerken ortak sınıra tam geldiğinde, önceki hücresi A ise A korunur.
- Sınırı B tarafına geçtiğinde B, A'dan daha yakın hâle gelir ve seçilir.
- Karakter B'den sınıra geri geldiğinde aynı kural simetrik olarak B hücresini korur.
- Böylece karakter tam sınırda hücreler arasında titreşmez; sınırı geçtiğinde hücresi güncellenir.

## Uygulama notu
Geometri dönüşüm fonksiyonu `world_to_axial(point, layout, previous_cell=None)` önceki hücreyi isteğe bağlı alır. Bu bilgi karakter/hareket katmanından sağlanır. Önceki hücre, yalnızca gerçekten eşit uzaklıktaki hücrelerden biriyse korunur.

## Ödünleşimler ve kapsam
- Önceki hücre bilgisi saf geometri fonksiyonuna isteğe bağlı parametre olarak eklenir; geometri katmanı karakter durumunu kendisi saklamaz.
- Önceki hücre verilmezse sonuç yine deterministiktir.
- Bu karar karakterin hareket sistemini uygulamaz; hareket katmanı bu parametreyi her güncellemede sağlamalıdır.
- Çok büyük dünya koordinatlarında floating-point hassasiyeti ayrıca stres testine tabi tutulmalıdır.

## Doğrulama ölçütleri
- Flat-top ve pointy-top yönelimlerinde sınırın tam ortasında önceki hücre korunmalı.
- Sınır geçildikten sonra daha yakın olan yeni hücre seçilmeli.
- Önceki hücre verilmediğinde deterministik yedek seçim sürmeli.
