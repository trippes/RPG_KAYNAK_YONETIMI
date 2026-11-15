# ADR-002 — Coordinate axes, origin, and hex scale

- Durum: KABUL EDİLDİ
- Tarih: 2026-11-15
- Aşama: 2
- Onay: Kullanıcı matematiksel eksen ve circumradius tercihlerini onayladı.

## Karar
- Dünya uzayında X sağa, Y yukarı artar.
- Axial (0,0) hücresinin merkezi layout origin'idir.
- Hex boyutu circumradius R olarak tanımlanır.
- Varsayılan normalize yarıçap 1.0 dünya birimidir.
- Pygame ekran koordinatına dönüşüm kamera/render aşamasına aittir.

## Gerekçe
Matematik katmanını grafik kütüphanesinden bağımsız tutar. Circumradius merkez, köşe ve kenar hesaplarının aynı parametreden türetilmesini sağlar.

## Sonuçlar
Ekran koordinatına dönüşümde Y ekseni ters çevrilir. Geometri saf Python kalır.
