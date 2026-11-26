# A1 + A5 — Oyuncu Kimliği ve Kayıt Uyumluluğu Uygulama Planı

> **Belge türü:** Mimari uygulama planı  
> **Durum:** A1.1–A1.3 tamamlandı; A1.4 kod ve CI doğrulaması tamamlandı, sandık manuel testi başarılı, görev alma/teslim manuel kabulü görev veren NPC bulunmadığı için beklemede; A1.5 kaynak taraması tamamlandı; A5 alternatif kimlikli kayıt/yükleme ve referans bütünlüğü testleri ile mevcut migrasyon uyumluluğu CI üzerinde doğrulandı  
> **Çalışma dalı:** `experiment/map-cleanup`  
> **Planın dayandığı kaynak:** `a961de7b91b6b7fe7d6b3aae48d2defc95fcb966`  
> **İlişkili yol haritası:** [24 — Legacy Architecture Cleanup Roadmap](24-legacy-architecture-cleanup-roadmap.md)

---

## 1. Amaç

A1, oyuncu kimliğinin uygulama genelinde tek ve tutarlı bir sözleşmeyle kullanılmasını; A5 ise bu kimlik düzenlemesinin kayıt/yükleme davranışını bozmadan uygulanmasını kapsar.

Bugünkü kodda oyuncuya ait aktör, karakter, envanter ve ekonomi hesabı kimlikleri bazı katmanlarda yapılandırılabilir durumdadır. Buna rağmen UI ekranlarının bir kısmı `"hero"` ve `"player"` sabitlerini doğrudan kullanır. Bazı ekranlar da aktör koleksiyonundaki ilk elemanın oyuncu olduğunu varsayar.

Bu çalışma aşağıdaki sonucu hedefler:

1. Oyuncu kimliklerinin kaynağı `GameplayService` olur.
2. UI, oyuncu kimliğini kendi içinde tahmin etmez veya sabit değerle belirlemez.
3. Aktör seçimi koleksiyon sırasına bağlı olmaz.
4. `actor_id`, `character_id`, `inventory_id` ve `account_id` birbirinden ayrı kimlikler olarak korunur.
5. Mevcut kayıt dosyaları yüklenmeye devam eder; yalnızca kodun iç erişim biçimi değişir.
6. Alternatif kimliklerle oluşturulmuş oturumların kaydedilip yüklenebildiği testlerle kanıtlanır.

Bu belge bir uygulama planıdır. Belge oluşturulurken kaynak kodu değiştirilmemiş, test çalıştırılmamış ve yeni bir oyun davranışı eklenmemiştir.

## 2. Kapsam ve kapsam dışı konular

### Kapsam

- `GameplayService` oyuncu kimliği sözleşmesinin netleştirilmesi.
- Karakter oluşturma ve karakter ekranlarının yapılandırılmış kimliklere geçirilmesi.
- Envanter, üretim, pazar, diyalog ve HUD erişimlerinin yapılandırılmış kimlikleri kullanması.
- Aktör koleksiyonunda `actors[0]` gibi sıra bağımlı oyuncu seçimlerinin kaldırılması.
- Alternatif kimliklerle servis ve UI davranışının hedefli testleri.
- Alternatif kimlikli oturumların kayıt/yükleme round-trip testleri.
- Mevcut kayıt sürümleri ve kimlik referansları için geriye dönük uyumluluk kontrolleri.

### Kapsam dışı

- Kayıtlardaki `hero`, `player` veya başka içerik kimliklerinin topluca yeniden adlandırılması.
- Eski kayıtların kimliklerini otomatik olarak yeni kimliklere dönüştüren bir migrasyonun şimdiden eklenmesi.
- Yeni bir PlayerIdentityManager / IdentityRegistry oluşturulması.
- UI ile uygulama servisleri arasındaki tüm sınırların bu aşamada yeniden tasarlanması. Bu daha geniş iş A3 kapsamındadır.
- Yeni oyun mekaniği, içerik, görsel tasarım veya performans optimizasyonu.
- `SessionBundle` yapısının yeniden yazılması.

## 3. Mevcut mimarinin doğrulanmış durumu

### 3.1. Oyuncu kimlikleri için mevcut merkez

`application/gameplay_service.py` içinde aşağıdaki mevcut alanlar ve erişim noktaları bulunur:

- `_player_actor_id`
- `_player_inventory_id`
- `_player_account_id`
- `player_actor_id`
- `player_inventory_id`
- `player_account_id`
- `configure_player_context(actor_id, inventory_id, account_id=None)`

Bu yapı yeni bir kimlik yöneticisi eklemeye gerek bırakmaz. Uygulama, var olan servisin sözleşmesini tamamlayıp UI'nin bu sözleşmeye uymasını sağlamalıdır.

### 3.2. İçerik paketi kurulumu

`application/content_pack.py` içindeki `populate_opening_content()`, içerik paketinin kimliklerini ve gameplay kurallarındaki oyuncu envanter/hesap kimliklerini çözümler. Ardından:

```python
service.configure_player_context(
    resolved_ids.hero_id,
    player_rules["inventory_id"],
    player_rules["account_id"],
)
```

çağrısıyla servis bağlamını yapılandırır.

Dolayısıyla içerik paketindeki `hero_id`, oyuncu aktör kimliği olarak; gameplay kurallarındaki `inventory_id` ve `account_id` ise ayrı kimlikler olarak kullanılmaktadır. Bu ayrım korunmalıdır.

### 3.3. Oturum ve kayıt ilişkileri

- `application/session_bundle.py`, aktör-karakter bağlantılarını doğrular.
- Aktörün `inventory_id` referansının envanter kayıtlarında bulunmasını doğrular.
- `application/actor_persistence.py`, aktör kaydında `actor_id`, `character_id` ve `inventory_id` alanlarını ayrı ayrı saklar.
- `application/migrations.py`, birleşik kayıt şemasının mevcut sürümlerini sürüm 3'e taşır.
- `tests/test_application/test_unified_save_document.py`, kayıt belgesi, round-trip, yedekleme/kurtarma, atomik yazma ve eski sürüm migrasyonları için mevcut test kapsamını içerir.
- `tests/test_application/test_game_application_save.py`, oyun uygulaması kayıt/yükleme davranışını kapsar.

Mevcut kayıt modelinde kimlik bağlantıları zaten açıkça tutulmaktadır. A1/A5 bu bağlantıları değiştirmemelidir.

## 4. Sorun envanteri

Kaynak taramasında aşağıdaki sabit kimlik ve sıra bağımlılıkları tespit edilmiştir. Satır numaraları kaynakta değişebileceğinden uygulama sırasında ilgili sembol ve çağrı tekrar bulunmalıdır.

| Dosya | Mevcut durum | Hedef |
|---|---|---|
| `game_ui/screens/character_creation.py` | Karakter erişimi ve özelleştirme `"hero"` kullanıyor. | Oyuncu karakterine servis üzerinden erişmek. |
| `game_ui/screens/character_screen.py` | Aktör/karakter/istatistik/beceri işlemleri `"hero"` kullanıyor; ayrıca `snapshot.actors[0]` erişimi var. | Yapılandırılmış oyuncu aktörünü kullanmak; sıra bağımlılığını kaldırmak. |
| `game_ui/screens/container_screen.py` | `actors[0]` üzerinden aktör seçimi var. | Konteyner etkileşiminde gerçek oyuncu aktörünü açıkça kullanmak. |
| `game_ui/screens/dialogue_screen.py` | `"player"` envanteri, `"hero"` karakteri ve aktör listesi fallback'i kullanılıyor; ayrıca doğrudan `holder.current` erişimleri var. | Oyuncu kimliklerini servisten almak; sıra fallback'ini kaldırmak. Doğrudan bundle erişimi A3'e bırakılacak. |
| `game_ui/screens/inventory_screen.py` | Kurucu varsayılanı `inventory_id="player"`; karakter işlemlerinde `"hero"` kullanılıyor. | Varsayılan envanteri servis kimliğinden almak; karakter işlemlerinde oyuncu aktör kimliğini kullanmak. |
| `game_ui/screens/market_screen.py` | `buy_offer()` çağrısı `"hero"` ve `"player"` sabitlerini gönderiyor. | Oyuncu aktör, hesap ve envanter kimliklerini doğru parametrelere geçirmek. |
| `game_ui/screens/production_screen.py` | Kurucu varsayılanı `inventory_id="player"`. | Varsayılanı servis kimliğinden almak. |
| `game_ui/screens/currency_exchange_screen.py` | Bakiye ve döviz işlemlerinde `"hero"` kullanılıyor. | Oyuncu hesap kimliğini kullanmak. |
| `game_ui/renderer.py` | Cüzdan/HUD için `"hero"`, kaynak çubuğu için `"player"`; görev hedefi bulmada `actors[0]` varsayımı var. | Servis kimlikleriyle çizim yapmak; hedef dünya/aktör bağını sıra bağımsız çözmek. |

Not: `dialogue_screen.py`, `production_screen.py`, `quest_log_screen.py`, `combat_screen.py`, `trade_screen.py` ve `renderer.py` içinde doğrudan `application.holder.current` veya bundle alanı erişimleri de görülmüştür. Bunlar A3 servis sınırı çalışmasına aittir. A1 sırasında yalnızca oyuncu kimliği ve aktör seçimiyle doğrudan ilgili en küçük değişiklikler yapılacaktır. Bu aşama, UI/bundle erişimlerinin tümünü temizlediği iddiasında bulunmayacaktır.

## 5. Hedef sözleşme ve tasarım kuralları

### 5.1. Kimliklerin anlamı

| Kimlik | Anlamı | Kullanılacağı yer |
|---|---|---|
| `player_actor_id` | Oyuncunun dünyadaki aktörü | Hareket, aktör durumu, oyuncu aktörüne bağlı karakter işlemleri |
| `character_id` | Karakter kayıt anahtarı | Karakter verisi, görünüm, özellikler ve beceriler |
| `player_inventory_id` | Oyuncunun envanter kaydı | Envanter, tüketim, üretim girdileri ve kaynak stokları |
| `player_account_id` | Oyuncunun ekonomi hesabı | Bakiye, cüzdan, alışveriş ve döviz işlemleri |

Bu kimlikler aynı metin değerine sahip olabilir; fakat mimari olarak eş anlamlı değildir. Kod bunların aynı olacağını varsaymamalıdır.

### 5.2. Servis API'si

- Mevcut `player_actor_id`, `player_inventory_id` ve `player_account_id` özellikleri korunur.
- `configure_player_context()` mevcut tek yapılandırma noktası olmaya devam eder.
- Karakter erişimi için mevcut servis API'si yeterli değilse, küçük ve açık bir servis metodu eklenir. Metot, oyuncu aktörünün bağlı olduğu karakter kaydını çözmelidir.
- Yeni bir genel amaçlı kimlik katmanı veya ikinci bir oyuncu kimliği kaynağı oluşturulmaz.
- UI, `GameplayService` tarafından sunulan kimlikleri kullanır; içerik paketinden veya varsayılan sabitlerden kimlik türetmez.
- Servis yapılandırılmamışsa sessizce `"hero"` / `"player"` fallback'i yapılmaz. Mevcut hata sözleşmesi incelenerek açık ve tanılanabilir hata davranışı korunur.

### 5.3. Aktör seçimi

- Oyuncu aktörü, `service.player_actor_id` ile seçilir.
- `snapshot.actors[0]`, `actors()[0]` veya sıralama sonucundaki ilk kayıt oyuncu kabul edilmez.
- Bir ekran oyuncu aktörünü bulamıyorsa başka bir aktörü oyuncu gibi kullanmaz; uygun boş durum veya mevcut servis hata davranışını gösterir.
- Dünya kimliği gerekiyorsa oyuncu aktörünün kendi `world_id` değeri kullanılır.
- NPC kimliği, NPC-aktör eşlemesi ve karakter kimliği mevcut domain bağlantıları üzerinden korunur.

## 6. Dosya bazlı uygulama planı

### A1.1 — Servis sözleşmesini doğrulama

**Dosyalar**
- `application/gameplay_service.py`
- `application/content_pack.py`
- İlgili uygulama/servis testleri

**İş**
1. `configure_player_context()` doğrulamalarını ve varsayılan davranışını incele.
2. `player_actor_id`, `player_inventory_id`, `player_account_id` özelliklerinin her çağrı yolunda yapılandırılmış bağlamı temsil ettiğini doğrula.
3. Oyuncu aktörünün bağlı olduğu `character_id` bilgisinin servis üzerinden güvenli biçimde çözümlenip çözümlenemediğini kontrol et.
4. Gerekliyse yalnızca karakter erişimi için dar kapsamlı bir servis metodu ekle.
5. `content_pack.py` içindeki yapılandırma çağrısını değiştirmeden koru; yalnızca testler bir eksiklik gösterirse düzelt.

**Kabul ölçütleri**
- Üç oyuncu kimliği birbirinden bağımsız okunabilir.
- Geçersiz veya eksik kimlikler sessiz fallback ile gizlenmez.
- Mevcut içerik paketleri aynı oyuncu bağlamını kurmaya devam eder.

### A1.2 — Karakter oluşturma ve karakter ekranları

**Dosyalar**
- `game_ui/screens/character_creation.py`
- `game_ui/screens/character_screen.py`
- `game_ui/screens/dialogue_screen.py` — yalnızca oyuncu karakterini bulma/adlandırma erişimleri; diğer diyalog kimliği ve envanter işleri A1.4 kapsamındadır.

**İş**
1. Karakter oluşturma ekranındaki karakter çözümlemesini servis sözleşmesiyle koru; özelleştirme çağrısında gerçek `player_character_id` kullanıldığını doğrula.
2. Karakter ekranındaki karakter, istatistik ve beceri işlemlerini `player_actor_id` üzerinden yürüt.
3. `snapshot.actors[0]` erişimini kaldır; oyuncu aktörünü açık kimliğiyle seç.
4. Diyalog ekranındaki oyuncu karakteri adlandırma ve oluşturma sonrası devam erişimlerini `service.actor_character(service.player_actor_id)` üzerinden çöz.
5. Karakter kaydının anahtarını aktör kimliğiyle aynı kabul etme; gerçek `character_id` bağlantısını kullan.

**Kabul ölçütleri**
- Oyuncu kimliği `hero` olmadığında karakter oluşturma ve görüntüleme çalışır.
- Oyuncu karakteri başka bir aktörden yanlışlıkla seçilmez; NPC koleksiyon sırası sonucu değiştirmez.
- Karakter kimliği ile aktör kimliği farklı olduğunda bağlantı korunur.
- Diyalog ekranı alternatif oyuncu aktörü/karakter kimliğiyle doğru karakter adını kullanır.

**Uygulama sonucu — 2026-11-25**
- `character_creation.py` üzerinde kaynak değişikliği gerekmedi: ekran zaten `player_actor_id` ile karakteri çözüyor ve özelleştirmede `player_character_id` kullanıyordu. Bu davranış farklı aktör/karakter kimlikleriyle test altına alındı.
- `character_screen.py` artık karakteri, istatistikleri ve beceri geliştirmeyi `player_actor_id` ile çözüyor. Render akışı oyuncu aktörünü snapshot içinden kimliğiyle buluyor; ilk aktör varsayımı kaldırıldı.
- `dialogue_screen.py` oyuncu karakterini iki noktada servis üzerinden çözüyor. Diyalogdaki `"player"` envanter referansları ve `"hero"` aktör fallback'i A1.4 için bırakıldı.
- `tests/test_game_ui/test_character_identity.py` içine 6 hedefli test eklendi. Mevcut karakter ekranı test fixture'ları da açık `player_actor_id` sağlayacak şekilde güncellendi.
- Core Quality Ruff listesine iki ekran ve yeni test dosyası eklendi.
- Otomatik CI kanıtı: Python 3.11/3.12 × Ubuntu/Windows dört test işi başarılı; her ortamda 1.623 unittest, 2.666 pytest ve 351 subtest başarılı, 59 warning. Pygame headless smoke test ve Core Quality Linux/Windows kontrolleri de başarılı.
- Kullanıcı 2026-11-26 tarihinde oyun penceresinde karakter oluşturma, karakter sayfası ve Eren ile diyalog akışını doğruladı; A1.2 manuel kabul edildi.

### A1.3 — Envanter, üretim ve ekonomi ekranları

**Dosyalar**
- `game_ui/screens/inventory_screen.py`
- `game_ui/screens/production_screen.py`
- `game_ui/screens/market_screen.py`
- `game_ui/screens/currency_exchange_screen.py`
- `game_ui/renderer.py`

**İş**
1. Envanter ve üretim ekranlarının varsayılan envanter kimliğini `service.player_inventory_id` üzerinden çöz.
2. Ekran kurucularına dışarıdan açık bir envanter kimliği verilmesini desteklemeye devam et; açıkça verilen değer servis varsayılanını geçersiz kılabilir.
3. Pazar satın alma çağrısının parametre sırasını ve anlamını doğrula; aktör, hesap ve envanter kimliklerini doğru yerlere ver.
4. Döviz işlemlerinde oyuncu hesabı kimliğini kullan.
5. HUD ve cüzdan gösteriminde hesap kimliğini; kaynak/stock gösteriminde envanter kimliğini kullan.
6. UI metotlarının mevcut kullanıcı davranışlarını, kısayollarını ve pencere akışını değiştirme.

**Kabul ölçütleri**
- Alternatif envanter ve hesap kimlikleri doğru kayıtlara erişir.
- Alışverişte para doğru hesaptan düşer, ürün doğru envantere eklenir.
- Üretim girdileri doğru oyuncu envanterinden tüketilir.
- Mevcut demo paketindeki davranış değişmez.

**Uygulama sonucu — 2026-11-26**
- Ekranların servis kimliklerini kullandığı kaynak incelemesiyle doğrulandı; alternatif aktör/envanter/hesap kimlikleriyle altı regresyon testi eklendi.
- İlk CI turunda testin pygame.Rect taklidi tuple döndürdüğü için tek test hatası oluştu. Yalnızca test düzeneği düzeltildi; üretim koduna dokunulmadı.
- Son doğrulama commit'i 326d8524; Eldoria CI ve Core Quality başarılı: [Eldoria CI](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/45879427448), [Core Quality](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/45879427512).
- A1.3 kimlik sözleşmesi ve otomatik doğrulaması tamamlandı. Item çizimlerinin envanter/sandık/üretim pencerelerinde farklı görünmesi ayrı görsel tutarlılık işi olarak izlenecek; A1.3 kapsamına alınmadı.

### A1.4 — Diyalog ve dünya aktör seçimi

**Dosyalar**
- `game_ui/screens/dialogue_screen.py`
- `game_ui/screens/container_screen.py`
- `game_ui/renderer.py`

**İş**
1. Diyalog görev/ödül/teslim kontrollerindeki oyuncu envanteri referanslarını servis kimliğine geçir.
2. Diyalogda oyuncu aktörü bulunamadığında ilk aktöre geçiş yapan fallback'i kaldır.
3. Konteyner ekranındaki ilk aktör varsayımını kaldır.
4. Renderer görev hedefi çözümlemesinde ilk aktör yerine gerçek oyuncu aktörünü kullan.
5. Bu dosyalardaki doğrudan bundle erişimlerini A3 kapsamında ayrıca işaretle; A1 için gereksiz servis API'si genişletme.

**Kabul ölçütleri**
- NPC kayıt sırası değiştiğinde diyalog oyuncu kimliği değişmez.
- Oyuncu aktörü bulunmadığında NPC oyuncu gibi işlenmez.
- Görev hedefi oyuncunun bağlı olduğu doğru dünyada aranır.

### A1.5 — Kalan sabit kimlik taraması

**Uygulama sonucu — 2026-11-26**
- `experiment/map-cleanup` HEAD `a100aee57fc337b95f93128a130f2985a0056076` üzerinden `game_ui/` altındaki 58 Python dosyasının tamamı tarandı.
- Oyuncu aktörü/karakteri/envanteri/hesabı için kullanılan sabit `"hero"` veya `"player"` kimlik eşleşmesi bulunmadı; bu nedenle üretim kodunda değişiklik yapılmadı.
- Bulunan sözcükler bağlamına göre ayrıştırıldı: `game_ui/screens/character_creation.py` içindeki `hero` yerel değişkeni ve `hero.png` görsel varlığıdır; `character_sprite_factory.py` içindeki `"player"` varsayılanı karakter çizim paletidir; `hex_gameplay_view.py` içindeki `player` değişkenleri `service.player_actor_id` ile çözümlenen oyuncu entity'sini, `entity.kind == "player"` ise entity türünü belirtir. Diğer eşleşmeler oyuncuyu anlatan yorum/docstring veya görsel sunum terimleridir.
- Bu eşleşmeler kimlik sabiti olmadığından değiştirilmedi. A1.5 kaynak taraması tamamlandı; kod değişikliği gerektirmedi.

**İş**
- `game_ui/` altında oyuncu aktörü, karakter, envanter veya hesap için kullanılan sabit `"hero"` / `"player"` değerlerini tekrar tara.
- Her eşleşmeyi bağlamına göre sınıflandır: oyuncu kimliği mi, içerik/NPC/quest kimliği mi, test fixture mı?
- Yalnızca oyuncu bağlamını temsil ettiği doğrulanan eşleşmeleri değiştir.
- İçerik kimliklerini, NPC kimliklerini, görev hedeflerini ve fixture'ları topluca değiştirme.

**Kabul ölçütleri**
- UI katmanında oyuncu kimliği olarak kullanılan sabitler kalmaz.
- İçerik ve domain kimlikleri yanlışlıkla değiştirilmez.
- Tarama sonucu ve istisnalar bu belgenin uygulama notlarına eklenir.

## 7. A5 — Kayıt/yükleme ve geriye dönük uyumluluk planı

### 7.1. Migrasyon kararı

Bu aşamada yeni bir kimlik migrasyonu eklenmeyecektir.

Gerekçe:
- Kayıt dosyalarında kimlikler referans olarak saklanır.
- Aktör, karakter ve envanter bağlantıları ayrı alanlarda tutulur.
- A1'in hedefi kayıt kimliklerini yeniden adlandırmak değil, UI'nin yapılandırılmış kimlikleri kullanmasını sağlamaktır.
- Kimlikleri topluca yeniden adlandırmak; quest, ekonomi, envanter, NPC, actor ve karakter referanslarında zincirleme değişiklik riski doğurur.

İleride gerçekten saklanan kimliklerin değiştirilmesi gerekirse, bu ayrı bir sürümlü migrasyon kararı olmalıdır. Böyle bir migrasyon; eski/yeni kimlik eşleme tablosu, çakışma davranışı, referans bütünlüğü, yedekleme ve geri yükleme testleri olmadan uygulanamaz.

### 7.2. Eklenecek test senaryoları

Yeni testler mevcut test düzenine uygun olarak uygulama/servis ve kayıt testleri altında yerleştirilir. Gerekirse yeni bir test modülü açılır; gerçek dosya adları uygulama sırasında test ağacı incelenerek seçilir.

**Kimlik sözleşmesi**
1. Oyuncu aktör kimliği `hero` dışında bir değer olabilir.
2. Oyuncu envanter kimliği `player` dışında bir değer olabilir.
3. Oyuncu hesap kimliği envanter ve aktör kimliklerinden farklı olabilir.
4. Karakter kimliği aktör kimliğinden farklı olabilir.
5. UI/servis işlemleri doğru ilişkiyi kullanır; kimlikleri birbirine eşitlemez.

**Kayıt/yükleme**
1. Alternatif kimlikli oturumun birleşik kayıt belgesi oluşturulur.
2. Kayıt diske yazılır ve aynı uygulama sözleşmesiyle yeniden yüklenir.
3. Aktör-karakter bağlantısı korunur.
4. Aktör-envanter bağlantısı korunur.
5. Ekonomi hesabı ve envanter kimlikleri doğru kayıtlara bağlanır.
6. Yüklenen oturumda karakter, envanter ve ekonomi servisleri aynı oyuncu bağlamını çözer.

**Geriye dönük uyumluluk**
1. Mevcut schema v0/v1/v2 fixture'ları v3'e migrasyon testlerinden geçmeye devam eder.
2. Mevcut v3 kayıtları round-trip testinden geçer.
3. Migrasyon kaynak belgeyi yerinde değiştirmez.
4. Bozuk veya eksik referanslar sessizce başka bir oyuncu kaydına yönlendirilmez.
5. Mevcut yedekleme/kurtarma ve atomik yazma testleri bozulmaz.

### 7.3. Test dosyaları

Mevcut temel testler:
- `tests/test_application/test_unified_save_document.py`
- `tests/test_application/test_game_application_save.py`

Yeni kimlik sözleşmesi testleri, mevcut test ağacına göre uygun `tests/test_application/` modülüne eklenir. UI testleri mevcut ekran testlerinin bulunduğu modüllere eklenir; test dosyası isimleri uygulama öncesinde repo ağacından doğrulanır.

## 8. Uygulama ve doğrulama sırası

Her alt aşama küçük ve geri alınabilir bir değişiklik olarak yürütülür:

1. İlgili kaynak ve test dosyalarını tekrar exact-branch ref üzerinden incele.
2. Etki alanını ve mevcut davranışı belirle.
3. En küçük kod değişikliğini yap.
4. Önce ilgili hedefli testleri çalıştır.
5. İlgili uygulama/UI/kayıt test paketlerini çalıştır.
6. Ruff ve mimari sınır kontrollerini çalıştır.
7. GitHub Actions sonuçlarını kontrol et.
8. UI davranışı etkileniyorsa kullanıcı manuel kabul testi yapar.
9. Başarılı aşama ayrı ve açıklayıcı commit ile kaydedilir.
10. Belgedeki durum ve test kanıtı güncellenir.

### CI sınırları

Mevcut CI matrisi Python 3.11 ve 3.12 kullanır. Yerel ortamda Python 3.14.7 bulunduğundan, CI başarısı Python 3.14 uyumluluğunun kanıtı sayılmaz. Ayrıca CI Ruff kontrolü seçilmiş dosyalarla sınırlıdır; tüm repo üzerinde alınan Ruff bulguları ayrı değerlendirilmelidir. Bu aşamanın kabulünde test edilmemiş Python sürümü veya tarama kapsamı için başarı iddiası kurulmaz.

## 9. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| Aktör, karakter, envanter ve hesap kimliklerinin karıştırılması | Yanlış karakter, stok veya bakiye üzerinde işlem | Her parametrenin anlamını koru; birbirinden farklı test kimlikleri kullan. |
| İlk aktörün oyuncu sanılması | NPC'nin oyuncu gibi gösterilmesi veya işlenmesi | Aktör seçimini açık oyuncu kimliğiyle yap; fallback'i kaldır. |
| UI'nin sessizce eski sabitlere dönmesi | Alternatif içerik paketlerinin bozulması | UI sabit kimlik taraması ve mimari regresyon testi ekle. |
| Eski kayıtların bozulması | Kayıt yüklenememesi veya referans kaybı | Kimlikleri yeniden adlandırma; mevcut migrasyon fixture'larını koru. |
| Gereğinden geniş servis API'si | Mimari karmaşa ve yeni bağımlılıklar | Yalnızca gerçek UI ihtiyacı kanıtlanan metotları ekle. |
| A1 ile A3'ün karıştırılması | Büyük ve zor incelenebilir refaktör | Bundle erişimlerinin genel temizliğini A3'e bırak. |
| UI davranışının değişmesi | Pencere, envanter, diyalog veya pazar regresyonu | Kullanıcı tarafından doğrulanmış davranışları koru; ilgili manuel testleri tekrarla. |

## 10. Tamamlanma ölçütleri

A1 + A5 ancak aşağıdaki koşulların tamamı sağlandığında tamamlanmış sayılır:

- [ ] Oyuncu kimlikleri için tek kaynak `GameplayService` sözleşmesidir.
- [ ] UI'deki oyuncu bağlamlı `"hero"` / `"player"` sabitleri kaldırılmış veya gerekçeli istisna olarak belgelenmiştir.
- [ ] Oyuncu aktörü seçimi koleksiyon sırasına bağlı değildir.
- [ ] Aktör, karakter, envanter ve hesap kimlikleri birbirinden bağımsız çalışır.
- [ ] Alternatif kimliklerle hedefli servis/UI testleri geçer.
- [ ] Alternatif kimlikli kayıt/yükleme round-trip testi geçer.
- [ ] Eski kayıt migrasyon testleri geçer.
- [ ] İlgili tam test paketi ve gerekli mimari kontroller geçer.
- [ ] GitHub Actions sonuçları doğrulanır.
- [ ] Etkilenen UI akışları manuel kabul testinden geçer.
- [ ] Kod değişiklikleri ve test kanıtları ayrı, açıklayıcı commit'lerle kaydedilir.

**Bu belgeyi eklemek A1 veya A5'in tamamlandığı anlamına gelmez.** Kod ve test işleri tamamlanana kadar durumları planlandı/uygulamada olarak kalır.

## 11. Uygulama günlüğü

| Tarih | Aşama | Durum | Kanıt / not |
|---|---|---|---|
| 2026-11-25 | A0 | Tamamlandı | Kaynak envanteri, mimari bulgular ve CI tabanı önceki incelemede kaydedildi. |
| 2026-11-25 | A1 + A5 tasarımı | Tamamlandı | Bu belge uygulama planı olarak oluşturuldu. |
| 2026-11-25 | A1.1 | Tamamlandı | `e48ac660`; GameplayService oyuncu kimliği sözleşmesi ve A1.1 CI doğrulaması tamamlandı. |
| 2026-11-25 | A1.2 | Tamamlandı | `9dbb3e97`–`92b7786e`; 6 yeni UI kimlik testi ve CI başarılı; kullanıcı oyun penceresinde karakter oluşturma, karakter sayfası ve Eren diyaloğunu kabul etti. |
| 2026-11-26 | A1.3 | Tamamlandı | `d71820aa` ve test düzeneği düzeltmesi `326d8524`; alternatif kimlik testleri eklendi, Eldoria CI ve Core Quality başarılı. Item çizim tutarsızlığı ayrı görsel iş olarak takip edilecek. |
| 2026-11-26 | A1.4 | Kod ve CI doğrulaması tamamlandı; sandık manuel testi başarılı; görev/diyalog manuel kabulü beklemede | Son düzeltme HEAD `a100aee57fc337b95f93128a130f2985a0056076`; Eldoria CI run `45880916965` ve Core Quality run `45880917005` başarılı. Kullanıcı sandığı açma ve eşya aktarma testini başarılı doğruladı. Görev alma/eşya teslim akışı, görev veren NPC bulunmadığından henüz test edilemedi; bu akış başarılı kabul edilmeyecek. |
| 2026-11-26 | A1.5 | Kaynak taraması tamamlandı | `game_ui/` altındaki 58 Python dosyası `a100aee5` üzerinde tarandı. Oyuncu kimliği olarak kullanılan sabit `hero/player` bulunmadı; bulunan sözcükler görsel palet, sprite değişkeni, entity türü veya açıklama metni. Üretim kodu değişikliği gerekmedi. |
| 2026-11-26 | A1.4 manuel kabul | Kısmi kabul | Sandık açma ve eşya aktarımı kullanıcı tarafından başarılı doğrulandı. Görev alma/teslim akışı görev veren NPC olmadığı için test edilemedi; bu kabul maddesi açık kalacak. Bu eksik oyun içeriği A1/A5 kapsamına eklenmeyecek. |
| 2026-11-26 | A5 | Otomatik doğrulama tamamlandı | `tests/test_application/test_game_application_save.py` içinde `actor_custom`, `character_custom`, `inventory_custom`, `account_custom` kimlikleriyle kayıt/yükleme round-trip testi; bozuk aktör-envanter ve aktör-karakter referanslarını reddetme testleri eklendi. `tests/test_application/test_unified_save_document.py` içindeki v0 migrasyon kaynak-belge değişmezliği testi mevcut kapsamı sağlıyor. Son commit `70d9705cb47d0381345751e8f31ced97c08f0e9a`; Eldoria CI run `45886106774` ve Core Quality run `45886106806` tüm işlerde başarılı. Üretim kodu ve migrasyon şeması değiştirilmedi. |

---

## 12. Sonraki işlem

A5'in otomatik kabul ölçütleri tamamlandı. Alternatif kimlikli kayıt/yükleme round-trip testi dört kimliğin birbirinden bağımsız korunduğunu doğruluyor. Bozuk aktör-envanter ve aktör-karakter bağlantıları yükleme sırasında reddediliyor; hatalı yüklemede etkin oturum korunuyor. Mevcut v0/v1/v2→v3 migrasyon testleri korunuyor ve v0 migrasyonunun kaynak belgeyi değiştirmediği mevcut testle doğrulanıyor. Yeni migrasyon eklenmedi.

Son A5 doğrulama commit'i `70d9705cb47d0381345751e8f31ced97c08f0e9a`: Eldoria CI run `45886106774` ve Core Quality run `45886106806` başarılı. Eldoria CI'nin Python 3.11/3.12 × Ubuntu/Windows işleri ve Pygame headless smoke testi; Core Quality Linux/Windows işleri tamamı başarılı.

A1.4'ün görev alma/eşya teslim manuel kabulü görev veren NPC bulunmadığı için açık kalacaktır. Bu nedenle A1+A5 çalışma başlığı bütünüyle kapatılmayacak; A5 tamamlandı, A1.4 manuel kabulü kısmi olarak kaydedilecektir. Görev veren NPC oluşturmak bu kapsamın dışında kalır.
