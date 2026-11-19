# Harita Sistemi Temizliği — Genel Plan

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Durum | Uygulama onaylandı; 16.1 teknik baseline tamamlandı, teknik migration sıralaması uygulanacak |
| Kapsam | Ana altıgen dünya sisteminin sadeleştirilmesi ve tek kare harita easter egg'inin korunması |

## 1. Amaç ve ürün kararı

Laboratuvarda geliştirilen yeni dünya/harita altyapısı ana oyuna aktarılmadan önce, `demo_eldoria` dalındaki mevcut harita sistemini güvenli biçimde incelemek, sadeleştirmek ve entegrasyona hazırlamak.

Harita sistemleri için ürün kararı:

- **Altıgen harita:** Eldoria'nın ana ve yetkili dünya haritası sistemi olacaktır. Normal dünya dolaşımı ve ana oyun harita akışları bu sistemde yürütülecektir.
- **Kare harita:** Gelecekte detaycı oyuncuların keşfedebileceği tek ve sabit bir easter egg haritası olarak korunacaktır. İkinci bir ana dünya veya alternatif harita altyapısı olmayacaktır.
- **Sınır:** Kare harita, yalnızca tek haritayı yüklemek/göstermek ve ileride ayrıca kararlaştırılacak sınırlı etkileşimi desteklemek için gereken asgari kod ve veriyle yaşayacaktır. Yeni kare haritalar, editör, prosedürel üretim, çoklu harita ağı veya bağımsız kare dünya simülasyonu geliştirilmeyecektir.
- Kare ve altıgen koordinatlar birleştirilmeyecek; iki sistem arasında örtük konum/state paylaşımı kurulmayacaktır.

Bu dalda önce mevcut hex runtime ana oyunun authoritative dünya sistemi hâline getirilecektir; bu, experiment/hex-world-laboratory dalını birleştirmek anlamına gelmez. Laboratuvar dalı, Aşamalar 0–15'in teknik referansı ve arşivi olarak korunacaktır.

## 2. Dal stratejisi

1. `experiment/map-cleanup`, `demo_eldoria` dalının onaylı başlangıç HEAD'inden oluşturulur.
2. Tüm inceleme, düzenleme, test ve dokümantasyon bu dalda yürütülür.
3. `demo_eldoria` ve `main` doğrudan değiştirilmez.
4. `experiment/hex-world-laboratory` dalına commit, merge veya rebase yapılmaz.
5. Hex runtime'ın ana oyun sahipliği ve içerik/save entegrasyonu bu dalda tamamlanır. Laboratuvar dalına merge/rebase yapılmaz; laboratuvar kodunun ayrıca entegrasyonu gelecekte ayrı kapsam ve onay gerektirir.
6. Birleşik sürüm otomatik test, statik analiz, paketleme ve CI kapılarından geçerse kullanıcı onayıyla `demo_eldoria` dalına aktarılır. Görsel kabul bu teknik temizlik çalışmasının parçası değildir. Laboratuvar dalı arşiv olarak tutulur.

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
Harita modülleri, import/call ilişkileri, giriş noktaları, testler, içerik dosyaları ve kayıt referansları çıkarılır. Bu baseline tamamlandı ve [53 numaralı rapora](53-map-cleanup-phase-16-1-baseline.md) kaydedildi.

### 16.2 — Altıgen runtime'ı ana oyun otoritesi yapma
Mevcut hex runtime geçici H portalı olmaktan çıkarılıp normal oyun oturumunun parçası hâline getirilir. Tek konum yazarı, entity/actor kimliği, occupancy, hareket, map transition ve render/input sorumlulukları tanımlanır. Ayrıntılı sözleşme [54 numaralı hex runtime migration planında](54-hex-runtime-authoritative-gameplay-migration.md) yer alır.

### 16.3 — İçerik ve gameplay referanslarını hex dünyaya taşıma
Başlangıç noktası, NPC, resource landmark, market, trade partner ve dünya nesnesi referansları axial hex map sözleşmesine geçirilir. Quest'lerin NPC/resource kimlikleri korunur. NPC AI veya otomatik hareket eklenmez.

### 16.4 — Kayıt/yükleme ve legacy save uyumluluğu
Oyuncu ve ilgili dünya entity konumları axial EntityPosition olarak kaydedilir/geri yüklenir. Kare kayıtların konumu otomatik olarak hex koordinatlarına dönüştürülmez. Açık, test edilmiş ve geri alınabilir eski kayıt politikası olmadan kare harita dosyaları silinmez.

### 16.5 — Ana oyun UI ve runtime akışının hex'e alınması
Normal oyun akışı doğrudan hex dünyada başlar. H portalı ve geçici enter/leave akışı kaldırılır. GameWindow pencere yönetimi ve mevcut oyun içi pencereler korunur. Renderer yalnızca authoritative runtime state'ini okur.

### 16.6 — Kare sistemi tek Paskalya yumurtasına indirme
Hex gameplay, content ve save entegrasyonu tamamlandıktan sonra tek kare easter egg haritası seçilir. Diğer sekiz kare harita ve çoklu kare dünya altyapısı; kod, içerik, asset, save ve test referansları sıfırlandığında kaldırılır. Kare (x,y) koordinatları ayrı kalır; hex koordinatına dönüşüm yapılmaz.

### 16.7 — Otomatik regresyon ve teknik doğrulama
Temiz kurulum, tüm otomatik testler, Ruff, paketleme, içerik doğrulaması, movement/transition, NPC/resource/market/quest/container entegrasyonu, save/load ve Linux/Windows CI doğrulanır. Görsel kabul testi bu çalışmanın parçası değildir; kullanıcıdan manuel oyun testi istenmez.

### 16.8 — Kapanış ve entegrasyon hazırlığı
Ana hex dünya mimarisi, tek kare easter egg yüzeyi, legacy adaptörleri, save migration politikası ve kalan riskler raporlanır. experiment/hex-world-laboratory arşiv dalı olarak korunur; bu dala otomatik merge/rebase yapılmaz.

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
8. Otomatik test, statik analiz, paketleme ve CI doğrulamaları başarılı olmalı.
9. Laboratuvar entegrasyonuna ilişkin açık arayüzler ve kalan riskler raporlanmalı.

Bu genel plan ve ayrıntılı teknik plan, kullanıcının teknik temizlik onayıyla uygulama için geçerlidir; kapsam dışı gameplay/ürün kararları ayrıca onay gerektirir.

## 8. Kullanıcı kararı eki — 2026-11-19 (önceki sıralamayı geçersiz kılar)

Kullanıcının son kararıyla eski NPC ve kaynak düğümü içerikleri yeni Hex sistemine taşınmayacaktır. Mevcut dört NPC kaydı, yirmi iki kaynak düğümü ve bunların kare harita yerleşimleri legacy demo içeriği olarak kaldırılacaktır. Bu kayıtlara bağlı eski görev tanımları, NPC diyalog içerikleri ve NPC'ye bağlı başlangıç pazarı da eski demo içerik setinin parçası olarak kaldırılacaktır; yeni dünya entegrasyonundan sonra yeni tasarımla sıfırdan yazılacaktır.

Bu karar yalnızca içerik kayıtlarını kapsar. NPC sistemi, kaynak düğümü domain/runtime mekanikleri, kaynak toplama, diyalog altyapısı, görev sistemi, ekonomi, pazar, envanter ve ilişkili genel oyun servisleri silinmeyecektir. Yeniden kullanılabilir mekanikler korunacak; eski demo tanımları ve eski harita konumlarına bağlı örnek veriler temizlenecektir.

Uygulama sıralaması da kesinleştirilmiştir: önce eski kare harita sistemi ve eski yedi haritalı Hex demo/portal sistemi ile bunlara bağlı demo içerikleri temizlenecek; ardından laboratuvar dalındaki yeni Hex mimarisi bu temizlik dalına entegre edilecektir. Önce Hex entegrasyonu yapıp sonra legacy kare sistemi temizleme yönündeki bu belgenin önceki 16.2–16.6 sıralaması geçersizdir. Laboratuvar dalı arşiv olarak değişmeden kalacaktır.

Tek kare kare-harita easter egg'i, eski dokuz haritanın hiçbirini otomatik olarak koruma gerekçesi değildir. Eski kare harita sistemi tamamen kaldırıldıktan sonra, daha sonra ayrıca tasarlanacak tek ve bağımsız easter egg içeriği gerekirse sıfırdan oluşturulacaktır. Kare (x, y) ile axial (q, r) koordinatları arasında dönüşüm yapılmayacaktır.

## 9. Uygulama kapanış durumu — 2026-11-19

Bu bölüm önceki kapsam/sıralama metinlerindeki çelişkili ifadeleri geçersiz kılar ve gerçek cleanup dalı durumunu kaydeder.

### Tamamlanan temizlik

- Dokuz eski kare harita ve yedi eski Hex demo haritası ile bunların demo dünya/portal bağlantıları kaldırıldı.
- Eski NPC, kaynak düğümü, görev, diyalog, başlangıç pazarı ve sahne yerleşimi demo kayıtları silindi. Dört NPC ve yirmi iki kaynak düğümü yeni sisteme taşınmadı.
- Kare harita katalog/loader, WorldMap konum grafı, kare movement manager, kare local-map/nesne yerleşimi, eski Hex demo görünümü ve kare dünya haritası renderer bağlantıları kaldırıldı.
- Oyuncu aktöründen, NPC modelinden ve kaynak düğümü modelinden kare konum/koordinat sahipliği kaldırıldı. NPC, kaynak, görev, diyalog, market, inventory, container içeriği ve genel gameplay mekanikleri korunuyor.
- Yeni save kayıtları eski kare konum/yerleşim verisi üretmiyor. Eski actor, NPC, resource-node veya container placement verisi tespit edildiğinde kayıt açık hata ile reddediliyor; (x, y) → (q, r) dönüşümü yapılmıyor.
- Yeni Hex mimarisinin axial map/world placement sözleşmeleri entegrasyon arayüzleri oldukları için korundu; demo map verisi ve demo runtime bağlantısı korunmadı.

### Teknik kabul

Cleanup dalı HEAD: 3790463394b1f47c81655169554e30202de66724.

GitHub Actions run [#44492476381](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44492476381) Linux ve Windows işlerinin ikisinde de başarılı:
- Pytest: 1.341 test + 235 subtest geçti.
- Ruff: başarılı.
- compileall: başarılı.
- Wheel build ve izole hedefe kurulum: başarılı.
- Release-candidate verification: başarılı.

Korunan main, demo_eldoria ve experiment/hex-world-laboratory dalları değiştirilmedi. Görsel/manuel test yapılmadı; cleanup kabul kapısı otomatik teknik doğrulamadır.

### Sıradaki aşama

Eski sistem temizliği ve teknik kabul tamamlandı. Altıncı aşama olarak laboratuvar Hex mimarisinin bu dala entegrasyonu başlayabilir. Bu entegrasyon tamamlanmadan yeni NPC, kaynak, görev, diyalog ve pazar demo kayıtları eklenmeyecek. Tek kare easter egg bu entegrasyonun parçası değildir ve ayrıca tasarlanacaktır.
