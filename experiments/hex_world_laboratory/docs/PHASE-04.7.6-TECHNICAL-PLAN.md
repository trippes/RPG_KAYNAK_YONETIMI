# Aşama 4.7.6 — Son Teknik Doğrulama ve Kapanış Planı

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Ön koşul:** Aşama 4.7.5 teknik kapanışı tamamlandı.  
> **Durum:** TEKNİK DOĞRULAMA TAMAMLANDI — KAPATILDI; Aşama 4 masaüstü kabulini bekliyor

## 1. Amaç

Aşama 4.7.6'nın amacı, Aşama 4.1–4.7.5 boyunca oluşturulan sürekli hareket sistemini son kez teknik açıdan denetlemek; hareket modları, zaman tutarlılığı, hex hücre entegrasyonu, odak yaşam döngüsü, mimari bağımlılık sınırları ve performans ölçümünü tek bir doğrulama kapısında birleştirmektir.

Bu alt aşama **teknik kapanış** aşamasıdır. Kullanıcının kararı doğrultusunda gerçek bilgisayardaki Pygame masaüstü kabulü burada yapılmayacak; Aşama 4 genel kapanışında, tüm teknik işler tamamlandıktan sonra toplu olarak yürütülecektir. Bu nedenle Aşama 4.7.6'nın kapanması, Aşama 4'ün genel olarak kapandığı anlamına gelmez.

## 2. Mevcut ve doğrulanmış durum

Aşama 4.7.5 için:
- Teşhis paneli `NORMAL`, `RUNNING`, `STEALTH` modlarını gösterir.
- Mod çarpanı ve teorik mod hızı, yapılandırılmış `MovementConfig` üzerinden hesaplanır.
- Gerçek Velocity ile teorik mod hızı ayrı gösterilir.
- Teşhis çizimi salt okunur kalır.
- 40 birim/s temel hız için 40 / 60 / 20 birim/s değerleri test edilir.
- Alt toggle, Shift önceliği ve odak kaybı senaryoları otomatik test kapsamındadır.
- Laboratuvar CI: 504 test başarılı.
- Son kapanış commit'i `257524130869156e3b54dc4dc8002276ebeeb85e` için Laboratory CI ve Core Quality Linux/Windows başarılıdır.

Mevcut benchmark aracı:
`benchmarks/benchmark_movement_demo.py`

Bu araç 1, 10, 100 ve 1.000 aktör için hareket + hex hücre çözümleme maliyetini ölçer; ısınma ve ölçüm partileri, ortalama batch süresi, P95 batch süresi, aktör-tick başına ortalama süre ve Python/platform/işlemci bilgisini raporlar. Mevcut CI workflow'u bu hareket benchmark'ını henüz çalıştırmamakta; yalnızca harita ve runtime persistence benchmark'larını çalıştırmaktadır.

## 3. Kapsam

### 3.1 Hareket ve giriş regresyonu

Aşağıdaki mevcut test grupları hedefli olarak çalıştırılacak ve sonuçları incelenecektir:

- `tests/unit/test_movement_mode.py`
- `tests/unit/test_movement_mode_profiles.py`
- `tests/unit/test_movement_integrator.py`
- `tests/unit/test_movement_system.py`
- `tests/unit/test_pygame_keyboard_modes.py`
- `tests/integration/test_movement_demo_flow.py`
- `tests/integration/test_movement_demo_fps.py`
- `tests/integration/test_movement_demo_render.py`
- `tests/integration/test_keyboard_focus_lifecycle.py`
- `tests/integration/test_movement_tick_contract.py`
- `tests/integration/test_movement_world_integration.py`
- `tests/integration/test_movement_demo_lifecycle.py`

Özellikle aşağıdaki davranışlar birlikte değerlendirilir:
- Normal 1.0x, Shift basılıyken Koşma 1.5x, Alt toggle açıkken Gizlilik 0.5x.
- Gizlilik > Koşma > Normal önceliği.
- Alt basılı tutma, sol/sağ Alt örtüşmesi ve Alt toggle kapatıldığında Shift'in hâlâ basılı olması.
- Odak kaybında yön ve mod sıfırlama; odak kazanımında sahte Alt basışı oluşmaması.
- Mod değişimleri sırasında fiziksel WorldPoint sürekliliği ve doğru hücre çözümlemesi.
- 30/60/120 render FPS altında aynı tick-indexed girdi dizisinin aynı state ve hücre sonucunu üretmesi.
- Render/diagnostics çiziminin state, tick ve tracker verisini değiştirmemesi.

### 3.2 Tam regresyon ve CI

1. Laboratuvar kökünde tam test paketi: `python -m pytest -q`.
2. Hex World Laboratory CI başarılı olmalı.
3. Core Quality Linux `verify` işi başarılı olmalı.
4. Core Quality Windows `verify-windows` işi başarılı olmalı.
5. Persistence benchmark adımları mevcut CI sözleşmesine göre başarılı olmalı.

### 3.3 Hareket benchmark'ı

Mevcut `benchmarks/benchmark_movement_demo.py` aracı değişmeden kullanılacaktır.

CI iş akışına şu gözlemsel adım eklenecektir:
`python benchmarks/benchmark_movement_demo.py`

- 1 / 10 / 100 / 1.000 aktör sonuçları CI logunda görünür olmalıdır.
- Benchmark için keyfî bir FPS veya süre eşiği konulmayacaktır.
- Ortalama ve P95 değerleri, Python sürümü, işletim sistemi ve işlemci bilgisiyle rapora aktarılır.
- Sonuçlar yalnızca çalıştırıldığı CI ortamı için geçerlidir; kullanıcının düşük donanımlı bilgisayarında aynı performansın garanti edildiği ileri sürülmez.
- Benchmark başarısız olursa teknik neden incelenir; hareket çekirdeğinde ölçüm olmadan optimizasyon yapılmaz.

### 3.4 Mimari sınır denetimi

- `movement` çekirdeğinin Pygame import etmediği kaynak kodu ve import davranışı üzerinden doğrulanır.
- Pygame bağımlılığı input/application sınırında kalmalıdır.
- Movement çekirdeği kendi saatini, tick üretimini veya accumulator'ı yönetmemelidir.
- Hex dönüşüm matematiği yeniden yazılmamalı; mevcut geometry API'si kullanılmalıdır.
- WorldPoint authoritative fiziksel konum olarak kalmalı; hücre takibi konumu snap etmemelidir.
- Kayıtlı fakat yüklenmemiş haritalar hareket döngüsüne otomatik alınmamalıdır.

Mevcut testler bu sınırları yeterince otomatik doğrulamıyorsa, yalnızca bu kapsamı güvenceye alan küçük bir mimari test eklenebilir. Üretim mimarisi değiştirilmeyecektir.

### 3.5 Dokümantasyon ve kapanış raporları

Teknik doğrulama başarılı olursa:
- Aşama 4.7 genel planındaki eski onay bekliyor durum metni güncellenir; 4.7.5 ve 4.7.6 sonuçları işlenir.
- Aşama 4 teknik planındaki eski kullanıcı onayı bekliyor ifadesi, gerçekleşmiş onay ve uygulama durumuyla tutarlı hâle getirilir.
- Aşama 4 genel planı 4.7 hareket modlarını kapsayacak şekilde güncellenir.
- `reports/PHASE-04.7-CLOSURE-REPORT.md` oluşturulur.
- `reports/PHASE-04.7-CLOSURE-REPORT.md` hazırlanarak 4.7.1–4.7.6 kanıtları birleştirilir.
- Aşama 4 genel kapanış raporu, masaüstü kabulü yapılmadan tamamlandı olarak işaretlenmez.

## 4. Dosya değişiklik sınırı

### Güncellenmesi planlanan
- `.github/workflows/hex-world-lab-ci.yml` — yalnızca mevcut hareket benchmark'ını çalıştıran CI adımı.
- `docs/PHASE-04.7-GENERAL-PLAN.md`
- `docs/PHASE-04-TECHNICAL-PLAN.md`
- `docs/PHASE-04-GENERAL-PLAN.md`

### Yeni raporlar
- `reports/PHASE-04.7-CLOSURE-REPORT.md`
- `reports/PHASE-04.7-CLOSURE-REPORT.md`

### Koşullu test
- Gerekli görülürse yalnızca movement/Pygame bağımlılık sınırını doğrulayan küçük bir mimari test.

**Üretim hareket kodunda özellik veya refaktör değişikliği planlanmamaktadır.** Bir test mevcut davranışta gerçek kusur gösterirse, kapsam genişletilmeden önce bulgu ve etkisi kullanıcıya sunulur.

## 5. Aşama 4.7.6 kabul ölçütleri

1. Hedefli hareket, klavye, FPS, render, odak ve dünya entegrasyon testleri başarılıdır.
2. Tam laboratuvar pytest paketi başarılıdır.
3. Hex World Laboratory CI başarılıdır.
4. Core Quality Linux ve Windows işleri başarılıdır.
5. Persistence benchmark adımları başarılıdır.
6. Hareket benchmark'ı 1 / 10 / 100 / 1.000 aktör için ölçüm üretir ve ortam bilgisiyle raporlanır; keyfî performans garantisi verilmez.
7. Mimari bağımlılık sınırları doğrulanır.
8. Aşama 4.7 ve Aşama 4 dokümanları gerçekleşen durumla tutarlıdır.
9. Kapanış raporları yalnızca gerçek test/CI kanıtlarını içerir.
10. `main` ve `demo_eldoria` dalları değişmeden kalır.
11. Gerçek masaüstü kabulünün Aşama 4 genel kapanışına ertelendiği açıkça kaydedilir.

## 6. Aşama 4 genel kapanışına ertelenen masaüstü kabulü

Aşağıdaki kontroller 4.7.6 teknik kapanışının değil, Aşama 4'ün son genel kapanışının şartıdır:

- Uygulama açılışı ve 61 hücreli haritanın görünmesi.
- WASD/ok tuşları, durma, zıt yön ve çapraz hareket.
- Normal, Shift ile koşma ve Alt toggle ile gizlilik.
- Alt basılı tutma ve sol/sağ Alt örtüşmesi.
- Shift + Alt önceliği ve toggle kapatıldığında koşmaya dönüş.
- Hücre sınırını mod değiştirirken kesintisiz geçme.
- Kesirli konum, harita dışına çıkış ve hücre verisi durumu.
- Odak kaybı/geri kazanımı; takılı modifier ve sahte toggle olmaması.
- Teşhis panelinde mod, çarpan, teorik hız ve gerçek Velocity ayrımı.
- Pencere boyutu/teşhis paneli taşması ve normal kapanış.

Bu maddeler `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md` içinde NOT RUN olarak kalır; kullanıcı gerçek bilgisayarda kontrol edip sonuçları bildirmeden PASS olarak işaretlenmez.

## 7. Kapsam dışı

- Hareket fiziği, çarpışma, pathfinding veya NPC algı sistemi eklemek.
- Stamina, ivme, sürtünme, momentum veya animasyon eklemek.
- Yeni harita/aktör simülasyon mimarisi kurmak.
- Kamera veya nihai render sistemi geliştirmek.
- Ana Eldoria oyununa entegrasyon.
- `main` veya `demo_eldoria` dalına yazmak/merge etmek.
- Masaüstü kabulü yapılmadan Aşama 4'ü kapalı ilan etmek.
- Aşama 5'e başlamak.

## 8. Uygulama kapısı

Bu belge yalnızca teknik plan önerisidir. Kullanıcı açıkça onaylamadan:
- CI workflow dosyası değiştirilmeyecek.
- Yeni test eklenmeyecek.
- Kod veya rapor güncellemesi uygulanmayacak.
- Aşama 4.7.6 uygulaması başlatılmayacaktır.

**Önerilen karar:** Aşama 4.7.6'yı üretim koduna dokunmadan, otomatik doğrulama + gözlemsel hareket benchmark'ı + dokümantasyon kapanışı olarak tamamlamak; gerçek Pygame masaüstü kabulini Aşama 4 genel kapanışında yapmak.


## 9. Uygulama ve doğrulama sonuçları

Kullanıcı planı 16 Kasım 2026 tarihinde onayladı. Onaylı kapsam uygulandı; üretim hareket kodunda özellik/refaktör değişikliği yapılmadı.

### 9.1 Test ve CI

- Laboratuvar tam test paketi: **505 passed**.
- Core Quality Linux: **1.968 passed, 1 warning**.
- Core Quality Windows: **1.968 passed**.
- Harita persistence benchmark: başarılı.
- Runtime persistence benchmark: başarılı.
- Hareket + hex hücre takip benchmark'ı: 1 / 10 / 100 / 1.000 aktör ölçümleri üretildi.
- Mimari sınır testi eklendi: geometry, movement, simulation ve world paketlerinde Pygame import'u yasaklanır.

Kanıt commit'i: `dafb5ce674c2356b1e07c4fde1965c7ee67ec611`.

- Hex World Laboratory CI run: [43882088050](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882088050)
- Core Quality run: [43882087966](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882087966)

Her iki workflow da aynı commit üzerinde başarılı tamamlanmıştır. Sonuçlar GitHub Actions ortamına aittir; kullanıcının yerel bilgisayarında test veya masaüstü kabulü yapıldığı anlamına gelmez.

### 9.2 Hareket benchmark sonucu

Ortam: Python 3.12.16, Linux 7.0.0-1019-azure x86_64, glibc 2.43. İşlemci adı CI ortamında sağlanmadı. Her aktör sayısında 3 ısınma partisi ve 20 ölçüm partisi; parti başına 10 simülasyon tick'i kullanıldı.

| Aktör | Ortalama parti (ms) | P95 parti (ms) | Ortalama aktör-tick (µs) |
|---:|---:|---:|---:|
| 1 | 0.1548 | 0.1756 | 15.4797 |
| 10 | 1.5196 | 1.5367 | 15.1961 |
| 100 | 15.1547 | 15.3680 | 15.1547 |
| 1.000 | 153.4378 | 156.1921 | 15.3438 |

Bu ölçüm yalnızca hareket adımı ve hex hücre çözümleme maliyetini kapsar. Render, NPC kararları, çarpışma, görevler, kaynak simülasyonu ve diğer oyun sistemleri dahil değildir. Bu nedenle sonuçlardan toplam oyun FPS'i veya hedef donanım performansı garantisi çıkarılmaz. 1.000 aktör için 10 tick'lik partinin ortalama süresi yaklaşık 153.44 ms'dir; sonraki optimizasyon kararı ancak hedef donanımda ve daha geniş simülasyon yüküyle yapılacak ölçümden sonra verilmelidir.

### 9.3 Manuel kabul

Kullanıcının kararı gereği gerçek Pygame masaüstü kabulü Aşama 4 genel kapanışına ertelenmiştir. `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md` maddeleri kullanıcı bilgisayarında kontrol edilene kadar açık kalır ve PASS olarak işaretlenmez.

**Karar:** Aşama 4.7.6 teknik doğrulama kapsamında kapatılmıştır. Bu karar Aşama 4'ün genel kapanışı değildir.
