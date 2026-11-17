# Aşama 9 — Manuel Görsel ve İşlevsel Kabul Kontrol Listesi

> **Durum:** Otomatik doğrulama tamamlandı — kullanıcı manuel kabulini bekliyor  
> **Tarih:** 17 Kasım 2026  
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
| Hedef seçimi | Fareyle NPC veya kaynak üzerine tıkla |
| Collider görünümü | C tuşuyla collider/interaction debug görünümünü açıp kapat |
| Yoldaş edinme | R tuşuyla muhafız NPC'yi yoldaş olarak al |
| FOLLOW | 1 tuşuna bas |
| WAIT | 2 tuşuna bas |
| RETURN | 3 tuşuna bas |
| Çıkış | ESC |

## 3. Görsel kontroller

- [ ] Sahne açıldığında bir oyuncu, iki NPC ve iki kaynak görünür.
- [ ] NPC'ler oyuncudan farklı görsel varlıklarla ayırt edilir.
- [ ] Kaynak varlıkları NPC/oyuncu sprite'larından görsel olarak ayırt edilir.
- [ ] Sprite'ların ayak/zemin temas noktaları beklenen dünya konumlarına oturur.
- [ ] Y-sort sırası, dünya Y konumuna göre tutarlı görünür.
- [ ] Collider debug görünümü gövde konumlarıyla hizalıdır.
- [ ] Interaction yarıçapı gösterimleri kaynak/NPC hedefleriyle ilişkilidir.
- [ ] Kamera yakınlaştırıldığında sprite-foot-anchor ve collider hizası bozulmaz.
- [ ] Pencere boyutu değiştiğinde sahne ve kamera koordinatları tutarlı kalır.

## 4. İşlevsel kontroller

- [ ] WASD hareketi oyuncuyu hareket ettirir; NPC ve kaynaklar kendiliğinden hareket etmez.
- [ ] Fareyle NPC seçildiğinde sağ alt diagnostics alanında seçilen hedef kimliği görünür.
- [ ] Aynı dünya noktasındaki hedef, kamera zoom seviyesi değişse de seçilebilir.
- [ ] Fareyle kaynak seçimi çalışır.
- [ ] R ile muhafız yoldaş olarak kaydedilir; diagnostics alanında ilişki görünür.
- [ ] 1 komutu FOLLOW durumunu kaydeder.
- [ ] 2 komutu WAIT durumunu kaydeder ve verildiği andaki NPC konumunu saklar.
- [ ] 3 komutu RETURN durumunu kaydeder.
- [ ] Komut revizyonu her komut değişiminde artar.
- [ ] FOLLOW/WAIT/RETURN komutları NPC'yi hareket ettirmez veya ışınlamaz.
- [ ] Yoldaşı dismiss etme/ilişkiyi silme otomatik testlerde NPC entity'sini silmeden çalışır.

## 5. Otomatik doğrulama kanıtı

- [x] Laboratuvar pytest: 741/741 başarılı.
- [x] Core Quality Linux: 2.204/2.204 başarılı.
- [x] Core Quality Windows: 2.204/2.204 başarılı.
- [x] Laboratuvar benchmark adımları başarılı.
- [x] Aşama 9 entity spatial benchmark (100 / 1.000 / 10.000 entity) başarılı.
- [x] Aşama 9 PNG ve JSON sahne kanıtı üretildi ve GitHub Actions artifact olarak yüklendi.
- [x] main ve demo_eldoria dalları değişmedi.

## 6. Kabul sonucu

Kullanıcı yukarıdaki görsel ve işlevsel kontrolleri tamamlayıp sonucu bildirdiğinde Aşama 9 kapanış raporu hazırlanacaktır. Bu kontrol listesi tamamlanmadan aşama resmen kapatılmış sayılmaz.

**Manuel kabul sonucu:** Bekleniyor.
