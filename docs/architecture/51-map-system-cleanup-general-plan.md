# Harita Sistemi Temizliği — Genel Plan

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Durum | Genel plan onaylandı; teknik plan easter egg kararıyla revize edildi |
| Kapsam | Ana altıgen dünya sisteminin sadeleştirilmesi ve tek kare harita easter egg'inin korunması |

## 1. Amaç ve ürün kararı

Laboratuvarda geliştirilen yeni dünya/harita altyapısı ana oyuna aktarılmadan önce, `demo_eldoria` dalındaki mevcut harita sistemini güvenli biçimde incelemek, sadeleştirmek ve entegrasyona hazırlamak.

Harita sistemleri için ürün kararı:

- **Altıgen harita:** Eldoria'nın ana ve yetkili dünya haritası sistemi olacaktır. Normal dünya dolaşımı ve ana oyun harita akışları bu sistemde yürütülecektir.
- **Kare harita:** Gelecekte detaycı oyuncuların keşfedebileceği tek ve sabit bir easter egg haritası olarak korunacaktır. İkinci bir ana dünya veya alternatif harita altyapısı olmayacaktır.
- **Sınır:** Kare harita, yalnızca tek haritayı yüklemek/göstermek ve ileride ayrıca kararlaştırılacak sınırlı etkileşimi desteklemek için gereken asgari kod ve veriyle yaşayacaktır. Yeni kare haritalar, editör, prosedürel üretim, çoklu harita ağı veya bağımsız kare dünya simülasyonu geliştirilmeyecektir.
- Kare ve altıgen koordinatlar birleştirilmeyecek; iki sistem arasında örtük konum/state paylaşımı kurulmayacaktır.

Temizlik çalışması kendi başına bir entegrasyon değildir. Bu aşamada Hex World Laboratory kodu ana oyuna taşınmayacak. Laboratuvar dalı, Aşamalar 0–15'in teknik referansı ve arşivi olarak korunacaktır.

## 2. Dal stratejisi

1. `experiment/map-cleanup`, `demo_eldoria` dalının onaylı başlangıç HEAD'inden oluşturulur.
2. Tüm inceleme, düzenleme, test ve dokümantasyon bu dalda yürütülür.
3. `demo_eldoria` ve `main` doğrudan değiştirilmez.
4. `experiment/hex-world-laboratory` dalına commit, merge veya rebase yapılmaz.
5. Temizlik tamamlandıktan ve kullanıcı kabulünden sonra, bu dalda hazırlanmış temiz altyapı ile laboratuvar sistemleri ayrı entegrasyon çalışmasında birleştirilir.
6. Birleşik sürüm test ve görsel kabulden geçerse kullanıcı onayıyla `demo_eldoria` dalına aktarılır. Laboratuvar dalı arşiv olarak tutulur.

## 3. Mevcut sistemin ilk envanteri

İlk depo taramasında aşağıdaki alanlar tespit edildi:

- `world/`: kare tabanlı yerel harita tanımları/yükleyicileri ve konum grafı.
- `application/`: içerik paketi yükleme, kare/altıgen harita tanımları, dünya haritası doğrulama, altıgen hareket ve geçiş runtime'ı.
- `core/world/`: dünya kimliği/yönetimi ve eski runtime uyumluluk kodu.
- `game_ui/`: kare harita ekranı, altıgen dünya görünümü, kamera, dönüşüm ve çizim katmanı.
- `content/demo_eldoria/maps/`: schema v1 kare harita adayları ile schema v2 altıgen haritalar.
- `content/demo_eldoria/world.json`: altıgen dünya yerleşim/bağlantı tanımı.
- `content/demo_eldoria/placements/`, `asset_catalog.json` ve `presentation_assets.json`: görsel varlık ve sahne yerleşimi verileri.
- `tests/test_world/`, `tests/test_application/`, `tests/test_game_ui/`, `tests/test_foundation/`, `tests/test_architecture/` ve uyumluluk testleri.

Bu envanter başlangıç keşfidir; kare harita adaylarından hangisinin korunacağı ve hangi eski modüllerin gereksiz olduğu henüz kesinleştirilmemiştir. Bir dosyanın kullanılmadığına veya silinebileceğine dair tek başına kanıt değildir.

## 4. Genel çalışma adımları

### 16.1 — Envanter ve bağımlılık haritası
Harita modülleri, import/call ilişkileri, giriş noktaları, testler, içerik dosyaları ve kayıt referansları çıkarılır. Ana altıgen dünya için gerekli parçalar, tek kare easter egg için gereken asgari parçalar, uyumluluk amaçlı bileşenler ve sahipsiz olduğu düşünülen parçalar ayrı sınıflandırılır.

### 16.2 — Harita veri paketinin denetimi
Tüm harita JSON dosyaları, schema sürümleri, benzersiz map ID'leri, geçiş hedefleri, dünya yerleşimleri, başlangıç konumları, hücre koordinatları ve asset/placement referansları doğrulanır. Ana altıgen dünya içerikleri korunur. Kare harita adaylarından tek bir easter egg haritası seçilir; diğer kare içerikler ancak manifest/kod/test/save bağımlılıkları incelendikten sonra deprecate/remove adayı olabilir.

### 16.3 — Runtime ve koordinat sahipliği
Ana altıgen dünya için authoritative konum/runtime zinciri belgelenir. Kare easter egg'in yükleme ve sunum için ihtiyaç duyduğu minimum runtime belirlenir. Kare harita `(x, y)`, altıgen axial `(q, r)`, `LocalHexPosition`, `EntityPosition`, dünya yerleşimi ve piksel/screen koordinatları ayrı sözleşmeler olarak ele alınır. Kare/hex koordinat dönüşümü veya örtük state paylaşımı yapılmaz.

### 16.4 — UI/render ve geçiş akışları
Normal gameplay'in altıgen dünya görünümü ve geçişleri incelenir. Kare harita ekranının tek easter egg sahnesi için gereken minimum sunum yolu ayrıştırılır. Olası easter egg erişim/çıkış biçimi bu aşamada ürün tasarımı olarak varsayılmaz. Görsel sunumun authoritative gameplay state'i değiştirmemesi ilkesi korunur.

### 16.5 — Kontrollü sadeleştirme
Tek kare harita için gerekli veri, loader, render/UI ve gerekiyorsa sınırlı etkileşim yüzeyi korunur. Çoklu kare harita katalogları, gereksiz dünya grafı/runtime bileşenleri ve kullanılmayan kare içerikler yalnızca bağımlılık, save ve test kanıtıyla deprecate/remove edilir. Önce test/çağrı kanıtı, sonra küçük refactor veya deprecation, en son kaldırma uygulanır.

### 16.6 — Regresyon ve kullanıcı kabulü
Temiz kurulum, otomatik testler, içerik paketi yükleme, ana altıgen dünya dolaşımı, geçişler, hareket, çarpışma, yerleşimler, kamera, kayıt/yükleme ve mevcut oynanabilir akış doğrulanır. Seçilmiş tek kare easter egg haritasının yüklenmesi/gösterilmesi de doğrulanır. Kullanıcı görsel ve işlevsel kabulü tamamlamadan aşama kapanmaz.

### 16.7 — Entegrasyona hazır olma kararı
Ana altıgen dünya mimarisi, korunacak tek kare easter egg yüzeyi, kalan legacy adaptörleri, kaldırılan parçalar ve laboratuvarla entegrasyon sınırları raporlanır. Sonuç "hazır", "koşullu hazır" veya "hazır değil" olarak gerekçelendirilir.

## 5. Güvenlik ve değişmezler

- Ana altıgen dünya, ana oyunun tek yetkili dünya sistemi olarak korunur.
- Tek kare easter egg haritası, gerçek veri/bağımlılık incelemesiyle seçilir; kimliği envanterden önce varsayılmaz.
- Kare harita sistemi yeni haritalar veya genel amaçlı genişletilebilir altyapı yönünde büyütülmez.
- Kare ve axial koordinatlar ayrı kalır; örtük koordinat dönüşümü veya ortak konum state'i kurulmaz.
- Harita dosyaları ve save verileri yalnızca kullanım/bağımlılık incelemesi sonrası değiştirilebilir.
- Map ID, world ID, transition ID, başlangıç noktası ve kayıt sözleşmeleri açıkça korunur veya sürümlü migration ile değiştirilir.
- `AssetCatalog`, `ScenePlacementCatalog`, `PresentationContentService` ve `PresentationContentStore` mevcut ana oyun içerik altyapısıdır; laboratuvarın content modeliyle karşılaştırılmadan kopyalanmaz veya silinmez.
- Save schema ve restore davranışları bu aşamada keyfî biçimde değiştirilmez.
- Her mantıksal değişiklik küçük ve geri alınabilir commit'lere bölünür.
- Testler çalıştırılmadan ve sonuçlar raporlanmadan dosya kaldırma yapılmaz.

## 6. Kapsam dışı

- Hex World Laboratory kodunun ana oyuna entegrasyonu.
- `main` veya `demo_eldoria` dalına doğrudan yazma/merge.
- Yeni harita editörü, görsel içerik editörü veya harita üretim aracı.
- Yeni kare haritalar, çoklu kare harita ağı veya bağımsız kare dünya simülasyonu.
- Yeni pathfinding, NPC AI, otomatik hareket veya oyun mekaniği.
- Yeni izometrik kamera/projection veya büyük görsel tasarım revizyonu.
- Save formatını ilgisiz alanlarda yeniden tasarlama.
- Tek easter egg haritası için gerekli olduğu kanıtlanmayan kare harita kodunu sırf eski olduğu için topluca silme.

## 7. Kapanış ölçütleri

Aşama ancak aşağıdakiler sağlandığında tamamlanabilir:

1. Harita kodu/veri/test envanteri ve bağımlılık haritası belgelenmiş olmalı.
2. Korunacak tek kare harita ve minimum çalışma yüzeyi gerekçelendirilmiş olmalı.
3. Silinen veya değiştirilen her öğe için gerekçe ve etki kaydı bulunmalı.
4. Ana altıgen dünya haritaları, bağlantıları ve içerik paketi yüklenebilmeli.
5. Tek kare easter egg haritası hedeflenen minimum yolla yüklenebilmeli/gösterilebilmeli.
6. Mevcut save ve içerik paketleri için uyumluluk sonucu kanıtlanmalı.
7. İlgili testler ve tam regresyon başarılı olmalı.
8. Kullanıcı manuel/görsel kabulü vermeli.
9. Laboratuvar entegrasyonuna ilişkin açık arayüzler ve kalan riskler raporlanmalı.

Bu genel plan, ayrıntılı teknik plan ve kullanıcı onayı olmadan temizlik kodu uygulamasına izin vermez.
