# Aşama 8 — Manuel Görsel ve Regresyon Kabul Kontrol Listesi

> **Durum:** Kullanıcı kontrolü bekleniyor.  
> **Amaç:** Aşama 8'in veri yapıları ve fizik sorgu değişikliklerinin mevcut Pygame dünya ekranında görsel/işlevsel gerilemeye yol açmadığını doğrulamak.

## Önemli kapsam notu

Aşama 8 yeni görsel içerik veya render özelliği eklemez. UniformGrid/Quadtree veri yapıları ve indeksli collision provider otomatik testlerle doğrulanmıştır. Oynanabilir demo varsayılan olarak mevcut linear broadphase yolunu korur; indeksli yol ayrıca test edilmiştir. Bu nedenle aşağıdaki masaüstü kontrolü bir görsel zenginleştirme testi değil, mevcut oyun ekranının regresyon kontrolüdür.

## Hazırlık

1. Laboratuvar deposunu güncel `experiment/hex-world-laboratory` dalından al.
2. PowerShell'de laboratuvar klasörüne geç:
   ```powershell
   cd experiments/hex_world_laboratory
   .\.venv\Scripts\Activate.ps1
   ```
3. Oyunu başlat:
   ```powershell
   python -m hex_world_lab
   ```

## Görsel ve işlevsel kontroller

- [ ] Pygame penceresi hatasız açılıyor ve başlangıç haritası yükleniyor.
- [ ] Oyuncu karakteri harita üzerinde normal hareket ediyor.
- [ ] Engel/duvar temasında karakter engelin içinden geçmiyor.
- [ ] Duvar boyunca çapraz hareket denendiğinde mevcut kayma davranışı korunuyor.
- [ ] Harita sınırlarında mevcut sınır/çarpışma davranışı korunuyor.
- [ ] Fareyle hex seçimi doğru hücreyi işaretliyor.
- [ ] Kamera takip, zoom ve pencere boyutu değişiminde dünya/ekran hizası bozulmuyor.
- [ ] Hareket sırasında belirgin titreme, konum sıçraması veya takılma görülmüyor.
- [ ] Debug/diagnostics ekranı varsa ekran koordinatında kalıyor.
- [ ] Önceki aşamalardan gelen hiçbir görsel davranışta gerileme yok.

## Sonuç bildirimi

Kontrol sonunda aşağıdakilerden biriyle geri bildirim ver:

- **Kabul:** Tüm maddeler başarılı.
- **Koşullu kabul:** Belirtilen maddeler dışında sorun yok; sorunlar açıklanır.
- **Ret:** Görsel/işlevsel regresyon var; hangi adımda ve nasıl oluştuğu belirtilir.

Sorun görülürse mümkünse ekran görüntüsü ve tekrar adımları ekle. Kullanıcı kabulinden sonra Aşama 8 kapanış raporu hazırlanacaktır.
