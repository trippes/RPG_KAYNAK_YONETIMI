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
| Gizlilik | Sol veya sağ Alt | 0,5x | 30 birim/sn |

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

Aynı keyboard snapshot içinden aşağıdaki değiştiriciler okunur:

- Shift: `pygame.K_LSHIFT` veya `pygame.K_RSHIFT`.
- Alt: `pygame.K_LALT` veya `pygame.K_RALT`.

Mod seçimi tek bir açık karar sırasıyla yapılır:

1. Herhangi bir Alt basılıysa STEALTH.
2. Değilse herhangi bir Shift basılıysa RUNNING.
3. Aksi halde NORMAL.

Sol ve sağ aynı tür tuşların birlikte basılması tek boolean durum sayılır; çarpan birikmez. Alt+Shift birlikteyse Alt kazanır.

WASD/ok yön eşlemesi, karşıt yönlerin iptali, ham çapraz vektörün integrator'da normalize edilmesi ve her tick'te provider'ın yeniden örneklenmesi korunur.

Odak kaybında `MovementIntent()` döndürülür: yön sıfır ve mod NORMAL. Odak geri geldiğinde o anki gerçek keyboard snapshot yeniden okunur. Eski değiştirici durumu saklanmaz.

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

- Sol Shift, sağ Shift, sol Alt, sağ Alt ayrı ayrı test edilir.
- Shift+Alt → STEALTH.
- Alt basılı kalırken Shift'in bırakılması → STEALTH.
- Shift basılı kalırken Alt'ın bırakılması → RUNNING.
- İkisi bırakılınca → NORMAL.
- Sol+sağ Shift birlikte → yalnızca RUNNING; çarpan iki kat olmaz.
- Sol+sağ Alt birlikte → yalnızca STEALTH; çarpan iki kat olmaz.
- Hareket yönü testleri ve karşıt tuş iptali korunur.
- Focus lost → yön sıfır, mod NORMAL ve provider çağrılmaz.
- Focus gained → güncel snapshot yeniden okunur.

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
4. Alt basılı: yaklaşık 30 birim/sn.
5. Alt bırak: Normal hıza dönüş.
6. Shift+Alt birlikte: 30 birim/sn gizlilik önceliği.
7. Alt basılıyken Shift'i bırakma: gizlilik sürer.
8. Shift basılıyken Alt'ı bırakma: koşma sürer.
9. Pencere odağı kaybı: hareket ve mod Normal/nötr duruma döner.
10. Teşhis paneli doğru mod ve çarpanı gösterir.
11. Çapraz koşma ve çapraz gizlilikte yön normalizasyonu korunur.
12. 30/60/120 FPS altında aynı tick-input dizisi aynı sonucu üretir.

## 9. Hata davranışı ve uyumluluk

- Geçersiz mod/çarpan sessizce varsayılana çevrilmez; giriş doğrulamasında reddedilir.
- Eski MovementIntent ve MovementState constructor çağrıları Normal varsayılanıyla çalışır.
- Eski MovementConfig(max_speed=...) çağrısı varsayılan çarpanları alır.
- Pygame focus loss nötr intent üretir; modifier keydown/keyup geçmişi tutulmaz.
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
