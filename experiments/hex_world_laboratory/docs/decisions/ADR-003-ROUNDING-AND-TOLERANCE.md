# ADR-003 — Cell selection rounding and numeric tolerance

- Durum: ÖNERİ — uygulandı, aşama kapanışında kullanıcı kabulü bekliyor
- Tarih: 2026-11-15
- Aşama: 2
- Onay: Kullanıcı deterministik sınır davranışını istedi; kesin formül kapanışta değerlendirilecek.

## Problem
World-to-axial dönüşümü kesirli cube koordinatlarını bir hücreye yuvarlar. Kenar/köşe noktaları eşit uzaklık durumları oluşturur.

## Seçenekler
- Python round (banker's rounding).
- Bileşenleri bağımsız yuvarlamak.
- Cube rounding ve deterministik düzeltme sırası.

## Uygulanan öneri
- En yakın tam sayıya half-up rounding (tam yarımlar pozitif sonsuza).
- Cube toplamı sıfır değilse en büyük mutlak yuvarlama hatasına sahip bileşen düzeltilir.
- Eşitlik önceliği q, r, s sırasıdır.
- Mutlak ve göreli tolerans 1e-9.
- Toleranslar hücre atama kuralını değiştirmez.

## Gerekçe ve ödünleşimler
Aynı girdinin her çalıştırmada aynı hücreyi seçmesini sağlar. Sınırın iki tarafında hücre seçimi kesikli değişir; sınırın kendisi tek hücreye atanır. Çok büyük dünya koordinatlarında float çözünürlüğü ayrıca ölçülmelidir.

## Doğrulama
Pozitif/negatif koordinatlar, paylaşılan kenar, köşe ve dönüşüm testleri.
