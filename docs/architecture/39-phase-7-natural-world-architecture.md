# Eldoria — Aşama 7 Görsel Dünya Mimarisi

## Temel ilke
**Simülasyon altıgen, görsel dünya doğaldır.**

Aşama 7, `HexWorldRuntime`, axial koordinatlar, `WorldTransform`, kamera, hareket, yol bulma ve yedi haritalı bağlantı sözleşmelerini değiştirmez.

## Katmanlar
- **Simülasyon:** hücre koordinatları, hareket, çarpışma, yol bulma ve dünya geçişleri.
- **Görsel dünya:** sürekli zemin tabanı, organik arazi ayrıntıları, görünür alan culling'i, nesne çizimi ve derinlik.
- **Varlık:** `AssetCatalog`; PNG yolu, ölçek, anchor/pivot, collision ve animasyon metadatası.
- **İçerik:** `presentation_assets.json`; harita bazlı nesne yerleşimi, offset, footprint, collision box ve katman.

## Doğal sunum
Normal oynanışta hücre kenarı çizilmez, aktif geçiş hücreleri işaretlenmez ve axial koordinatlar oyuncu arayüzünde gösterilmez. Fare hedefi için yalnızca küçük, sade bir hedef halkası kullanılır.

Zemin önce sürekli bir arka plan olarak çizilir. Hücre verileri bunun üzerine büyük ve birbirini örten organik damgalar, doku görselleri veya deterministik ayrıntılar olarak uygulanır.

## Nesneler ve derinlik
Nesnelerin görsel boyutu çarpışma alanından bağımsızdır. `anchor` zemin temas/pivot noktasını, `collision` veya `collision_box` fiziksel etki alanını tanımlar. Derinlik sıralaması zemin ankrajı, katman ve stabil ikincil anahtar ile yapılır.

Eksik sanat dosyaları oyunu kırmaz; veri kimliğine göre düşük maliyetli, deterministik çevresel siluetler kullanılır. Bu fallback yalnızca geliştirme ve eksik içerik güvenliği içindir; gerçek PNG varlıkları aynı veri sözleşmesini kullanarak sonradan eklenebilir.

## Performans
- Görünür alan dışındaki hücre ve nesneler çizilmez.
- Zemin ve nesne ölçeklemeleri önbelleğe alınır.
- Varlık yükleme `AssetManager` üzerinden tekrar kullanılabilir.
- Çevresel sway animasyonu zaman tabanlı ve düşük maliyetlidir.

## Content Editor hazırlığı
Editor bu aşamada geliştirilmez. Ancak katalog ve yerleşim verileri gelecekte harita seçimi, zemin türü, varlık seçimi, hassas konum/ölçek, pivot, çarpışma ve katman düzenleme işlemlerine doğrudan temel sağlar.
