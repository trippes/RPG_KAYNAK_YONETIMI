# Aşama 7 — Manuel Görsel Kabul Kontrol Listesi

**Durum:** Otomatik doğrulama tamamlandıktan sonra kullanıcı görsel kabulü bekliyor  
**Kapsam:** Yalnızca Aşama 7 — Render ve Görsel Doğrulama  
**Dal:** `experiment/hex-world-laboratory`

Bu liste, otomatik testlerin kanıtlayamadığı görsel davranışları masaüstünde doğrulamak içindir. Hiçbir madde kullanıcı kontrolü yapılmadan PASS olarak işaretlenmemelidir.

## 1. Hazırlık

PowerShell'de laboratuvar klasörüne geç:

```powershell
cd "C:\Users\sabri\Documents\GitHub\RPG_KAYNAK_YONETIMI\experiments\hex_world_laboratory"
python -m pip install -e ".[test]"
```

Görsel test sahnelerini üret:

```powershell
python scripts/render_phase_07_scenes.py --output artifacts/phase-07
```

Aşağıdaki PNG dosyalarını açıp incele:

- `01-hex-geometry-debug.png`
- `02-visible-region-culling.png`
- `03-sprite-foot-anchor.png`
- `04-collider-physics-overlay.png`
- `05-viewport-edge-culling.png`
- `06-subpixel-camera-sample.png`
- `07-y-sort-depth-order.png`

Ardından uygulamayı başlat:

```powershell
python -m hex_world_lab
```

## 2. Görsel kontroller

| ID | Kontrol | Beklenen sonuç | Sonuç |
|---|---|---|---|
| V-01 | Hex sınırları ve merkezleri | Merkez işaretleri hücrelerin gerçek geometrik merkezlerinde; sınırlar düzgün ve boşluksuz | BEKLENİYOR |
| V-02 | Koordinat etiketleri | Her etiket doğru axial `q,r` hücresini gösteriyor; komşu hücreye kaymıyor | BEKLENİYOR |
| V-03 | Görünür alan culling | Viewport kenarlarında kısmen görünen hex'ler eksiksiz; boş zemin veya kesilmiş hücre yok | BEKLENİYOR |
| V-04 | Sprite foot-anchor | Karakterin ayak/zemin noktası hareket ve zoom sırasında dünya konumuna sabit oturuyor | BEKLENİYOR |
| V-05 | Y-sort | Karakter/nesne üstünden ve altından geçerken önde-arkada görünme sırası doğru | BEKLENİYOR |
| V-06 | Kamera subpixel davranışı | Yavaş kamera hareketinde belirgin titreme, sıçrama veya sprite-zemin kayması yok | BEKLENİYOR |
| V-07 | Collider overlay | Magenta fiziksel collider çizgileri gerçek fizik sınırlarıyla ve aktör ground-anchor'ıyla hizalı | BEKLENİYOR |
| V-08 | Debug katmanları | Merkez, koordinat, culling ve collider katmanları normal dünya görünümünü bozmadan okunaklı | BEKLENİYOR |
| V-09 | Kamera zoom/pan | Fare tekerleğiyle yakınlaştırma/uzaklaştırma ve karakter hareketi sırasında dünya görselleri birlikte tutarlı hareket ediyor | BEKLENİYOR |
| V-10 | Pencere yeniden boyutlandırma | Viewport değiştiğinde hücreler, sprite ve debug overlay doğru hizayı koruyor | BEKLENİYOR |
| V-11 | Normal görünüm | Debug overlay kapalıyken normal dünya görünümü temiz; debug çizgileri görünmüyor | BEKLENİYOR |
| V-12 | Ekran sabitli tanılar | FPS ve tanı paneli kamera pan/zoom'undan etkilenmiyor | BEKLENİYOR |

## 3. Hareket sırasında kontrol

1. Karakteri WASD ile farklı yönlerde hareket ettir.
2. Özellikle çapraz hareket sırasında sprite ayak noktasını izle.
3. Hareket ederken fare tekerleğiyle zoom seviyesini birkaç kez değiştir.
4. Karakter hareket ederken pencereyi büyütüp küçült.
5. Ağaç/taş/duvar gibi engellerin önünden ve arkasından geçerek örtüşme sırasını kontrol et.
6. Görsel konum ile fiziksel collider arasında gözle görülür kayma olup olmadığını incele.

Bu aşamada fareyle hedef seçerek hareket veya A* yol bulma bulunmaz; bu kontroller yapılmayacaktır.

## 4. Sonuç

- PASS: Görsel davranış beklendiği gibi.
- FAIL: Görsel hata veya hizalama sorunu var.
- BLOCKED: Kontrol gerçekleştirilemedi.

Kullanıcı sonucu ve varsa ekran görüntüsü/ekran kaydı notları, Aşama 7 kapanış raporuna aktarılacaktır. Kullanıcı görsel kabulü verilene kadar Aşama 7 kapatılmış sayılmaz.
