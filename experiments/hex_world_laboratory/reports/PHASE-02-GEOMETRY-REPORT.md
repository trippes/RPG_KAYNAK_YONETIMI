# Aşama 2 — Hex Geometri Çekirdeği Uygulama Raporu

- Proje: Eldoria — Kaynak Yönetimi RPG
- Depo: trippes/RPG_KAYNAK_YONETIMI
- Dal: experiment/hex-world-laboratory
- Tarih: 15 Kasım 2026
- Durum: UYGULANDI — KULLANICI MAKİNESİNDE DOĞRULAMA VE KABUL BEKLİYOR
- Başlangıç HEAD: a36ea81b7defb8d307fd62015367a142996587f3

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
- ADR-003: Half-up cube rounding, q/r/s düzeltme önceliği ve tolerans — uygulandı; kullanıcı kapanış kabuline sunulacak.

## 5. Test kapsamı
Axial/cube invariant, dönüşüm döngüsü, iki yönelim, farklı radius/origin, polygon köşe/kenar eşitliği, komşuluk simetrisi, mesafe, negatif koordinat, paylaşılan kenar tie-break, tolerans ve Pygame'siz import.

## 6. Test kanıtı
İzole geometri test paketi geliştirme ortamında:
- Python 3.13.5
- Linux x86_64
- 47 passed
Bu sonuç kullanıcının Windows/Python 3.12 tam laboratuvar testinin yerine geçmez.

Kullanıcı ortamında çalıştırılacak komut:
```powershell
python -m pytest -q
```

## 7. Açık konular
- Nihai görsel yönelim kamera/render aşamasında seçilecek.
- Tie-break formülü kullanıcı kapanışında değerlendirilecek.
- Çok büyük koordinatlarda floating-point hassasiyeti ayrıca stres testine tabi tutulmalı.
- WorldPosition, dünya hücre verisi, hareket, fizik, kamera ve render bu aşamanın dışındadır.

## 8. Kabul durumu
**BEKLEMEDE — KULLANICI MAKİNESİNDE TAM TEST VE KULLANICI KABULÜ GEREKLİ.**

Bu rapor Aşama 3 uygulama izni değildir.
