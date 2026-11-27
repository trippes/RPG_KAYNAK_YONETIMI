# A0 — Tarihsel Başlangıç Temel Çizgisi ve Kanıtların Yeniden Kurulması

**İncelenen dal:** `experiment/map-cleanup`  
**Tarihsel temel çizgisi:** `f9e4914edb25fd0d8943934de8dd41d67cfab813`  
**Temel çizginin üst commit'i:** `a961de7b91b6b7fe7d6b3aae48d2defc95fcb966` — `docs: add legacy architecture cleanup roadmap`  
**Rapor durumu:** A0 tamamlandı (2026-11-27); tarihsel tarama ve CI kanıtları kaydedildi.  
**Kapsam:** Yalnızca GitHub üzerinden erişilebilen commit ağacı, belgeler, yapılandırmalar ve CI tanımları. Bu rapor yerel test çalıştırma çıktısı veya tamamlanmış statik kod taraması iddiasında bulunmaz.

## 1. Sonuç

A0'ın tarihsel başlangıç noktası, dosya envanteri, legacy gösterge taraması, altı kategoriye göre bulguları ve başlangıç CI/test sonuçları yeniden doğrulandı. Tarama kapsamı ve hariç tutulan dosyalar açıkça kaydedildi. Tarihsel CI kayıtları başlangıç commit'ine doğrudan bağlıdır.

Bu nedenle A0, yol haritasındaki kabul ölçütleri karşılanarak 2026-11-27 tarihinde tamamlandı. Bulguların giderilmesi A1–A5 ve sonraki aşamaların kapsamındadır; A0 bir keşif ve temel çizgi aşamasıdır, runtime kodunu değiştirmez.

## 2. Git temel çizgisi

- A0 öncesi kaynak ağacı: `f9e4914edb25fd0d8943934de8dd41d67cfab813`.
- `a961de7b91b6b7fe7d6b3aae48d2defc95fcb966` commit'i yalnızca A0 yol haritası belgesini ekleyen commit olarak tanımlanmıştır; dolayısıyla `f9e4914e` yol haritası eklenmeden önceki kaynak ağacıdır.
- A0 planında hedef dal `experiment/map-cleanup` olarak belirlenmiştir.
- Tarihsel konuşma kaydında dal değişimi sonrası HEAD ve origin'in `a961de7b` olduğu ve çalışma ağacının temiz olduğu bildirilmiştir. Bu, GitHub'da bugün görülen dosya ağacıyla aynı şey değildir; geçmişteki yerel çalışma ağacı durumu GitHub API'sinden geriye dönük olarak doğrulanamaz.
- Başlangıç commit'inin güncel `main` ile karşılaştırması, dalın önemli ölçüde ayrışmış olduğunu göstermektedir. Bu karşılaştırma A0'ın yerel çalışma ağacının temizliğini veya o tarihteki test durumunu kanıtlamaz.

## 3. Tarihsel dosya envanteri

GitHub recursive tree çıktısında `f9e4914e` commit'inde **931 dosya** bulundu. Aşağıdaki sayımlar, ilgili üst dizinin altındaki dosya sayılarıdır:

| Alan | Toplam dosya | Python | JSON |
|---|---:|---:|---:|
| `application/` | 59 | 59 | 0 |
| `character/` | 11 | 11 | 0 |
| `combat/` | 8 | 8 | 0 |
| `containers/` | 6 | 6 | 0 |
| `core/` | 101 | 101 | 0 |
| `economy/` | 11 | 11 | 0 |
| `game_ui/` | 65 | 58 | 0 |
| `npc/` | 7 | 7 | 0 |
| `quests/` | 8 | 8 | 0 |
| `resources/` | 11 | 11 | 0 |
| `tests/` | 302 | 301 | 0 |
| `content/` | 26 | 0 | 23 |
| `docs/` | 104 | 0 | 0 |
| `scripts/` | 14 | 14 | 0 |
| `.github/workflows/` | 7 | 0 | 0 |

Notlar:
- `tests/` altında 301 Python dosyası ve bir Python dışı dosya vardır.
- `content/` altında 23 JSON dosyasına ek olarak görsel ve diğer içerik dosyaları vardır.
- Bu tablo yalnızca belirtilen dizinleri gösterir; toplam 931 dosyanın kalan kısmı kök dosyaları ve tabloda ayrıca listelenmeyen dizinlerdedir.
- Bu sayımlar tarihsel commit ağacına aittir; güncel dalın dosya sayıları olarak yorumlanmamalıdır.

## 4. Yapılandırma ve kalite kapıları

Tarihsel commit'te doğrulanan yapılandırma dosyaları:

- `pyproject.toml`
  - Python gereksinimi: `>=3.11`
  - Runtime bağımlılığı: `pygame-ce>=2.5`
  - Pytest keşfi: `tests/`, `test_*.py`
  - Ruff hedefi: Python 3.11, satır uzunluğu 100
  - Ruff kural seçimi: `E4,E7,E9,F`
- `requirements.txt`: Pygame-ce runtime bağımlılığı.
- `requirements-test.txt`: `requirements.txt` üzerine `pytest>=8.3` ve `ruff>=0.11`.
- `requirements-release.txt`: release/paketleme araçları ve Pygame-ce.

Tarihsel CI tanımlarında:
- Eldoria CI, Python 3.11 ve 3.12 üzerinde Ubuntu ve Windows matrisinde unittest keşfi, pytest ve seçilmiş dosyalarda Ruff çalıştıracak şekilde tanımlanmıştır.
- Core Quality, Python 3.11 Ubuntu ve Python 3.12 Windows işlerini; seçilmiş Ruff kontrollerini, legacy API kullanım raporlamasını, benchmark ve release doğrulamasını içerir.

**Önemli ayrım:** Workflow dosyaları komutların tanımını, GitHub Actions check-run kayıtları ise f9e4914e üzerinde gerçekten çalıştıklarını ve sonuçlarını kanıtlar. Bu commit'e bağlı Eldoria CI, Core Quality ve humanoid benchmark çalışmaları 15. bölümde kayıtlıdır. Ruff tüm repo için tek seferde değil, workflow'larda belirtilen seçilmiş dosya kümelerinde çalıştırılmıştır; bu sınır özellikle korunmuştur.

## 5. Önceden mevcut mimari belgeler — A0 kanıtı olarak kullanma sınırı

Tarihsel ağaçta çok sayıda mimari belge mevcuttur. Ancak bunların hepsi A0'ın istediği envanter değildir:

- `docs/architecture/00-core-2.0-baseline.md`: Core 2.0 mimari temel sözleşmesidir; A0'ın bütün legacy kod taramasını karşılamaz.
- `docs/architecture/34-legacy-system-dependency-map.md`: Belge kendi açıklamasında `fix/phase-1-critical-stability` dalındaki kaynakları temel aldığını belirtir. Bu nedenle `experiment/map-cleanup` tarihsel A0 taramasının doğrudan kanıtı sayılamaz.
- `docs/architecture/37-hexagonal-world-dependency-inventory.md`: İncelenen commit olarak `5e77ef0c` ve `demo_eldoria` dalını belirtir. Bu, farklı bir altıgen dönüşüm envanteridir; A0'ın tüm repo kapsamını karşılamaz.
- `docs/architecture/55-actor-identity-and-hex-spatial-ownership.md`: Belirli bir mekânsal sahiplik dönüşümünün sözleşmesidir; genel legacy mimari taraması değildir.

Bu belgeler ilgili alanlarda yararlı teknik bağlam sağlar; fakat A0'ın eksik kabul kanıtlarının yerine geçirilemez.

## 6. A1 planında kayıtlı tarihsel risk adayları

`docs/architecture/25-a1-a5-player-identity-persistence-plan.md`, oyuncu kimliği çalışması için şu dosyalarda sabit kimlik veya sıra bağımlılığı adaylarını kaydeder:

- `game_ui/screens/character_creation.py`
- `game_ui/screens/character_screen.py`
- `game_ui/screens/container_screen.py`
- `game_ui/screens/dialogue_screen.py`
- `game_ui/screens/inventory_screen.py`
- `game_ui/screens/market_screen.py`
- `game_ui/screens/production_screen.py`
- `game_ui/screens/currency_exchange_screen.py`
- `game_ui/renderer.py`

Planın anlattığı aday kalıplar arasında `"hero"` / `"player"` sabitleri, `actors[0]` gibi ilk eleman varsayımları ve bazı doğrudan holder erişimleri bulunur. Bu liste A1'in kendi sorun envanteridir; A0'ın bütün runtime, content, persistence, UI, tests ve tooling/docs alanlarını taradığını göstermez. Bu rapor, A1 planındaki adayları A0'ın tamamlanmış ve satır numaralı bulgu listesi olarak yeniden etiketlemez.

## 7. A0 kabul ölçütleri — kanıt matrisi

| A0 gereksinimi | Bulunan kanıt | Durum |
|---|---|---|
| Dal/commit temel çizgisini tanımlama | Tarihsel commit ve roadmap ekleme commit'i | Kısmen doğrulandı |
| Kaynak, içerik, yapılandırma, test, persistence ve dokümantasyon envanteri | Recursive tree sayımları ve yapılandırma dosyaları | Kısmen doğrulandı |
| Legacy göstergelerini tarama | 290 ana üretim Python dosyası, 14 script, 123 Hex World Lab Python dosyası ve 301 test Python dosyası üzerinde tanımlı pattern taraması | Doğrulandı; kapsam sınırı 15. bölümde |
| Bulguları altı kategoriye ayırma | Runtime, content, persistence, UI, tests, tooling/docs sınıflandırması | Doğrulandı |
| Her bulguyu dosya/satır/kullanım amacıyla ilişkilendirme | 10, 12, 13 ve 15. bölümlerde somut bulgu tabloları | Doğrulandı |
| Test ve lint komutlarını belirleme | Tarihsel pyproject ve CI workflow tanımları | Doğrulandı |
| Test/lint başlangıç sonuçlarını raporlama | Başlangıç commit'ine bağlı 8/8 başarılı GitHub Actions check-run | Doğrulandı; Ruff kapsamı sınırlı |

## 8. A0 kapanış kontrolü

A0'ın kalan keşif işleri 15. bölümde tamamlanmış olarak kaydedilmiştir. Sonraki aşamalarda bu rapordaki riskler için ayrı uygulama ve kabul işleri yürütülür; A0 kapsamına geriye dönük runtime değişikliği eklenmez.

## 9. Değişiklik ve doğrulama kaydı

- Bu rapor hazırlanırken runtime koduna dokunulmadı.
- `main`, `demo_eldoria` veya `experiment/hex-world-laboratory` dallarında işlem yapılmadı.
- Bu rapor A0'ın keşif ve temel çizgi çıktısıdır; runtime kodu değiştirilmemiştir.
- Tarihsel test/lint sonuçları GitHub Actions check-run kayıtlarından doğrulanmıştır; rapor hazırlanırken yerel test çalıştırıldığı iddia edilmez.


## 10. Tarihsel kaynak kodunda doğrulanan somut legacy bulguları

Aşağıdaki satır incelemeleri doğrudan `f9e4914e` commit'indeki Git blob'larından yapılmıştır. Bunlar A0 taramasının tamamı değildir; fakat A0'ın aradığı kalıpların tarihsel başlangıç kodunda gerçekten bulunduğunu doğrular. Satır numaraları bu tarihsel commit'e aittir.

| Kategori | Dosya ve satır | Gözlenen kalıp | Kullanım / risk |
|---|---|---|---|
| UI / kimlik | `game_ui/screens/character_creation.py:132,408` | `hero` sabit kimliği ve `.holder.current.characters` erişimi | Karakter oluşturma ekranı oyuncuyu sabit kimlikle buluyor; servis sınırını aşıyor. |
| UI / kimlik | `game_ui/screens/character_screen.py:74,77,135` | `actor_character("hero")`, `actor_stats("hero")`, `improve_skill("hero", ...)` | Karakter ekranı oyuncu kimliğini sabit kabul ediyor. |
| UI / sıra varsayımı | `game_ui/screens/character_screen.py:153` | `snapshot.actors[0]` | İlk aktörün oyuncu olduğu varsayılıyor. |
| UI / sıra varsayımı | `game_ui/screens/container_screen.py:68` | `actors[0]` | Konteyner etkileşiminde ilk aktör seçiliyor. |
| UI / servis sınırı | `game_ui/screens/dialogue_screen.py:57,96,144,227,347,524,545,571` | `service.application.holder.current` | Diyalog ekranı servis arkasındaki Application/SessionBundle verisine doğrudan erişiyor. |
| UI / kimlik ve sıra | `game_ui/screens/dialogue_screen.py:159,184,238-239,245,348,454,467,480,493` | `player` / `hero` sabitleri ve ilk aktöre geri dönüş | Envanter, görev ve diyalog akışlarında oyuncu kimliği sabit; aktör seçimi ilk elemana düşebiliyor. |
| UI / kimlik | `game_ui/screens/inventory_screen.py:22,219,234,242-243,390` | Varsayılan `inventory_id="player"`; `hero` ile eşya/istatistik işlemleri | Envanter kimliği ile aktör kimliği sabit varsayımlara bağlı. |
| UI / kimlik | `game_ui/screens/market_screen.py:36,119` | Satın alma ve cüzdan için `hero` / `player` | Pazar işlemleri sabit oyuncu kimliğine bağlı. |
| UI / servis sınırı | `game_ui/screens/production_screen.py:12,39,46` | `inventory_id="player"` ve doğrudan `service.application.holder.current` | Üretim ekranı hem sabit envanter kimliği hem Application erişimi kullanıyor. |
| UI / kimlik | `game_ui/screens/currency_exchange_screen.py:75,107` | Bakiye ve döviz işlemlerinde `hero` | Döviz ekranı sabit oyuncu kimliğine bağlı. |
| UI / servis sınırı | `game_ui/renderer.py:563,634,654` | HUD/quest/map çiziminde `service.application.holder.current` | Renderer UI dışı oturum verisini servis sınırı arkasından doğrudan okuyor. |
| UI / servis sınırı | `game_ui/screens/combat_screen.py:8,17,33,39` | `service.application.holder.current.combat` | Savaş ekranı doğrudan Application oturumundaki savaş durumunu okuyor. |
| UI / servis sınırı | `game_ui/screens/quest_log_screen.py:251,366,423` | `service.application.holder.current` | Görev günlüğü ekranı quest log ve NPC verisini doğrudan okuyor. |
| UI / servis sınırı | `game_ui/screens/trade_screen.py:71` | `service.application.holder.current` | Ticaret ekranı partner/oturum verisine servis sınırını aşarak erişiyor. |
| UI / sıra varsayımı | `game_ui/renderer.py:657` | `actors[0].world_id` | Harita seçimi ilk aktörün dünyasına bağlanmış. |
| UI / varsayılan kimlik | `game_ui/renderer.py:455,559,605` | `actor_id="hero"`, `inventory_id="player"` | Render API'leri varsayılan oyuncu/çanta kimliği varsayıyor. |

### 10.1 Sınıflandırma

Bu somut bulguların tamamı esas olarak **UI** kategorisindedir. Bir kısmı aynı zamanda **kimlik/servis sınırı** riskidir; ancak rapordaki altı ana kategoriye göre tek birincil kategori seçildiğinde UI altında tutulmuştur. Bu örnekler runtime, content, persistence, tests ve tooling/docs kategorilerinin tamamının tarandığı anlamına gelmez.

### 10.2 Tarama kapsamı sınırı

Bu turda tarihsel commit ağacı ve ilgili 13 UI/Application dosyasının bir bölümü incelendi. Özellikle karakter, konteyner, diyalog, envanter, pazar, üretim, döviz, renderer ve Application kodundan somut satırlar doğrulandı. `application/game_application.py` içindeki `holder.current` kullanımlarının önemli bölümü Application katmanının kendi içidir; bunlar UI servis sınırı ihlaliyle aynı risk olarak sınıflandırılmamalıdır.

Bu nedenle henüz:
- 290 üretim Python dosyasının tamamı,
- 301 test dosyasının tamamı,
- `hex_world_lab/` altındaki 123 Python dosyası,
- bütün persistence/save-load ve content/config dosyaları
aynı pattern setiyle satır satır taranmış değildir. Bu sayılar tarama kapsamının büyüklüğünü belirtir; taranmış dosya sayısı değildir.

Kod arama servisi bu incelemede `ref=f9e4914e` parametresini dikkate almayıp varsayılan dal sonuçlarını döndürdüğü için, güncel kod arama sonuçları tarihsel bulgu kanıtı olarak kullanılmadı. Yukarıdaki bulgular yalnızca tarihsel commit ağacından elde edilen blob SHA'ları okunarak doğrulandı.

## 11. Güncel A0 kararı

Bu bölüm, ilk aşamadaki kısmi incelemenin ara kararını kaydeder. 15. bölümde tamamlanan kapsamlı pattern taraması ve tarihsel CI kanıtı bu ara kararı güncellemiştir; nihai kapanış kararı 16. bölümde verilmiştir.


## 12. Tarihsel persistence / save-load incelemesi

Bu bölümde yalnızca `f9e4914e` tarihsel ağacındaki persistence dosyaları incelendi. Recursive tree'de save/persistence ile ilişkili 42 dosya yolu bulundu; aşağıdaki satır bulguları bunların tamamının değil, seçilmiş ana sözleşme ve adaptörlerin doğrudan okunmasına dayanır.

### 12.1 Yapısal olarak doğrulanan kayıt mimarisi

- `application/save_document.py:24-25,57-67,129-154`: Uygulama kaydı `rpg-game-save` şeması ve sürüm 3 ile tanımlanmış. Bilinmeyen şema, geçersiz sürüm ve desteklenmeyen gelecek sürüm açık hata ile reddediliyor.
- `application/migrations.py:9-33`: Uygulama zarfında v0→v1, v1→v2 ve v2→v3 geçişleri açıkça uygulanıyor. Eski kayıtlara `containers` ve `hex_world` alanları ekleniyor; kare koordinatların otomatik altıgen dönüşümü yapılmadığı yorumda da belirtilmiş.
- `application/save_codec.py:10-31`: JSON kodlama deterministik; anahtarlar sıralanıyor, NaN/Infinity gibi standart dışı sayılar reddediliyor.
- `application/save_storage.py:70-95,97-175`: On kayıt yuvası ve kullanıcı Belgelerim dizinindeki Eldoria kayıt klasörü tanımlı. Eski `save/` dizininden slot kayıtları ve `eldoria_save.json` kontrollü biçimde taşınıyor; geçersiz kaynaklar ve çakışmalar raporlanıyor, mevcut hedef kayıt korunuyor.
- `core/persistence/contracts.py:17-24,76-100,141-157`: Core kaydı ayrı `rpg-core` şeması/sürümüyle tanımlı; durum verisi kopyalanıp üst düzeyde salt okunur hale getiriliyor. Bilinmeyen alanlar Core belgesinde ileriye dönük uyumluluk için tolere ediliyor.
- `application/hex_world_persistence.py:18-19,227-255,325-359,398-423`: Hex-world kaydı kendi sürümlü sözleşmesine sahip; entity kimliği, dünya sahipliği, harita hücresi ve NPC registry gereksinimleri restore öncesinde doğrulanıyor.
- `resources/persistence.py:24-25,229-285`, `character/persistence.py:14-15,70-78`, `economy/persistence.py` ve `quests/persistence.py`: Gameplay, karakter, ekonomi ve görev verileri ayrı snapshot/şema sınırlarıyla ayrıştırılmış.

### 12.2 Doğrulanan risk adayları ve dikkat noktaları

| Kategori | Dosya ve satır | Gözlenen durum | A0 değerlendirmesi |
|---|---|---|---|
| Persistence / sürüm geçişi | `core/persistence/restore.py:167-185` | Core `PersistenceMigrationBoundary` sürüm kontrolü yapıyor; v1→v2 dönüşümünün bilerek ertelendiği açıklanıyor ve mevcut sürüm dışı belge reddediliyor. | Açık bir uyumluluk sınırı; tarihsel eski Core kayıtlarının ayrıca dönüştürülmediği bir risk/ürün kararıdır, tek başına hata kanıtı değildir. |
| Persistence / geriye uyumluluk | `application/migrations.py:12-33` | Uygulama zarfı için üç aşamalı geçiş var; kare dünya konumlarını yeni altıgen koordinatlara dönüştürmüyor. | Dönüşümün yapılmaması bilinçli ve belgelenmiş. Eski kayıtların konumsal verilerinin nasıl ele alındığı ayrı kabul ölçütü gerektirir. |
| Persistence / varsayılan alanlar | `application/extended_persistence.py:130-187,288-311,351-406` | Sosyal snapshot sürüm 1/2 kabul ediyor; bazı eksik alanları boş liste, `idle`, `civilian`, `active=True`, varsayılan hız/istatistik gibi değerlere tamamlıyor. | Geriye uyumluluk amacı taşıyor olabilir. Eksik alanların sessizce varsayılanlanmasının bozuk/eksik kayıtları gizleyip gizlemediği testlerle doğrulanmalı; bu inceleme bunu hata olarak kanıtlamaz. |
| Persistence / restore sözleşmesi | `application/hex_world_persistence.py:231-255,325-359,398-423` | Katı alan kümeleri ve domain owner doğrulamaları var; restore hedefinin boş olması ve NPC registry bulunması zorunlu. | Güçlü doğrulama kanıtı; tam test kapsamı ayrıca incelenmedi. |
| Persistence / eski kayıt taşıma | `application/save_storage.py:82-86,109-175` | Varsayılan legacy kaynak yolu proje içindeki `save/`; taşıma çakışma ve bozuk kaynakları ayrı raporluyor. | Açık bir migration kaynağı. Kullanıcı verisinin yeni konuma taşınması davranışı için test dosyası mevcut; bu aşamada test çalıştırılmadı. |

**Önemli:** Varsayılan değer kullanımı tek başına “sessiz hata” sayılmadı. Şema sürümüyle ilişkilendirilmiş eski kayıt uyumluluğu olabileceği için, yalnızca eksik alanın hangi sürümde geçerli olduğu ve testlerin bunu güvenceye alıp almadığıyla birlikte değerlendirilmelidir.

## 13. Tarihsel content ve yapılandırma incelemesi

### 13.1 Paket ve manifest yapısı

- `content/active_package.json`: Etkin paket `demo_eldoria` olarak açıkça seçilmiş; `schema_version: 1`.
- `content/demo_eldoria/manifest.json`: Paket kimliği `demo_eldoria`, sürüm `0.7.1`; starter, NPC, quest, resource, character, gameplay_rules ve containers dosyaları ile harita/yerleşim dizinlerini tanımlıyor.
- `content/movement_test/manifest.json`: Ayrı test paketi `movement_test`, sürüm `1.0.0-test`; starter, NPC, quest, resource, character ve gameplay_rules dosyalarını tanımlıyor.
- Tarihsel ağaç üzerinde iki manifestteki `files` referanslarının tamamı gerçek dosyalara çözümleniyor. Bu iki paket için manifestin var olmayan JSON dosyasına işaret ettiği yönünde bulgu yok.
- `application/content_pack.py:51-70`: Etkin paket yapılandırması okunamazsa, şeması yanlışsa, paket yolu boşsa veya paket bulunamazsa açık hata üretiliyor; sessizce başka pakete düşülmüyor.
- `application/content_loader.py:86-110` ve `application/content_pack.py:135-157`: Manifest sürümü, paket sürümü, zorunlu kayıt alanları ve yinelenen NPC kimlikleri doğrulanıyor.

### 13.2 Kimlik ve varsayılanların içerik tarafından tanımlanması

- `content/demo_eldoria/gameplay_rules.json:1-7` ve `content/movement_test/gameplay_rules.json:1-7`: Oyuncu envanteri `player`, hesap kimliği `hero` olarak açıkça içerik kurallarında tanımlı.
- Her iki `starter_content.json` dosyasında da `ids.world_id` ve `ids.hero_id` açıkça veriliyor. Bu, UI kodundaki sabit kimlik kullanımından farklı olarak paket yapılandırmasından gelen bir kimlik sözleşmesidir; kendi başına gizli varsayılan veya legacy kusuru olarak sınıflandırılmadı.
- `application/content_pack.py:825-845`: Oyuncu envanteri yapılandırılmış `inventory_id` ile oluşturuluyor ve oyuncu aktörüne bağlanıyor; oyuncu aktörünün bulunmaması veya başka envantere bağlı olması hata veriyor.
- `content/demo_eldoria/manifest.json` ve `content/movement_test/manifest.json` referans denetimleri bu iki paketin dosya bütünlüğü için olumlu kanıt sağlar; içeriklerin oyun tasarımı bakımından doğru veya dengeli olduğunu kanıtlamaz.

### 13.3 Yapılandırma çoğulluğu adayı

- `core/domain/movement/config.py:1-48` ve `hex_world_lab/movement/config.py` aynı adlı `MovementConfig` veri sınıfını ayrı modüllerde tanımlıyor.
- Core sürümü ivmelenme, yavaşlama ve frenleme değerlerini de içerirken laboratuvar sürümü yalnızca hız ve koşu/gizlilik katsayılarını içeriyor.
- Bu, iki hareket altyapısının ayrı sözleşmeleri olabilir; yalnızca benzer sınıf adı bulunması kopya/çakışan aktif yapılandırma kanıtı değildir. Hangi modülün ana oyun tarafından kullanıldığı ve iki tanımın ortaklaştırılması gerekip gerekmediği A0'ın runtime bağımlılık taramasında doğrulanmalıdır.

### 13.4 Test ve paketleme yapılandırması

- `pyproject.toml`: Pytest keşfi `tests/` ve `test_*.py` olarak tanımlı; ayrıca `[tool.unittest]` altında `python -m unittest discover -s . -t . -p test_*.py` komutu yer alıyor.
- `requirements-test.txt`: Test bağımlılıkları `pytest` ve `ruff`; `requirements.txt` ise Pygame-ce runtime bağımlılığını içeriyor.
- `pyproject.toml` paket veri listesi `demo_eldoria` içeriğini dağıtım paketine dahil ediyor; `movement_test` test paketi olarak listelenmiyor. Etkin paket de `demo_eldoria` olduğundan, incelenen konfigürasyonda bu bir çelişki olarak değerlendirilmedi.
- Test komutu tanımları ve workflow'lar mevcuttur; A0 tarihsel test/lint sonuçları hâlâ bulunamamıştır.

## 14. Bu turun kapsamı ve A0 kararı

Bu bölüm, persistence ve content/config incelemesinin ilk turundaki kapsam sınırlarını kaydeder. Daha sonra 15. bölümde tüm ilgili Python dosyalarına pattern taraması uygulanmış ve başlangıç commit'ine ait CI kayıtları bulunmuştur. Nihai karar 16. bölümde verilmiştir.

## 15. Tamamlanan tarihsel kaynak ve test taraması

### 15.1 Kapsam ve yöntem

Tarihsel commit f9e4914edb25fd0d8943934de8dd41d67cfab813 ağacındaki Python dosyaları Git tree'den tek tek çıkarıldı ve Git blob içerikleri üzerinden aşağıdaki pattern kümeleriyle tarandı:

- Sabit kimlik adayları: "hero", "player".
- Sıra/ilk eleman varsayımları: actors[0], entities[0], characters[0], npcs[0] ve benzerleri.
- Servis/oturum kaçışları: service.application, .holder.current, global/tekil erişim göstergeleri.
- Varsayılan davranışlar: setdefault, varsayılan argümanlı .get(...), boş değer ve sabit varsayılan kullanımları.
- Bakım/uyumluluk işaretleri: TODO, FIXME, legacy, deprecated ve çıplak except kontrolleri.

Tarama kapsamı:
- Ana oyun/üretim kaynakları: 290 Python dosyası.
- scripts/: 14 Python dosyası.
- hex_world_lab/: 123 Python dosyası; ana oyun kaynaklarından ayrı laboratuvar alt sistemi olarak ayrıca tarandı.
- tests/: 301 Python dosyası.
- İçerik: 26 dosya, bunların 23'ü JSON; etkin paket ve iki paket manifesti ile manifestin referans verdiği dosyalar kontrol edildi.
- Dokümantasyon: 104 dosya envantere alındı; A0/kimlik/persistence/hex-world kapsamını etkileyen 00, 24, 25, 34, 37, 55, 80 ve ilgili kayıt sözleşmeleri ayrıca okundu.
- Yapılandırma ve CI: pyproject.toml, requirements dosyaları ve 7 GitHub Actions workflow dosyası incelendi.

Bu, tanımlanan pattern seti için tüm Python dosyalarını kapsayan statik taramadır; Python AST veya type-checker analizi değildir. JSON dışı asset ikili içerikleri, bağımlılıkların kaynak kodları ve tüm 104 dokümanın kelime kelime semantik incelemesi A0 kapsamına alınmadı. Test fixture eşleşmeleri üretim kusuru sayılmadı.

### 15.2 Altı kategoriye göre nihai bulgu özeti

| Kategori | Doğrulanan bulgular | Sonuç / sonraki aşamaya etkisi |
|---|---|---|
| Runtime | application/gameplay_service.py:186-188 oyuncu actor/inventory/account kimlikleri için hero/player/hero başlangıç değerleri veriyor; aynı servis configure_player_context() ile bunların yapılandırılmasına izin veriyor (:695-699). application/hex_world_initializer.py:71,138 servis arkasındaki Application nesnesine doğrudan erişiyor. core/game.py:140 tek açık deprecated API dekoratörünü taşıyor. | Oyuncu kimliği A1'e; servis/Application sınırı A3'e; uyumluluk API'sinin kontrollü kaldırılması ilgili sonraki mimari aşamaya aittir. |
| Content | İki paket manifestinin tüm dosya referansları tarihsel ağaçta mevcut. demo_eldoria etkin paket; oyuncu kimliği ve envanter/account bağları içerik kurallarında açık. Paket yükleyici manifest/sürüm/kimlik ve referans doğrulaması yapıyor. | Manifest dosya bütünlüğü doğrulandı. İçerik kimlikleri UI'daki dağınık sabit kullanımlarıyla karıştırılmadı; A2 içerik sözleşmesi çalışmalarıyla ilişkilendirildi. |
| Persistence | Uygulama save envelope v0–v3 migrasyonu; Core ve HexWorld için ayrı şemalar; atomik eski kayıt taşıma ve çakışma raporu; domain snapshot doğrulamaları bulundu. Sosyal snapshot'ta sürüme bağlı varsayılan alanlar var. | Kayıt sözleşmeleri ve olası varsayılan alan riskleri 12. bölümde dosya/satır bazında kayıtlı. Varsayılanlar otomatik olarak kusur sayılmadı; sürüm uyumluluğu bağlamında tutuldu. |
| UI | hero/player sabitleri, ilk aktör seçimi ve service.application.holder.current erişimleri karakter, diyalog, envanter, pazar, üretim, döviz, görev günlüğü, savaş, ticaret ve renderer alanlarında bulundu. | Somut dosya/satır/kullanım amacı 10. bölümde kayıtlı; A1/A3 sonraki uygulama aşamalarının temelini oluşturdu. |
| Tests | 301 test dosyası aynı pattern setiyle tarandı. hero/player eşleşmelerinin büyük bölümü test aktörü/fixture kimlikleri; holder.current eşleşmeleri Application davranışını test eden beyaz-kutu kurulum/assertion kodu. actors[0] eşleşmeleri testteki sıra/ilk kayıt assertion'larıdır; üretim UI'daki ilk oyuncu seçimiyle aynı sınıfta değerlendirilmedi. | Test eşleşmeleri runtime bulgusu olarak raporlanmadı. Mimari sınır ve migrasyon testleri mevcut. Tam otomatik test sonucu 15.3'te kayıtlı. |
| Tooling/docs | 14 script ve 7 workflow incelendi. scripts/check_map_cleanup.py legacy harita/presentation ve eski NPC pozisyon backfill sınırlarını kontrol ediyor. core/compatibility/usage.py statik legacy API kullanım raporu üretiyor. core/compatibility/deprecation.py:32 yalnızca Game.dunya_olaylarini_aktar API'sini açıkça deprecated olarak işaretliyor; diğer kayıtlar alias/adapter/compatibility türünde. | CI, harita cleanup kontrolünü ve legacy API kullanım raporunu çalıştırmış. Eski API uyumluluk katmanı bilinçli geçiş mekanizması olarak sınıflandırıldı; bütün adapter'lar kusur sayılmadı. |

### 15.3 Tarihsel CI ve test/lint başlangıç kanıtı

Aşağıdaki bütün kontrollerin head_sha değeri A0 tarihsel temel çizgisi olan f9e4914edb25fd0d8943934de8dd41d67cfab813 ile birebir eşleşir:

| Workflow | Run ID | İşler | Sonuç |
|---|---:|---:|---|
| Eldoria CI | 45582449692 | 4 Python test matrisi (Ubuntu/Windows × Python 3.11/3.12) + Pygame headless smoke | **5/5 başarılı** |
| Core Quality | 45582449472 | verify, verify-windows | **2/2 başarılı** |
| Humanoid locomotion benchmark | 45582449722 | benchmark | **1/1 başarılı** |
| **Toplam** |  | **8 check-run** | **8/8 başarılı** |

Eldoria CI işlerinde unittest discover, pytest suite ve seçilmiş application/anatomical-rig dosyalarında Ruff adımları başarılıdır. Pygame headless smoke işi Pygame başlatma, isometric world/actor render ve humanoid benchmark adımlarını tamamlamıştır.

Core Quality verify işinde seçilmiş runtime entegrasyon dosyalarının Ruff kontrolü, legacy map cleanup kontrolü, legacy API kullanım raporu, player click-to-move benchmark ve release-candidate doğrulaması başarılıdır. Windows işi map cleanup, legacy API raporu ve release-candidate doğrulamasını tamamlamıştır.

**Lint sınırı:** Bu sonuçlar workflow tarafından seçilmiş dosyalarda Ruff başarısını kanıtlar; tüm repo için tek seferlik ruff check . çalıştırıldığı anlamına gelmez. Tarihsel test/lint temel çizgisi olarak yalnızca gerçekten çalıştırılmış bu CI adımları raporlanmıştır.

### 15.4 Tarama sırasında kusur sayılmayan eşleşmeler

- application/game_application.py içindeki holder.current erişimleri Application katmanının kendi oturum/composition sorumluluğudur; UI servis sınırı ihlali olarak sınıflandırılmadı.
- continuous_player_movement.py, physics binding ve HexWorld entity kodlarındaki kind == "player" kontrolleri aktör türünü ifade eder; hero gibi sabit actor ID değildir.
- game_ui/world_rendering/character_sprite_factory.py içindeki palette="player" görsel palet adıdır; oyuncu kimliği değildir.
- hex_world_lab/entities/kind.py içindeki PLAYER = "player" entity türü enum değeridir; oyuncu instance ID'si değildir.
- hex_world_lab/entities/spatial_index.py içindeki setdefault indeks oluşturma davranışıdır; sessiz içerik/persistence fallback'i değildir.
- Benchmark scriptlerindeki hero/player sabitleri kontrollü ölçüm fixture'larıdır.
- Testlerdeki sabit kimlikler, beyaz-kutu oturum erişimleri ve ilk eleman assertion'ları test verisi/kurulum davranışıdır; production kodu olarak sayılmadı.

## 16. A0 kapanış kararı

A0'ın roadmap kabul ölçütleri karşılanmıştır:
1. Tarihsel dal/commit temel çizgisi ve başlangıç ağacı tanımlandı.
2. Kaynak, içerik, yapılandırma, test, persistence, dokümantasyon ve tooling dosya envanteri çıkarıldı.
3. Legacy pattern seti tüm ana üretim Python, script, Hex World Lab ve test Python dosyalarına uygulandı; hariç tutulan dosya türleri ve yanlış pozitif sınıfları açıklandı.
4. Bulgular runtime, content, persistence, UI, tests ve tooling/docs olarak sınıflandırıldı; gerçek riskler dosya/satır/kullanım amacıyla ilişkilendirildi.
5. Tarihsel başlangıç commit'ine bağlı 8/8 başarılı CI check-run doğrulandı; Ruff kapsam sınırı ayrıca kaydedildi.

**A0 — Başlangıç envanteri ve güvenli temel çizgi, 2026-11-27 tarihinde tamamlandı.** A0 sırasında runtime kodu değiştirilmedi. Bulunan risklerin giderilmesi A1 ve sonraki aşamaların kapsamındadır.
