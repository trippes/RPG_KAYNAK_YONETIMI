# Aşama 3.5 — Dünya Görünümü ve Çalışma Zamanı Teknik Planı

**Durum:** KULLANICI ONAYI ALINDI — UYGULAMA VE DOĞRULAMA TAMAMLANDI (194 TEST)  
**Aşama:** 3.5  
**Çalışma dalı:** `experiment/hex-world-laboratory`  
**Ön koşul HEAD:** `5399dcb43c4c3548698bce9ba8fbe0365b0a6654`

## 1. Amaç

Haritanın değişmeyen başlangıç tanımını, oyun çalışırken meydana gelen hücre değişikliklerinden ayırmak ve diğer sistemlere hücrelerin güncel durumunu salt okunur bir arayüzle sunmak.

Bu aşama, Aşama 3'te tanımlanan `HexWorld`, `HexWorldView` ve `HexWorldRuntime` mimarisini tamamlar. Harita tanımı başlangıç verisi olarak kalır; çalışma zamanı yalnızca değişiklikleri saklar; görünüm iki kaynağı birleştirerek güncel hücre durumunu sunar.

## 2. Temel mimari

### 2.1. HexMapDefinition — değişmeyen başlangıç tanımı

Aşama 3.3'te oluşturulmuş `HexMapDefinition` değiştirilmeden başlangıç verisinin kaynağı olarak kullanılacaktır.

Aşağıdakiler çalışma zamanı tarafından değiştirilemez:
- Dünya ve harita kimliği.
- Hücre adresleri ve haritanın hücre kümesi.
- Harita geometrisi, yönelimi, başlangıç noktası ve hex boyutu.
- Hücre metadata bilgileri.
- Hücrelerin başlangıç arazi, geçilebilirlik ve engel değerleri.

### 2.2. HexWorldRuntime — seyrek değişiklik deposu

Yeni `HexWorldRuntime`, yalnızca başlangıç tanımından farklı olan hücre alanlarını saklar.

- Değişiklik anahtarı: `(MapId, AxialCoord)`. Runtime tek bir `HexWorld` örneğine aittir; bu nedenle WorldId ayrıca anahtara eklenmez.
- Desteklenen değişebilir alanlar yalnızca `terrain_id`, `is_walkable` ve `has_obstacle` olacaktır.
- Hücre metadata'sı, adresi, geometrisi ve hücre varlığı değiştirilemez.
- Yalnızca başlangıç değerinden farklı alanlar saklanır. Bir alan başlangıç değerine döndürülürse o alanın override kaydı kaldırılır. Hücrede override kalmazsa hücre kaydı da silinir.
- Runtime, haritanın tamamını veya değişmeyen hücreleri kopyalamaz.
- Runtime içindeki değiştirilebilir sözlükler veya kayıtlar dışarıya açılmaz.

Mutasyonlar yalnızca harita kayıtlı ve yüklü olduğunda, ayrıca hedef hücre harita tanımında mevcut olduğunda yapılabilir. Bilinmeyen harita için `UnknownMapError`, kayıtlı fakat yüklü olmayan harita için `MapNotLoadedError`, haritada bulunmayan hücre için `UnknownCellError` kullanılır. Başka bir WorldId'ye ait adres reddedilir.

Runtime API'si, desteklenen alanları değiştirmek ve sıfırlamak için açık metotlar sunacaktır. Uygulama, alanı değiştirmeden önce tür doğrulaması yapacak ve geçersiz değerleri reddedecektir. `None` bir alanı sıfırlama anlamına gelmeyecek; sıfırlama ayrı ve açık metotlarla yapılacaktır.

### 2.3. HexWorldView — salt okunur güncel dünya görünümü

Yeni `HexWorldView`, bir `CellAddress` için başlangıç hücre verisini ve varsa runtime override'larını birleştirerek güncel, değiştirilemez `HexCellData` sonucunu sunar.

- Override bulunmayan hücrede başlangıç `HexCellData` nesnesi doğrudan döndürülebilir.
- Override bulunan hücrede yalnızca sorgu sırasında güncel bir immutable sonuç oluşturulur; kalıcı tam harita kopyası veya önbellek oluşturulmaz.
- Metadata her zaman başlangıç tanımından gelir.
- View, runtime mutasyon metotlarını veya iç kayıtlarını dışarıya sunmaz.
- `get_cell(address)`: Hücre mevcut değilse `None`; mevcutsa güncel hücre verisi. Bilinmeyen harita `UnknownMapError`, kayıtlı fakat yüklenmemiş harita `MapNotLoadedError` üretir.
- `require_cell(address)`: Hücre mevcut değilse `UnknownCellError`; diğer harita/yükleme hataları `get_cell` ile aynı şekilde korunur.
- Başka bir WorldId'ye ait adres reddedilir.

Böylece haritada bulunmayan hücre ile geçici olarak yüklenmemiş harita birbirine karıştırılmaz.

### 2.4. HexWorld sahipliği ve harita yaşam döngüsü

`HexWorld`, kendi `MapRegistry` nesnesinin yanında tek bir `HexWorldRuntime` ve tek bir `HexWorldView` örneğine sahip olacaktır. Bu bileşenler aynı WorldId ve MapRegistry bağlamını kullanır. Bağımlılıklar tek yönlü kurulacak; modüller arasında döngüsel import oluşturulmayacaktır.

Harita yaşam döngüsü:
- `register_map`: Mevcut kayıt davranışı korunur; runtime hücre verisi oluşturulmaz.
- `load_map`: Harita tanımı yüklendiğinde mevcut seyrek override'lar görünüm tarafından tekrar uygulanır.
- `unload_map`: Yüklü harita tanımı bellekten çıkarılır; haritaya ait seyrek runtime override'ları korunur. Bu, harita tekrar yüklendiğinde oyuncunun değişikliklerinin kaybolmamasını sağlar.
- `remove_map`: Harita kaydı ve varsa yüklü tanımı kaldırılır; o MapId'ye ait runtime override'ları da temizlenir.

Bu aşamada override'lar yalnızca süreç belleğinde yaşar. Uygulama kapandığında kalıcı olmayacaktır; disk kaydı/yüklemesi bu aşamanın kapsamında değildir.

## 3. Gelecekteki iç mekân haritalarıyla uyumluluk

Binaların iç mekânları ileride ayrı ve bağımsız `MapId` değerlerine sahip normal haritalar olarak modellenebilecektir. Örneğin bir köy dış haritası, demirci dükkânının iç haritası ve dükkânın üst katı ayrı haritalar olabilir.

Bu aşamada yalnızca mimari uyumluluk gözetilecektir:
- İç ve dış mekânlar aynı harita tanımı, kayıt, yükleme, runtime ve view mekanizmalarını kullanabilecektir.
- Her haritanın hücreleri ve runtime değişiklikleri kendi MapId alanında yalıtılır.
- Yapı nesnesi ile iç harita arasındaki bağlantı, kapı/geçiş sistemi ve kat bağlantıları daha sonraki ayrı bir aşamada tasarlanacaktır.

Aşama 3.5'te bina, kapı, iç mekân üretimi veya haritalar arası geçiş kodu yazılmayacaktır.

## 4. Değiştirilecek dosyalar

| Dosya | İşlem | Sorumluluk |
|---|---|---|
| `src/hex_world_lab/world/runtime.py` | Yeni | Seyrek hücre alanı override'ları ve kontrollü mutasyon API'si |
| `src/hex_world_lab/world/world_view.py` | Yeni | Salt okunur güncel hücre görünümü |
| `src/hex_world_lab/world/world.py` | Güncelleme | Runtime ve View sahipliği; harita yaşam döngüsü entegrasyonu |
| `src/hex_world_lab/world/__init__.py` | Güncelleme | Yeni public tip ve sınıfların dışa aktarımı |
| `tests/unit/test_world/test_runtime.py` | Yeni | Runtime davranışı ve yaşam döngüsü testleri |
| `tests/unit/test_world/test_world_view.py` | Yeni | Güncel görünüm, hata semantiği ve salt okunurluk testleri |

Başka dosyalara ihtiyaç doğarsa uygulama sırasında kapsam genişletilmeyecek; önce kullanıcıya gerekçesi sunulup ek onay alınacaktır.

## 5. Uygulama yaklaşımı

1. Mevcut `HexWorld`, `MapRegistry`, `HexMapDefinition`, `HexCellData` ve hata tipleri tekrar incelenecek.
2. Runtime için immutable override değer nesnesi ve private seyrek kayıt yapısı kurulacak.
3. Mutasyon API'si dünya kimliği, harita kayıt/yükleme durumu, hücre varlığı ve alan tiplerini doğrulayacak.
4. Harita unload/remove davranışları runtime kayıtlarıyla entegre edilecek.
5. WorldView, başlangıç verisi ile override'ları birleştiren salt okunur arayüz olarak eklenecek.
6. HexWorld, runtime ve view bileşenlerini sahiplenip dışa açacak.
7. Hedefli testler, ardından laboratuvarın tam test paketi çalıştırılacak.

## 6. Test ve kabul ölçütleri

### Runtime testleri
- Başlangıç harita tanımı mutasyonlardan sonra değişmeden kalır.
- Yalnızca başlangıç değerinden farklı alanlar saklanır.
- Bir alanı başlangıç değerine döndürmek o override'ı kaldırır.
- Son override da kaldırıldığında hücre kaydı silinir.
- Geçersiz alan türleri/değerleri reddedilir.
- Bilinmeyen WorldId, harita, yükleme durumu ve hücre adresi doğru hata tipleriyle ele alınır.
- Aynı axial koordinatın farklı MapId değerlerindeki kayıtları birbirinden bağımsızdır.
- Unload override'ları korur; yeniden load güncel durumu yeniden görünür kılar.
- Remove ilgili haritanın tüm override'larını temizler.

### WorldView testleri
- Override olmayan hücre başlangıç verisini sunar.
- Override olan hücre güncel değerleri sunar; değişmeyen metadata başlangıç tanımından korunur.
- View üzerinden runtime veya harita tanımı değiştirilemez.
- Eksik hücre için `get_cell` None, `require_cell` UnknownCellError üretir.
- Bilinmeyen harita ve yüklü olmayan harita eksik hücreyle karıştırılmaz.
- Başka WorldId'ye ait adres reddedilir.
- Farklı haritaların aynı koordinattaki hücreleri birbirine karışmaz.

### Genel kabul
- Önceki kimlik, harita tanımı, çoklu harita ve geometri testleri gerileme olmadan geçer.
- Laboratuvarın tam test paketi başarılı olur.
- Yalnızca belirtilen laboratuvar dosyaları değiştirilir.
- GitHub Actions laboratuvar CI sonucu başarılı olur.
- Commit ve son dosya içerikleri GitHub üzerinden doğrulanır.

## 7. Kapsam dışı

- Ağaç, taş, sandık, bina, eşya gibi bağımsız oyun nesneleri sistemi.
- Yapı yerleştirme, bina iç haritaları, kapılar, katlar ve haritalar arası geçiş.
- Oyuncu hareketi, çarpışma ve pathfinding.
- NPC veya kaynak simülasyonu.
- Render, kamera, Pygame arayüzü ve harita editörü.
- Diskten harita yükleme veya runtime değişikliklerini diske kaydetme.
- Otomatik yükleme/tahliye, cache/eviction ve bellek bütçesi yönetimi.
- Pasif harita simülasyonu veya offline progression.
- Ana Eldoria oyununa entegrasyon.

## 8. Riskler ve önlemler

- **Başlangıç verisinin yanlışlıkla değiştirilmesi:** Runtime yalnızca override tutar; testler başlangıç tanımının değişmediğini doğrular.
- **Harita yaşam döngüsünde veri kaybı:** Unload ve remove davranışları ayrı tanımlanır ve test edilir.
- **Eksik hücre ile yüklenmemiş haritanın karıştırılması:** Ayrı hata semantiği uygulanır.
- **Bellek kullanımının artması:** Yalnızca farklı alanlar saklanır; tam harita kopyası ve önbellek oluşturulmaz.
- **Modüller arası döngüsel bağımlılık:** Runtime ve View, MapRegistry üzerinden gerekli harita bilgisine erişir; import yönleri açık tutulur.
- **Erken kapsam genişlemesi:** Yapı/iç mekân bağlantıları bu aşamada yalnızca uyumluluk hedefi olarak belgelenir.

## 9. Güvenlik ve değişiklik sınırları

- Bütün işlemler yalnızca `experiment/hex-world-laboratory` dalında yapılacaktır.
- Uygulama öncesi branch HEAD ve değiştirilecek dosyaların güncel SHA değerleri doğrulanacaktır.
- `main` ve `demo_eldoria` dallarına yazma, merge, cherry-pick veya rebase yapılmayacaktır.
- Bu belgeyi kaydetme onayı kod uygulama onayı değildir. Kod değişiklikleri için kullanıcıdan ayrıca açık onay alınacaktır.

## 10. Tamamlanma koşulu

Aşama 3.5; belirtilen dosyalar uygulandığında, hedefli ve tam testler başarılı olduğunda, laboratuvar CI geçtiğinde ve GitHub üzerindeki commit/dosya durumu doğrulandığında tamamlanmış sayılır.
