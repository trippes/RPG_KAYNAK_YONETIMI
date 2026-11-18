# Harita Sistemi Temizliği — Genel Plan

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Durum | Plan onaylandı; teknik hazırlık |
| Kapsam | Eski harita altyapısının denetimi ve kontrollü temizliği |

## 1. Amaç

Laboratuvarda geliştirilen yeni dünya/harita altyapısı ana oyuna aktarılmadan önce, `demo_eldoria` dalındaki mevcut harita sistemini güvenli biçimde incelemek, sadeleştirmek ve entegrasyona hazırlamak.

Temizlik çalışması kendi başına bir entegrasyon değildir. Bu aşamada Hex World Laboratory kodu ana oyuna taşınmayacak. Laboratuvar dalı, Aşamalar 0–15'in doğrulanmış teknik referansı ve arşivi olarak korunacaktır.

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
- `content/demo_eldoria/maps/`: schema v1 kare haritalar ile schema v2 altıgen haritalar.
- `content/demo_eldoria/world.json`: altıgen dünya yerleşim/bağlantı tanımı.
- `content/demo_eldoria/placements/`, `asset_catalog.json` ve `presentation_assets.json`: görsel varlık ve sahne yerleşimi verileri.
- `tests/test_world/`, `tests/test_application/`, `tests/test_game_ui/`, `tests/test_foundation/`, `tests/test_architecture/` ve uyumluluk testleri.

Bu envanter başlangıç keşfidir; bir dosyanın kullanılmadığına veya silinebileceğine dair tek başına kanıt değildir.

## 4. Genel çalışma adımları

### 16.1 — Envanter ve bağımlılık haritası
Harita modülleri, import/call ilişkileri, giriş noktaları, testler, içerik dosyaları ve kayıt referansları çıkarılır. Aktif, uyumluluk amaçlı, deneysel ve sahipsiz olduğu düşünülen parçalar ayrı sınıflandırılır.

### 16.2 — Harita veri paketinin denetimi
Tüm harita JSON dosyaları, schema sürümleri, benzersiz map ID'leri, geçiş hedefleri, dünya yerleşimleri, başlangıç konumları, hücre koordinatları ve asset/placement referansları doğrulanır. Veri kaybı olmadan önce mevcut içeriklerin envanteri ve checksum/karşılaştırma kanıtı saklanır.

### 16.3 — Runtime ve koordinat sahipliği
Kare harita `(x, y)`, altıgen axial `(q, r)`, `LocalHexPosition`, `EntityPosition`, dünya yerleşimi ve piksel/screen koordinatlarının nerede üretildiği ve dönüştürüldüğü belgelenir. Tek bir koordinat biçimini zorla bütün sistemlere yaymak yerine, her alanın yetkili kaynağı ve adaptör sınırı belirlenir.

### 16.4 — UI/render ve geçiş akışları
Kare harita ekranı ile altıgen görünümün hangi koşullarda etkinleştiği, geçici giriş/çıkış yolları, kamera/dönüşüm sorumluluğu, harita geçişleri ve oyuncu konumu akışı incelenir. Görsel sunumun authoritative gameplay state'i değiştirmemesi ilkesi korunur.

### 16.5 — Kontrollü sadeleştirme
Yalnızca kanıtlanmış tekrarlar, erişilemeyen kodlar veya yeni mimariyle çakışan sorumluluklar ele alınır. Önce test/çağrı kanıtı, sonra küçük refactor veya deprecation, en son kaldırma uygulanır. Gerekli eski içerikler için açık bir geriye uyumluluk yolu tanımlanır.

### 16.6 — Regresyon ve kullanıcı kabulü
Temiz kurulum, tüm otomatik testler, içerik paketi yükleme, kare/altıgen harita keşfi, geçişler, hareket, çarpışma, yerleşimler, kamera, kayıt/yükleme ve mevcut oynanabilir akış doğrulanır. Kullanıcı görsel ve işlevsel kabulü tamamlamadan aşama kapanmaz.

### 16.7 — Entegrasyona hazır olma kararı
Temizliğin kapsamı, kalan uyumluluk borcu, korunacak legacy adaptörleri, kaldırılan parçalar ve laboratuvarla entegrasyon sınırları raporlanır. Sonuç "hazır", "koşullu hazır" veya "hazır değil" olarak gerekçelendirilir.

## 5. Güvenlik ve değişmezler

- Harita dosyaları ve save verileri yalnızca kullanım/bağımlılık incelemesi sonrası değiştirilebilir.
- Map ID, world ID, transition ID, başlangıç noktası ve kayıt sözleşmeleri açıkça korunur veya sürümlü migration ile değiştirilir.
- `content_loader` içinde v1 kare ve v2 altıgen haritaların birlikte keşfedilmesi, bilinçli bir geçiş kararı olmadan bozulamaz.
- `HexWorldView` ile legacy kare harita actor/runtime ilişkisi incelenmeden bir taraf diğerinin yerine geçirilmez.
- `AssetCatalog`, `ScenePlacementCatalog`, `PresentationContentService` ve `PresentationContentStore` mevcut ana oyun içerik altyapısıdır; laboratuvarın content modeliyle karşılaştırılmadan kopyalanmaz veya silinmez.
- Save schema ve restore davranışları bu aşamada keyfî biçimde değiştirilmez.
- Her mantıksal değişiklik küçük ve geri alınabilir commit'lere bölünür.
- Testler çalıştırılmadan ve sonuçlar raporlanmadan dosya kaldırma yapılmaz.

## 6. Kapsam dışı

- Hex World Laboratory kodunun ana oyuna entegrasyonu.
- `main` veya `demo_eldoria` dalına doğrudan yazma/merge.
- Yeni harita editörü, görsel içerik editörü veya harita üretim aracı.
- Yeni pathfinding, NPC AI, otomatik hareket veya oyun mekaniği.
- Yeni izometrik kamera/projection veya büyük görsel tasarım revizyonu.
- Save formatını ilgisiz alanlarda yeniden tasarlama.
- Sırf eski oldukları için kare harita içeriklerini topluca silme.

## 7. Kapanış ölçütleri

Aşama ancak aşağıdakiler sağlandığında tamamlanabilir:

1. Harita kodu/veri/test envanteri ve bağımlılık haritası belgelenmiş olmalı.
2. Silinen veya değiştirilen her öğe için gerekçe ve etki kaydı bulunmalı.
3. Mevcut gerekli haritalar ve bağlantılar yüklenebilmeli.
4. Mevcut save ve içerik paketleri için uyumluluk sonucu kanıtlanmalı.
5. İlgili testler ve tam regresyon başarılı olmalı.
6. Kullanıcı manuel/görsel kabulü vermeli.
7. Laboratuvar entegrasyonuna ilişkin açık arayüzler ve kalan riskler raporlanmalı.

Bu genel plan, ayrıntılı teknik plan ve kullanıcı onayı olmadan temizlik kodu uygulamasına izin vermez.
