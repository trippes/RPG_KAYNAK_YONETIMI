# Mekanik Test Paketi

Bu paket yalnızca `experiment/map-cleanup` dalında aktarılan oyun mekaniklerini doğrulamak içindir. Görsel kalite, sanat varlıkları veya nihai oyun dengesi hedeflemez. Paket bağımsızdır; `demo_eldoria` ve `content/active_package.json` değiştirilmez.

## Başlatma

Proje kök dizininde:

```powershell
python main.py --play --content-package content/movement_test
```

Bu komut varsayılan aktif paket seçimini değiştirmeden doğrudan test paketini yükler.

## Test alanları

- **Oyuncu hareketi:** WASD veya yön tuşları; Shift basılıyken koşma; Alt ile gizlilik modunu açıp kapatma.
- **Hız profili:** oyuncu ve test NPC'leri için 64 dünya birimi/s başlangıç test değeri; koşma çarpanı 1.5, gizlilik çarpanı 0.5. Bunlar yalnızca test değerleridir, nihai oyun dengesi değildir.
- **Sürekli hareket ve altıgen eşlemesi:** hücre merkezleri arasında değil, hücre içinde de hareket; hücre sınırını geçerken konum ve doluluk senkronizasyonu.
- **Fizik ve çarpışma:** haritanın kuzeyindeki su/taş engel kümesi, harita sınırı ve NPC gövdeleri. Engellere doğru yürüyerek çarpışma ve duvar boyunca kayma davranışını gözlemle.
- **NPC ve etkileşim:** batıdaki görevli NPC'ye sol tıklayarak diyalog başlat; doğudaki test hedefi oyuncu hareketi için doluluk/çarpışma engeli görevi görür. Sağ tık mevcut boş eylem menüsü kabuğunu doğrular.
- **Kaynak yerleşimleri:** güneydoğu ve güneybatıdaki iki kaynak düğümü, domain kaydı ile harita yerleşiminin eşleşmesini doğrular.
- **Kayıt/yükleme:** karakter oluşturduktan sonra ESC menüsünden kaydet; ana menüye dönüp aynı kaydı yükle. Sürekli konumun ve harita varlığının korunmasını kontrol et.

## Bilinen kapsam sınırı

NPC'ler bu pakette gerçek NPC kayıtları ve harita konumlarıyla bulunur; NPC hareket hız profilleri de içerik verisi olarak yüklenir. Ancak NPC'lerin kendi kendine dolaşmasını sağlayan otonom hareket/AI orkestrasyonu henüz bu entegrasyon diliminin parçası değildir. Bu nedenle NPC hareket profili tanımlanmış olması, NPC'nin kendiliğinden yürüyeceği anlamına gelmez.

Paket bilerek sanat varlığı veya özel görsel efekt içermez. Test sırasında görülen basit/yer tutucu sunum beklenen durumdur.
