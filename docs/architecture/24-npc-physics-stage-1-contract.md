# Aşama 1 — NPC Fizik Gövdeleri Teknik Sözleşmesi

**Durum:** Uygulama öncesi onaylı teknik plan  
**Hedef dal:** `experiment/map-cleanup`  
**Kapsam:** NPC başına fizik tanımı ve merkezi fizik altyapısına güvenli bağlanma  
**Bağlantılı aşamalar:** Aşama 2 (dinamik aktör çarpışması), Aşama 3 (itilme), Aşama 5 (NPC sürekli hareketi), Aşama 7 (kalıcılık ve yaşam döngüsü)

---

## 1. Amaç

Her NPC'nin kendisine ait, içerikten üretilebilen bir fizik gövdesi tanımı bulunacaktır. Binlerce NPC hedefinde bu gereksinim, NPC başına fizik motoru veya simülasyon döngüsü oluşturmadan karşılanacaktır.

Bu aşamanın çıktısı; mevcut Eldoria kimlik, konum ve NPC sahipliği sınırlarını koruyan, fizik tanımını NPC'ye bağlayan ve ileride merkezi dinamik fizik çözümlemesine temel oluşturacak test edilmiş bir altyapıdır.

Aşama 1 tek başına oyuncu-NPC çarpışması, NPC itilmesi, NPC navigasyonu veya fizik tabanlı çevre etkileşimini tamamlamaz. Bunlar sonraki aşamaların kapsamıdır.

## 2. Mimari kararlar ve değişmezler

1. **NPC kimliği:** NPC kimliği mevcut `NPCRegistry` ve `WorldActorRegistry` düzeninde kalır. Yeni bir kimlik sistemi kurulmaz.
2. **Konum sahipliği:** Harita ve sürekli dünya konumunun tek otoritesi `HexWorldRuntime` olmaya devam eder. Fizik katmanı ikinci bir konum kaynağı oluşturmaz.
3. **Fizik tanımı:** Her NPC'nin kendine ait fizik tanımı olur. Tanım başka bir NPC'nin kimliğine veya mutable runtime durumuna bağlı olmaz.
4. **Merkezi simülasyon:** NPC başına fizik motoru, fizik dünyası, indeks veya update döngüsü oluşturulmaz. İleride tek merkezi koordinatör ortak altyapıyı yönetir.
5. **Veri ve durum ayrımı:** Değişmez içerik tanımı ile değişken runtime fizik durumu birbirinden ayrılır.
6. **Mekânsal indeks:** Dinamik aktör broadphase'i statik engel indeksiyle karıştırılmaz. Mevcut `UniformGridIndex` öncelikli adaydır; ayrı indeks kararı ölçüm ve entegrasyon incelemesi olmadan verilmez.
7. **Collider farkındalığı:** Fizik broadphase kayıtları aktör merkez noktası değil, gerçek collider'ın dünya AABB sınırları olmalıdır.
8. **Kare/altıgen uyumu:** Sürekli dünya fiziği mevcut dünya koordinatlarında çalışır; hex hücre ve occupancy kuralları `HexWorldRuntime` sorumluluğunda kalır. Kare koordinatına veya farklı koordinat sistemine sessiz geçiş yapılmaz.
9. **Kayıt uyumluluğu:** `rpg-actors` v1 ve `rpg-hex-world` v2 şemaları bu aşamada değiştirilmez.
10. **Denge değerleri:** Kütle, direnç, hız, collider boyutu ve benzeri oyun dengesi değerleri kullanıcı onayı olmadan sabitlenmez.
11. **Ölçüm disiplini:** Benchmark yapılmadan performans artışı veya binlerce NPC ölçeklenebilirliği iddia edilmez.

## 3. Mevcut altyapı ve entegrasyon noktaları

İncelenen kaynaklar:

- `core/domain/physics/body.py`: `PhysicsBodyDefinition` mevcut; `frozen=True` ve `slots=True`, collider, kimlik, yerel ofset, yükseklik ve enabled alanlarını içeriyor.
- `core/domain/physics/shapes.py`: Daire ve dışbükey çokgen collider tipleri mevcut.
- `core/domain/spatial/uniform_grid_index.py`: Seyrek, harita kapsamlı grid; AABB insert/update/remove/query işlemleri ve kesişim filtresi var.
- `core/domain/spatial/aabb.py`: Değişmez AABB veri tipi mevcut.
- `application/actor_system.py`: Dünya aktör kimliği ve aktör yaşam döngüsü.
- `application/hex_world_runtime.py`: Sürekli konum, hex hücresi, occupancy ve mekânsal kayıt otoritesi.
- `application/npc_hex_binding.py`: NPC ile mevcut aktör/spatial runtime bağını kuran servis.
- `application/hex_physics_bridge.py`: Harita kaynaklı statik fizik geometrisi köprüsü.
- `application/actor_persistence.py`: `rpg-actors` v1.
- `application/hex_world_persistence.py`: `rpg-hex-world` v2.

Önemli mevcut durum: `HexWorldRuntime` mekânsal indeksine sürekli konumlar şu anda `AABB.at_point(...)` biçiminde kaydediliyor. Bu kayıtlar fizik broadphase'i için yeterli değildir. Aşama 1'de indeksin NPC collider AABB'siyle kaydedilmesi veya bunun için açık bir fizik-spatial kayıt yolu tasarlanması gereklidir. Konumun otoritesi yine runtime olarak kalır.

## 4. Veri sözleşmesi

### 4.1 NPC fizik tanımı (değişmez)

Her NPC için içerik/karakter tanımından oluşturulan bir fizik tanımı bulunmalıdır. Tanımın mantıksal alanları:

| Alan | Sorumluluk | Durum |
|---|---|---|
| Collider şekli ve ölçüsü | Fiziksel temas hacmi | Mevcut shape tipleriyle temsil edilmeli |
| Yerel collider ofseti | Görsel/zemin anchor'ına göre fizik merkezi | Mevcut `local_offset` değerlendirilmeli |
| Gövde yüksekliği | Mevcut dikey/ground-anchor hesaplarıyla uyum | Mevcut alan korunmalı |
| Etkinlik | Fiziksel katılıma izin | Mevcut `enabled` alanı değerlendirilmeli |
| Kütle/inertia benzeri parametre | Sonraki dinamik çözümleme | Semantik ve birim kararı açık |
| İtme/yer değiştirme direnci | Sonraki itilme aşaması | Denge değeri onaylanmadı |
| Çarpışma katmanı/maskesi | Hangi aktörlerle etkileşeceği | Bitmask/enum tasarımı açık |
| Hareket profili uyumluluğu | NPC hareket tanımıyla bağlantı | Mevcut `MovementProfile` ile sorumluluk çakışması olmamalı |

Bu tablo, tüm alanların Aşama 1'de zorunlu olarak kodlanacağı anlamına gelmez. İlk uygulamada yalnızca mevcut fizik motorunun gerçekten ihtiyaç duyduğu ve anlamı netleştirilmiş alanlar eklenir. Kütle, direnç ve layer/mask alanlarının isimleri, birimleri, varsayılanları ve doğrulaması teknik uygulama öncesi netleştirilir. Uydurma varsayılanlarla oyun dengesi belirlenmez.

Tanım `PhysicsBodyDefinition` üzerine genişletilerek çözülebiliyorsa yeni paralel bir tanım sınıfı yaratılmaz. Ancak alanların anlamı veya yaşam döngüsü mevcut sınıfla uyumsuzsa küçük, immutable bir fizik özellik nesnesi önerilebilir. Bu seçim gerçek çağrı noktaları ve testler üzerinden yapılır.

### 4.2 Runtime fizik durumu (değişken)

Fizik runtime durumu tanımdan ayrı tutulur. İleride gerekli olacak kavramsal alanlar:

- NPC/aktör referansı (yeni kimlik üretmeden);
- güncel hız/velocity;
- geçici itme etkisi veya momentum;
- fizik güncellemesine katılım/uyku durumu;
- son fizik güncelleme veya aktivasyon bilgisi (yalnızca ihtiyaç kanıtlanırsa).

**Konum runtime fizik durumunda ikinci kez saklanmaz.** Güncel konum `HexWorldRuntime` üzerinden okunur. Fizik gövdesi, mevcut konumdan türetilen fiziksel temsildir.

Aşama 1'de Aşama 2/3/5 davranışları henüz uygulanmayacağından, kullanılmayan runtime alanları peşinen eklenmemelidir. Gerekli en küçük state modeli seçilmelidir.

### 4.3 İçerik kaynağı

NPC collider ölçüleri içerik tanımından gelmelidir; sprite ölçüsünden otomatik collider türetilmemelidir. Görsel boyut ile fiziksel temas hacmi ayrı kavramlardır. Kullanılan birim sürekli dünya birimi olmalıdır. Hex boyutu 32 dünya birimi olarak mevcut proje kararıdır; NPC dairesel collider yarıçapı kullanıcı tarafından 4 dünya birimi olarak onaylanmıştır.

Eksik/bozuk fizik tanımının nasıl ele alınacağı açık ve deterministik olmalıdır: sessizce rastgele değer üretmek veya tüm NPC'lere onaysız tek collider atamak yasaktır. İçerik doğrulaması hata raporlamalıdır. Geriye dönük içerik uyumluluğu gerekiyorsa geçiş stratejisi ayrıca tanımlanmalıdır.

## 5. Sorumluluk sınırları

| Bileşen | Sahip olduğu sorumluluk | Sahip OLMADIĞI sorumluluk |
|---|---|---|
| `NPCRegistry` | NPC sosyal/karakter verisi | Fizik konumu veya simülasyon |
| `WorldActorRegistry` | Genel aktör kimliği ve yaşam döngüsü | Fizik konumu |
| `HexWorldRuntime` | Harita, sürekli konum, hex occupancy | NPC fizik özelliklerinin kaynağı |
| Fizik domain | Şekil, fizik tanımı, geometri ve çözümleme ilkeleri | NPC kimliği veya harita otoritesi |
| NPC fizik binding/application servisi | NPC fizik tanımını mevcut aktör/runtime'a bağlama ve kaldırma | Yeni kimlik/konum sistemi |
| Dinamik mekânsal indeks | Collider AABB broadphase adayları | Kimlik/konum otoritesi |
| AI/navigasyon | Bilinçli kenara çekilme ve hareket niyeti | Fizik çarpışma çözümü |

## 6. İndeks ve ölçeklenebilirlik sözleşmesi

1. Her kayıt, mevcut kararlı aktör/NPC ID'siyle ilişkilendirilir.
2. Kayıt AABB'si collider şekli ve güncel runtime konumundan türetilir.
3. Harita ID'si indeks anahtarının parçası olarak korunur; haritalar arası aday karışması olmaz.
4. Konum veya collider değiştiğinde indeks güncellemesi tutarlı ve atomik olmalıdır. Başarısız güncelleme eski geçerli kaydı bozmamalıdır.
5. Kaldırma, NPC/aktör unregister ve harita geçişi yaşam döngüsüyle eşgüdümlü olmalıdır; eski harita kaydı sızmamalıdır.
6. Statik engeller `StaticObstacleIndex` içinde kalır. Dinamik aktörler statik indeksin içine yazılmaz.
7. Uyku/aktiflik kararı verilirse uyuyan fakat fiziksel olarak çarpışmayı engelleyen NPC broadphase sorgularında temsil edilmeye devam etmelidir. Uyku yalnızca pahalı hareket/çözümleme güncellemelerini azaltabilir; varlığı fizik dünyasından silmek anlamına gelmez.
8. NPC başına grid, solver veya timer oluşturulmaz.
9. `UniformGridIndex` sorgusunun aday seti ve sıralama maliyetleri ölçülür. Gerçek benchmark olmadan indeks değiştirilmez.
10. Çok büyük collider'ların çok sayıda grid hücresine yazılması ve yoğun kümelerde bucket büyümesi ayrıca ölçülür.

### 6.1 Uyku/uzaklık politikası

Uyku, aktif yarıçap veya uzak NPC update sıklığı Aşama 1'in zorunlu davranış kararı değildir. Önce yalnızca tasarım seçeneği olarak tutulur. Uygulamaya alınırsa:
- fiziksel engel olma ve simülasyon güncellemesi birbirinden ayrılır;
- uyanma koşulları deterministik olur;
- oyuncu/etkileşim/çarpışma yakınlığı gibi tetikleyiciler açıkça tanımlanır;
- oyun zamanı, NPC rutinleri ve AI simülasyonu etkileri ayrıca değerlendirilir;
- kullanıcı onayı olmadan aktif yarıçap veya uyku zamanlaması sabitlenmez.

## 7. Yaşam döngüsü

Aşama 1 bağlama işlemi şu koşulları sağlamalıdır:

- NPC kaydı ve mevcut dünya aktörü doğrulanmadan fizik kaydı oluşturulmaz.
- Fizik tanımı doğrulanmadan kısmi kayıt bırakılmaz.
- Aynı NPC için mükerrer fizik kaydı reddedilir veya açıkça idempotent tasarlanır; sessiz çoğaltma yasaktır.
- NPC pasifleştiğinde, kaldırıldığında veya harita değiştirdiğinde fizik binding ve indeks kaydı tutarlı biçimde güncellenir.
- Bir adım başarısız olursa önceki geçerli kayıt korunur veya işlem tamamen geri alınır.
- Fizik binding, NPC/aktör kimliğini veya authoritative konumu kendi içinde kopyalayarak sahiplenmez.

Bu aşamada kayıt şemasına yeni alan eklenmez. Fizik tanımları içerikten yeniden kurulabilir olmalıdır. Runtime hız/itilme gibi geçici durumların kaydedilip kaydedilmeyeceği Aşama 7'de kararlaştırılır.

## 8. Aşama kapsamı dışı

- Oyuncu-NPC ve NPC-NPC dinamik çarpışma çözümü (Aşama 2).
- Oyuncunun NPC'yi fiziksel olarak itmesi ve itmenin sönümlenmesi (Aşama 3).
- İtilebilir/etkileşimli çevre nesneleri (Aşama 4).
- NPC sürekli hareket integratörü ve hareket döngüsü (Aşama 5).
- NPC'nin bilinçli olarak kenara çekilmesi/kaçınması (Aşama 6).
- Fizik runtime durumunun kalıcı kaydı, kapsamlı restore ve performans optimizasyonlarının son kabulü (Aşama 7).
- Görsel/sprite collider otomasyonu.
- Yeni fizik motoru, ikinci world runtime veya ikinci aktör kayıt sistemi.

## 9. Önerilen uygulama dosya kapsamı

Dosyalar uygulama öncesi güncel dalda yeniden doğrulanacaktır.

### Öncelikli inceleme/değişiklik adayları
- `core/domain/physics/body.py`: Var olan tanımı genişletme veya küçük immutable özellik bileşeni kararı.
- `application/npc_hex_binding.py`: NPC fizik tanımının mevcut spatial binding yaşam döngüsüne bağlanması.
- `application/hex_world_runtime.py`: Konum otoritesini koruyarak collider AABB kayıt/güncelleme yolunun sağlanması.
- `core/domain/spatial/uniform_grid_index.py`: Yalnızca gerçek ihtiyaç/test gösterirse değişiklik.
- `core/domain/physics/__init__.py`: Yeni public domain tipleri gerekiyorsa dışa aktarım.
- NPC içerik şeması/loader dosyaları: Gerçek içerik kaynağı belirlendikten sonra, yalnızca gerekli alanlar için.

### Test adayları
- Mevcut fizik primitive testleri.
- `tests/test_spatial/test_uniform_grid_index.py`.
- `tests/test_application/test_hex_world_runtime.py`.
- `tests/test_application/test_npc_hex_binding.py` (dosya adı ve mevcut test düzeni uygulama öncesi doğrulanacak).
- İçerik doğrulama ve kayıt geriye uyumluluk testleri.

### Korunacak alanlar
- `main` dalına hiçbir işlem yapılmaz.
- `content/demo_eldoria/` dosyaları açık izin olmadan değiştirilmez.
- `content/active_package.json` değiştirilmez.
- `experiment/hex-world-laboratory` yalnızca okunur referanstır; kod doğrudan kopyalanmaz.
- Kayıt şemaları değiştirilmez.
- Test amaçlı hız/collider değerleri demo içeriğine aktarılmaz.

## 10. Test sözleşmesi

Mevcut test altyapısı `unittest` olduğundan, proje gerektirmedikçe Pytest bağımlılığı eklenmez. Testler en az şu durumları kapsamalıdır:

### Domain ve içerik
1. Geçerli her collider türü için NPC fizik tanımı kurulabilmeli.
2. Geçersiz boyut, ofset, kütle/direnç veya layer değeri deterministik doğrulama hatası vermeli.
3. Tanım immutable davranmalı; mutable iç nesneler varsa bunların da gerçekten değişmez olup olmadığı test edilmeli.
4. Eksik fizik tanımı sessizce uydurulmamalı.
5. Farklı NPC'ler farklı fizik tanımları taşıyabilmeli; ortak profil paylaşımı zorunlu olmamalı.

### Binding ve yaşam döngüsü
6. Fizik tanımı doğru NPC/aktör ID'sine bağlanmalı.
7. İkinci kimlik veya ikinci authoritative konum üretilmemeli.
8. Kayıt, mükerrer kayıt, kaldırma, pasif NPC ve başarısız kısmi kayıt senaryoları test edilmeli.
9. Harita geçişinde eski harita indeks kaydı kalmamalı.
10. Aynı ID'nin başka NPC veya aktöre yanlış bağlanması engellenmeli.

### Broadphase
11. Collider AABB kayıtları merkez nokta AABB'sinden farklı ve geometriyle tutarlı olmalı.
12. Sorgu yalnızca aynı haritadaki AABB kesişim adaylarını döndürmeli.
13. AABB sınır temasları mevcut inclusive intersection semantiğiyle tutarlı olmalı.
14. Update/remove sonrası eski bucket üyeliği kalmamalı.
15. Başarısız update eski indeksi bozmamalı.
16. Statik engel indeksi ile dinamik aktör indeksi birbirine karışmamalı.

### Uyumluluk
17. Mevcut hex occupancy ve continuous position testleri bozulmamalı.
18. `rpg-actors` v1 ve `rpg-hex-world` v2 kayıt round-trip ve restore testleri aynı kalmalı.
19. Mevcut statik fizik çözümleyicisi testleri geçmeli.
20. Harita değişimi ve runtime temizliği testleri geçmeli.

## 11. Performans benchmark planı

Benchmark bir doğruluk testi değildir; ayrıca raporlanır. En az aşağıdaki popülasyonlar kullanılmalıdır: 100, 500, 1.000 ve 5.000 NPC. Hareketli oranlar için %0, %10, %50 ve %100 senaryoları önerilir. Bunlar benchmark yük profilleridir, oyun tasarımında aynı oranların bulunacağı anlamına gelmez.

Her senaryoda:
- fizik tanımı ve runtime durumunun toplam bellek maliyeti;
- tüm NPC collider AABB'lerini ilk kaydetme süresi;
- tek tick indeks güncelleme süresi;
- sorgu başına aday sayısı ve gerçek AABB kesişim sayısı;
- yoğun kümelerde en kötü/ortalama sorgu maliyeti;
- harita geçişi/kaldırma maliyeti;
- merkezi koordinatörün tick maliyeti (yalnızca ilgili koordinatör sonraki aşamada mevcutsa)

ölçülür.

Sonuçlar aynı makine, Python sürümü, seed, collider dağılımı ve tekrar sayısıyla karşılaştırılmalıdır. Ortalama yanında p50/p95/p99 veya açıkça seçilmiş dağılım istatistikleri raporlanmalıdır. Ölçüm altyapısı yoksa önce küçük, tekrarlanabilir benchmark eklenir; benchmark kodu demo içeriğine konmaz. Kabul hedefi ölçüm öncesinde uydurulmaz; mevcut baseline alındıktan sonra kullanıcıyla belirlenir.

## 12. Ruff, CI ve entegrasyon kontrolleri

- Projenin mevcut Ruff yapılandırması ve komutları kullanılır; yeni kural seti keyfî eklenmez.
- İlgili testler ve tam test paketi mevcut proje talimatlarına göre çalıştırılır.
- GitHub Actions sonuçları commit/branch bazında doğrulanır.
- Diff yalnızca onaylı dosya kapsamını içermelidir.
- Commit yalnızca `experiment/map-cleanup` dalına yapılır.
- `main` dalına merge, cherry-pick, commit, push, reset veya değişiklik yapılmaz.
- CI yeşil olması oyun içi davranışın görsel olarak doğrulandığı anlamına gelmez.

## 13. Aşama 1 kabul kriterleri

Aşama 1 ancak aşağıdakilerin tamamı sağlanınca tamamlanmış sayılır:

- [ ] Her NPC için içerikten üretilebilen bağımsız fizik tanımı mevcut.
- [ ] NPC başına ayrı fizik motoru/simülasyon döngüsü/indeks yok.
- [ ] Değişmez tanım ile runtime değişken durumunun sınırı açık ve testli.
- [ ] Kimlik ve konum sahipliği mevcut sistemlerde kalıyor.
- [ ] Broadphase collider AABB kullanıyor; merkez nokta kaydı fizik sınırı olarak kullanılmıyor.
- [ ] NPC register/unregister, pasiflik ve harita geçişi yaşam döngüsü tutarlı.
- [ ] Mevcut kayıt şemaları ve eski kayıt uyumluluğu korunuyor.
- [ ] İlgili ve tam testler çalıştırılmış, sonuçlar raporlanmış.
- [ ] Ruff kontrolü çalıştırılmış ve sonucu raporlanmış.
- [ ] GitHub Actions sonucu incelenmiş.
- [ ] Benchmark sonuçları ölçülmüş ve baseline raporlanmış; performans iddiası ölçüme dayanıyor.
- [ ] Kullanıcı gerçek oyun testi gereken noktaları uygulayıp doğrulamış.

## 14. Açık kararlar — uygulama öncesi teknik keşif

Aşağıdaki konular uygulama sırasında mevcut kod ve içerik şeması incelenerek öneriye dönüştürülecek; oyun tasarımı değeri gerektirenler kullanıcı onayı olmadan sabitlenmeyecek:

1. Kütle/direnç/layer alanlarının mevcut `PhysicsBodyDefinition` içine mi yoksa ayrı immutable özellik nesnesine mi konacağı.
2. Collider ölçülerinin NPC içerik şemasındaki kesin kaynağı ve birimi.
3. `UniformGridIndex` güncelleme maliyetinin yeterliliği; ayrı dinamik indeks gerekip gerekmediği.
4. Uyku/aktif yarıçap/uzak NPC güncelleme politikasının kapsamı.
5. Benchmark makinesi, tekrar sayısı ve performans kabul hedefleri.
6. Fizik tanımı eksik olan mevcut NPC içerikleri için geçiş/validasyon stratejisi.

## 15. Uygulama çalışma sırası

1. Dalın güncel HEAD'ini ve çalışma ağacını doğrula; yalnızca `experiment/map-cleanup`.
2. NPC içerik modeli, loader, tüm `PhysicsBodyDefinition` kullanım yerleri ve indeks çağrılarını tarayıp sözleşmedeki açık kararları somutlaştır.
3. Dosya bazında değişiklik planı ve riskleri çıkar.
4. En küçük uyumlu domain değişikliğini uygula.
5. NPC binding ve collider-AABB indeks kayıt yaşam döngüsünü uygula.
6. Birim, entegrasyon, hata/rollback ve kayıt uyumluluk testlerini ekle.
7. Mevcut test komutlarını çalıştır.
8. Ruff çalıştır.
9. Benchmark baseline ve yük sonuçlarını kaydet.
10. Diff'i korunan dosyalar ve dal kuralları açısından denetle.
11. Commit ve GitHub Actions sonuçlarını doğrula.
12. Kullanıcıya aşama raporunu sun; gerçek oyun testi gerekiyorsa açık adımlar ver.

**Aşama 1 uygulaması bu sözleşmeye bağlıdır.** Sözleşme, sonraki aşamaların davranışlarını erkenden uygulama izni vermez. Herhangi bir gereksinim mevcut mimariyle çelişirse kodlamadan önce gerekçe ve alternatif raporlanır.


## 16. Kullanıcı kararı — NPC collider ölçüsü

**Tarih:** 2026-11-19  
**Karar:** NPC'ler için başlangıç collider biçimi daire, yarıçapı **4 dünya birimi** olacaktır. Bu değer oyuncunun onaylı 8 dünya birimi yarıçapından ayrıdır. Her NPC kendi PhysicsBodyDefinition örneğini taşır; ortak fizik profili veya NPC başına simülasyon motoru oluşturulmaz.

Bu karar collider geometrisini ve başlangıç ölçüsünü onaylar. Kütle, itme direnci, collision layer/mask, hareket hızı, NPC aktif yarıçapı ve performans kabul hedefi için değer belirlemez. İleride içerik tanımıyla NPC bazında farklı ölçü verilmesi desteklenebilir; 4 birim başlangıç varsayılanıdır.


## 17. Aşama 1 uygulama ayrıntıları — içerik ve broadphase

- NPC içerik kaydı, isteğe bağlı `physics` nesnesiyle dairesel collider tanımlayabilir: `{"shape": "circle", "radius": 4.0}`. Radius sonlu ve pozitif olmalıdır. Bu aşamada içerik loader yalnızca daire collider biçimini kabul eder; domain fizik sistemi diğer mevcut şekilleri desteklemeye devam eder.
- Eski NPC içerikleriyle geriye dönük uyum için `physics` alanı bulunmayan kayıtlar NPC domain varsayılanını (yarıçap 4 dünya birimi) kullanır. Yeni içerik kayıtlarında fizik alanının açıkça yazılması tercih edilir.
- `HexWorldRuntime` aktör kimliği ve konum otoritesi olarak kalır. `local_spatial_bounds`, yalnızca anchor'a göre collider AABB'sini taşır; konum veya ikinci aktör kaydı oluşturmaz.
- Sürekli hareket, hücre hareketi ve harita transferi sırasında broadphase AABB'si aynı yerel collider sınırlarıyla yeni anchor'a taşınır. Varsayılanı olmayan aktörlerin mevcut nokta tabanlı indeksi korunur.
- NPC binding, NPC'nin kendi `PhysicsBodyDefinition` nesnesinden yerel AABB üretip mevcut actor binding/runtime hattına iletir. Statik engel indeksi değiştirilmez.
- Bu entegrasyon yalnızca broadphase aday kayıtlarının collider boyutunu dikkate almasını sağlar; henüz dinamik dar faz çarpışması, itiş veya NPC hareket çözümlemesi uygulamaz.


## 18. Tekrarlanabilir NPC mekânsal indeks benchmark'ı

Depoda `scripts/benchmark_npc_spatial_index.py` aracı bulunur. Depo kökünde şu komutla çalıştırılır:

```powershell
python scripts/benchmark_npc_spatial_index.py --output npc-spatial-benchmark.json
notepad npc-spatial-benchmark.json
```

Araç 100, 500, 1.000 ve 5.000 NPC sayılarında nokta tabanlı indeks ile collider AABB indeksini aynı makinede karşılaştırır. Her senaryoda kayıt süresi, kayıt sonrası bellek, %0/%10/%50/%100 kümülatif hareket güncelleme süresi ve yakın sorgu maliyeti raporlanır. Sonuçlar donanım ve çalışma ortamına bağlıdır; GitHub runner sonucu kullanıcının hedef donanımındaki performansın yerine geçmez. Ölçüm alınmadan ölçeklenebilirlik veya performans kabulü verilmez.
