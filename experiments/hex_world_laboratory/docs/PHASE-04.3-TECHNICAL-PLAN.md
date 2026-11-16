# Aşama 4.3 — Canonical Tick Sözleşmesi ve Demo Tick Pump Teknik Planı

**Belge türü:** Alt aşama teknik mimari ve uygulama planı  
**Proje:** Eldoria — Hex World Laboratory  
**Çalışma dalı:** `experiment/hex-world-laboratory`  
**Tarih:** 16 Kasım 2026  
**Durum:** KULLANICI ONAYI BEKLİYOR  
**Ön koşullar:** Aşama 4 genel planı ve revize edilmiş Aşama 4 teknik mimari planı onaylandı; Aşama 4.1 ve 4.2 tamamlandı.

---

## 1. Amaç

Aşama 4.3'ün amacı, Aşama 4.2'de tamamlanan `MovementIntegrator` ile dışarıdan gelen canonical simülasyon tick'leri arasında açık ve test edilebilir bir sözleşme kurmak; laboratuvar prototipini gerçek zamanlı çalıştırmak için yalnızca demo katmanında kullanılacak bir tick pump oluşturmaktır.

Bu alt aşama sonunda:

1. Hareket, dışarıdan verilen her ardışık simülasyon tick'i için tam bir kez hesaplanacaktır.
2. Bir hareket tick'inin süresi sabit olarak `1 / 60` saniye olacaktır.
3. Yinelenen, geriye giden veya atlanan tick kimlikleri sessizce kabul edilmeyecektir.
4. Render FPS'i ile simülasyon tick sayısı birbirinden ayrılacaktır.
5. Demo döngüsü bir karede en fazla 8 tick işleyebilecek; kalan zaman/tick borcunu silmeden sonraki karelere taşıyacaktır.
6. Hareket çekirdeği kendi gerçek zaman saatini, tick üreticisini veya accumulator'ını edinmeyecektir.

Bu aşama bir görsel hareket demosu veya klavye adaptörü geliştirme aşaması değildir. Sadece tick yürütüm sözleşmesi ve onu laboratuvarda sınamak için gereken küçük demo zaman köprüsü ele alınır.

## 2. Mevcut depo ve mimari durumu

Uygulama öncesi laboratuvar dalı incelendi:

- Dal HEAD: `190a4b6b9b015cc2799ce531b5bd74f0966840cf`
- Aşama 4.2 hareket çekirdeği: `movement/integrator.py`
- Mevcut hareket veri sözleşmeleri: `MovementState`, `MovementIntent`, `MovementConfig`, `Vector2`, `WorldPoint`
- `simulation/` dizini mevcut; henüz hareket tick sürücüsü içermiyor.
- Laboratuvar kökünde mevcut Pygame kabuğu `app.py` bulunuyor.
- `application/` paketi henüz bulunmuyor; demo zaman köprüsü için yeni ve ayrı bir paket olarak oluşturulabilir.

Aşama 4.2'nin saf Python integratörü korunacaktır. Mevcut geometri, dünya, harita ve persistence API'lerinde değişiklik yapılmayacaktır.

## 3. Sabit mimari kararlar

| Konu | Aşama 4.3 kararı |
|---|---|
| Canonical simülasyon hızı | 60 tick/saniye |
| Bir tick süresi | Tam sözleşme olarak `1.0 / 60.0` saniye |
| Tick kimliğinin kaynağı | Dış simülasyon orkestratörü |
| Laboratuvar tick tipi | Negatif olmayan tam sayı tick numarası |
| Hareket hesaplaması | Mevcut `MovementIntegrator.step(..., delta_time=1/60)` |
| Tick başına çağrı | Tam olarak bir başarılı hareket adımı |
| Yinelenen/atlanan tick | Açık hata; otomatik düzeltme veya sessiz atlama yok |
| Gerçek zaman ölçümü | Yalnızca demo pump içinde monotonic saat |
| Kare başına catch-up sınırı | En fazla 8 tick |
| Kalan zaman borcu | Korunur; sonraki karelere aktarılır |
| Ana oyun bağımlılığı | Yok; `core.time.Tick` import edilmez |
| Pygame bağımlılığı | Tick yürütüm çekirdeğinde yok; demo pump da Pygame import etmez |

### 3.1 Tick kimliği ve ardışıklık

Laboratuvar katmanı canonical `core.time.Tick` sınıfını import etmeyecektir. Ana oyunla gelecekteki adaptör, `Tick.value` değerini laboratuvar sınırına tam sayı olarak aktaracaktır.

`MovementSystem` açık bir `first_tick_number` parametresi alacaktır (varsayılan `0`). İlk başarılı çağrı bu tick numarasıyla yapılmalıdır. Her başarılı adımdan sonra beklenen tick numarası bir artar.

Örnek: İlk tick 0 ise geçerli sıra 0, 1, 2, 3 şeklindedir. 1'in iki kez gönderilmesi, 0'dan sonra 2'ye atlanması veya daha küçük bir numara verilmesi reddedilir.

Tick numarası bool, negatif veya tam sayı olmayan bir değer olamaz. Hata durumunda hareket state'i ve beklenen tick numarası değişmeden kalmalıdır.

Bu doğrulama, hareket sisteminin oyun saatini yönettiği anlamına gelmez. Sistem yalnızca kendisine teslim edilen tick sırasını doğrular; tick üretmez, gerçek zaman okumaz ve kendi başına ilerlemez.

### 3.2 Hareket sisteminin sorumluluğu

Yeni `MovementSystem`, mevcut `MovementIntegrator` üzerinde ince bir simülasyon orkestrasyon katmanı olacaktır.

Önerilen kurucu sözleşmesi:

```python
MovementSystem(
    initial_state: MovementState,
    config: MovementConfig,
    *,
    first_tick_number: int = 0,
)
```

Önerilen adım sözleşmesi:

```python
step(tick_number: int, intent: MovementIntent) -> MovementState
```

Sorumlulukları:

1. Tick numarasının beklenen sırada olduğunu doğrulamak.
2. Hareket niyetinin geçerli tipte olduğunu doğrulamak.
3. Integrator'ı sabit `1 / 60` saniye ile çağırmak.
4. Hesaplama başarılı olduktan sonra yeni state'i ve sıradaki tick bilgisini atomik biçimde kabul etmek.
5. Yeni değişmez `MovementState` nesnesini döndürmek.

Sistemin güncel state'i salt okunur bir özellik üzerinden sunulabilir. Dış katmanların state'i doğrudan değiştirmesine izin verilmez. Geçersiz çağrı, sistemin mevcut state'ini veya tick sırasını ilerletmez.

Her tick için `MovementIntent` açıkça verilir. Bu aşamada klavye örneklemesi, tuş durumu saklama veya önceki girdiyi otomatik tekrar etme davranışı eklenmez.

### 3.3 Demo tick pump

Yeni `DemoTickPump`, yalnızca laboratuvar uygulamasının gerçek zamanlı demo döngüsünde kullanılacaktır. Üretim hareket paketinin veya ana oyunun zaman motorunun parçası değildir.

Önerilen kullanım:

- Pump oluşturulurken tick callback'i, monotonic saat sağlayıcısı ve ilk demo tick numarası verilir.
- `start()` başlangıç zamanını kaydeder.
- Her render karesinde `pump()` çağrılır.
- Pump geçen gerçek süreyi accumulator'a ekler.
- Biriken süre bir tick'e ulaştığında callback'e sıradaki tick numarası verilir.
- Tek `pump()` çağrısında en fazla 8 başarılı tick işlenir.
- Borçta kalan tam tick'ler ve kesirli süre accumulator'da korunur.
- Sonraki karede yeni süre eklenmeden de önceki borçtan tick işlenebilir.

Önerilen saat kaynağı `time.monotonic` olacaktır. Testlerde gerçek zaman beklemek yerine sahte/injected saat kullanılacaktır. Pump, Pygame import etmeyecek; render döngüsü tarafından çağrılan bağımsız bir yardımcı olacaktır.

Önerilen public davranış:

- `start()`: başlangıç saatini alır; ikinci kez başlatma açıkça reddedilir.
- `pump()`: geçen süreyi hesaplar, en fazla 8 tick callback'i çalıştırır ve tanılama bilgisini döndürür.
- `diagnostics`: toplam işlenen tick, sıradaki tick numarası, son karede işlenen tick sayısı, bekleyen tam tick sayısı ve birikmiş süre borcunu salt okunur sunar.

Pump'ta kare başına 8 sınırı sabit bir güvenlik sınırıdır. Bu aşamada ayarlanabilir performans profili veya farklı catch-up politikaları tasarlanmayacaktır.

### 3.4 Hata ve zaman borcu davranışı

- Monotonic saat değeri sonlu sayısal değer olmalıdır.
- Saatin önceki ölçüme göre geriye gitmesi reddedilir; son geçerli zaman damgası bozulmaz.
- Birikmiş süre negatif veya sonlu olmayan bir değere dönüşemez.
- Tick callback'i hata verirse hata yukarı taşınır; başarısız tick tüketilmiş sayılmaz ve zaman borcu silinmez.
- Başarılı callback sonrasında ilgili tick tüketilir, tick numarası ilerletilir ve accumulator'dan bir tick süresi düşülür.
- Uzun karede 8'den fazla tick birikirse fazlası sonraki `pump()` çağrılarına taşınır.
- Hiçbir koşulda zaman borcu sessizce sıfırlanmaz, kırpılmaz veya atılmaz.

Callback'in başarısız olabileceği durumlarda callback'in tek bir tick işlemini atomik yürütmesi beklenir. Pump, callback'in kendi içinde gerçekleştirdiği harici yan etkileri geri alamaz.

## 4. Yeni ve değişecek dosyalar

### 4.1 Üretim kodu

| Dosya | İşlem | Sorumluluk |
|---|---|---|
| `src/hex_world_lab/simulation/__init__.py` | Yeni | Simulation public API dışa aktarımı |
| `src/hex_world_lab/simulation/movement_system.py` | Yeni | Ardışık tick doğrulaması ve sabit 60 TPS hareket çağrısı |
| `src/hex_world_lab/application/__init__.py` | Yeni | Demo application yardımcıları için paket |
| `src/hex_world_lab/application/demo_tick_pump.py` | Yeni | Monotonic zaman ölçümü, accumulator, 8 tick catch-up sınırı ve borç tanılaması |

Aşama 4.2 dosyaları:
- `movement/integrator.py`
- `movement/state.py`
- `movement/intent.py`
- `movement/config.py`
- `movement/vector.py`

Bu dosyalar yalnızca zorunlu bir uyumsuzluk tespit edilirse ve kullanıcıya etki açıklanıp yeniden onay alınırsa değiştirilebilir. Normal uygulama planında değiştirilmeleri beklenmez.

### 4.2 Test dosyaları

| Dosya | Kapsam |
|---|---|
| `tests/unit/test_movement_system.py` | İlk tick, ardışık tick, tekrar, atlama, geriye gitme, geçersiz tip, sabit delta, state'in atomik korunması |
| `tests/integration/test_demo_tick_pump.py` | Sahte saatle tick üretimi, 8 tick sınırı, borç taşıma, sıfır elapsed, kesirli süre, callback hatası, saat gerilemesi |
| `tests/integration/test_movement_tick_contract.py` | Aynı tick girdisinin tek adım üretmesi; 60 tick'in 1 saniyelik simülasyon hareketi üretmesi; render çağrı sayısından bağımsızlık |

Mevcut testler değiştirilmeden tam laboratuvar test paketi regresyon için çalıştırılacaktır.

## 5. Uygulama sırası

1. Mevcut `MovementIntegrator` API'sini ve test sözleşmelerini tekrar doğrula.
2. `simulation.MovementSystem` sınıfını ekle.
3. Tick numarası doğrulama ve state atomikliği unit testlerini ekle.
4. `application.DemoTickPump` sınıfını injected monotonic saat ile ekle.
5. Catch-up, borç koruma ve hata davranışları için entegrasyon testlerini ekle.
6. Aynı simülasyon tick dizisini farklı render çağrı sıklıklarıyla çalıştıran tick sözleşmesi testini ekle.
7. Public API export'larını tamamla.
8. Tam laboratuvar pytest paketini ve CI Linux/Windows doğrulamasını çalıştır.
9. Sonuçları incele; kabul koşulları sağlanırsa Aşama 4.3 kapanış raporunu hazırla.

Bu sıra içinde klavye adaptörü, dünya/hex çözümlemesi veya görsel demo geliştirmesine başlanmaz.

## 6. Test ve kabul ölçütleri

### 6.1 MovementSystem unit testleri

- Varsayılan ilk tick 0 ile başlar.
- Farklı bir ilk tick numarası açıkça yapılandırılabilir.
- Ardışık her geçerli tick tam bir integrator adımı üretir.
- Aynı tick'in ikinci kez verilmesi reddedilir.
- Tick atlanması reddedilir.
- Geriye giden tick reddedilir.
- Bool, negatif, float ve metin tick numarası reddedilir.
- Geçersiz intent reddedilir.
- Başarılı her adımda delta tam olarak `1 / 60` olur.
- Bir hata sonrasında state ve beklenen tick numarası değişmez.
- Hareket sisteminin kendi saat veya gerçek zaman accumulator'ı yoktur.

### 6.2 DemoTickPump entegrasyon testleri

- 1 saniyelik toplam gerçek zaman, 60 tick borcu üretir.
- Tek karede en fazla 8 tick callback'i çalışır.
- 1 saniyelik borç ilk çağrıda 8 tick işlenince kaybolmaz; 52 tam tick borcu kalır.
- Yeni zaman eklenmeyen sonraki çağrılar da kalan borcu işlemeye devam eder.
- Borç tamamen boşaldığında yalnızca kesirli süre kalır.
- Bir tick'ten kısa süre henüz callback üretmez.
- Parçalı frame sürelerinin toplamı doğru tick sayısını üretir.
- Callback hatasında başarısız tick tüketilmez ve borç korunur.
- Saatin geriye gitmesi ve geçersiz saat değeri reddedilir.
- Testler gerçek bekleme veya işletim sistemi zamanlamasına bağlı değildir.

### 6.3 Render FPS bağımsızlığı

Sahte saat kullanılarak aynı toplam 1 saniyelik zaman:
- 30 render FPS,
- 60 render FPS,
- 120 render FPS

ile pump'a verilir. Her senaryoda aynı sıralı 60 tick kimliği üretilmeli ve aynı başlangıç state'i/sabit intent ile aynı son hareket state'i elde edilmelidir.

Bu test, gerçek klavye girdisinin farklı render karelerinde örneklenmesiyle ilgili input-latency garantisi vermez. Yalnızca aynı tick girdilerinin render FPS'ten bağımsız işlendiğini kanıtlar.

### 6.4 Regresyon ve CI

- Tam laboratuvar pytest paketi.
- Aşama 2 geometri testleri.
- Aşama 3 world ve persistence testleri.
- Aşama 4.1 ve 4.2 hareket testleri.
- GitHub Actions Core quality Linux ve Windows job'ları.
- Hareket ve simulation paketlerinin Pygame import etmediğine dair mimari kontrol.

## 7. Performans ve kaynak kullanımı

- Pump her render karesinde yalnızca tek saat ölçümü ve gerekli accumulator hesabını yapar.
- Her simülasyon tick'inde tek hareket integrator çağrısı yapılır.
- Catch-up üst sınırı tek render karesindeki hareket güncelleme sayısını 8 ile sınırlar.
- Kalan borç saklanır; performans sorunu varsa diagnostics üzerinden görünür.
- Tick borcu büyüdüğünde zaman atmak yerine borç miktarı raporlanır.
- Bu aşamada binlerce aktör benchmark'ı yapılmaz; çoklu aktör performans ölçümü sonraki kapsam değerlendirmesine bırakılır.
- Sabit FPS veya donanım performansı garantisi verilmez.

## 8. Kapsam dışı

Aşama 4.3'te aşağıdakiler yapılmayacaktır:

- Pygame klavye adaptörü ve WASD/ok tuşları (Aşama 4.4).
- World/Map context ve axial hücre çözümleme (Aşama 4.5).
- Görsel hareket prototipi ve kamera/render değişiklikleri (Aşama 4.6).
- Çarpışma, collider, engel, duvar, pathfinding veya harita sınırında durma.
- İvme, sürtünme, atalet veya hız eğrileri.
- Ana oyunun `core.time.Tick` veya `SimulationRuntime` kodunda değişiklik.
- Laboratuvara ana oyun bağımlılığı eklemek.
- Ana oyuna, `main` dalına veya `demo_eldoria` dalına entegrasyon.
- Offline progression, çoklu harita, NPC veya çoklu aktör simülasyonu.
- Zaman borcunu atma/kırpma politikası.

## 9. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| Render FPS'in hareket hızını etkilemesi | Farklı makinelerde farklı simülasyon sonucu | Sabit 1/60 tick ve aynı tick dizisiyle FPS testleri |
| Aynı tick'in iki kez işlenmesi | Fazladan hareket | Ardışık tick doğrulaması |
| Tick atlanması | Simülasyon zamanının kaybı | Beklenen tick numarasından sapmayı reddetme |
| Uzun karede çok fazla catch-up işi | Tek karede CPU sıçraması | Kare başına en fazla 8 başarılı tick |
| Catch-up sınırında zamanın kaybolması | Hareketin yavaşlaması ve deterministik fark | Borcu accumulator'da koruma ve diagnostics |
| Testlerin gerçek saate bağlı olması | CI kararsızlığı | Injected fake monotonic clock |
| Callback hatasında tick'in yanlış tüketilmesi | Hareket ve tick sırasının ayrışması | Başarılı callback sonrasında tüketim; hata durumunda borcu koruma |
| Demo zaman kodunun core'a sızması | Mimari bağımlılık ve test zorluğu | Pump'ı application katmanında izole etme |

## 10. Beklenen teslimatlar

1. `MovementSystem`: dış tick numarasını doğrulayan, her geçerli tick'te integrator'ı 1/60 saniye ile bir kez çalıştıran sınıf.
2. `DemoTickPump`: injected monotonic saat, accumulator, 8 tick/kare sınırı ve borç diagnostics'i.
3. Tick sırası, sabit delta, hata atomikliği ve zaman borcu testleri.
4. 30/60/120 render FPS eşdeğerliği testi.
5. Tam laboratuvar test ve Linux/Windows CI sonuçları.
6. Aşama 4.3 kapanış raporu.

## 11. Kabul kapısı

Aşama 4.3 ancak aşağıdaki koşulların tamamı sağlandığında tamamlanmış sayılır:

- [ ] Hareket sistemi tick üretmiyor; yalnızca dış tick numarasını doğruluyor.
- [ ] Ardışık geçerli her tick'te tam bir 1/60 saniyelik hareket adımı çalışıyor.
- [ ] Yinelenen, atlanan ve geriye giden tick'ler reddediliyor.
- [ ] Hatalı adım state veya tick sırasını değiştirmiyor.
- [ ] Demo pump kare başına en fazla 8 tick işliyor.
- [ ] Kalan zaman borcu atılmadan korunuyor ve ölçülebiliyor.
- [ ] Sahte saat testleri gerçek zaman beklemeden geçiyor.
- [ ] 30/60/120 FPS testleri aynı tick dizisi ve aynı son state'i doğruluyor.
- [ ] Mevcut tüm laboratuvar testleri geçiyor.
- [ ] Linux ve Windows CI job'ları başarılı.
- [ ] Kapanış raporu laboratuvar dalına eklenip doğrulanıyor.

## 12. Onay ve değişiklik kontrolü

Bu belge yalnızca Aşama 4.3 teknik planıdır. Kod, test, demo veya mimari değişiklik yetkisi vermez.

Uygulama başlamadan önce kullanıcı onayı gereken noktalar:

1. `MovementSystem` sınıfının `simulation` katmanında yer alması ve dışarıdan verilen tick kimliklerini ardışık doğrulaması.
2. İlk tick numarasının açık parametre olması ve varsayılan olarak 0 kabul edilmesi.
3. Tick başına mevcut integrator'ın sabit `1 / 60` saniye ile bir kez çağrılması.
4. Demo pump'ın yalnızca `application` katmanında, injected `time.monotonic` sağlayıcısıyla çalışması.
5. Demo pump'ın kare başına en fazla 8 tick işlemesi ve kalan borcu hiçbir zaman düşürmemesi.
6. Tick callback'i başarısız olduğunda ilgili tick'in tüketilmemesi ve hatanın yukarı taşınması.
7. Bu belgede tanımlanan dosya sınırları, testler ve kapsam dışı maddeler.

Onay verilirse yalnızca bu alt aşamanın kapsamı uygulanacaktır. Aşama 4.4'e geçiş için ayrıca teknik plan ve kullanıcı onayı gerekir.

**Durum:** TEKNİK PLAN SUNULDU — KULLANICI ONAYI BEKLENİYOR.
