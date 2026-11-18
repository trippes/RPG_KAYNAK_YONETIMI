# Aşama 12 — Prosedürel Çevresel Nesneler Uygulama ve Doğrulama Raporu

> **Durum:** RESMEN KAPATILDI — OTOMATİK DOĞRULAMA VE KULLANICI MANUEL KABULÜ BAŞARILI
> **Çalışma dalı:** `experiment/hex-world-laboratory`
> **Doğrulanan commit:** `1af8abe1fce7467b25b6423a5737819e1d0260fa`
> **Hex World Laboratory CI:** [Run #44323325450](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44323325450)
> **Core Quality:** [Run #44323325329](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44323325329)
> **Görsel ve benchmark artifact:** [phase-12-environment-validation — Artifact 14436541384](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44323325450/artifacts/14436541384)

## 1. Uygulanan prosedürel çizim

Ağaç, kaya ve çalı hazır PNG/JPG/WebP dosyası yüklenmeden laboratuvarın kendi Pygame çizim koduyla üretilir.

- `rendering/procedural_environment.py`: Üç nesneye ait ayrı çizim fonksiyonları; şeffaf Surface üzerinde 3x supersampling ve son boyuta yumuşak ölçekleme.
- `EnvironmentArtPalette`: Ağaç yaprak/gövde, kaya, çalı ve zemin gölgesi renklerini parametre olarak ayırır; RGB değerleri doğrulanır.
- `rendering/environment_assets.py`: Prosedürel yüzeyleri oluşturur ve mevcut renderer'a SpriteAsset olarak kaydeder; dosya sistemi veya raster görsel yüklemez.
- Reddedilen `assets/tree_test.png` laboratuvar dalından silinmiştir.
- Aynı palet aynı piksel çıktısını üretir. Palet değişikliği çizim yüzeyini değiştirir; çevresel nesnenin world placement veya collider verisini değiştirmez.

Görsel yaklaşım stilize, katmanlı bir prototiptir; nihai sanat yönü ve masaüstü görsel kabul kararı kullanıcıya aittir.

## 2. Korunan mimari sınırlar

- `EnvironmentalObjectDefinition`, `EnvironmentalObjectPlacement` ve `EnvironmentalObjectScene` immutable domain sözleşmeleri olarak kalır.
- Ground Anchor, Depth Anchor, Visual Bounds, Canopy Bounds ve Collision Geometry ayrı sorumluluklardır.
- Ağaç gövdesi collider'ı ve kaya polygon collider'ı mevcut fizik hattına aktarılır; çalı collider'sızdır.
- Çizim boyutu, palet ve canopy görsel alanı collider üretmez.
- Ortak Y-sort kuyruğu, tam sprite bounds culling ve F4 debug görünümü korunur.
- F3 collider görünümü mevcut davranışını sürdürür.
- Tek başlatıcı `python -m hex_world_lab`; ana oyun modüllerine import veya entegrasyon yoktur.

## 3. Otomatik test ve platform CI

| Kontrol | Sonuç |
|---|---:|
| Hex World Laboratory tam test paketi | **800 passed** |
| Test failures / errors | **0 / 0** |
| Core Quality — Linux | **2.263 passed**, 1 uyarı |
| Core Quality — Windows | **2.263 passed** |
| Linux release-candidate verification | Başarılı |
| Windows release-candidate verification | Başarılı |
| Aşama 12 benchmark | 10 / 100 / 1.000 nesne, üç oturum başarılı |
| Aşama 12 görsel kanıt | 5/5 PNG sahnesi üretildi |
| Artifact upload | Başarılı |

Linux uyarısı test başarısızlığı değildir. Her iki Core Quality işi de başarıyla tamamlanmıştır.

## 4. Aşama 12 üç oturumlu performans sonuçları

Değerler üç bağımsız oturumun ölçüm medyanlarının medyanıdır. Süreler milisaniyedir.

| Nesne sayısı | Scene oluşturma | Collider adaptörü | Sprite DTO adaptörü | Debug bounds | Render culling açık | Render culling kapalı | Görünür / elenen |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0,1447 | 0,0208 | 0,0511 | 0,1278 | 0,4885 | 0,4787 | 10 / 0 |
| 100 | 0,8207 | 0,1864 | 0,5174 | 1,7432 | 0,8310 | 1,6019 | 11 / 89 |
| 1.000 | 8,6466 | 1,8533 | 6,1542 | 19,7489 | 6,5259 | 15,6021 | 91 / 909 |

- 100 nesnede culling açık render, culling kapalı duruma göre yaklaşık **%48,1** daha kısa sürdü.
- 1.000 nesnede yaklaşık **%58,2** daha kısa sürdü.
- 1.000 nesneli profilde 909 sprite viewport dışında elendi.
- Python traced-heap tepe ölçümü 1.000 nesne profilinde yaklaşık **1,345 MiB** idi. Bu değer toplam süreç RAM'i değildir.
- 10 nesnede culling elenecek nesne bulmadığından küçük sabit kontrol maliyeti gözlendi.

Bunlar GitHub Actions runner'ında gözlenen karşılaştırmalı değerlerdir; mutlak donanım performans eşiği değildir.

## 5. Görsel kanıtlar

Artifact beş sahne içerir:

1. Normal çevresel nesne sahnesi.
2. F3 collider overlay.
3. F4 anchor/bounds overlay.
4. Oyuncunun ağacın arkasında olduğu Y-sort sahnesi.
5. Oyuncunun ağacın önünde olduğu Y-sort sahnesi.

[Beş görseli ve benchmark JSON dosyasını içeren artifact](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44323325450/artifacts/14436541384)

Bu görseller otomatik üretilmiştir; kullanıcı masaüstü kabulünün yerine geçmez.

## 6. Manuel kabul ve kapanış

Kullanıcı 18 Kasım 2026 tarihinde prosedürel çevresel nesnelerin görsel ve işlevsel kabulünü verdi. Özellikle ağaç gövdesi/taç ayrımı ile kaya görseli ve çarpışma sınırlarının bütünleşik olduğu doğrulandı. Böylece otomatik ve manuel kabul kapılarının ikisi de geçildi; **Aşama 12 resmen kapatıldı**.

Kullanıcı tarafından tamamlanan temel masaüstü kontrolleri:

- Ağaç, kaya ve çalının çizim kalitesi ve ortak sanat yönü.
- Ağaç gövdesi engelleyici, yaprak tacı geçilebilir; gövde collider'ı görselle bütünleşik.
- Oyuncunun ağacın önünden ve arkasından geçişi.
- Kaya collider'ı görsel dış sınırlarıyla bütünleşik; ağaç gövdesi çarpışması doğrulandı.
- F3 ve F4 debug görünümleri.
- Kamera pan/zoom ve mevcut oyuncu/NPC/kaynak davranışlarında regresyon bulunmaması.

Kontrol adımları: [PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md](../docs/PHASE-12-MANUAL-ACCEPTANCE-CHECKLIST.md)

## 7. Son düzeltme ve manuel kabul

Son collider hizalama düzeltmesi `movement_demo.py` içinde ağaç ve kaya çarpışma çokgenlerini gerçek sprite piksel sınırları ve ground-anchor koordinatlarıyla hizaladı. `tests/unit/test_environment_collision_footprints.py` bu geometriyi regresyon testleriyle güvenceye alır. Son commit `3b33eed8aa7b73c521ae4a97391e56216d5f0ff0` için Hex World Laboratory CI #44332584764 ve Core Quality #44332584736 başarılıdır. Kullanıcı masaüstünde F3 collider görünümünü kontrol ederek ağaç ve kaya görsel/çarpışma bütünleşmesini açıkça kabul etti.

## 8. Dal güvenliği

- Bütün uygulama ve dokümantasyon değişiklikleri yalnızca `experiment/hex-world-laboratory` dalında yapıldı.
- `main` ve `demo_eldoria` dalları değiştirilmedi.
- Merge yapılmadı.
