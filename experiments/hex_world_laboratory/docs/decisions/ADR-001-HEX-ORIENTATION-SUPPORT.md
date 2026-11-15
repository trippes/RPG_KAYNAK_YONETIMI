# ADR-001 — Hex orientation support

- Durum: KABUL EDİLDİ
- Tarih: 2026-11-15
- Aşama: 2
- Onay: Kullanıcı iki yönelimi destekleme tercihini onayladı.

## Bağlam
Nihai görsel yönelim, kamera ve render aşamaları henüz uygulanmadığı için erken sabitlenmemelidir.

## Seçenekler
A. Yalnız flat-top: basit, ancak erken görsel karar dayatır.
B. Yalnız pointy-top: basit, ancak erken görsel karar dayatır.
C. İkisini desteklemek: parametrik kod maliyeti, karşılaştırma ve esneklik sağlar.

## Karar
Geometry çekirdeği Flat-top ve Pointy-top seçeneklerini destekler. Aşama 2'de biri canon olarak ilan edilmez. Nihai oyun görsel tercihi kamera/render prototipleriyle ayrı karara bırakılır.

## Gerekçe ve doğrulama
Kullanıcının açık tercihi iki yönelimi desteklemektir. Her iki formül, polygon ve dönüşüm testleriyle doğrulanır. Görsel karşılaştırma kanıtı henüz yoktur.

## Sonuçlar
İki yönelim aynı API'yi kullanır; yeni yönelim için ADR ve test gerekir.
