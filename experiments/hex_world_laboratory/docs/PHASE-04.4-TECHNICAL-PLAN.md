# Aşama 4.4 — Pygame Klavye Adaptörü Teknik Mimari Planı

> **Belge türü:** Teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK PLAN — KULLANICI ONAYI BEKLİYOR  
> **Ön koşul:** Aşama 4.4 genel planı kullanıcı tarafından onaylandı.

---

## 1. Teknik hedef

Pygame klavye durumunu, mevcut cihazdan bağımsız `MovementIntent` sözleşmesine dönüştüren bir adaptör oluşturulacaktır. Adaptör, mevcut `DemoTickPump` ve `MovementSystem` akışına bağlanacak; hareket çekirdeği değişmeden kalacaktır.

Bu alt aşamada:
- Pygame klavye durumundan WASD ve ok tuşları okunur.
- Her simülasyon tick'inde güncel hareket niyeti örneklenir.
- Her tick'e ait niyet `MovementSystem.step(tick_number, intent)` metoduna aktarılır.
- Pencere odağı kaybolduğunda hareket niyeti nötrlenir.
- Uygulama kabuğu gerçek klavye adaptörünü kullanır; headless testlerde klavye sağlayıcısı enjekte edilir.

Tam hareket sahnesi, oyuncu çizimi, kamera ve hex dünya entegrasyonu bu aşamanın dışında kalır.

## 2. Mevcut kod tabanıyla uyum

İncelenen mevcut dosyalar:

| Dosya | Mevcut durum | Kullanım |
|---|---|---|
| `src/hex_world_lab/movement/intent.py` | Değişmez `MovementIntent(direction: Vector2)` | Adaptörün çıktısı |
| `src/hex_world_lab/movement/vector.py` | Matematiksel eksenleri kullanan `Vector2`; +X sağ, +Y yukarı | Ham yön bileşenleri |
| `src/hex_world_lab/movement/integrator.py` | Yön normalizasyonu ve konum güncellemesi | Değişmeden kalır |
| `src/hex_world_lab/simulation/movement_system.py` | Ardışık tick başına tek hareket adımı | Intent tüketicisi |
| `src/hex_world_lab/application/demo_tick_pump.py` | 60 TPS, pump başına en fazla 8 tick, borç kaybetmez | Tick callback orkestrasyonu |
| `src/hex_world_lab/app.py` | Minimal Pygame event/render döngüsü | Adaptör ve tick pump bağlantısı |
| `src/hex_world_lab/config.py` | Pencere ayarları | Bu aşamada yalnız gerekirse küçük yapılandırma eklenir |

Yeni input katmanı mevcut hareket paketinin içine konmayacaktır. Böylece `movement` paketi Pygame'den habersiz kalır.

## 3. Önerilen paket ve dosya yapısı

Yeni üretim dosyası:

```text
src/hex_world_lab/input/
    __init__.py
    pygame_keyboard.py
```

Test dosyaları:

```text
tests/unit/
    test_pygame_keyboard.py

tests/integration/
    test_keyboard_movement_flow.py
    test_keyboard_focus_lifecycle.py
```

Gerekirse mevcut uygulama yaşam döngüsü testi güncellenecektir:
- `tests/integration/test_app_lifecycle.py`

Yeni harici bağımlılık eklenmeyecektir. Pygame zaten laboratuvarın mevcut çalışma bağımlılığıdır.

## 4. Adaptör API sözleşmesi

### 4.1 Sınıf

Önerilen sınıf:

`PygameKeyboardAdapter`

Modül:

`hex_world_lab.input.pygame_keyboard`

Public API:

- `__init__(key_state_provider=None)`
- `handle_event(event) -> None`
- `read_intent() -> MovementIntent`
- `focused -> bool` (salt okunur özellik)

### 4.2 Klavye durumu sağlayıcısı

Varsayılan sağlayıcı `pygame.key.get_pressed` olacaktır.

Test edilebilirlik için constructor'a isteğe bağlı bir `key_state_provider` callable enjekte edilecektir. Sağlayıcı her çağrıldığında tuş kodundan basılı durumuna erişilebilen bir nesne döndürmelidir. Üretimde Pygame'in `ScancodeWrapper` nesnesi bu sözleşmeyi karşılar; testlerde aynı indeksleme davranışını sağlayan küçük bir dict/fake nesne kullanılabilir.

Sağlayıcı yalnızca `read_intent()` çağrısında örneklenir. Böylece adaptör eski bir tuş snapshot'ını kendi içinde saklamaz.

Sağlayıcıdan dönen durumun beklenen tuş kodlarını okuyamaması bir programlama/entegrasyon hatasıdır; sessizce yanlış yön üretmek yerine hata görünür olmalıdır.

### 4.3 Tuş eşlemesi

Pygame sabitleri:

| Yön bileşeni | Birinci tuş | İkinci tuş |
|---|---|---|
| X pozitif | `pygame.K_d` | `pygame.K_RIGHT` |
| X negatif | `pygame.K_a` | `pygame.K_LEFT` |
| Y pozitif | `pygame.K_w` | `pygame.K_UP` |
| Y negatif | `pygame.K_s` | `pygame.K_DOWN` |

Her eksen bileşeni Boolean yönlerin farkı olarak hesaplanır:

- `x = int(right_pressed) - int(left_pressed)`
- `y = int(up_pressed) - int(down_pressed)`

Bu yöntem:
- Aynı yönün WASD ve ok tuşuyla birlikte basılmasında bileşeni +1/-1 olarak tutar.
- Aynı eksende zıt yönlerin birlikte basılmasını sıfırlar.
- Çapraz ham vektörü (-1, 0, +1) bileşenleriyle üretir.
- Normalizasyonu adaptörde yapmaz; mevcut integratörün sorumluluğuna bırakır.

### 4.4 Odak yönetimi

Adaptör başlangıçta odaklı kabul edilir. `handle_event(event)` şu Pygame 2 olaylarını işler:

- `pygame.WINDOWFOCUSLOST`: `focused = False`
- `pygame.WINDOWFOCUSGAINED`: `focused = True`

Odak yokken `read_intent()` klavye sağlayıcısını çağırmadan sıfır yönlü `MovementIntent` döndürür. Bu, eski klavye snapshot'ı veya kaçırılmış KEYUP olayı nedeniyle karakterin hareket etmeye devam etmesini engeller.

Odak yeniden kazanıldığında bir sonraki tick'te güncel klavye durumu yeniden okunur. Adaptör tuş basılı geçmişi tutmadığı için eski bir hareket niyeti otomatik olarak devam ettirilmez.

Pencere kapatma (`pygame.QUIT`) adaptörün değil uygulama yaşam döngüsünün sorumluluğudur.

Not: Bu aşamada Pygame 2'nin `WINDOWFOCUSLOST` ve `WINDOWFOCUSGAINED` olayları hedeflenir. Eski `ACTIVEEVENT` uyumluluk yolu eklenmeyecektir; destek gereksinimi ortaya çıkarsa ayrıca değerlendirilir.

## 5. Tick ve event örnekleme sırası

Uygulama döngüsünde sıra şu şekilde olacaktır:

1. Her render karesinde `pygame.event.get()` ile event kuyruğu tüketilir.
2. Her event adaptöre iletilir; QUIT olayı uygulamayı kapatır.
3. Demo tick pump `pump()` ile çağrılır.
4. Pump o karede sıfır veya daha fazla (en fazla 8) tick işler.
5. Her tick callback'i içinde adaptörün `read_intent()` metodu çağrılır.
6. Elde edilen intent aynı tick numarasıyla `MovementSystem.step(tick_number, intent)` metoduna aktarılır.
7. Render aşaması yalnızca mevcut movement state'ini okur; bu aşamada karakter çizimi eklenmez.

Bu sıra, event kuyruğunun render karesi başına bir kez işlenmesini ve tuş durumunun her simülasyon tick'inde yeniden örneklenmesini sağlar. Bir pump çağrısı birden fazla tick işlerse her tick için ayrı `read_intent()` çağrısı yapılır. Aynı fiziksel klavye durumu bu tick'lerde tekrar okunabilir; bu beklenen davranıştır.

Pump'ın 8 tick sınırı, hareket çekirdeğinin değil mevcut demo zaman pompasının sorumluluğudur. Biriken zaman borcu korunur.

## 6. LabApplication bağlantısı

Mevcut `LabApplication` sınıfı yalnızca minimum ölçüde genişletilecektir:

- Pygame başlatıldıktan sonra `PygameKeyboardAdapter` oluşturulur.
- Başlangıç hareket state'i `WorldPoint(0, 0)` ve mevcut `MovementConfig` ile oluşturulur.
- `MovementSystem`, laboratuvar demosu için belirlenen sabit bir başlangıç hızıyla kurulur. Hız değeri uygulama yapılandırmasında tek bir açık varsayılan olarak tanımlanır; yeni hız modeli veya kullanıcı ayarı oluşturulmaz.
- `DemoTickPump` callback'i adaptörden güncel intent alıp MovementSystem'e iletir.
- Pump, ana Pygame döngüsü başlamadan önce `start()` ile başlatılır ve her frame `pump()` edilir.
- Event'ler pump çağrısından önce adaptöre aktarılır.
- Mevcut QUIT ve `max_frames` test davranışları korunur.
- Uygulama kapanırken mevcut `pygame.quit()` temizliği sürdürülür.

Bu bağlantı hareket sisteminin gerçekten klavye girdisi tükettiğini doğrular; ekranda oyuncu veya hex harita çizmez. Hareket state'ine erişim için yeni genel uygulama API'si eklemek zorunlu görülmedikçe private state dışarı açılmaz.

Başlangıç hızı için önerilen değer: **60 dünya birimi/saniye**. Bu yalnızca laboratuvar uygulamasının test edilebilir varsayılanıdır; nihai oyun karakter hızı kararı değildir. Dünya birimi mevcut `HexLayout.radius` ölçeğine bağlı olduğundan Aşama 4.6 prototipinde tekrar değerlendirilebilir.

## 7. Bağımlılık kuralları

İzin verilen yön:

```text
input.pygame_keyboard ---> movement.intent / movement.vector
input.pygame_keyboard ---> pygame

app.py ---> input adapter
app.py ---> application.DemoTickPump
app.py ---> simulation.MovementSystem
app.py ---> geometry.WorldPoint
```

Yasaklanan bağımlılıklar:

- `movement` → `pygame`
- `simulation` → `pygame`
- `movement` → `input`
- `input` → `simulation` veya `MovementSystem`
- Laboratuvar paketleri → ana oyun `core` modülleri

Adaptör yalnızca niyet üretir; hareket state'ine, tick sayacına veya dünya modeline erişmez.

## 8. Test planı

### 8.1 Unit test — tuş eşlemesi

`tests/unit/test_pygame_keyboard.py`:

- W, A, S, D tek tek doğru yönü üretir.
- Yukarı, sol, aşağı, sağ ok tuşları tek tek doğru yönü üretir.
- WASD ve ok tuşları aynı yön için birlikte basıldığında değer iki katına çıkmaz.
- W + D, W + A, S + D, S + A çapraz ham vektörleri doğru üretilir.
- W + S ve A + D aynı eksende sıfır üretir.
- Hiç tuş basılı değilken sıfır intent döner.
- Aynı yön tuşu basılı kaldığında ardışık okumalar aynı intent'i verir.
- Tuş bırakıldığında sonraki okuma yeni durumu yansıtır.
- Bir tuşun bırakılması diğer eksendeki basılı tuşu etkilemez.
- Sağlayıcı her okumada çağrılır; eski snapshot cache edilmez.
- Sağlayıcının bozuk/eksik veri döndürmesi sessizce yutulmaz.

### 8.2 Unit test — odak

- Başlangıçta adaptör odaklıdır.
- WINDOWFOCUSLOST sonrası read_intent sıfır döndürür.
- Odak yokken key_state_provider çağrılmaz.
- WINDOWFOCUSGAINED sonrası güncel klavye durumu tekrar okunur.
- Odak kaybı ve kazanımı tekrarlı işlendiğinde durum deterministiktir.

### 8.3 Integration test — tick akışı

`tests/integration/test_keyboard_movement_flow.py`:

- Fake monotonic clock ile `DemoTickPump` başlatılır.
- Fake klavye sağlayıcısı belirli yönleri raporlar.
- Pump'ın her callback'inde adaptör okunur ve MovementSystem'e intent iletilir.
- Bir saniyelik simülasyon zamanı 60 ardışık hareket tick'i üretir.
- Her tick'te güncel input örneklenir.
- İlk tick'lerde sağ, sonraki tick'lerde nötr girdi verildiğinde konum yalnızca sağ yön verilen tick'lerde ilerler.
- Pump'ın 8 tick/frame sınırı ve kalan borç davranışı mevcut testlerle birlikte korunur.

### 8.4 Integration test — pencere odağı

`tests/integration/test_keyboard_focus_lifecycle.py`:

- Odak kaybı event'i adaptöre iletildiğinde sonraki tick'ler nötr intent tüketir.
- Odak kazanımı event'inden sonra yeni fiziksel tuş durumu geçerli olur.
- Bu senaryo Pygame penceresi açmadan event nesneleri ve fake provider ile test edilir.

### 8.5 Uygulama yaşam döngüsü

Mevcut headless `test_app_lifecycle.py` korunur ve gerekiyorsa güncellenir:
- Dummy SDL sürücüsüyle uygulama bir frame çalışıp kapanır.
- Tick pump ve adaptör kurulumu uygulama başlatmayı bozmaz.
- QUIT ve `max_frames` kapanış davranışları sürer.
- Pencere odağı event'leri doğru şekilde adaptöre iletilir.

### 8.6 Regresyon ve CI

- Tüm laboratuvar testleri `python -m pytest -q` ile çalışır.
- Hareket, tick pump, geometri ve world testleri gerilemez.
- CI Core quality workflow Linux ve Windows job'ları başarılı olmalıdır.
- Testler gerçek klavye veya görünür masaüstü penceresi gerektirmez.

## 9. Hata ve kenar durumları

- Adaptör yanlış tipte event alırsa olay tipini okumak mümkün olduğu sürece etkisiz biçimde yok sayar; Pygame event nesneleri dışındaki hatalı sağlayıcı sözleşmeleri açık hata üretir.
- Pencere odağı yoksa her durumda nötr intent üretilir.
- Aynı eksende zıt yönler sıfırlanır; “son basılan tuş kazanır” davranışı uygulanmaz.
- WASD ve ok tuşlarının eşdeğer olması nedeniyle ikisinin birlikte basılması daha yüksek hız üretmez.
- Klavye repeat ayarı açılmaz ve KEYDOWN sayısı hareket hızına etki etmez.
- Tick pump callback hatası verirse mevcut DemoTickPump sözleşmesi gereği başarısız tick tüketilmez; MovementSystem'in atomik state/tick davranışı korunur.

## 10. Performans ve kaynak kullanımı

- Adaptör her örneklemede yalnızca sekiz tuş durumunu okur.
- Klavye örneklemesi için thread, timer veya ayrı accumulator oluşturulmaz.
- Pygame event kuyruğu render döngüsünde bir kez tüketilir.
- Harita, hücre veya NPC verisi taranmaz.
- Yeni harici bağımlılık eklenmez.
- Bu aşamada ayrı bir mikrobenchmark zorunlu değildir; klavye adaptörünün maliyeti küçük ve sabit sayıda tuş okumasıyla sınırlıdır. Ölçülmemiş performans garantisi verilmeyecektir.

## 11. Uygulama sırası ve dosya değişiklikleri

1. Dalın güncel HEAD ve ilgili dosya blob SHA'larını tekrar doğrula.
2. `input/__init__.py` ve `input/pygame_keyboard.py` dosyalarını ekle.
3. Adaptörün unit testlerini ekle.
4. Pump → adapter → MovementSystem entegrasyon testlerini ekle.
5. `app.py` dosyasını yalnızca event forwarding, tick callback ve pump bağlantısı için güncelle.
6. Gerekirse `config.py` içinde laboratuvar başlangıç hareket hızını tek bir sabit yapılandırma alanı olarak tanımla.
7. Uygulama lifecycle testini güncelle.
8. Hedefli testleri, ardından tam test paketini çalıştır.
9. GitHub Actions Linux/Windows sonuçlarını doğrula.
10. Kapanış raporunu oluştur, commit et ve GitHub üzerinden tekrar oku.

Beklenen değişiklik sınırı:
- Yeni: `src/hex_world_lab/input/__init__.py`
- Yeni: `src/hex_world_lab/input/pygame_keyboard.py`
- Değişebilir: `src/hex_world_lab/app.py`
- Gerekirse değişebilir: `src/hex_world_lab/config.py`
- Yeni: `tests/unit/test_pygame_keyboard.py`
- Yeni: `tests/integration/test_keyboard_movement_flow.py`
- Yeni: `tests/integration/test_keyboard_focus_lifecycle.py`
- Gerekirse değişebilir: `tests/integration/test_app_lifecycle.py`
- Yeni kapanış belgesi: `reports/PHASE-04.4-CLOSURE-REPORT.md`

Bu liste dışındaki dosyalara ihtiyaç doğarsa uygulama durdurulup kapsam etkisi kullanıcıya sunulacaktır.

## 12. Riskler ve azaltımlar

| Risk | Azaltım |
|---|---|
| Pygame ScancodeWrapper test edilebilirliği | Callable provider enjeksiyonu ve dict/fake tabanlı unit test |
| Y ekseni tersliği | Matematiksel +Y yukarı eşlemesi ve tekil yön testleri |
| Tuşların çift sayılması | Boolean OR ile yön durumu, eksen farkı |
| Odak kaybında stuck input | Focus lost durumunda provider okumadan nötr intent |
| Event/tick örnekleme sırası | Her frame event pump önce, tick pump sonra |
| Pump birden fazla tick işlediğinde eski input | Her callback'te read_intent çağrısı |
| Uygulama kabuğunda kapsam genişlemesi | Çizim, kamera ve sahne eklememek |
| Pygame bağımlılığının çekirdeğe sızması | Import sınırı testleri ve dosya mimarisi denetimi |

## 13. Kabul ölçütleri

- [ ] WASD ve dört ok tuşu doğru matematiksel yönleri üretir.
- [ ] Aynı yönün eşdeğer tuşları bileşeni iki katına çıkarmaz.
- [ ] Aynı eksendeki zıt tuşlar birbirini götürür.
- [ ] Dört çapraz kombinasyon doğru ham vektörü üretir.
- [ ] Adaptör normalizasyon veya hareket hesabı yapmaz.
- [ ] Tuş bırakma sonraki tick'te nötr veya kalan yönü üretir.
- [ ] Her simülasyon tick'inde klavye sağlayıcısı yeniden örneklenir.
- [ ] Focus lost nötr girdi üretir ve provider'ı çağırmaz.
- [ ] Focus gained sonrası güncel fiziksel durum tekrar okunur.
- [ ] DemoTickPump → adapter → MovementSystem akışı test edilir.
- [ ] LabApplication headless yaşam döngüsü testi başarılıdır.
- [ ] Movement ve Simulation paketleri Pygame import etmez.
- [ ] Tam laboratuvar test paketi başarılıdır.
- [ ] Linux ve Windows CI başarılıdır.
- [ ] Kapanış raporu laboratuvar dalında commit edilip doğrulanır.

## 14. Onay ve dal güvenliği

Bu belge Aşama 4.4 teknik mimari planıdır. Kullanıcı açıkça onaylamadan kod veya test dosyalarında değişiklik yapılmayacaktır.

Uygulama yalnızca `experiment/hex-world-laboratory` dalında yürütülecektir. `main` ve `demo_eldoria` dallarına yazma, merge, cherry-pick, rebase, reset veya geçmiş değiştirme işlemi yapılmayacaktır.

**Mevcut durum:** Teknik mimari planı kullanıcı onayı bekliyor. Kod uygulaması başlamamıştır.
