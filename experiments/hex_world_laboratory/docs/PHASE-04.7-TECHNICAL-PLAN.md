# Aşama 4.7 — Hareket Modları Teknik Mimari Planı

> **Belge türü:** Onaylı genel planın teknik tasarım belgesi  
> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK PLAN — KULLANICI ONAYI BEKLİYOR  
> **Ön koşul:** Aşama 4.7 genel planı kullanıcı tarafından onaylandı.

## 1. Teknik hedef ve sınırlar

Mevcut sürekli hareket hattı korunarak üç cihazdan bağımsız hareket modu eklenecek:

| Mod | Girdi | Çarpan | Demo temel hızı 60 ise |
|---|---|---:|---:|
| Normal | Shift/Alt yok | 1,0x | 60 birim/sn |
| Koşma | Sol veya sağ Shift | 1,5x | 90 birim/sn |
| Gizlilik | Sol veya sağ Alt'a basışla aç/kapa (toggle) | 0,5x | 30 birim/sn |

Öncelik: **Gizlilik > Koşma > Normal**.

Mod her simülasyon tick'inde örneklenen `MovementIntent` üzerinden uygulanır. Geçiş anlıktır. İvme, sürtünme, stamina, ses, animasyon ve NPC algılaması bu planın dışındadır.

## 2. Mevcut mimari ve korunacak akış

Bugünkü veri/çalışma akışı:

`PygameKeyboardAdapter.read_intent()` → `MovementIntent` → `MovementSystem.step(tick, intent)` → `MovementIntegrator.step(...)` → yeni `MovementState` → `MovementCellTracker.update(position)`.

Bu akış değişmeyecek. Hareket çekirdeği Pygame'i import etmeyecek; tick kaynağı veya accumulator eklenmeyecek. Hex hücre takibi hareketten sonra aynı fiziksel konumu kullanmaya devam edecek.

## 3. Veri sözleşmeleri ve API

### 3.1 Yeni `movement/mode.py`

Cihazdan bağımsız enum:

- `MovementMode.NORMAL`
- `MovementMode.RUNNING`
- `MovementMode.STEALTH`

Enum yalnızca mod kimliğini temsil eder; tuş veya Pygame sabiti içermez. Public export `hex_world_lab.movement` paketinden yapılır.

### 3.2 `MovementIntent`

Mevcut frozen/slots dataclass korunur ve ikinci alan eklenir:

- `direction: Vector2` — mevcut varsayılanı korunur.
- `mode: MovementMode = MovementMode.NORMAL` — yeni alan, geriye dönük uyumluluk için varsayılanlıdır.

`__post_init__` hem yön hem mod türünü doğrular. Eski `MovementIntent()` ve `MovementIntent(Vector2(...))` çağrıları Normal modda çalışmaya devam eder. Geçersiz mod `TypeError` ile reddedilir.

### 3.3 `MovementConfig`

Mevcut `max_speed` zorunlu alanı korunur. Sonuna varsayılanlı iki alan eklenir:

- `running_speed_multiplier: float = 1.5`
- `stealth_speed_multiplier: float = 0.5`

Böylece mevcut `MovementConfig(max_speed=...)` çağrıları değişmez.

Tüm hız değerleri bool olmayan gerçek sayılar olmalı, sonlu ve negatif olmayan değerler olarak doğrulanmalıdır. Sıfır çarpan izinlidir ve ilgili modda hareketi durdurur. `max_speed` için mevcut doğrulama davranışı korunur.

Config üzerinde tek bir saf çözümleme metodu bulunur:

`speed_multiplier_for(mode: MovementMode) -> float`

- NORMAL → 1.0
- RUNNING → `running_speed_multiplier`
- STEALTH → `stealth_speed_multiplier`
- Bilinmeyen tür/değer → `TypeError` veya açık doğrulama hatası; sessizce Normal'e düşülmez.

### 3.4 `MovementState`

Mevcut immutable state'e son alan olarak:

`mode: MovementMode = MovementMode.NORMAL`

eklenir. Böylece son işlenmiş tick'te seçilen mod, aktör dururken de teşhis edilebilir. Mevcut iki konumsal argüman ve keyword kullanımları geçerliliğini korur. State doğrulaması mod tipini de denetler.

### 3.5 `MovementIntegrator`

Hız hesabı tek noktada yapılır:

1. Intent yönü mevcut şekilde normalize edilir.
2. Config, intent modunun çarpanını çözümler.
3. Etkin hız = `max_speed × mode_multiplier`.
4. Velocity = normalize edilmiş yön × etkin hız.
5. Konum = önceki konum + velocity × delta_time.
6. Yeni state, velocity ile birlikte intent'in modunu taşır.

Yön sıfırsa velocity sıfır kalır; state modu yine seçilmiş modu gösterir. Sıfır delta time konumu ilerletmez; mevcut sözleşme gereği hareket yönü varsa velocity hesaplanmış olur. Input state değiştirilemez ve integrator saat/tick sahiplenmez.

### 3.6 `MovementSystem`

Tick doğrulama, ardışık tick kuralı ve 1/60 saniyelik adım değişmez. Yeni mod bilgisi MovementIntent üzerinden integrator'a aktarılır. Bu sınıfta ayrı mod önceliği veya Pygame mantığı bulunmaz.

## 4. Klavye adaptörü

Dosya: `input/pygame_keyboard.py`

Shift ve Alt farklı giriş semantiğine sahiptir:

- Shift: `pygame.K_LSHIFT` veya `pygame.K_RSHIFT` basılı tutulduğu sürece RUNNING. Tuş bırakılınca diğer etkin duruma göre mod yeniden çözülür.
- Alt: `pygame.K_LALT` veya `pygame.K_RALT` için basış kenarı (aggregate rising edge) algılanır. İlk basış STEALTH toggle durumunu açar; sonraki ayrı basış kapatır. Basılı tutma ve OS key-repeat yeni toggle üretmez.

Sol ve sağ Shift tek bir boolean RUNNING girdisidir. Sol ve sağ Alt da tek bir mantıksal Alt girdisi olarak birleştirilir: iki Alt tuşunun aynı anda basılması tek toggle üretir; bir Alt bırakılırken diğeri hâlâ basılıysa yeni basış kenarı sayılmaz.

Etkin mod çözümleme sırası:

1. Toggle STEALTH açık ise STEALTH.
2. Değilse herhangi bir Shift basılıysa RUNNING.
3. Aksi halde NORMAL.

Böylece Shift basılıyken Alt'a basılması STEALTH'i açar ve öncelik kazanır. Alt'a tekrar basılıp STEALTH kapatıldığında Shift hâlâ basılıysa RUNNING anında geri gelir.

Adaptör, önceki aggregate Alt-down durumunu ve toggle STEALTH durumunu saklar. WASD/ok yön eşlemesi, karşıt yönlerin iptali, ham çapraz vektörün integrator'da normalize edilmesi korunur.

Odak kaybında `MovementIntent()` döndürülür: yön sıfır ve mod NORMAL; toggle durumu ve Alt kenar hafızası temizlenir. Odak geri kazanımında mevcut keyboard snapshot kenar üretmeden senkronize edilir; odak geri geldiği anda Alt basılı bulunması stealth'i kendiliğinden açmaz. Böylece takılı kalmış modifier veya sahte toggle önlenir.

## 5. Demo ve teşhis paneli

Dosya: `application/movement_demo.py`

- Demo'nun temel hızı ve MovementConfig yapılandırması tek kaynaktan tutulur.
- Teşhis paneline aktif mod ve mod çarpanı/teorik mod hızı satırı eklenir.
- Mevcut velocity satırı gerçek anlık hız vektörünü göstermeye devam eder; karakter dururken mod hızını gerçek hareket hızı gibi göstermeyiz.
- Mod teşhisi son işlenmiş MovementState snapshot'ından okunur.
- `render()` yalnızca okur/çizer; MovementSystem, tick pump veya tracker state'ini değiştirmez.
- Hex çizimi, cell tracker ve harita dışı davranış değişmez.

Önerilen satır örnekleri:
- `Mode: NORMAL | multiplier: 1.00x | mode speed: 60.0`
- `Mode: RUNNING | multiplier: 1.50x | mode speed: 90.0`
- `Mode: STEALTH | multiplier: 0.50x | mode speed: 30.0`

## 6. Dosya değişiklik listesi

### Yeni
- `src/hex_world_lab/movement/mode.py`
- `tests/unit/test_movement_mode.py`

### Güncellenecek
- `src/hex_world_lab/movement/__init__.py`
- `src/hex_world_lab/movement/intent.py`
- `src/hex_world_lab/movement/config.py`
- `src/hex_world_lab/movement/state.py`
- `src/hex_world_lab/movement/integrator.py`
- `src/hex_world_lab/input/pygame_keyboard.py`
- `src/hex_world_lab/application/movement_demo.py`
- `tests/unit/test_movement_integrator.py`
- `tests/unit/test_pygame_keyboard.py`
- `tests/integration/test_keyboard_movement_flow.py`
- `tests/integration/test_keyboard_focus_lifecycle.py`
- `tests/integration/test_movement_demo_flow.py`
- `tests/integration/test_movement_demo_fps.py`
- `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md`

Gerekirse yalnızca doğrudan ilgili test dosyaları genişletilir. `MovementSystem`, tick pump ve world tracker kodunda işlevsel değişiklik planlanmıyor.

## 7. Test tasarımı

### 7.1 Enum ve veri sözleşmesi

- Her enum değeri ve public import testi.
- Intent varsayılanı Normal.
- Eski positional/keyword constructor çağrıları geriye dönük uyumlu.
- Geçersiz mod tipi reddedilir.
- State varsayılan modu Normal; geçersiz mod reddedilir.

### 7.2 Config doğrulaması

- Varsayılan çarpanlar 1.5 ve 0.5.
- Normal çarpanı sabit 1.0.
- Negatif, NaN, +Inf, -Inf ve bool çarpanlar reddedilir.
- Sıfır çarpan kabul edilir.
- Her mod için `speed_multiplier_for` doğru değer verir.

### 7.3 Integrator

- 60 temel hızda Normal=60, Running=90, Stealth=30.
- Farklı temel hız konfigürasyonlarında oranlar korunur.
- Tek eksen ve çapraz hareket aynı modda eşit hız büyüklüğü üretir.
- Sıfır yön bütün modlarda konumu değiştirmez.
- Durmuş aktörün state.mode değeri intent modunu korur.
- Mod değişimi ilk hesaplanan adımda uygulanır.
- Input state immutable kalır; delta-time doğrulaması korunur.

### 7.4 Keyboard

- Sol/sağ Shift ayrı ayrı basılı-tutma ile RUNNING üretir; bırakma RUNNING'i sonlandırır.
- Sol/sağ Alt'ın ilk basış kenarı STEALTH'i açar; sonraki ayrı basış kapatır.
- Alt basılı tutulması ve OS key-repeat toggle'ı tekrarlamaz.
- Shift basılıyken Alt toggle açılırsa STEALTH; Alt toggle kapanırsa Shift hâlâ basılı olduğunda RUNNING.
- STEALTH açıkken Shift'in basılı/bırakılması STEALTH durumunu değiştirmez.
- Sol+sağ Shift birlikte → yalnızca RUNNING.
- Sol+sağ Alt birlikte → tek toggle; bir Alt bırakılırken diğeri basılıysa ikinci toggle yok.
- Hareket yönü testleri ve karşıt tuş iptali korunur.
- Focus lost → yön sıfır, mod NORMAL, toggle kapalı ve provider çağrılmaz.
- Focus gained → snapshot kenar üretmeden senkronize edilir; Alt basılı bulunması toggle başlatmaz.

### 7.5 Uçtan uca ve zaman

- Klavye → MovementIntent → MovementSystem → MovementState → CellTracker zinciri.
- Mod değişimi hücre takibinde snap veya koordinat kaymasına yol açmaz.
- Tick başına bir intent snapshot kullanılır.
- Aynı tick-indexed yön+mod dizisi 30/60/120 render FPS'te aynı state ve hücre çözümlemesi üretir.
- Tick pump 60 TPS, 8 tick/frame sınırı ve backlog korumasını değiştirmez.
- Render tekrarları mod veya state değiştirmez.

### 7.6 Regresyon ve CI

- Önce ilgili test modülleri; sonra tam laboratuvar `python -m pytest -q`.
- Lab CI ve Core Quality CI Linux/Windows.
- Aşama 4.1–4.6 testleri regresyon olarak korunur.
- Benchmark 1/10/100/1000 actor setinde tekrar çalıştırılır; önceki benchmark ile karşılaştırılır. Bu küçük veri sözleşmesi eklemesinin orantısız maliyet yaratmadığı doğrulanır.
- Gerçek Pygame penceresi için manuel kabul yapılır; CI masaüstü testinin yerine sayılmaz.

## 8. Manuel kabul kontrol listesi güncellemesi

Mevcut Aşama 4.6 maddeleri korunur; aşağıdakiler eklenir:

1. Normal hız: 60 temel hız örneğinde 1 saniyede yaklaşık 60 dünya birimi.
2. Shift basılı: yaklaşık 90 birim/sn.
3. Shift bırak: Normal hıza dönüş.
4. Alt'a bir kez bas: yaklaşık 30 birim/sn Stealth açılır; Alt'ı basılı tutmak gerekmez.
5. Alt'a ikinci kez bas: Stealth kapanır; Shift basılı değilse Normal'e dönülür.
6. Shift basılıyken Alt toggle aç: Stealth öncelikli; Alt toggle kapat: Shift hâlâ basılıysa Koşma.
7. Stealth açıkken Shift'i basıp bırak: Stealth açık kalır.
8. Alt tuşunu basılı tut ve otomatik tekrarın toggle üretmediğini doğrula.
9. Sol ve sağ Alt'ı birlikte kullan: tek toggle; birini bırakmak diğer basılıyken ikinci toggle üretmez.
10. Pencere odağı kaybı: hareket, toggle ve mod Normal/nötr duruma döner.
11. Odak geri geldiğinde Alt basılıysa sahte toggle oluşmaz.
12. Teşhis paneli doğru mod ve çarpanı gösterir.
13. Çapraz koşma ve çapraz gizlilikte yön normalizasyonu korunur.
14. 30/60/120 FPS altında aynı tick-input dizisi aynı sonucu üretir.

## 9. Hata davranışı ve uyumluluk

- Geçersiz mod/çarpan sessizce varsayılana çevrilmez; giriş doğrulamasında reddedilir.
- Eski MovementIntent ve MovementState constructor çağrıları Normal varsayılanıyla çalışır.
- Eski MovementConfig(max_speed=...) çağrısı varsayılan çarpanları alır.
- Pygame focus loss nötr intent üretir; toggle stealth ve Alt basış-kenarı hafızası temizlenir. Focus gain mevcut Alt durumunu toggle üretmeden senkronize eder.
- MovementSystem tick sırası ve atomic commit davranışı değişmez.
- Dünya haritası, hücre kimliği, runtime persistence ve geometri API'leri değişmez.

## 10. Uygulama sırası ve kabul kapıları

1. **4.7.1:** MovementMode, intent ve state sözleşmeleri; hedefli testler.
2. **4.7.2:** Config çarpanları ve integrator; hız/validasyon testleri.
3. **4.7.3:** Klavye adapterı; modifier/öncelik/focus testleri.
4. **4.7.4:** Demo entegrasyonu ve uçtan uca FPS testleri.
5. **4.7.5:** Teşhis paneli ve manuel kontrol listesi.
6. **4.7.6:** Tam regresyon, benchmark, CI, masaüstü kabul ve kapanış raporu.

Her alt aşamada kapsam genişletilmeden hedefli testler çalıştırılır. Tam doğrulama sonunda GitHub branch HEAD ve korunan branch'ler tekrar kontrol edilir. Kapanış raporu yazıldıktan sonra GitHub'dan geri okunarak SHA doğrulanır.

## 11. Dal güvenliği ve açık kapsam dışılar

- Tüm değişiklikler yalnızca `experiment/hex-world-laboratory` dalına yapılır.
- `main` ve `demo_eldoria` dalına açık, ayrı kullanıcı onayı olmadan yazma/merge/cherry-pick/rebase/reset yapılmaz.
- NPC algısı, gerçek stealth, ses/gürültü, stamina, animasyon, collision ve ana oyun entegrasyonu bu planla yetkilendirilmez.
- Bu belge kod uygulama izni değildir. Uygulama ancak kullanıcının bu teknik planı açıkça onaylamasından sonra başlar.
