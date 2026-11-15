# Aşama 2 — Hex Geometri Çekirdeği Uygulama Raporu

- Proje: Eldoria — Kaynak Yönetimi RPG
- Depo: trippes/RPG_KAYNAK_YONETIMI
- Dal: experiment/hex-world-laboratory
- Tarih: 15 Kasım 2026
- Durum: UYGULANDI — TEKNİK TESTLER GEÇTİ; ADR-003 VE KULLANICI KAPANIŞ KABULÜ BEKLENİYOR
- Başlangıç HEAD: a36ea81b7defb8d307fd62015367a142996587f3
- Geometri uygulama commit'i: 32c0ab33cf1b10b8dfe5d8f75aa76c5d446dec69

## 1. Hedef
Pygame'den bağımsız saf Python hex koordinat ve geometri çekirdeği. Dünya modeli, hareket, fizik, kamera ve render kapsam dışıdır.

## 2. Onaylanan tercihler
- Flat-top ve pointy-top desteklenir.
- Dünya eksenleri matematiksel: X sağa, Y yukarı.
- Hex boyutu circumradius.
- Axial (0,0) hücresinin merkezi layout origin'idir.
- Nihai görsel yönelim bu aşamada seçilmemiştir.

## 3. Uygulanan modüller
- coordinates.py: AxialCoord, CubeCoord, WorldPoint.
- orientation.py: Flat-top ve pointy-top.
- layout.py: yönelim, circumradius ve origin.
- transforms.py: axial/cube, axial/world, fractional axial ve cube rounding.
- polygon.py: altı köşe, kenar ve hücre polygon'u.
- neighbors.py: altı axial komşu yönü.
- distance.py: hex mesafesi.
- tolerance.py: merkezi mutlak/göreli tolerans.
- geometry/__init__.py: geometri API dışa aktarımı.

## 4. ADR kayıtları
- ADR-001: İki yönelimi destekleme — kullanıcı tercihiyle kabul edildi.
- ADR-002: Matematiksel eksen, origin ve circumradius — kullanıcı tercihiyle kabul edildi.
- ADR-003: Half-up cube rounding, q/r/s düzeltme önceliği ve tolerans — uygulandı; nihai mimari karar için kullanıcı değerlendirmesi bekleniyor.

## 5. Test kapsamı
Axial/cube invariant, dönüşüm döngüsü, iki yönelim, farklı radius/origin, polygon köşe/kenar eşitliği, komşuluk simetrisi, mesafe, negatif koordinat, paylaşılan kenar tie-break, tolerans ve Pygame'siz import.

## 6. Test kanıtı

### Geliştirme ortamı — izole geometri test paketi
- Python 3.13.5
- Linux x86_64
- 47 passed

### Kullanıcı ortamı — tam laboratuvar test paketi
- İşletim sistemi: Windows
- Python: 3.12.10
- Komut: `python -m pytest -q`
- Kullanıcının teyit ettiği sonuç: **49 passed**
- Kullanıcı, 49/49 sonucunun yukarıdaki tam laboratuvar test komutundan alındığını açıkça doğruladı.

İki sonuç farklı ortamlara ve test kapsamlarına aittir; birbirinin yerine yazılmamıştır.

## 7. Açık konular
- Nihai görsel yönelim kamera/render aşamasında seçilecek.
- Tie-break ve tolerans politikası ADR-003 kapsamında kullanıcı kapanışında kabul edilmeli veya revize edilmelidir.
- Çok büyük koordinatlarda floating-point hassasiyeti ayrıca stres testine tabi tutulmalı.
- WorldPosition, dünya hücre verisi, hareket, fizik, kamera ve render bu aşamanın dışındadır.

## 8. Kabul durumu
**TEKNİK TESTLER GEÇTİ (49/49, kullanıcı ortamı). AŞAMA KAPANIŞI ADR-003'ÜN KULLANICI TARAFINDAN DEĞERLENDİRİLMESİ VE KABULÜNE BAĞLIDIR.**

Bu rapor Aşama 3 uygulama izni değildir.
