# Aşama 12 — Uygulama ve Doğrulama Raporu

> **Durum:** ÖNCEKİ MİMARİ DOĞRULAMA TARİHSEL KAYIT — PROSEDÜREL GÖRSEL REVİZYON AÇIK
> **Çalışma dalı:** `experiment/hex-world-laboratory`
> **Kod doğrulama commit'i:** `386ca0353e22269f91a3fbff5281d1e9604013f8`
> **Laboratuvar CI:** [Run #44293278865](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44293278865)
> **Core Quality:** [Run #44293278840](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44293278840)

## 1. İş paketi durumu

| Paket | Sonuç |
|---|---|
| 12.1 — Mevcut altyapı denetimi | Tamamlandı |
| 12.2 — Ortak çevresel nesne sözleşmesi | Tamamlandı |
| 12.3 — Ağaç prototipi | Tamamlandı |
| 12.4 — Depth sorting ve görsel sınır culling | Tamamlandı |
| 12.5 — Collider/render ayrımı | Tamamlandı |
| 12.6 — Kaya ve çalı profilleri | Tamamlandı |
| 12.7 — F4 çevresel nesne debug görünümü | Tamamlandı |
| 12.8 — Test, performans, platform CI ve kanıt | Otomatik doğrulama tamamlandı; manuel kabul bekleniyor |

## 2. Uygulanan mimari

- Pygame bağımsız `environment` paketi: immutable `EnvironmentalObjectDefinition`, `EnvironmentalObjectPlacement`, `EnvironmentalObjectScene`.
- Tanımlar; asset key, normalize ground/depth anchor, opsiyonel canopy bounds ve opsiyonel mevcut fizik collider türünü taşır.
- Yerleşimler authoritative `WorldPoint`, world ID ve map ID ile sabit konumda tutulur.
- Fizik adaptörü yalnızca açıkça tanımlanmış collider'ları mevcut `ObstacleDefinition` hattına aktarır.
- Render adaptörü ağaç/kaya/çalıyı mevcut ortak Y-sort kuyruğuna ekler.
- Sprite anchor override ve tam görsel dikdörtgen culling'i eklendi.
- Viewport world AABB'si render başına bir kez hesaplanır; her sprite için tekrarlanan ekran/dünya dönüşümü kaldırıldı.
- Normal görünümde çevresel collider şekilleri ikinci bir prop gibi çizilmez; F3 debug katmanında gösterilir.
- F4; ground anchor, depth anchor, visual bounds, canopy bounds, instance ID ve dünya konumunu gösterir.
- Ağaç görseli `game_ui/assets/tree_test.png` kaynak blob'undan laboratuvar `assets/tree_test.png` dosyasına aynen kopyalandı. Laboratuvar ana oyun Python modüllerini import etmez.
- Kaya deterministik polygon collider'a, çalı ise collider'sız profile sahiptir.
- Tek başlatıcı `python -m hex_world_lab` olarak korunmuştur.

## 3. Otomatik test ve platform doğrulaması

| Doğrulama | Sonuç |
|---|---:|
| Hex World Laboratory CI test paketi | **796 passed** |
| Core Quality — Linux | **2.259 passed**, 1 uyarı |
| Core Quality — Windows | **2.259 passed** |
| Linux release-candidate verification | Başarılı |
| Windows release-candidate verification | Başarılı |
| Phase 12 görsel kanıt üretimi | 5/5 sahne başarılı |
| Phase 12 benchmark | 10 / 100 / 1.000 profil, 3 oturum başarılı |

Linux uyarısı pygame bağımlılık ağacındaki `pkg_resources` deprecation uyarısıdır; test başarısızlığı değildir.

## 4. Üç oturumlu performans sonuçları

Aşağıdaki değerler üç bağımsız oturumun oturum-medyanlarının medyanıdır. Süreler milisaniyedir. Render karşılaştırması aynı snapshot ve aynı viewport ile culling açık/kapalı ölçülmüştür.

| Nesne | Obstacle adapter | Sprite snapshot adapter | Debug bounds adapter | Render culling açık | Render culling kapalı | Görünür | Culling ile elenen |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0,0295 | 0,0790 | 0,2159 | 0,5349 | 0,5064 | 10 | 0 |
| 100 | 0,2731 | 0,8140 | 2,8045 | 1,1236 | 2,3762 | 11 | 89 |
| 1.000 | 2,6953 | 9,8229 | 32,6163 | 10,7335 | 25,4991 | 91 | 909 |

### Culling optimizasyonu

İlk ölçüm, viewport world dönüşümünün her sprite için yeniden hesaplanmasının culling maliyetini artırdığını gösterdi. Bu hesap render başına bir kez yapılacak şekilde optimize edildi.

Son ölçümde:
- 100 nesnede culling açık render yaklaşık **%52,7 daha kısa** sürdü.
- 1.000 nesnede culling açık render yaklaşık **%57,9 daha kısa** sürdü.
- 1.000 nesneli sahnede 909 sprite viewport dışında elendi.
- 10 nesneli sahnede hiçbir sprite elenmediği için culling kontrolünün küçük sabit maliyeti ölçüldü.

Bu değerler GitHub Actions runner'ında gözlenen karşılaştırmalı ölçümlerdir; mutlak donanım performans eşiği değildir.

## 5. Görsel kanıtlar

CI artifact paketi beş PNG sahnesi içerir:
1. Normal çevresel nesne sahnesi.
2. F3 collider overlay.
3. F4 anchor/bounds overlay.
4. Oyuncu ağacın arkasındayken Y-sort.
5. Oyuncu ağacın önündeyken Y-sort.

[Phase 12 benchmark ve görsel kanıt ZIP dosyası](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44293278865/artifacts/14421903600)

Artifact GitHub Actions saklama süresine tabidir.

## 6. Kalan tek kabul kapısı

Otomatik doğrulama tamamlanmıştır. Aşama 12 henüz resmen kapatılmamıştır; kullanıcı aşağıdaki kontrol listesini masaüstünde uygulayıp sonucunu bildirmelidir:

[`PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md`](../docs/PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md)

Kullanıcı manuel kontrolleri geçtiğini onayladıktan sonra kapanış raporu hazırlanacak ve Master Plan durumu Aşama 12 kapalı olarak güncellenecektir.

## 7. Dal güvenliği

- Çalışma yalnızca `experiment/hex-world-laboratory` dalında yürütüldü.
- `main` ve `demo_eldoria` dallarına yazılmadı.
- Merge yapılmadı.

## 18 Kasım 2026 kapsam revizyonu — bağlayıcı karar

Aşama 12, çevresel nesne mimarisini ve bu mimariyi doğrulayan yalnızca üç kod çizimi prototipini (ağaç, kaya, çalı) kapsar. Hazır PNG/JPG/WebP dosyaları bu prototiplerin görsel kaynağı olarak kullanılmayacaktır; yüzeyler Pygame çizim primitifleri ve deterministik geometriyle koddan üretilecektir.

Aşama 12 içinde çizim fonksiyonları, paletler, geometri ve nesne profilleri ayrık/parametrelenebilir tutulur. Ağaçta kök-gövde, dallar, farklı tonlarda yaprak kümeleri, hacim, ışık ve gölge; kayada çok yüzeyli hacim ve ışık-gölge; çalıda kümelenmiş yapraklar ve alt gölge bulunur. Üç nesne aynı sanat yönü ve harita ölçeği kalitesini hedefler. Ground Anchor, Depth Anchor, Visual Bounds, Canopy Bounds ve Collision Geometry çizimden bağımsız kalır. Çizim collider üretmez. Aynı parametreler deterministik sonuç verir.

Aşama 12 dışında: genel amaçlı grafik motoru, serbest biçimli çizim arayüzü, fareyle dal/yaprak düzenleme, içerik kütüphanesi, dosya içe/dışa aktarma aracı, bina/karakter/NPC çizim paketi, animasyon/rig/wind sistemi ve ana oyun entegrasyonu.

Aşama 13, farklı içerik türlerini destekleyen genel prosedürel grafik/çizim altyapısıdır. Aşama 14, bu altyapıyı kullanan Content Editor ve görsel düzenleme araçlarıdır. İki aşama da ayrıca planlanıp onaylanacaktır.

Önceki doğrulama raporundaki tree_test.png kopyası yeni karar kapsamında kabul edilmez; PNG tabanlı sunum geçici/ret edilmiş prototiptir. Önceki test/CI sonuçları yalnızca o commit'teki teknik kod için geçerlidir; prosedürel görsel kabul kanıtı değildir. Aşama 12'nin görsel uygulaması, testleri, benchmarkı, CI ve manuel kabulü yeniden tamamlanmalıdır.
