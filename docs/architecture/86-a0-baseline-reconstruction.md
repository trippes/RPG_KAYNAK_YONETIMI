# A0 — Tarihsel Başlangıç Temel Çizgisi ve Kanıtların Yeniden Kurulması

**İncelenen dal:** `experiment/map-cleanup`  
**Tarihsel temel çizgisi:** `f9e4914edb25fd0d8943934de8dd41d67cfab813`  
**Temel çizginin üst commit'i:** `a961de7b91b6b7fe7d6b3aae48d2defc95fcb966` — `docs: add legacy architecture cleanup roadmap`  
**Rapor durumu:** Kısmi tarihsel doğrulama; A0 kapanış kanıtı değildir.  
**Kapsam:** Yalnızca GitHub üzerinden erişilebilen commit ağacı, belgeler, yapılandırmalar ve CI tanımları. Bu rapor yerel test çalıştırma çıktısı veya tamamlanmış statik kod taraması iddiasında bulunmaz.

## 1. Sonuç

A0'ın başlangıç noktası ve dosya envanterinin önemli bir bölümü yeniden oluşturuldu. Bununla birlikte yol haritasının kabul ölçütü olan eski mimari göstergelerinin kapsamlı, dosya/satır/kullanım amacı bazında taraması ile tarihsel test/lint başlangıç sonuçları bulunamadı.

Bu nedenle A0 **tamamlandı olarak işaretlenemez**. Bu rapor, önceki “A0 tamamlandı” kaydının yerine geçmez; hangi kanıtların gerçekten bulunduğunu ve hangi kanıtların hâlâ eksik olduğunu ayırır.

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

**Önemli ayrım:** Workflow dosyaları hangi komutların çalıştırılmak üzere tanımlandığını kanıtlar. Bu komutların `f9e4914e` üzerinde gerçekten çalıştırıldığını veya başarılı olduğunu kanıtlamaz. Bu incelemede tarihsel A0 test/lint çıktısı ya da A0'a ait CI run kimliği doğrulanamamıştır. Dolayısıyla A0 test temel çizgisi sonucu **bilinmiyor** olarak kalır.

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
| Legacy göstergelerini kapsamlı tarama | A1 planında kimlik alanına özgü adaylar var; genel tarama raporu yok | Eksik |
| Bulguları altı kategoriye ayırma | A0'a ait kapsamlı, sınıflandırılmış bulgu tablosu yok | Eksik |
| Her bulguyu dosya/satır/kullanım amacıyla ilişkilendirme | A0 için satır numaralı envanter yok | Eksik |
| Test ve lint komutlarını belirleme | Tarihsel pyproject ve CI workflow tanımları | Doğrulandı |
| Test/lint başlangıç sonuçlarını raporlama | A0'a ait çalıştırma çıktısı veya CI run kimliği yok | Eksik |

## 8. A0'ı kapatmak için kalan işler

1. Tarihsel `f9e4914e` kaynak ağacında legacy göstergeleri için kapsamı ve hariç tutulan dosyaları açıkça tanımlanmış bir tarama yapmak.
2. Her gerçek bulguyu dosya, satır aralığı, kullanım amacı, kategori ve risk ile kaydetmek; salt test fixture veya doküman eşleşmelerini runtime bulgusu gibi saymamak.
3. Persistence/save-load, content/config, UI, tests ve tooling/docs alanlarını ayrı ayrı kontrol etmek.
4. A0 başlangıç test/lint çıktısı bulunamıyorsa bunu açıkça “tarihsel çıktı yok” olarak bırakmak. Güncel kodda çalıştırılan testleri tarihsel baseline sonucu diye sunmamak.
5. Kullanılabilir bir CI yolu varsa, yalnızca tarihsel commit'e ait olduğu kesin olarak belirlenebilen sonuçları ayrıca kaydetmek. Güncel branch CI sonuçları A0 başlangıç sonucu yerine geçmez.

## 9. Değişiklik ve doğrulama kaydı

- Bu rapor hazırlanırken runtime koduna dokunulmadı.
- `main`, `demo_eldoria` veya `experiment/hex-world-laboratory` dallarında işlem yapılmadı.
- Bu rapor, A0'ı tamamlandı olarak işaretlemez.
- Tarihsel test/lint komutları bu rapor hazırlanırken çalıştırılmadı; raporda test başarısı iddia edilmez.


## 10. Tarihsel kaynak kodunda doğrulanan somut legacy bulguları

Aşağıdaki satır incelemeleri doğrudan `f9e4914e` commit'indeki Git blob'larından yapılmıştır. Bunlar A0 taramasının tamamı değildir; fakat A0'ın aradığı kalıpların tarihsel başlangıç kodunda gerçekten bulunduğunu doğrular. Satır numaraları bu tarihsel commit'e aittir.

| Kategori | Dosya ve satır | Gözlenen kalıp | Kullanım / risk |
|---|---|---|---|
| UI / kimlik | `game_ui/screens/character_creation.py:132,408` | `hero` sabit kimliği ve `.holder.current.characters` erişimi | Karakter oluşturma ekranı oyuncuyu sabit kimlikle buluyor; servis sınırını aşıyor. |
| UI / kimlik | `game_ui/screens/character_screen.py:74,77,135` | `actor_character("hero")`, `actor_stats("hero")`, `improve_skill("hero", ...)` | Karakter ekranı oyuncu kimliğini sabit kabul ediyor. |
| UI / sıra varsayımı | `game_ui/screens/character_screen.py:153` | `snapshot.actors[0]` | İlk aktörün oyuncu olduğu varsayılıyor. |
| UI / sıra varsayımı | `game_ui/screens/container_screen.py:68` | `actors[0]` | Konteyner etkileşiminde ilk aktör seçiliyor. |
| UI / servis sınırı | `game_ui/screens/dialogue_screen.py:57,96,144,227,347,524,545,571` | `service.application.holder.current` | Diyalog ekranı servis arkasındaki Application/SessionBundle verisine doğrudan erişiyor. |
| UI / kimlik ve sıra | `game_ui/screens/dialogue_screen.py:159,184,238-239,348,454,467,480,493` | `player` / `hero` sabitleri ve ilk aktöre geri dönüş | Envanter, görev ve diyalog akışlarında oyuncu kimliği sabit; aktör seçimi ilk elemana düşebiliyor. |
| UI / kimlik | `game_ui/screens/inventory_screen.py:22,219,234,242-243,390` | Varsayılan `inventory_id="player"`; `hero` ile eşya/istatistik işlemleri | Envanter kimliği ile aktör kimliği sabit varsayımlara bağlı. |
| UI / kimlik | `game_ui/screens/market_screen.py:36,119` | Satın alma ve cüzdan için `hero` / `player` | Pazar işlemleri sabit oyuncu kimliğine bağlı. |
| UI / servis sınırı | `game_ui/screens/production_screen.py:12,39,46` | `inventory_id="player"` ve doğrudan `service.application.holder.current` | Üretim ekranı hem sabit envanter kimliği hem Application erişimi kullanıyor. |
| UI / kimlik | `game_ui/screens/currency_exchange_screen.py:75,107` | Bakiye ve döviz işlemlerinde `hero` | Döviz ekranı sabit oyuncu kimliğine bağlı. |
| UI / servis sınırı | `game_ui/renderer.py:563,634,654` | HUD/quest/map çiziminde `service.application.holder.current` | Renderer UI dışı oturum verisini servis sınırı arkasından doğrudan okuyor. |
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

Tarihsel kodda A0'ın hedeflediği legacy kalıpların somut örnekleri artık dosya/satır/kullanım amacıyla kanıtlanmıştır. Bununla birlikte tam kapsamlı kategori taraması ve tarihsel test/lint başlangıç çıktısı hâlâ eksiktir. A0 bu nedenle **kısmen doğrulanmış ve açık** durumundadır; kapanış onayı verilmemiştir.
