# Aşama 7 — Uygulama ve Otomatik Doğrulama Raporu

**Tarih:** 17 Kasım 2026  
**Dal:** `experiment/hex-world-laboratory`  
**Durum:** 7.1–7.8 uygulama ve otomatik doğrulama tamamlandı; kullanıcı manuel görsel kabulü bekleniyor. Aşama henüz kapatılmadı.

## 1. Kapsam sonucu

Onaylı genel plan ve teknik mimari plan kapsamındaki 7.1–7.8 çalışma paketleri uygulandı:

- 7.1: Viewport tabanlı axial hex culling ve snapshot öncesi görünür hücre seçimi.
- 7.2: Hex kenarı/merkezi/koordinat ve culling debug katmanları.
- 7.3: Normalize sprite foot-anchor ve world ground-anchor eşleştirmesi.
- 7.4: Ground-anchor Y, layer priority ve stable visual ID kullanan deterministik Y-sort.
- 7.5: Float world/screen hesapları ve nihai raster/blit konumunda tek yuvarlama.
- 7.6: ActorBodyTransform ve statik physics shape kaynaklı collider debug overlay.
- 7.7: 61–50.000 hücre profillerinde culling açık/kapalı performans benchmark'ı.
- 7.8: Bütünleşik testler, görsel sahne üretimi ve manuel kabul kontrol listesi.

A* pathfinding, click-to-move veya hareket/çarpışma sistemi değişikliği eklenmedi.

## 2. Otomatik test ve CI

- Hex World Laboratory CI: **703 test başarılı** (Python 3.12, 3.40 saniye).
- Laboratuvar benchmark adımları: başarılı.
- Görsel test sahnelerinin otomatik üretimi: başarılı.
- Görsel kanıt artifact yüklemesi: başarılı.
- Core Quality Linux: başarılı.
- Core Quality Windows: başarılı.

Laboratuvar CI: [GitHub Actions run](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44044016648)

Core Quality: [GitHub Actions run](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44044016657)

## 3. Culling performans ölçümü

**Koşullar:** GitHub-hosted Linux runner, Pygame 2.6.1, 960×640 viewport, zoom 1.0, flat-top hex, warm-up sonrası 7 tekrar (küçük/orta) veya 3 tekrar (büyük/stres). Süreler snapshot hazırlama + render ve culling sorgusu dahil ortalama pipeline süresidir.

| Harita hücresi | Görünür | Elenen | Tam pipeline | Culling pipeline | Fark |
|---:|---:|---:|---:|---:|---:|
| 61 | 61 | 0 | 1.040 ms | 1.474 ms | %41,64 yavaş |
| 128 | 128 | 0 | 3.239 ms | 2.784 ms | %14,05 hızlı* |
| 256 | 256 | 0 | 3.675 ms | 4.265 ms | %16,06 yavaş |
| 1.000 | 675 | 325 | 14.336 ms | 9.980 ms | %30,39 hızlı |
| 10.000 | 675 | 9.325 | 127.284 ms | 9.894 ms | %92,23 hızlı |
| 50.000 | 675 | 49.325 | 629.630 ms | 9.824 ms | %98,44 hızlı |

* 128 hücre profilinde hiçbir hücre elenmediği hâlde render süresi tek ölçüm serisinde daha düşük çıktı; bu sonuç culling'in hücre azaltımı sağladığı anlamına gelmez ve ölçüm varyansı olarak değerlendirilmiştir.

Ölçüm sonucu:
- 61 ve 256 hücre profillerinde tüm hücreler görünürdür; culling sorgusu ek maliyet getirir.
- 1.000 ve üzeri profillerde görünür hücre kümesi 675 hücrede kalırken harita büyüklüğü artar; pipeline kazancı belirginleşir.
- Bu nedenle uygulama varsayılanı, **257 hücreden küçük haritalarda culling'i atlar**; 257 ve üzerindeki haritalarda görünür alan sorgusunu kullanır.
- Benchmark değerleri CI makinesine aittir; kullanıcının yerel bilgisayarı için FPS garantisi değildir.

## 4. Görsel test kanıtları

Yedi PNG sahnesi otomatik olarak üretildi ve GitHub Actions artifact'ına yüklendi:

- Hex geometri/debug.
- Görünür alan culling.
- Sprite foot-anchor.
- Fiziksel collider overlay.
- Viewport kenarı culling.
- Subpixel kamera örneği.
- Y-sort/depth sıralaması.

[Phase 7 görsel sahnelerini indir — GitHub Actions artifact](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44044016648/artifacts/14310377737)

Yerel üretim komutu:

```powershell
python scripts/render_phase_07_scenes.py --output artifacts/phase-07
```

## 5. Manuel görsel kabul

Otomatik testler, benchmark'lar ve görsel sahne üretimi tamamlandı. Ancak kamera titremesi, sprite zemine oturma, Y-sort ve collider hizasının gerçek masaüstü görünümü kullanıcı tarafından kontrol edilmelidir.

Kontrol listesi: [PHASE-07-MANUAL-ACCEPTANCE-CHECKLIST.md](../docs/PHASE-07-MANUAL-ACCEPTANCE-CHECKLIST.md)

**Aşama 7 henüz kapatılmadı.** Kullanıcı manuel görsel kabul sonuçlarını bildirdikten sonra bulgular rapora işlenecek ve kapanış kararı verilecektir.

## 6. Değişmezler

- Çalışma yalnızca `experiment/hex-world-laboratory` dalında yapıldı.
- `main` ve `demo_eldoria` dallarına yazılmadı.
- Aşama 6 kamera/movement/physics davranışı korundu.
- Render katmanı simülasyon state'ini değiştirmiyor.
- A* ve click-to-move bu aşamaya dahil edilmedi.
