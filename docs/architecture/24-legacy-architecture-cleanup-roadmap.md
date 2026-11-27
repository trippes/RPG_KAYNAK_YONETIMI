# Eldoria — Eski Mimari Bağımlılıklarını Temizleme Roadmap'i

**Durum:** Aşama 3 sürüyor — A3.1–A3.4 tamamlandı; A3.5 kod/test değişiklikleri tamamlandı ve otomatik CI başarılı, manuel kabul doğrulaması bekleniyor
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

| 2026-11-26 | A2.3 — Zorunlu/isteğe bağlı alan ve varsayılan sözleşmeleri | Tamamlandı | Starter `ids/world/character` alanları ve opsiyonel `hex_start/dialogue/production/markets/trade_partners/faction` bölümleri yükleme aşamasında tür/değer kontrolünden geçiyor; world width/height bilinçli olarak opsiyonel. NPC varsayılanları (IDLE davranış, boş patrol/faction listeleri, 0.5 sn patrol aralığı), quest varsayılanları (sequential=false, required=1, optional=false, sıfır/boş reward), item/container/production varsayılanları ve movement profilinin eksik olması hâlinde hız uydurulmaması incelendi. Item/container tag alanları ve production capability alanları JSON listesi; item attribute_bonuses nesne ve bilinen Attribute anahtarları; item description metin. Market kataloglarında ID, diyalog, katalog, fiyat ve miktar; trade partner kayıtlarında ID, accepted_resources, başlangıç bakiyesi, buyback_rate ve unit_prices sözleşmeleri doğrulanıyor. Quest item ödül miktarı pozitif olmak zorunda. Geçerli market/trade örneği için pozitif test eklendi. Tekrarlanan varsayılanlar ortaklaştırıldı: `_movement_config_from_profile` MovementConfig sınıfının varsayılanlarını tek kaynak olarak kullanıyor; `_container_definition_from_record` doğrulama ve kayıt aşamasında aynı ContainerDefinition kurulumunu kullanıyor. Demo/test paket farkları amaçlı: demo_eldoria sunum asset/map placement, item/container katalogları ve production tanımı taşıyor; movement_test bunları içermeyen hareket odaklı paket, iki NPC ve üç hareket aktör profiliyle ayrılıyor. Her iki pakette quests dosyası boş, resources dosyası mevcut; items/containers/production ve sunum kataloglarının yokluğu opsiyonel davranış. Kod commitleri: `0a1e5a819937309327c046391b56cbda22c04a57`, `5f01db494bbab506f249fd6d86a4d79438dc178e`, `b8a908313e76b9d8db8dc57f458277809fb75df6`, `3a78283c400e345b520bbdaa109fc7a5054c99e1`, `37bbf036e39d98a91d5fee5a2bc6c67a7ee7b2c9`, `35df08e3708ffc367d2a45c5dadbe85adfd77c49`, `b8ad9e9642c17f9093ed21e28b13c96b24c7f637`, `da0598c43594870734a087584917c4fc54602377`; test commitleri: `633aa8efa9dcbeadee5952c7b301bbb48cf0fd84`, `0cb16091dad050458b98c5e2fd1f66ad5a101481`, `5a09ebe80638b3dbb8ba3878dddd00dde91bb200`, `e9e98ce1afed1fc79962d7693b784b098f81e0fe`, `f1603aaf882a94de7441ba705fe6acb65eab3f27`, `9dcf5eb5a8528abc51fbfbbd2ece5f0976f423a2`, `e4434ff0eaede58869dcdba434ed37185c72b526`. Eldoria CI run `45898866323` başarılı: Python 3.11/3.12 × Ubuntu/Windows matrisinde `2718 passed`, `390 subtests passed` (59 uyarı, hata yok), Ruff ve Pygame headless başarılı. Core Quality `45898866304` ve NPC spatial benchmark `45898866426` başarılı. |

**Aşama 2 kapanışı (2026-11-26):** A2.1 şema sürümü tür doğrulaması, A2.2 kimlik/referans ilişkileri ve A2.3 zorunlu/isteğe bağlı/varsayılan sözleşmeleri tamamlandı. Aşama 3'e geçiş için içerik paketleri ve yapılandırma sözleşmeleri kabul ölçütleri karşılandı.

| 2026-11-27 | A3.1 — GameplayService sorumluluk/API ve UI tüketici envanteri | **Tamamlandı (salt okunur envanter; kod değişikliği yok)** | Güncel dal kaynakları üzerinden servis ve bilinen UI tüketicileri yeniden incelendi; önceki yaklaşık sayılar güncellendi. Kesin bulgular ve dosya bazlı erişim listesi Bölüm 7.2'de kayıtlı. A3.1'in çıktısı servis sorumluluk haritası, public/private API envanteri, UI tüketici haritası, doğrudan Application erişimlerinin sınıflandırması ve read-model sözleşme boşluklarıdır. Bu kapanış A3.2 veya sonraki işlerin başladığı anlamına gelmez. |

| 2026-11-27 | A3.2 — Sorgu/read-model sözleşmesi | **Tamamlandı; CI başarılı** | `GameplayService.state()` ve `combat_state()` için salt okunur, deterministik, immutable view sözleşmesi tanımlandı. `test_gameplay_state_returns_detached_immutable_value_views` testi sıralama, tekrar sorguda kararlılık, frozen view alanları, snapshot'ın sonradan değişmemesi ve sorgunun tick ilerletmemesini doğrular. Eldoria CI run `45971100509` (Python 3.11/3.12 × Ubuntu/Windows test matrisi ve Pygame headless smoke) ile Core Quality run `45971100516` (Linux/Windows doğrulama) başarılı. Runtime/UI davranışı değiştirilmedi. |



### 7.3. A3.2 — Sorgu ve read-model sözleşmesi (2026-11-27)

**Amaç ve sınır:** A3.1'de tespit edilen doğrudan UI veri okumalarına geçiş yapmadan önce, mevcut servis sorgularının güvenilir read-model davranışını açıklaştırmak. Bu alt iş, mevcut `GameplayService.state()` ve `GameplayService.combat_state()` sorgularının sözleşmesini sabitler. Yeni oyun özelliği, ekran refaktörü veya UI'nin Application erişimlerini taşıma bu alt işin kapsamında değildir.

**Kabul edilen sözleşme:**

1. Sorgu metotları simülasyon tick'ini ilerletmez, kaynak/nesne tüketmez, faaliyet başlatmaz ve domain state üzerinde değişiklik yapmaz.
2. Sorgu sonucu, mutable domain aggregate yerine immutable view dataclass'ları ve tuple koleksiyonları sunar.
3. View alanları sorgu anındaki değeri temsil eder; kaynak aggregate daha sonra değişse de daha önce alınmış snapshot değişmez (detached snapshot).
4. Aynı state için tekrarlanan sorgu eşit ve deterministik sonuç verir; koleksiyonlar kararlı kimlik sırasıyla sunulur.
5. Komutlar mevcut servis komutlarında kalır; read-model nesneleri üzerinden state değiştirilemez.
6. UI için henüz read-model'i bulunmayan NPC/dialogue, quest/graph, recipe/facility kataloğu ve aktif dünya başlığı verileri doğrudan Application erişimiyle okunmaya devam ediyor. Bunlar bilinen açıklar olarak korunur; A3.2'de sahte veya eksik bir birleşik snapshot üretmek yerine sonraki alt iş için açıkça bırakılır.

**Mevcut yüzeyin sınıflandırması:**

| Sorgu | Dönüş sözleşmesi | A3.2 kararı |
|---|---|---|
| `state()` | `GameplaySnapshotView`; frozen dataclass ve tuple tabanlı inventory/node/facility/job/chain/actor/activity görünümleri | Kabul edildi; deterministiklik, değişmezlik ve snapshot ayrışması testle güvenceye alındı. |
| `combat_state()` | `CombatSnapshotView`; frozen combatant/encounter view tuple'ları | Kabul edildi; mevcut detached/immutable regresyon testi korundu. |
| `inventory()`, `actor()`, `activity()`, `container_state()`, `lock_state()` | Alan bazlı immutable view'lar | Mevcut view sözleşmesiyle uyumlu; sonraki servis sınırı çalışmasında korunacak. |
| `actor_character()`, `market_for_npc()`, `trade_partner_for_npc()`, `available_quests()` | Domain nesnesi/aggregate döndüren geçiş API'leri | UI-safe read-model olarak kabul edilmedi; dönüş tipi standardizasyonu ayrı iş olarak açık bırakıldı. |

**Test ve CI kanıtı:** `tests/test_application/test_gameplay_service.py` içine `test_gameplay_state_returns_detached_immutable_value_views` eklendi. Test; inventory sıralamasını, actor sıralamasını, aynı state için tekrarlanan snapshot eşitliğini, frozen view alanlarının değiştirilememesini, kaynak inventory/node değiştikten sonra eski snapshot'ın korunmasını ve sorgular arasında simulation tick'in sabit kalmasını doğrular. Aynı dosyadaki `test_combat_state_returns_detached_immutable_views` combatant/encounter read-model'inin detached ve immutable davranışını zaten doğruladığından tekrar yazılmadı. Eldoria CI run `45971100509` içindeki beş işin tamamı başarılı; Core Quality run `45971100516` içindeki `verify` ve `verify-windows` işleri de başarılı. Her iki run `experiment/map-cleanup` dalındaki `e94aa181770461c6125954271ed6c9421c5d35bb` commit'ini doğruladı.

**Değişiklik sınırı:** Runtime kodu, UI dosyaları, GameApplication composition root, persistence biçimi ve mevcut oyun davranışı değiştirilmedi. Tek kod deposu değişikliği hedefli regresyon testidir; bu nedenle A3.2 bir servis read-model sözleşmesi/kalite kapısı alt işi olarak kapatılır. A3.1'de sayılan doğrudan Application/private erişimler bu alt iş sonunda hâlâ mevcuttur; kaldırıldıkları iddia edilmez. Bunların güvenli servis sorgularına taşınması A3'ün sonraki alt işidir.

| 2026-11-27 | A3.3 — Üretim kataloğu ve tesis sorgu sınırı | **Tamamlandı; CI başarılı** | Kapsam yalnızca production_screen.py içindeki iki doğrudan service.application sorgusudur. Tarif kataloğu GameplayService.recipes_state() ile immutable RecipeView olarak; uygun tesis çözümlemesi production_facility_for_recipe() ile immutable FacilityView olarak sunulur. Tesis uyumluluğu/otomatik seçim kuralı UI'den servise taşındı. test_production_catalog_queries_are_immutable_and_service_owned sıralama, tekrar sorgu kararlılığı, değişmezlik, uyumlu/uyumsuz tesis seçimi ve tick'in değişmemesini doğrular. Eldoria CI run `45972943220` içindeki beş işin tamamı (Python 3.11/3.12 × Ubuntu/Windows ve Pygame headless smoke) başarılı; Core Quality run `45972943211` içindeki `verify` ve `verify-windows` işleri başarılı. Her iki run `a527135ef5dfe7ac16466962a3bdcb5f9324fa0b` kod/test commit'ini doğruladı. Başka UI ekranları, özel servis alanları, genel application property'si ve A4 kapsamı değiştirilmedi. |
| 2026-11-27 | A3.4 — Görev ve diyalog sorgu sınırı | **Tamamlandı; CI başarılı** | GameplayService artık immutable QuestView, QuestObjectiveView, QuestRewardView, QuestBranchView ve DialogueSessionView read-model'lerini sunuyor. quest_log_state() / quest_log_counts() görev günlüğünü; dialogue_session_for_npc(), dialogue_npc_name() ve dialogue_choices() NPC/diyalog sorgularını servis sınırına taşıyor. Diyalog seçeneklerinin mevcut marangoz, demirci, kervancı ve han görev koşulları servis katmanına alındı; mevcut görev kabul/teslim komutları ve diyalog ilerletme davranışı korunuyor. dialogue_screen.py ile quest_log_screen.py artık service.application veya application.holder okumuyor; diyalog ekranı _dialogue_context, _player_name_confirmed ve _creation_from_eren private erişimlerini kullanmıyor. Yeni read-model değişmezliği, tekrarlı sorgu tutarlılığı, tick'in değişmemesi, diyalog seçeneği filtrelemesi ve görev grafiği görünümü test edildi. Kod/test doğrulaması commit 0545dae2f22f2dbfe97f057f2ecce799b8a6d49e üzerinde Eldoria CI run 45975606001 (5/5 iş başarılı) ve Core Quality run 45975606008 (2/2 iş başarılı) ile tamamlandı. Görev veren NPC/içerik eksikliği nedeniyle oyun içi görev kabul/teslim manuel kabulü bu alt aşamanın CI doğrulamasından ayrı olarak beklemede kalır. |

### 7.4. A3.3 — Üretim kataloğu ve tesis sorgu sınırı (2026-11-27)

**Amaç ve sınır:** A3.1 envanterinde belirlenen doğrudan Application erişimlerinden yalnızca game_ui/screens/production_screen.py dosyasındaki tarif kataloğu ve üretim tesisi sorgularını servis sınırına almak. Bu alt aşama üretim ekranının tamamını yeniden tasarlamaz; üretim mekaniğini, UI düzenini, pencere yaşam döngüsünü veya diğer ekranları değiştirmez.

**Uygulanan sözleşme:**

1. GameplayService.recipes_state() tarifleri kimliklerine göre sıralı, frozen RecipeView tuple'ı olarak döndürür. Tarif girdileri/çıktıları ve süreleri immutable değer nesneleri olarak korunur.
2. GameplayService.production_facility_for_recipe(recipe_id, facility_id=None) tesis uyumluluğunu ve otomatik tesis seçimini servis katmanında çözer; UI'ye mutable tesis aggregate'ı yerine FacilityView döndürür.
3. Açıkça seçilmiş tesis için önceki davranış korunur: tesis mevcut, aktif ve tarifi destekli olmalıdır. Otomatik seçimde bunlara ek olarak kapasite boş olmalıdır. Adaylar tesis kimliğine göre deterministik sıralanır.
4. ProductionScreen artık service.application üzerinden tarif/tesis deposuna erişmez; yalnızca servis sorgularını kullanır.
5. Üretimi başlatan mevcut start_production komutu ve ekranın görünüm/etkileşim davranışı değiştirilmez.

**Test kanıtı:** test_production_catalog_queries_are_immutable_and_service_owned; tarif sıralaması, tekrarlı sorgu eşitliği, frozen view, uygun/uyumsuz tesis çözümlemesi ve sorgular arasında simulation tick'in sabit kalmasını doğrular. Eldoria CI run `45972943220` içindeki beş işin tamamı ve Core Quality run `45972943211` içindeki iki işin tamamı başarılıdır; her iki workflow da kod/test commit'i `a527135ef5dfe7ac16466962a3bdcb5f9324fa0b` üzerinde yeşildir.

**Hariç tutulanlar:** Diyalog, görev günlüğü, renderer, karakter oluşturma ve ticaret ekranlarındaki Application erişimleri; servis private alanlarına erişimler; GameplayService.application property'sinin kaldırılması; A4 ekran/pencere uyumu. Bunlar bu alt aşamanın kapsamına alınmamıştır.


### 7.5. A3.4 — Görev ve diyalog sorgu sınırı (2026-11-27)

**Amaç ve sınır:** A3.1 envanterinde belirlenen dialogue_screen.py ve quest_log_screen.py içindeki doğrudan Application/SessionBundle okumalarını, görev/graph verisi okumalarını ve diyalog ekranının servis private erişimlerini yalnızca bu iki ekran kapsamında servis sözleşmesine taşımak. Başka ekranlar, renderer, karakter oluşturma ekranının kendi private erişimleri, A4 pencere/yaşam döngüsü çalışmaları ve yeni görev/NPC/diyalog içeriği bu alt aşamaya dahil değildir.

**Uygulanan sözleşme:**

1. quest_log_state(category) aktif/tamamlanmış/başarısız görevleri kimlik sıralı, detached ve frozen QuestView tuple'ı olarak döndürür. Her görünüm immutable objective, reward ve graph branch bilgilerini; görev verenin görünen adını taşır. quest_log_counts() üç kategori için sayıları sunar.
2. dialogue_session_for_npc(target_npc_id) oyuncu aktörünü merkezi player context üzerinden çözer; NPC ve uygun diyalog kimliğini servis katmanında seçerek frozen DialogueSessionView döndürür. dialogue_npc_name() NPC adını registry erişimini UI'den saklayarak sunar.
3. dialogue_choices(actor_id, npc_id, dialogue_id, node_id) diyalog koşullarını ve mevcut kervancı/demirci/marangoz/han görev koşullarını servis içinde değerlendirir. UI yalnızca sunulacak immutable DialogueChoice kayıtlarını alır.
4. Açılış diyaloğunun isim onayı ve karakter oluşturma yönlendirmesi için player_name_confirmed, confirm_player_name() ve begin_character_creation_from_dialogue() public servis girişleri eklendi. Diyalog ekranı ilgili private alanlara doğrudan erişmez.
5. DialogueScreen ve QuestLogScreen doğrudan service.application / application.holder erişimlerini kaldırıp yalnızca servis sorgu/komutlarını kullanır. Görev branch seçimi mevcut choose_quest_branch() komutundan yürür; mevcut görev kabul/teslim komutları değiştirilmez.
6. Görev kabulü, teslimi, ödül, diyalog seçimi veya oyun içeriği için yeni özellik eklenmedi; UI düzeni ve pencere davranışı değiştirilmedi.

**Test ve CI kanıtı:** test_quest_journal_read_models_are_immutable_and_read_only, test_dialogue_choice_query_is_service_owned_and_read_only ve test_dialogue_choice_query_hides_blacksmith_delivery_for_incomplete_objective testleri read-model kararlılığı/değişmezliği, salt okunurluk, tick sabitliği ve görev koşullarını doğrular. Quest graph integration ve UI testleri yeni view sözleşmesine göre güncellendi. Eldoria CI run 45975606001 içindeki Python 3.11/3.12 × Ubuntu/Windows test işleri ile Pygame headless smoke işi (5/5) başarılıdır. Core Quality run 45975606008 içindeki Linux/Windows verify işleri (2/2) başarılıdır. İki run da kod/test commit'i 0545dae2f22f2dbfe97f057f2ecce799b8a6d49e üzerinde tamamlandı.

**Değişiklik sınırı ve kalan manuel kontrol:** Runtime değişiklikleri yalnızca application/gameplay_service.py, game_ui/screens/dialogue_screen.py ve game_ui/screens/quest_log_screen.py dosyalarındadır. İlgili servis/UI testleri güncellendi. Diğer UI ekranları ve A4 kapsamı değiştirilmedi. Diyalog/görev servis sözleşmesi CI ile doğrulanmıştır; ancak mevcut içerikte görev veren NPC bulunmadığından gerçek oyun içi görev alma/teslim etme manuel kabulü yapılmış sayılmaz. character_creation.py içindeki ayrı private alan erişimleri A3.4 kapsamına alınmamıştır.

### 7.6. A3.5 — UI/servis sınırlarının kapanışı (2026-11-27)

**Amaç ve sınır:** A3.5, Aşama 3'ün son alt aşamasıdır. A3.1–A3.4 sonrasında kalan UI iç depo erişimlerini, servis private alan kaçışlarını ve oturum kapsamlı runtime cache yaşam döngüsünü kapatır. Yeni A3.6/A3.7/A3.8 alt aşamaları oluşturulmaz. A4 pencere yöneticisi/ekran yaşam döngüsü, savaş, hareket, harita, animasyon ve görsel değişiklikler kapsam dışıdır.

**Uygulanan servis sözleşmeleri:**

1. Renderer için `active_world_state()` immutable `WorldView` döndürür; `quest_panel_state()` aktif görev özetini mevcut immutable `QuestView` sözleşmesiyle sunar. Görev hedefinin konum/NPC görünen adı servis içinde çözülür.
2. Ticaret ekranı `trade_partner_state()` ile immutable `TradePartnerView`, `dialogue_npc_name()` ile NPC görünen adını alır.
3. Karakter oluşturma ekranı `character_creation_state()`, `character_creation_options()` ve `customize_player_character()` girişlerini kullanır. Irk/sınıf seçenekleri immutable view olarak sunulur; yaş, isim, özellik puanı ve seçilen içerik kimliklerinin doğrulanması ile mevcut NPC ilişki davranışı servis katmanında yürütülür.
4. `GameplayService.application` genel kaçış noktası kaldırıldı. UI'nin `_character_factory`, `_creation_from_eren`, `_player_name_confirmed` veya `_dialogue_context` gibi private servis alanlarına erişimi kaldırıldı.
5. SessionBundle değiştiğinde zincirler dispose edilip session-bound hex physics, companion, NPC behavior ve NPC avoidance cache'leri temizlenir. `load()` ve lazy bundle değişimi aynı reset yolunu kullanır. İçerik tanımları, oyuncu bağlamı ve diyalog action kayıtları session geçişinde korunur; yeniden bağlama davranışı korunur.

**UI sınırı:** `renderer.py`, `character_creation.py` ve `trade_screen.py` artık `service.application` veya `application.holder` okumaz. Önceki A3 alt aşamalarında taşınmış production, dialogue ve quest log ekranlarıyla birlikte bilinen UI tüketicilerinde doğrudan GameplayService Application erişimi kalmamıştır. `tests/test_application/test_gameplay_service_boundaries.py` tüm `game_ui` Python dosyalarını tarayarak Application/private-service kaçışlarını regresyon testiyle yasaklar ve servis üzerindeki public `application` property'sinin bulunmadığını doğrular.

**Test kapsamı eklendi/güncellendi:**

- `test_active_world_and_quest_panel_queries_are_read_only_views`: aktif dünya view değişmezliği, tekrarlı sorgu ve tick'in sabitliği.
- `test_quest_panel_state_returns_populated_immutable_snapshot`: HUD görev panelinin dolu görev, hedef/amaç ilerlemesi ve ödül alanlarını tekrarlanabilir/değişmez sorgu olarak sunması.
- `test_character_creation_service_owns_validation`: karakter oluşturma iş kurallarının servis tarafından reddedilmesi.
- `test_character_creation_and_trade_queries_return_immutable_views`: karakter seçenekleri ve ticaret ortağı view değişmezliği.
- `test_load_switch_discards_session_bound_runtime_caches`: kayıt yükleme sırasında chain dispose/temizliği ve oturuma bağlı runtime cache invalidation.
- `test_game_ui_does_not_reach_gameplay_service_internals` ve `test_gameplay_service_does_not_publish_application_escape_hatch`: mimari sınır regresyonları.
- Önceden var olan servis, görev/diyalog, üretim, UI ve save/load testleri korunmuştur.

**Doğrulama durumu:** İlk A3.5 CI denemelerinde `GameplayService.application` kaldırılmasına rağmen `hex_world_initializer.py` ve eski testlerde kalan erişimler, ayrıca HUD/karakter oluşturma test double'larının yeni servis read-model sözleşmesine uyumsuzluğu tespit edildi. Eksikler `8d153b24c797f6a38543674215ff5bc01ec13c86` commit'inde giderildi: Hex dünya başlatıcısı `active_world_state()` ve `validate_session()` kullanır; yeni oyun testi `customize_player_character()` komutunu ve servis API'si üzerinden oturum kimliğini doğrular; HUD ve karakter oluşturma testleri yeni read-model sözleşmesine uyarlandı. Hex initializer test düzenekleri de `cf520d6497eea8b466fe0799685162c21b8b01b1` commit'inde Application yerel composition-root değişkeni üzerinden kurulum yapacak ve yeni servis sorgularını taklit edecek şekilde düzeltildi. Son durum commit'i `6a259efce1d61c25a06384f836c8011dd2c8e56e` üzerinde Eldoria CI run `45980434458` içindeki Python 3.11/3.12 × Ubuntu/Windows test işleri ve Pygame headless smoke işi (5/5) başarılıdır; Core Quality run `45980434434` içindeki Linux/Windows doğrulama işleri (2/2) başarılıdır. Böylece A3.5 otomatik kod/test ve CI doğrulaması tamamlanmıştır. Kullanıcının bildirdiği manuel kabul sonucuna göre oyun penceresinde HUD/görev paneli ve karakter oluşturma kontrolleri başarılıdır. Ticaret ekranı için gerekli hancı NPC bu aşamada eklenmeyecek; ticaret ekranının manuel kabulü tüm geliştirme aşamaları tamamlandıktan sonraki genel oyun kabul testine ertelenmiştir. Bu nedenle A3.5'in kendi manuel kabul kapsamı tamamlanmıştır; ticaret ekranı genel oyun kabulü için açık takip maddesi olarak kalır.

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


### 7.2. A3.1 — GameplayService ve UI tüketici envanteri (2026-11-27)

**İnceleme sınırı:** Yalnızca `experiment/map-cleanup` dalındaki `application/gameplay_service.py` ve A3.1 önceki taramasında belirlenen yedi UI tüketicisi incelendi. Bu çalışma salt okunur keşif ve dokümantasyondur; runtime/UI kodu değiştirilmedi. Kaynak dosya anlık görüntüleri: `application/gameplay_service.py` blob `ead3443856219f7f27310d89295dfb5389589f40`; UI dosyaları: `combat_screen.py` `f20946bdf1203330dc04a5b1c4e7f934392f5b7e`, `dialogue_screen.py` `d27bf3041c4d2fd0b0e463ab3bbb9512e4dd5378`, `renderer.py` `f2ade0ea2b8d2bd72b2c761a7c052d84a0dfd384`, `production_screen.py` `7c59b491d0388d562ea55cdd010f6c4854329ff1`, `quest_log_screen.py` `e027b60158fbab80ed8052f4c361ce47f8f6d875`, `character_creation.py` `7cac72f625336ba21cee35fcf1284c363728c812`, `trade_screen.py` `ecbdf4ca050725293787d6ed0d00bfd7c995d9f1`.

**Servis büyüklüğü ve API envanteri:** Dosya 2.571 satırdır. `__init__` hariç 151 metot tanımı vardır: 133 public isim (property erişimleri dâhil) ve 18 private metot. Public yüzeyin ana sorumluluk kümeleri:

- Oturum/kimlik/yaşam döngüsü: `application`, `player_actor_id`, `player_character_id`, `player_inventory_id`, `player_account_id`, `configure_player_context`, `save`, `load`, `state`.
- Hareket ve mekânsal etkileşim: sürekli/yönlü/hedefe hareket, hex actor binding, NPC spatial binding ve patrol/avoidance, companion komutları, dünya noktası hedef/transition çözümleme.
- Aktör, envanter, ekipman ve faaliyet: actor kaydı/bağları, `actor`, `actor_character`, `actor_stats`, inventory/item/equipment sorguları, equip/unequip, gathering, activity ve tüketim.
- Konteyner/kilit: konteyner ve kilit tanımları/kayıtları, durum sorguları, anahtar/lockpick/force denemeleri, taşıma/custody ve item/resource transferleri.
- Üretim/kaynak: collect, action cost, production başlatma, chain başlatma/ilerletme, zaman ilerletme.
- Ekonomi/ticaret: balance/credit/exchange, market offer ve merchant, market profile, NPC trade partner, satılabilir teklif ve satış.
- Sosyal/diyalog: NPC/faction kaydı, reputation/relationship, dialogue kaydı/eylemi, talk ve dialogue choice.
- Görev/ilerleme: quest graph/definition kaydı, kabul, durumlar, branch seçimi, objective ilerletme, teslim, experience ve skill.
- Savaş: combatant ekleme, combat snapshot, encounter oluşturma/tur ilerletme, attack ve round ilerletme.
- Okuma/raporlama: `state`, `actors_state`, `activities_state` ve alan bazlı read API'leri.

Bu kümeler tek bir facade üzerinde toplanmıştır. Servis canonical world state'in sahibi olduğunu söylemiyor; her işlemde güncel SessionBundle'ı çözüp mevcut alan sahiplerine delege ediyor. Bununla birlikte servis içinde chain/dialogue/quest kayıtları, consumable etkileri, hex physics snapshot'ları ve NPC behavior/avoidance sistemlerine ait cache/yardımcı durumlar tutuluyor. Bu nedenle servis yalnızca ince bir yönlendirme katmanı değildir; orchestration ve bazı oturum kapsamlı yardımcı durumları da taşır.

**UI tüketici haritası ve doğrudan Application erişimleri:**

| UI dosyası | `service.application` kullanımı | Gözlenen amaç |
|---|---:|---|
| `game_ui/screens/combat_screen.py` | 0 | Combat işlemleri `combat_state`, `combat_attack`, `next_combat_turn`, `advance_combat_round` servis API'leri üzerinden. |
| `game_ui/screens/dialogue_screen.py` | 6 | SessionBundle, NPC ve dialogue registry okumaları; ayrıca aşağıdaki private erişimler. |
| `game_ui/renderer.py` | 3 | Aktif dünya, aktif quest log ve SessionBundle okuması. |
| `game_ui/screens/production_screen.py` | 2 | Recipe ve facility verilerine erişim. |
| `game_ui/screens/quest_log_screen.py` | 3 | Quest log ve NPC/giver verilerine erişim. |
| `game_ui/screens/character_creation.py` | 2 | Karakter özelleştirme komutu ve NPC registry erişimi. |
| `game_ui/screens/trade_screen.py` | 1 | NPC kaydı/ismi erişimi. |
| **Toplam** | **17** | 6 dosyada 17 `service.application` ifadesi; 16 veri/registry okuması ve 1 doğrudan `application.customize_character` komutu. |

Ayrıca `dialogue_screen.py` ve `character_creation.py`, servis private alanlarına toplam 6 yerde erişiyor: `_dialogue_context` private metot çağrısı; `_character_factory`, `_creation_from_eren` ve `_player_name_confirmed` private durumlarına doğrudan erişim/değişiklik. Bu alanların bazıları iki ekran arasında ortak kullanılıyor. Dolayısıyla UI sınırındaki sorun yalnızca Application nesnesinin açığa çıkması değil, servis iç durumunun da UI tarafından tüketilmesidir.

**Read-model ve API sözleşmesi bulguları:**

- `GameplaySnapshotView` immutable bir görünüm olarak world_id/tick, inventories, resource nodes, facilities, jobs, chains, actors ve activities alanlarını kapsıyor.
- Combat için ayrı `CombatSnapshotView` / `combat_state` mevcut.
- UI'nin doğrudan okuduğu NPC/dialogue registry, quest log/graph/progress, recipes/facilities kataloğu ve aktif dünya adı için ortak snapshot/read-model yüzeyi bulunmuyor. Bu eksiklikler doğrudan Application erişimlerinin nedenlerinden bazılarıdır; A3.1'de yalnızca kayda geçirildi.
- `actor`, `inventory`, `container_state`, `lock_state` ve `activity` gibi API'ler immutable view döndürürken `actor_character`, `market_for_npc`, `trade_partner_for_npc` ve `available_quests` domain nesneleri/aggregate'ları döndürür. UI sınırında view ile domain aggregate ayrımı tutarlı değildir.
- Public `application` property'si tüm GameApplication'a erişim sağlıyor. Bu, servis API sınırını dışarıdan dolaşmayı mümkün kılan ana kaçış noktasıdır.
- `game_window.py` içindeki GameApplication oluşturma noktası composition root olarak sınıflandırıldı; tek başına UI tüketici ihlali sayılmadı.
- Mevcut architecture testleri Core/domain sınırlarını koruyor; game_ui katmanının `GameplayService.application` veya private servis alanlarına erişmesini engelleyen özel bir mimari koruma testi envanterde bulunmadı.

**A3.1 çıktısı ve karar:** Servis sorumlulukları, API yüzeyi, UI tüketicileri, doğrudan erişimlerin sayısı/amacı ve read-model boşlukları belgelenmiştir. Önceki nottaki 7 dosyada 21 `service.application` erişimi ifadesi güncel kaynakta doğrulanmadığı için kaldırılmış; güncel sayım 7 bilinen UI tüketicisinde 6 dosyada 17 erişim olarak düzeltilmiştir. A3.1 tamamlandı. Bu aşamada hiçbir UI erişimi taşınmadı, yeni read model eklenmedi, mimari test veya runtime kodu değiştirilmedi. Bunlar A3.2 ve devamındaki ayrı, sınırlandırılmış işlerin konusu olarak bırakıldı.
