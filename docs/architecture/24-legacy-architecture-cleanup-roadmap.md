# Eldoria — Eski Mimari Bağımlılıklarını Temizleme Roadmap'i

**Durum:** Uygulama sürüyor — Aşama 2 (A2.3 isteğe bağlı alan ve varsayılan sözleşmeleri)  
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

**Hareket yapılandırması — güncel durum (2026-11-26):** Önceki incelemede `demo_eldoria/gameplay_rules.json` içinde movement bölümü olmadığı not edilmişti. `experiment/map-cleanup` dalının güncel içeriği yeniden kontrol edildiğinde bu notun artık geçerli olmadığı görüldü: demo paketi `movement.actors.hero` profilini açıkça tanımlıyor (`max_speed: 200`, koşu/gizlilik çarpanları ve ivmelenme/frenleme değerleri); `tests/test_application/test_content_pack.py` bu değerleri doğruluyor. `movement_test` paketi de oyuncu ve test NPC profillerini tanımlıyor. Loader'ın movement bölümünü isteğe bağlı kabul etmesi ve profil yoksa hız uydurmaması mevcut testlerle korunan bilinçli davranıştır. Bu nedenle hareket değerlerinde veya loader varsayılanlarında değişiklik yapılmadı. Oyuncu aktörü için profil bulunmaması durumunda `GameWindow` hareketi devre dışı bırakıp hata bildirimi gösterir; içerik sözleşmesi incelemesinde bu davranış ayrıca değerlendirilebilir.

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
3. Demo paketindeki movement konfigürasyonunun güncel varlığını ve actor-ID eşleşmesini doğrula; eksik profil varsa loader varsayılanı uydurmak yerine paket sözleşmesi kapsamında ele al.
4. Kimlik geçişini küçük adımlarla uygula; UI ve persistence regresyonlarını test et.
5. Her aşama sonunda kullanıcıya değişen dosyaları, test sonuçlarını ve manuel kabul adımlarını sun.

## 7.1. Aşama 2 uygulama günlüğü

| Tarih | Alt iş | Durum | Kanıt / not |
|---|---|---|---|
| 2026-11-26 | A2.1 — Şema sürümü tür doğrulaması | Kod ve CI doğrulaması tamamlandı | `application/content_pack.py` içindeki aktif paket yapılandırması ve sekiz içerik tanımı yükleyicisi artık `schema_version` alanının boolean değil gerçek integer olmasını şart koşuyor. `tests/test_application/test_content_pack.py` sekiz tanım yükleyicisi ve aktif paket yapılandırması için `true` değerini reddeden regresyon testleri içeriyor. Kod commit `fb0409029a166b02808b8af18a1a1591509d1506`, test commit `6f8775ba1f9d4bc5d94b99cb9493dd5082d95386`. Eldoria CI run `45887625332` ve Core Quality run `45887625379` başarılı. |
| 2026-11-26 | A2 — Hareket profili envanteri | İnceleme tamamlandı | Güncel demo paketi `hero` hareket profilini içeriyor; önceki “demo paketinde movement bölümü eksik” notu geçersiz olarak düzeltildi. Hareket davranışı değiştirilmedi. |
| 2026-11-26 | A2.2 — Item referans bütünlüğü | Bu alt kontrol tamamlandı; A2.2 denetimi sürüyor | İncelemede `_validate_content_references` görev veren NPC, `collect` kaynak düğümü, `talk` NPC, pazar ve ticaret ortağı referanslarını zaten doğruluyordu. Ancak görev ödüllerindeki item ID'leri ve konteyner başlangıç içeriklerindeki item ID'leri paket item kataloğuna karşı doğrulanmıyordu. `populate_opening_content` artık item ve konteyner tanımlarını da önceden yükleyip bu iki ilişkiyi kayıt/oyun kurulumu öncesinde doğruluyor. Eksik item referansları için iki entegrasyon regresyon testi eklendi. Kod commit `078e3475568452802040743fd592b9b5699c3e58`, test commit `ee5ea5227392329a174f6923598ef2b5d0e22767`. Eldoria CI run `45893116927` ve Core Quality run `45893116972` başarılı; Python 3.11/3.12 × Ubuntu/Windows test matrisinde 2.700 pytest testi ve 359 subtest geçti. Demo ve movement_test paketlerinin mevcut içerik referansları incelendi; item/container kataloğu olmayan movement_test paketi bu tanımları kullanmadığı ve görev listesi boş olduğu için geçerli kaldı. A2.2'nin NPC/diyalog, starter-map, kaynak, üretim ve placement ilişkilerinin kalan denetimi devam ediyor. |

| 2026-11-26 | A2.2 — NPC/diyalog ve harita kaynak referansları | Tamamlandı | NPC `dialogue_id` alanı artık boş/geçersiz ve yinelenen değerleri reddediyor; NPC referansının starter açılış diyaloğunda gerçekten tanımlı olması, açılış diyaloğunun `opening` aşamasındaki NPC'ye ait olması ve tanımlı her düğüm `speaker` alanının diyalog sahibiyle uyuşması doğrulanıyor. Açılış, görev, pazar ve ticaret diyalog tanımlarında global ID çakışmaları da erken reddediliyor. Harita paketi dünya haritası dosyası içermediğinde dahi etkin geçişin hedef haritası ve hedef hücreleri doğrulanıyor; harita landmark'larının `resource_node_id` alanı kaynak düğümü kataloğuna bağlanıyor. Starter `hex_start` map/hücre kontrolü, quest giver/talk/collect, market/trade NPC, placement→map/NPC/resource/container, patrol hücreleri ve production recipe→facility type kontrolleri de mevcut kod/testlerle yeniden incelendi; bunlara yeni kısıt eklenmedi. Dokuz regresyon testi eklendi. Kod commitleri: `5cbb5ce52c19134f38effe66e8ac2dde32268357`, `8997bae1233e8a464d9659f83cdda8b2c2a49e73`, `1d181c90ff7dea5d5ae7bb84ca0c89aefde1b3fd`, `9defa98b12b21de15689e343ce422e8685659867`; test commitleri: `8bc38bde0ae105f6e1a0f37835c5c0dabcd09805`, `9fa9b2e8c361fffc90e4f4440663677491d487ed`, `73e0c24cc73402455933e04befae297cc8176ea1`, `9134f9a48feff9c4cc846dbb212a737869967117`. Eldoria CI run `45895749526` başarılı: Python 3.11/3.12 × Ubuntu/Windows matrisinde `2709 passed`, `359 subtests passed` (59 uyarı, hata yok); Pygame headless smoke ve seçili Ruff kontrolleri başarılı. Core Quality run `45895749551` ve NPC spatial benchmark run `45895732846` de başarılı. A2.2 referans ilişkileri denetimi kapatıldı. Hareket aktör kimlikleri, faction kimlikleri, kill/reach/custom görev hedefleri, serbest ResourceType değerleri ve break_profile_id için yetkili katalog/semantik bulunmadığından tahminî referans kısıtları eklenmedi; bu alanlar kendi sözleşme tanımları gerektiğinde ele alınacak. |

| 2026-11-26 | A2.3 — Zorunlu/isteğe bağlı alan ve varsayılan sözleşmeleri | Uygulama sürüyor | `load_starter_content` artık ids/world/character temel alanlarının tür ve değerlerini yükleme aşamasında doğruluyor; world width/height isteğe bağlı kalıyor. `hex_start`, dialogue, production, markets, trade_partners ve faction isteğe bağlı bölümlerinin temel şekilleri kontrol ediliyor. Item/container tag listeleri ile production capability listeleri artık JSON listesi olmak zorunda; scalar string karakterlerine ayrılarak kabul edilmiyor. Item `attribute_bonuses` nesne ve bilinen Attribute anahtarları gerektiriyor; description metin olmak zorunda. Regresyon testleri eklendi. Kod commitleri: `0a1e5a819937309327c046391b56cbda22c04a57`, `5f01db494bbab506f249fd6d86a4d79438dc178e`, `b8a908313e76b9d8db8dc57f458277809fb75df6`, `3a78283c400e345b520bbdaa109fc7a5054c99e1`; test commitleri: `633aa8efa9dcbeadee5952c7b301bbb48cf0fd84`, `0cb16091dad050458b98c5e2fd1f66ad5a101481`, `5a09ebe80638b3dbb8ba3878dddd00dde91bb200`, `e9e98ce1afed1fc79962d7693b784b098f81e0fe`. Eldoria CI run `45897319519` başarılı: Python 3.11/3.12 × Ubuntu/Windows matrisinde `2714 passed`, `383 subtests passed` (59 uyarı, hata yok); Pygame headless smoke başarılı. Core Quality run `45897319510` ve NPC spatial benchmark run `45897302167` başarılı. Pazar/ticaret kayıtlarının iç alanları ve kalan isteğe bağlı metadata alanları için denetim sürüyor. |

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
