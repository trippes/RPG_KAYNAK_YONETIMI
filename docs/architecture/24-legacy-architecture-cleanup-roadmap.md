# Eldoria — Eski Mimari Bağımlılıklarını Temizleme Roadmap'i

**Durum:** Planlama / uygulamaya hazırlık  
**Hedef dal:** `experiment/map-cleanup`  
**Kapsam:** Eski mimariden kalan sabit kimlikler, örtük varsayımlar, yinelenen durum ve servis erişimleri, içerik paketi sözleşmeleri, arayüz entegrasyonu ve kayıt uyumluluğu.

## 1. Amaç

Eldoria'nın yeni mimarisinde merkezi olarak tanımlanan bir bilginin alt sistemlerde yeniden sabitlenmesini önlemek. Eski mimariden kalan bağımlılıkları kontrollü biçimde tespit etmek, sınıflandırmak ve yeni mimarinin açık sözleşmelerine taşımak.

Bu çalışma yeni özellik geliştirme çalışması değildir. Öncelik mevcut sistemlerin tutarlılığı, güvenilirliği, sürdürülebilirliği ve geriye dönük uyumluluğudur.

## 2. Değişmez çalışma ilkeleri

1. **Önce keşif, sonra değişiklik:** İlgili kaynak kodu, içerik dosyaları, testler ve kayıt biçimleri incelenmeden refaktör yapılmaz.
2. **Tek doğruluk kaynağı:** Oyuncu kimliği, aktif içerik paketi, servis bağlamı ve benzeri merkezi bilgiler birden fazla modülde ayrı ayrı tanımlanmaz.
3. **Kimlik ile görünen ad ayrıdır:** Karakterin oyuncuya gösterilen adı değişebilir ve benzersiz olmak zorunda değildir. Kod, kayıt ve ilişkiler değişmeyen teknik kimlikleri kullanır.
4. **Uyumluluk korunur:** Eski kayıtlar ve içerik paketleri için geçiş/uyumluluk yolu tasarlanmadan kimlik veya şema kırıcı biçimde değiştirilmez.
5. **Küçük ve geri alınabilir adımlar:** Her aşama sınırlı dosya kapsamı, açık kabul ölçütleri ve ayrı testlerle tamamlanır.
6. **Davranış korunur:** Kullanıcı tarafından doğrulanmış oynanış, arayüz ve animasyon davranışları gerekçe olmadan değiştirilmez.
7. **Ölçmeden optimizasyon yok:** Performans değişiklikleri önce/sonra ölçümü ve temsilî senaryolarla doğrulanır.
8. **Ana dal korunur:** Bu programın değişiklikleri `experiment/map-cleanup` dalında tutulur; `main` üzerine doğrudan yazılmaz.
9. **Kanıtlanmamış tamamlanma yok:** Bir tarama veya test yapılmadıysa raporda yapılmış gibi gösterilmez.

## 3. Çalışma aşamaları

### Aşama 0 — Başlangıç envanteri ve güvenli temel çizgi

**Hedef:** Refaktör öncesi mevcut durumu kayıt altına almak.

İşler:
- Dal, commit, çalışma ağacı ve ana dal ile fark durumunu doğrula.
- Kaynak kodu, içerik paketleri, yapılandırmalar, testler, kayıt/yükleme kodu ve dokümantasyon için dosya envanteri çıkar.
- Eski mimari göstergelerini ara: sabit `hero` / `player` kimlikleri, ilk aktörü seçme, dizi indeksine dayalı oyuncu seçimi, varsayılan ID'ler, doğrudan global/tekil servis erişimi, yinelenen konfigürasyonlar ve sessiz varsayılanlar.
- Bulguları **runtime**, **content**, **persistence**, **UI**, **tests**, **tooling/docs** olarak sınıflandır.
- Mevcut test ve lint komutlarını doğrula; başlangıç sonuçlarını raporla.

**Çıktılar:** Bağımlılık envanteri, risk listesi, mevcut test temel çizgisi.

**Kabul ölçütü:** Arama kapsamı ve hariç tutulan dosyalar açıkça belgelenmiş; her bulgu dosya/satır ve kullanım amacıyla ilişkilendirilmiş olmalı.

### Aşama 1 — Oyuncu ve karakter kimliği sözleşmesi

**Hedef:** `hero` gibi tarihsel sabitlerin dağınık kullanımını merkezi oyuncu bağlamına taşımak.

İşler:
- Actor ID, Character ID, Inventory ID ve Account ID kavramlarını birbirinden ayır.
- `GameplayService.configure_player_context(...)` ve mevcut `player_actor_id`, `player_inventory_id`, `player_account_id` API'lerinin sorumluluklarını netleştir.
- `StarterContentIds.hero_id` alanının mevcut kullanımını ve içerik paketi ID çözümlemesini incele; yeni sözleşmenin gerektirdiği alanları belirle.
- Karakter ekranı, envanter, pazar, karakter oluşturma ve diyalog ekranlarındaki doğrudan `"hero"` erişimlerini merkezi bağlama geçir.
- `snapshot.actors[0]` gibi sıralama/ilk eleman varsayımlarını tespit edip açık kimlik ilişkileriyle değiştir.
- Test fixture'larında kalan eski kimlikleri runtime bağımlılıklarından ayır.
- Kimliklerin görünen karakter adından bağımsız olduğunu test et.

**Önemli:** Önerilen yeni ID adları (`player_actor`, `player_character`, `player_inventory`, `player_account`) yalnızca inceleme sonrasında uygun bulunursa kullanılacak; mevcut kayıt ve içerik sözleşmeleri incelenmeden kesinleştirilmeyecek.

**Kabul ölçütü:** Oyuncu kimliği tek bir sözleşmeden çözülür; oyuncu adı değişse de oyun sistemleri, UI ve ilişkiler çalışır; birden fazla aktör olduğunda ilk eleman varsayımı bulunmaz.

### Aşama 2 — İçerik paketi ve yapılandırma sözleşmeleri

**Hedef:** İçerik paketlerinin uygulama koduna eksik veya örtük varsayımlarla bağlanmasını önlemek.

İşler:
- Starter content, gameplay rules, world, character, actor ve resource tanımlarının şema/sözleşmelerini incele.
- Zorunlu, isteğe bağlı ve varsayılan alanları açıkça tanımla.
- İçerik paketi doğrulamasını yükleme aşamasında anlaşılır hata/uyarı üretecek şekilde değerlendir.
- Eksik konfigürasyonun sessizce boş değer üretmesinin güvenli olup olmadığını her alan için belirle.
- Demo ve test paketleri arasındaki davranış farklarını belgeleyip amaçlı hâle getir.
- Paketler arasında kopyalanmış değerleri ortak şemaya veya ortak tanımlara taşı.
- İçerik kimliklerinin uygulama içi teknik kimliklerle ilişkisini açıklaştır.

**Bilinen ayrı hata adayı:** `content/demo_eldoria/gameplay_rules.json` dosyasında movement bölümü bulunmadığı, `movement_test` paketinde ise `hero` için hareket profili bulunduğu daha önce tespit edildi. `game_window.py` hareket profili bulamadığında klavye ve tıklamayla hareket etkinleşmiyor. Loader'ın eksik movement alanında boş mapping döndürmesi mevcut testlerle korunan davranış olduğundan, düzeltme loader varsayılanını gelişigüzel değiştirmek yerine demo paketinin açıkça doğru hareket profilini tanımlaması üzerinden ele alınmalı. Bu konu kimlik refaktöründen ayrı izlenmeli.

**Kabul ölçütü:** Her paket kendi gerektirdiği sözleşmeyi karşılar; eksik zorunlu veri erken ve açıklayıcı biçimde raporlanır; mevcut test paketlerinin amaçlı farklılıkları korunur.

### Aşama 3 — Uygulama servisleri ve alan sınırları

**Hedef:** UI ve alan modüllerinin eski servis erişim kalıplarına bağımlılığını azaltmak.

İşler:
- `GameplayService` sorumluluklarını ve dışarı açtığı API'leri envanterle.
- UI katmanının doğrudan veri deposu/alt sistem iç yapılarına eriştiği yerleri bul.
- Aynı iş kuralının birden fazla katmanda uygulanıp uygulanmadığını incele.
- Komutlar, sorgular ve durum değişiklikleri için tutarlı servis giriş noktaları belirle.
- Servislerin başlangıç, yeniden yükleme ve oturum geçişi davranışlarını incele.
- Döngüsel import, gizli global durum ve yaşam döngüsü bağımlılıklarını azalt.

**Kabul ölçütü:** UI iş kurallarını kendisi yeniden uygulamaz; alan kuralları tek bir yetkili katmanda kalır; servis API'leri test edilebilir ve açık sözleşmelere sahiptir.

### Aşama 4 — Arayüzün yeni mimariye tam uyumu

**Hedef:** Ekranların ve taşınabilir pencerelerin eski ekran/oyuncu varsayımlarını kullanmamasını sağlamak.

İşler:
- Karakter, envanter, pazar, diyalog, görev, üretim, konteyner, ticaret ve savaş ekranlarını aynı kontrol listesiyle tara.
- Ekranların oyuncu/aktör/karakter kimliğini nereden aldığını doğrula.
- Pencere yöneticisi, ekran yaşam döngüsü, açılış-kapanış, odak ve klavye kısayolu sözleşmelerini incele.
- Dünya ekranının sürekli görünmesi ve diğer panellerin taşınabilir pencere olması kararını koru.
- ESC menüsü ve pencere X davranışlarını regresyon testleriyle güvenceye al.
- UI'nin snapshot veya koleksiyon sırasına bağlı varsayımlarını kaldır.

**Kabul ölçütü:** Ekranlar merkezi servis bağlamını kullanır; pencereler birbirlerinin durumunu bozmaz; klavye/fare ve pencere davranışları manuel kabul testinden geçer.

### Aşama 5 — Kayıt, yükleme ve eski veri uyumluluğu

**Hedef:** Mimari temizliğin mevcut kayıtları bozmasını engellemek.

İşler:
- Save schema sürümünü, serialize/deserialize akışını ve oturum geri yükleme adımlarını incele.
- Eski `hero` kimliklerinin kayıtlarda nerelerde geçtiğini belirle.
- Gerekliyse sürümlü ve idempotent bir migration tasarla.
- Actor-character, inventory-owner, account-owner, quest-owner ve diğer ilişkileri doğrula.
- Eksik/bozuk kayıtların güvenli hata davranışını belirle.
- Eski kayıt, yeni kayıt, yükle-kaydet-tekrar yükle ve migration testleri ekle.

**Kabul ölçütü:** Eski kayıtlar veri kaybı olmadan yüklenir veya açık ve test edilmiş migration ile dönüştürülür; yeni kayıtlar yeni sözleşmeyi kullanır.

### Aşama 6 — Test mimarisi ve kalite kapıları

**Hedef:** Eski bağımlılıkların tekrar eklenmesini otomatik olarak yakalamak.

İşler:
- Testleri unit, integration, content validation, persistence, UI ve end-to-end gruplarına ayır.
- Test fixture'larının gerçek runtime sözleşmesini yansıtmasını sağla.
- Kimlik, paket yükleme, hareket, UI pencereleri ve kayıt akışları için regresyon testleri ekle.
- Statik arama/lint kurallarıyla yeni doğrudan `"hero"` erişimlerini ve yasaklı varsayımları yakalamayı değerlendir.
- Testlerde gereksiz mock kullanımını ve aşırı ortak fixture bağımlılıklarını incele.
- CI'da gerekli test/lint kapılarını belgeleyip doğrula.

**Kabul ölçütü:** Kritik mimari kurallar otomatik testlerle korunur; tam test paketi ve kalite kontrolleri geçer.

### Aşama 7 — Dünya, hareket, render ve performans entegrasyon kontrolü

**Hedef:** Mimari temizlik sırasında dünya simülasyonu ve 2.5D görselleştirmenin kararlılığını korumak.

İşler:
- Oyuncu hareketi, NPC hareketi, click-to-move, çarpışma ve aktör seçimini merkezi kimlik/servis sözleşmeleriyle doğrula.
- Dünya render'ı, görünürlük/culling, kamera/projeksiyon ve animasyon akışlarının UI/servis refaktörlerinden etkilenmediğini kontrol et.
- Hareket girdisinin config eksikliği nedeniyle sessizce devre dışı kalmasını önleyen paket doğrulama/kabul testlerini ekle.
- Performans ölçümlerini aynı aktör sayısı ve aynı senaryolarla karşılaştır.
- Animasyonun zamana değil gerçek hareket/adım döngüsüne bağlı kalmasını doğrula.

**Kabul ölçütü:** Klavye ve mouse hareketi çalışır; oyuncu/NPC hareketi ve animasyon senkronu korunur; render testleri geçer; ölçülmemiş performans kazanımı iddia edilmez.

### Aşama 8 — Dokümantasyon, temizlik ve kapanış

**Hedef:** Yeni mimari kurallarını kalıcı ve anlaşılır hâle getirmek.

İşler:
- Güncel mimari kararları ve servis/kimlik/içerik sözleşmelerini belgele.
- Eski davranışlardan kalan geçici uyumluluk katmanlarını yalnızca artık gerekli olmadıkları kanıtlandıktan sonra kaldır.
- Kullanılmayan kod, yinelenen yardımcılar, ölü konfigürasyonlar ve güncelliğini yitirmiş dokümanları tespit et.
- Geliştirici çalışma yönergelerini, test komutlarını ve bilinen sınırlamaları güncelle.
- Son tarama ve test sonuçlarını başlangıç envanteriyle karşılaştır.

**Kabul ölçütü:** Bilinen eski mimari bağımlılıkların her biri kaldırılmış, bilinçli olarak korunmuş veya gerekçesiyle ertelenmiş olarak kayıtlıdır.

## 4. Öncelik sırası ve bağımlılıklar

| Öncelik | Aşama | Neden |
|---|---|---|
| P0 | 0 — Envanter | Değişiklik öncesi gerçek kapsamı ve riski belirler |
| P1 | 1 — Kimlik | Birçok ekran ve servis için ortak temel |
| P1 | 2 — İçerik sözleşmesi | Hareket gibi runtime özelliklerinin doğru yapılandırılmasını sağlar |
| P2 | 3 — Servis sınırları | UI ve alan modüllerinin bağımlılıklarını sadeleştirir |
| P2 | 4 — UI uyumu | Merkezi kimlik ve servis sözleşmelerini tüm ekranlara taşır |
| P1 | 5 — Persistence | Kimlik değişikliklerinin kayıt kaybına yol açmasını engeller; Aşama 1 ile birlikte tasarlanır |
| P2 | 6 — Test/CI | Her aşamaya eşlik eder; kapanışta kurallar otomatikleştirilir |
| P2 | 7 — Dünya ve performans | Oynanışın ve render'ın regresyona uğramadığını doğrular |
| P3 | 8 — Dokümantasyon/kapanış | Temizliği kalıcı hâle getirir |

Aşamalar katı biçimde birbirinden kopuk değildir. Özellikle kayıt uyumluluğu Aşama 1'den önce tasarlanmalı; testler ise tüm aşamalarda yazılmalıdır.

## 5. Her değişiklik için zorunlu iş akışı

1. Sorunu ve mevcut davranışı tanımla.
2. İlgili kod, içerik, test ve kayıt noktalarını tara.
3. Etki alanı ve geriye dönük uyumluluk riskini yaz.
4. En küçük güvenli değişikliği uygula.
5. İlgili hedefli testleri çalıştır.
6. Gerekirse tam test/lint paketini çalıştır.
7. Kullanıcıya oyun içi manuel kabul adımlarını ver.
8. Kullanıcı sonucu doğruladıktan sonra aşama maddesini tamamlandı olarak işaretle.
9. Ayrı ve açıklayıcı commit oluştur; `main` dalına doğrudan müdahale etme.

## 6. Şimdilik kapsam dışı

- Yeni oyun mekaniği veya içerik özelliği geliştirmek.
- Görsel tasarımı baştan değiştirmek.
- Pygame'den Godot'a geçmek.
- Kanıt olmadan tüm mimariyi yeniden yazmak.
- Sırf isim değiştirmek amacıyla kayıt kimliklerini topluca dönüştürmek.
- Ölçüm olmadan hız, animasyon, kamera veya render parametrelerini değiştirmek.
- Kullanıcı tarafından doğrulanmış davranışları refaktör gerekçesiyle sessizce değiştirmek.

## 7. İlk uygulama paketi

Roadmap onaylandıktan sonra ilk çalışma paketi şu sırayla yürütülür:

1. Aşama 0 envanterini tamamla; tüm runtime ve test kapsamını dosya bazında raporla.
2. Kimlik ve kayıt sözleşmelerini birlikte inceleyip Aşama 1 tasarımını kesinleştir.
3. Demo paketindeki eksik movement konfigürasyonunu kimlik refaktöründen ayrı, küçük bir düzeltme olarak ele al.
4. Kimlik geçişini küçük adımlarla uygula; UI ve persistence regresyonlarını test et.
5. Her aşama sonunda kullanıcıya değişen dosyaları, test sonuçlarını ve manuel kabul adımlarını sun.

## 8. Tamamlanma tanımı

Bu program ancak aşağıdaki koşulların tümü sağlandığında tamamlanmış sayılır:

- Eski mimari bağımlılıkları için kapsamlı, dosya bazlı envanter vardır.
- Runtime sistemleri oyuncu adını veya tarihsel `hero` sabitini kimlik olarak kullanmaz.
- Merkezi oyuncu bağlamı tüm ilgili ekran ve servislerde tutarlı kullanılır.
- İçerik paketleri gerekli yapılandırmaları açıkça sağlar ve doğrulanır.
- Eski kayıtlar için test edilmiş uyumluluk/migration yolu vardır.
- Kritik mimari kurallar regresyon testleriyle korunur.
- Tam test ve kalite kapıları geçer.
- Hareket, pencere yönetimi, kayıt/yükleme ve temel dünya etkileşimleri oyun içinde doğrulanır.
- Kalan istisnalar gerekçeleriyle belgelenir.

---

**Not:** Bu belge bir uygulama planıdır; aşamaların tamamlandığı anlamına gelmez. Her aşamanın durumu, gerçek kod değişikliği ve test kanıtı geldikçe güncellenecektir.
