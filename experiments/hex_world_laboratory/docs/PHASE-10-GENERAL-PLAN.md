# Aşama 10 — Simülasyon Orkestrasyonu ve Dünya Bütünlüğü: Genel Plan

> **Belge türü:** Aşama genel planı ve kapsam sözleşmesi  
> **Proje:** Eldoria — Kaynak Yönetimi RPG  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** TAMAMLANDI VE KULLANICI TARAFINDAN KABUL EDİLDİ — 18 KASIM 2026  
> **Ön koşul:** Aşama 0–9 tamamlandı ve kabul edildi  
> **Temel kullanıcı kararı:** Bu aşamada NPC hareketi yoktur.

---

## 1. Amaç

Aşama 10'un amacı, laboratuvarda bugüne kadar ayrı ayrı geliştirilmiş hareket, fizik, dünya, entity, spatial index ve etkileşim bileşenlerini tek ve açık bir simülasyon güncelleme düzeni altında bir araya getirmektir.

Bu aşamanın temel mimari ilkesi şudur:

**Simülasyon dünya durumunu günceller; render yalnızca simülasyon durumunu okur ve görüntüler.**

Aşama sonunda simülasyonun ne zaman ve hangi sırayla ilerlediği, authoritative konumun hangi noktada entity kayıtlarına ve mekânsal indekse yansıtıldığı, harita/varlık yaşam döngüsünün simülasyonla nasıl eşgüdümlendiği açık ve test edilebilir olacaktır.

Aşama 10 bir NPC yapay zekâsı veya hareket aşaması değildir. Kullanıcının açık kararı doğrultusunda bu aşamada hiçbir NPC hareket prototipi geliştirilmeyecektir.

## 2. Mevcut mimarideki yeri ve denetim bulgusu

Aşama 9 sonunda oyuncu, NPC ve kaynaklar ortak entity kimliği ve konum sözleşmesini kullanmaktadır. EntityWorldCoordinator, EntityRegistry, CompanionRoster ve entity spatial adapter altyapısı mevcuttur. DemoTickPump 60 TPS tabanlı tick üretmekte; MovementDemo bu tick içinde oyuncu hareketini ve hücre takibini ilerletmektedir.

Bununla birlikte simülasyon sistemlerinin tamamını yöneten tek bir orkestrasyon noktası henüz bulunmamaktadır. Ayrıca mevcut EntityDemo akışında oyuncu konumunun entity kaydına eşitlenmesi render snapshot oluşturulurken çağrılmaktadır. Bu, render yolunun entity registry ve spatial index üzerinde değişiklik oluşturmasına neden olabilir.

Aşama 10 bu sorumluluğu simülasyon güncelleme akışına taşıyacak ve render tarafının salt-okunur olmasını otomatik testlerle güvence altına alacaktır.

## 3. Kapsam ve bağlayıcı kararlar

### 3.1 Simülasyon orkestrasyonu

- Simülasyon tick'inin tek ve açık bir koordinasyon noktası üzerinden yürütülmesi.
- Simülasyon sistemlerinin sorumluluklarını koruyarak ortak bir güncelleme yaşam döngüsüne katılması.
- Sistemlerin güncelleme sırasının belgelenmesi ve deterministik testlerle doğrulanması.
- Zaman adımı, tick üretimi ve çizim sıklığı arasındaki ilişkinin netleştirilmesi.
- Simülasyon güncellemesi ile kamera/render güncellemesinin birbirinden ayrılması.

### 3.2 Authoritative konum ve entity eşitlemesi

- Oyuncu hareketinin authoritative konum kaynağı olmaya devam etmesi.
- Hareket/physics sonucunda kesinleşen konumun entity transform ve spatial index'e simülasyon güncellemesi sırasında aktarılması.
- Entity transform ve spatial index'in aynı tick'e ait tutarlı konumu temsil etmesi.
- Render snapshot üretiminin entity kaydı, hareket state'i, dünya verisi veya spatial index üzerinde değişiklik yapmaması.
- Aynı konumun farklı katmanlarda bağımsız authoritative kaynaklar olarak tutulmasının önlenmesi.

### 3.3 Dünya ve harita bütünlüğü

- Aktif harita ile simülasyona katılan entity kayıtlarının tutarlılığını korumak.
- Harita yükleme, boşaltma ve kaldırma işlemlerinin simülasyon ve spatial index yaşam döngüsüyle uyumunu doğrulamak.
- Pasif/boşaltılmış haritaya ait entity'lerin aktif sorgularda görünmesini önlemek.
- Harita yeniden yüklendiğinde geçerli entity ve yoldaş ilişki kayıtlarının doğru biçimde yeniden etkinleştirilmesini doğrulamak.
- Simülasyon tick'i sırasında yaşam döngüsü değişikliklerinin güvenli ele alınmasını sağlamak.

### 3.4 NPC, kaynak ve yoldaş davranış sınırı

- NPC'ler bu aşamada sabit konumlarında kalacaktır; devriye, gezinme, takip veya otonom hareket uygulanmayacaktır.
- Yoldaş FOLLOW, WAIT ve RETURN komutları yalnızca Aşama 9'da kurulan komut/ilişki verisi olarak kalacaktır; konum değiştirmeyecektir.
- Kaynak nesneleri sabit kalacaktır. Kaynak toplama, üretim, envantere aktarma veya ekonomi davranışı geliştirilmeyecektir.
- Kaynak ve NPC hedef seçimi/etkileşim sorguları mevcut Aşama 9 sözleşmeleri üzerinden çalışmaya devam edecektir.
- Bu aşama, gelecekteki hareket ve oynanış sistemlerinin simülasyona eklenebilmesi için genişletilebilir bir orkestrasyon altyapısı kuracaktır; bu davranışları şimdiden uygulamayacaktır.

## 4. İş paketleri

### 10.1 — Mevcut tick ve sistem sözleşmelerinin denetimi
- DemoTickPump, MovementDemo, EntityDemo, MovementSystem, Physics, MovementCellTracker ve EntityWorldCoordinator akışlarını dosya/API düzeyinde eşlemek.
- Mevcut tick sorumluluklarını ve yinelenen/örtüşen sorumlulukları belirlemek.
- Simülasyon, kamera, render ve input sınırlarını netleştirmek.
- Mevcut davranışları koruyacak geçiş ve geriye dönük uyumluluk gereksinimlerini kaydetmek.

### 10.2 — Merkezi simülasyon koordinasyonunun tasarımı ve uygulanması
- Simülasyon tick'ini yöneten merkezi koordinasyon bileşenini oluşturmak veya mevcut yapıyı bu sorumluluğu taşıyacak şekilde düzenlemek.
- Sistemlerin açık bağımlılık ve güncelleme sözleşmeleriyle kaydedilmesini/çağrılmasını sağlamak.
- Pygame pencere ve çizim ayrıntılarını simülasyon çekirdeğine taşımamak.
- Koordinatörün testlerde grafik penceresi olmadan çalıştırılabilmesini sağlamak.

### 10.3 — Deterministik tick sırası ve zaman yönetimi
- Input niyetinin tick için tutarlı biçimde alınmasını sağlamak.
- Hareket ve fizik güncellemelerinin sırasını mevcut authoritative state sözleşmesine göre belirlemek.
- Kesinleşmiş oyuncu konumunu hücre takibi, entity transform ve spatial index güncellemelerine doğru sırayla yansıtmak.
- Etkileşim sorgularının hangi tick state'ini gördüğünü açıkça tanımlamak.
- Sabit zaman adımı/tick üretimi ile değişken render sıklığının ilişkisini inceleyip teknik planda kesinleştirmek.
- Aynı başlangıç state'i ve aynı input/tick dizisinin aynı simülasyon sonucunu üretmesini doğrulamak.

### 10.4 — Entity ve spatial state eşitlemesinin simülasyona taşınması
- EntityDemo içindeki oyuncu konum eşitlemesini render snapshot yolundan çıkarmak.
- Eşitlemeyi merkezi simülasyon tick akışında, authoritative hareket güncellemesinden sonra gerçekleştirmek.
- Entity transform ve spatial index'in aynı konum güncellemesinden beslendiğini doğrulamak.
- Render snapshot ve render çağrılarının simülasyon state'ini değiştirmediğini test etmek.

### 10.5 — NPC ve kaynakların hareketsiz simülasyon katılımcıları olarak doğrulanması
- NPC ve kaynak entity'lerinin simülasyon koordinatörüyle uyumunu doğrulamak.
- NPC'lerin ve kaynakların kendiliğinden konum değiştirmediğini test etmek.
- Hedef seçimi, etkileşim uygunluğu ve spatial sorguların merkezi tick düzeni altında tutarlı kalmasını sağlamak.
- Kaynak toplama veya NPC davranış sistemi eklemeden mevcut etkileşim sözleşmelerini korumak.

### 10.6 — Yoldaş komut verisinin simülasyonla uyumu
- FOLLOW, WAIT ve RETURN komutlarının simülasyon state'inde doğru biçimde korunmasını doğrulamak.
- Komut değişikliklerinin revision/sıralama kurallarını korumak.
- Komutların NPC konumunu değiştirmediğini ve hareket sistemi tetiklemediğini test etmek.
- Harita unload/reload ve entity kaldırma senaryolarında Aşama 9 yoldaş yaşam döngüsünü korumak.

### 10.7 — Harita/entity yaşam döngüsü ve dünya bütünlüğü testleri
- Harita yükleme, boşaltma, yeniden yükleme ve kaldırma senaryolarını merkezi simülasyon akışında sınamak.
- Entity registry, companion roster ve spatial index kayıtlarının tutarlılığını doğrulamak.
- Pasif harita entity'lerinin aktif sorgulardan dışlandığını doğrulamak.
- Hata/istisna durumlarında yarım kalmış veya yinelenmiş indeks güncellemelerini araştırmak.

### 10.8 — Regresyon, performans ve kabul doğrulaması
- Unit, integration ve regression testlerini tamamlamak.
- Tekrarlanabilir tick dizileriyle deterministik sonuçları doğrulamak.
- Uzun süreli tick çalıştırmalarında konum/registry/spatial tutarlılığını izlemek.
- Simülasyon tick süresi ve render snapshot maliyetini ayrı ayrı ölçmek.
- Linux/Windows kalite kontrollerini ve laboratuvar benchmarklarını çalıştırmak.
- Kullanıcı manuel kabul kontrol listesini ve kapanış raporunu hazırlamak.

## 5. Beklenen teslimatlar

- Merkezi simülasyon/tick koordinasyon bileşeni.
- Belgelenmiş ve test edilmiş sistem güncelleme sırası.
- Simülasyon zaman adımı ve render döngüsü sorumluluklarının açık sözleşmesi.
- Oyuncu hareketi, entity transform ve spatial index arasında tutarlı tick güncellemesi.
- Simülasyon state'ini değiştirmeyen salt-okunur render snapshot akışı.
- NPC ve kaynakların hareketsiz katılımcılar olarak doğrulandığı test sahnesi.
- Hareket üretmeyen yoldaş komut durumlarının simülasyonla uyumluluk testleri.
- Harita/entity yaşam döngüsü ve uzun süreli bütünlük testleri.
- Performans/benchmark sonuçları.
- Manuel kabul kontrol listesi ve aşama kapanış raporu.

## 6. Kabul koşulları

Aşama 10 aşağıdaki koşulların tamamı sağlandığında teknik kabul için hazır sayılır:

1. Simülasyon tick'ini yöneten merkezi ve açık bir koordinasyon noktası vardır.
2. Simülasyon sistemlerinin güncelleme sırası belgelenmiş ve deterministik olarak test edilmiştir.
3. Aynı başlangıç state'i ve aynı input/tick dizisi aynı simülasyon sonucunu üretir.
4. Oyuncu hareketi authoritative konum kaynağı olmaya devam eder.
5. Oyuncu konumunun entity transform ve spatial index'e aktarılması render sırasında değil simülasyon güncellemesi sırasında gerçekleşir.
6. Render snapshot oluşturma ve render çağrıları authoritative simülasyon state'inde değişiklik yapmaz.
7. Entity transform ve spatial index aynı tick'e ait tutarlı konumu temsil eder.
8. NPC'ler bu aşama boyunca otonom veya komutla hareket etmez.
9. FOLLOW, WAIT ve RETURN komutları yalnızca komut/ilişki verisi olarak kalır; NPC konumunu değiştirmez.
10. Kaynak nesneleri hareket etmez; toplama, üretim, envanter transferi veya ekonomi davranışı eklenmez.
11. NPC/kaynak hedef seçimi ve mevcut etkileşim sorguları çalışmaya devam eder.
12. Harita yükleme, boşaltma, yeniden yükleme ve kaldırma işlemleri entity/companion/spatial kayıtlarını tutarlı bırakır.
13. Uzun süreli simülasyon testlerinde konum, entity registry ve spatial index tutarsızlığı birikmez.
14. Mevcut hareket, fizik, kamera, render ve Aşama 9 etkileşim davranışlarında regresyon oluşmaz.
15. Linux ve Windows kalite kontrolleri, laboratuvar testleri ve benchmarklar başarılıdır.
16. Kullanıcı manuel görsel/işlevsel kabulünü tamamlar ve kapanış raporu hazırlanır.

## 7. Test ve doğrulama yaklaşımı

- **Tick determinismi:** Aynı input ve tick dizisini tekrarlayarak state eşitliği.
- **Güncelleme sırası:** Sistemlerin beklenen sırada çağrıldığını doğrulayan testler.
- **Konum eşitlemesi:** Hareket sonrası player, entity transform ve spatial index konumlarının karşılaştırılması.
- **Render saflığı:** Snapshot/render öncesi ve sonrası authoritative state, registry ve spatial index karşılaştırması.
- **Hareketsizlik garantisi:** NPC, kaynak ve yoldaş komutları için konumun değişmediğini doğrulama.
- **Harita yaşam döngüsü:** Load/unload/reload/remove sonrasında aktif entity ve spatial sorgu sonuçlarının doğrulanması.
- **Regresyon:** Kamera, zoom, viewport, input, hareket, çarpışma ve hedef seçimi davranışlarının korunması.
- **Uzun süreli çalışma:** Çok sayıda tick sonrasında konum/indeks tutarlılığı ve hata birikiminin incelenmesi.
- **Performans:** Simülasyon tick maliyeti ile render snapshot maliyetinin ayrı ölçülmesi.

Test çalıştırılmadıysa başarılı kabul edilmez. Otomatik test ve CI sonuçları kullanıcı cihazındaki manuel görsel/işlevsel kabulün yerine geçmez.

## 8. Görsel kabul yaklaşımı

Laboratuvarın tek giriş noktası olan `python -m hex_world_lab` kullanılacaktır. Ayrı bir Aşama 10 başlatıcısı oluşturulmayacaktır.

Kullanıcı kabulünde:
- Oyuncu hareketinin önceki aşamalardaki gibi çalıştığı,
- NPC ve kaynakların sahnede mevcut olduğu ancak kendiliğinden hareket etmediği,
- NPC yoldaş komutlarının konum değiştirmediği,
- Hedef seçimi ve mevcut etkileşim menüsünün bozulmadığı,
- Kamera/zoom ve pencere boyutu değişiminde hareket/konum tutarlılığının korunduğu,
- Render sırasında görünür veya gizli simülasyon state değişikliği oluşmadığına ilişkin otomatik testlerin başarılı olduğu

kontrol edilecektir.

## 9. Kapsam dışı

Aşağıdakiler Aşama 10'da uygulanmayacaktır:

- NPC devriyesi, gezinmesi, rastgele hareketi veya otonom yapay zekâsı.
- Yoldaş FOLLOW/WAIT/RETURN komutlarının gerçek hareket üretmesi.
- Pathfinding (A*, Dijkstra), rota planlama, click-to-move ve engel dolaşma.
- NPC algı, karar verme, günlük rutin, savaş veya diyalog davranışları.
- Kaynak toplama, üretim, envantere aktarma ve ekonomi.
- Savaş, görev ve diyalog sistemlerinin yeni entegrasyonları.
- Nihai animasyon, ses, çevre sanatı veya görsel zenginleştirme.
- Pygame'den Godot'a geçiş.
- `main` veya `demo_eldoria` dallarında değişiklik ya da entegrasyon.

Bu kapsam değişikliklerinden biri gerekli görülürse uygulamaya başlamadan önce gerekçesi, mimari etkisi ve yeni kabul koşulları ayrı olarak sunulacak ve kullanıcı onayı alınacaktır.

## 10. Riskler ve önleyici yaklaşımlar

| Risk | Etki | Önleyici yaklaşım |
|---|---|---|
| Tick sorumluluğunun birden fazla yerde kalması | Çifte güncelleme veya sıralama belirsizliği | Merkezi koordinasyon ve açık sistem sözleşmeleri |
| Render sırasında state güncellenmesi | Kare hızına bağlı dünya/indeks tutarsızlığı | Render saflığı testleri ve simülasyon tarafında eşitleme |
| Birden fazla authoritative konum kaynağı | Entity ve hareket state'inin ayrışması | Hareket state'ini konum doğruluk kaynağı olarak korumak |
| Spatial index'in geç güncellenmesi | Eski/eksik hedef sorguları | Tick sırasını ve atomik güncelleme sınırlarını doğrulamak |
| Zaman adımı ve render hızının karışması | Cihaza bağlı simülasyon davranışı | Tick determinismi ve ayrı performans ölçümleri |
| Kapsamın NPC hareketine kayması | Onaylanan kararın ihlali ve aşama büyümesi | Hareketsizlik koşullarını açık kabul maddesi ve test yapmak |
| Harita yaşam döngüsünde eski kayıt kalması | Yanlış harita sorguları ve yetim ilişkiler | Load/unload/reload/remove entegrasyon testleri |

## 11. Onay kapıları ve uygulama yöntemi

1. Bu genel plan kullanıcı tarafından incelenir ve onaylanır.
2. Onaydan sonra mevcut kod üzerinde ayrıntılı dosya/API denetimi yapılır; Aşama 10 Teknik Mimari Planı ve kabul kontrol listesi hazırlanır.
3. Teknik plan kullanıcı tarafından ayrıca onaylanır.
4. Yalnızca onaylanan kapsamda 10.1–10.8 uygulaması başlatılır.
5. Her iş paketi otomatik testlerle doğrulanır; laboratuvar ve Core Quality CI, benchmark ve regresyon kontrolleri tamamlanır.
6. Kullanıcıya manuel görsel/işlevsel kabul listesi sunulur.
7. Kullanıcı kabulünden sonra kapanış raporu hazırlanır ve Master Plan güncellenir.

Genel plan ve teknik plan kullanıcı tarafından onaylanmıştır. Aşama 10.1–10.8 teknik uygulaması, otomatik testler, Linux/Windows Core Quality, laboratuvar CI ve kullanıcı manuel görsel/işlevsel kabulü tamamlanmıştır. Kullanıcı 18 Kasım 2026 tarihinde görsel testlerin başarılı olduğunu bildirmiş ve aşamayı tamamlanmış olarak kabul etmiştir. Kapanış kaydı `../reports/PHASE-10-CLOSURE-REPORT.md` dosyasındadır.

---

**Özet karar:** Aşama 10'un amacı merkezi simülasyon orkestrasyonunu ve dünya/entity/spatial bütünlüğünü kurmaktır. Bu aşamada NPC hareketi yoktur; NPC'ler, kaynaklar ve yoldaşlar konum değiştirmez. Render salt-okunur hale getirilir ve oyuncu hareketi ile entity/spatial state eşitlemesi simülasyon tick'ine taşınır.
