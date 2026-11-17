# Aşama 9 — Manuel Görsel ve İşlevsel Kabul Kontrol Listesi

> **Durum:** TAMAMLANDI VE KULLANICI TARAFINDAN KABUL EDİLDİ  
> **Kabul tarihi:** 18 Kasım 2026  
> **Çalışma dalı:** `experiment/hex-world-laboratory`

Bu kontrol listesi teknik prototipin görsel/işlevsel kabulü içindir. Nihai karakter sanatı, çevre dekorasyonu, NPC yapay zekâsı veya yoldaşların gerçek takip hareketi bu aşamanın kabul ölçütü değildir.

## 1. Demo'yu çalıştırma

Laboratuvar kök dizininde PowerShell veya terminal aç:

```powershell
cd experiments/hex_world_laboratory
python -m pip install -e ".[test]"
python scripts/run_phase_09_demo.py
```

## 2. Kontroller

| Kontrol | İşlem |
|---|---|
| Oyuncu hareketi | WASD ile hareket et; Shift ile koşu, Alt ile gizlilik modunu dene |
| Kamera | Fare tekerleğiyle yakınlaştır/uzaklaştır |
| Hedef seçimi | Fareyle NPC veya kaynak üzerine sol tıkla |
| Collider görünümü | F3 tuşuyla collider/interaction debug görünümünü açıp kapat |
| NPC eylem menüsü | Bir NPC üzerine sağ tıkla; eylem menüsünün doğru NPC için açıldığını doğrula |
| Yoldaş edinme | NPC eylem menüsünden “Yoldaş olarak al” seçeneğine tıkla |
| FOLLOW | Yoldaş NPC'ye sağ tıkla ve “Takip et (FOLLOW)” seçeneğine tıkla |
| WAIT | Yoldaş NPC'ye sağ tıkla ve “Bekle (WAIT)” seçeneğine tıkla |
| RETURN | Yoldaş NPC'ye sağ tıkla ve “Geri dön (RETURN)” seçeneğine tıkla |
| Yoldaşlıktan çıkar | Yoldaş NPC'ye sağ tıkla ve “Yoldaşlıktan çıkar” seçeneğine tıkla |
| Çıkış | ESC |

## 3. Görsel kontroller

- [x] Sahne açıldığında bir oyuncu, iki NPC ve iki kaynak görünür.
- [x] NPC'ler oyuncudan farklı görsel varlıklarla ayırt edilir.
- [x] Kaynak varlıkları NPC/oyuncu sprite'larından görsel olarak ayırt edilir.
- [x] Sprite'ların ayak/zemin temas noktaları beklenen dünya konumlarına oturur.
- [x] Y-sort sırası, dünya Y konumuna göre tutarlı görünür.
- [x] Collider debug görünümü gövde konumlarıyla hizalıdır.
- [x] Interaction yarıçapı gösterimleri kaynak/NPC hedefleriyle ilişkilidir.
- [x] Kamera yakınlaştırıldığında sprite-foot-anchor ve collider hizası bozulmaz.
- [x] Pencere boyutu değiştiğinde sahne ve kamera koordinatları tutarlı kalır.

## 4. İşlevsel kontroller

- [x] WASD hareketi oyuncuyu hareket ettirir; NPC ve kaynaklar kendiliğinden hareket etmez.
- [x] Fareyle NPC seçildiğinde sağ alt diagnostics alanında seçilen hedef kimliği görünür.
- [x] Aynı dünya noktasındaki hedef, kamera zoom seviyesi değişse de seçilebilir.
- [x] Fareyle kaynak seçimi çalışır.
- [x] NPC sağ tık menüsü doğru hedef için açılır.
- [x] Yoldaş edinme menü üzerinden çalışır ve ilişki diagnostics alanında görünür.
- [x] FOLLOW, WAIT ve RETURN komutları menü üzerinden kaydedilir.
- [x] WAIT komutu verildiği andaki NPC konumunu saklar.
- [x] Komut revizyonu her komut değişiminde artar.
- [x] FOLLOW/WAIT/RETURN komutları NPC'yi hareket ettirmez veya ışınlamaz.
- [x] Yoldaşı dismiss etme/ilişkiyi silme NPC entity'sini silmeden çalışır.
- [x] F3 collider/interaction debug görünümünü açıp kapatır.

**Kısayol notu:** Laboratuvar demosu ana oyunun başlatıcısından ve UI giriş akışından bağımsızdır. Bu nedenle C karakter ekranı kısayolu bu demoda test edilmez. C davranışı harita sistemi ana oyuna entegre edildiğinde ana oyun kabul testinde doğrulanacaktır. Laboratuvar demosunda debug görünümü için F3 kullanılır.

## 5. Otomatik doğrulama kanıtı

- [x] Laboratuvar pytest: 741/741 başarılı.
- [x] Core Quality Linux: 2.204/2.204 başarılı.
- [x] Core Quality Windows: 2.204/2.204 başarılı.
- [x] Laboratuvar benchmark adımları başarılı.
- [x] Aşama 9 entity spatial benchmark (100 / 1.000 / 10.000 entity) başarılı.
- [x] Aşama 9 PNG ve JSON sahne kanıtı üretildi ve GitHub Actions artifact olarak yüklendi.
- [x] main ve demo_eldoria dalları değişmedi.

## 6. Kabul sonucu

Kullanıcı 18 Kasım 2026 tarihinde görsel ve işlevsel testlerin tamamının başarılı olduğunu bildirmiştir.

**Manuel kabul sonucu: BAŞARILI — Aşama 9 kabul edildi.**
