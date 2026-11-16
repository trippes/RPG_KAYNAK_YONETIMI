# Aşama 4.7 — Hareket Modları Genel Planı

> **Belge türü:** Alt aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Ön koşul:** Aşama 4.6 kullanıcı kabulüyle kapatıldı.  
> **Durum:** KULLANICI ONAYI ALINDI — 4.7.1–4.7.6 teknik uygulama ve otomatik doğrulama tamamlandı; masaüstü kabulü Aşama 4 genel kapanışına ertelendi.

## 1. Amaç

Aşama 4.7, mevcut sürekli hareket sistemine üç açık hareket modu ekler:

1. **Normal:** temel hareket hızı.
2. **Koşma:** Shift basılıyken artırılmış hareket hızı.
3. **Gizlilik:** Alt'a bir kez basıldığında açılır; tekrar basıldığında kapanır. Açık kaldığı sürece azaltılmış hareket hızı uygulanır.

Kullanıcının kabul ettiği hız çarpanları:
- Normal: **1,0x**.
- Koşma: **1,5x**.
- Gizlilik: **0,5x**.
- Shift ve Alt aynı anda basılıysa **Gizlilik önceliklidir**.

Mevcut prototip temel hızı 60 dünya birimi/saniye olarak kullanır. Buna göre beklenen hızlar normalde 60, koşmada 90, gizlilikte 30 dünya birimi/saniyedir. Bu değerler prototip temel hızına göre örnektir; sistemin yapılandırılabilir temel hızını sabitlemez.

## 2. Devralınacak ve korunacak sözleşmeler

Aşama 4.7 aşağıdaki mevcut mimariyi genişletecek, yeniden kurmayacaktır:

- `WorldPoint` fiziksel konumun tek doğruluk kaynağıdır.
- `MovementIntent` cihazdan bağımsız hareket isteğini taşır.
- `MovementConfig` hareket hızını yapılandırır.
- `MovementIntegrator` sabit tick süresinde saf hareket hesabı yapar.
- `MovementSystem` dışarıdan sağlanan ardışık tick'lerde bir kez ilerler.
- `DemoTickPump` laboratuvar prototipinde 60 TPS üretir; hareket sistemi kendi saatini oluşturmaz.
- `PygameKeyboardAdapter` yalnızca Pygame girişini cihazdan bağımsız hareket niyetine çevirir.
- `MovementCellTracker` hareketten sonra hücreyi çözümler; konumu değiştirmez.
- Pygame bağımlılığı movement çekirdeğine taşınmaz.

Aşama 2 geometri, Aşama 3 dünya/persistence ve Aşama 4.1–4.6 test sözleşmeleri korunur.

## 3. Hareket modu davranışları

### 3.1 Normal

- Hiçbir hareket değiştirici tuş basılı değilse Normal modu seçilir.
- Hız çarpanı 1,0'dır.
- Hareket yönü yoksa hız vektörü sıfır kalır.

### 3.2 Koşma

- Sol veya sağ Shift basılıyken Koşma modu seçilir.
- Hız çarpanı 1,5'tir.
- Shift bırakıldığında, Alt basılı değilse Normal moda dönülür.
- Sol ve sağ Shift eşdeğer kabul edilir; ikisi birlikte basıldığında çarpan birikmez.

### 3.3 Gizlilik

- Sol veya sağ Alt'a bir kez basıldığında Gizlilik modu açılır; sonraki Alt basışı modu kapatır.
- Alt'ın basılı tutulması gerekmez; Gizlilik açık kaldığı sürece hız çarpanı 0,5'tir.
- Gizlilik kapatıldığında Shift basılıysa Koşma, değilse Normal modu seçilir.
- Sol ve sağ Alt aynı fiziksel basış olarak ele alınır; iki Alt tuşunu birlikte tutmak veya klavye otomatik tekrarları modu art arda açıp kapatmaz.
- Shift basılıyken Alt ile Gizlilik açılırsa Gizlilik önceliklidir; Alt ile kapatılırsa Shift hâlâ basılıysa Koşma etkinleşir.

### 3.4 Mod ve hareket yönü bağımsızlığı

Hareket modu, yön vektöründen ayrı bir kavramdır. Böylece oyuncu veya ilerideki yapay zekâ aynı yön isteğini farklı hız modlarıyla gönderebilir. Yön vektörü sıfırsa aktör hareket etmez; mod seçimi fiziksel konumu değiştirmez.

### 3.5 Anlık geçiş

Bu aşamada ivme, sürtünme, hızlanma/yavaşlama eğrisi veya animasyon eklenmez. Mod değiştiği ilk simülasyon tick'inde etkin hız çarpanı uygulanır. Tuş bırakma da aynı şekilde bir sonraki işlenen tick'te yeni modu uygular.

## 4. Kapsam içi işler

1. Hareket modlarını temsil eden cihazdan bağımsız bir enum/veri sözleşmesi oluşturmak.
2. `MovementIntent` içine varsayılanı Normal olan hareket modu bilgisini eklemek.
3. `MovementConfig` içine koşma ve gizlilik hız çarpanlarını eklemek; değerleri sonlu ve negatif olmayan sayılar olarak doğrulamak.
4. `MovementIntegrator` içinde seçilen moda ait etkin hızı hesaplamak; yön normalleştirmesini ve 60 TPS zaman hesabını korumak.
5. `PygameKeyboardAdapter` içinde Shift'i basılı-tutma, Alt'ı kenar-tetiklemeli aç/kapa olarak ele almak; sol/sağ tuşları tek mantıksal değiştirici olarak birleştirmek.
6. Öncelik kuralını tek yerde ve açık biçimde uygulamak: Gizlilik > Koşma > Normal.
7. Odak kaybında nötr yön ve Normal mod üretmek; takılı kalmış değiştirici tuşları önlemek.
8. Hareket demosu teşhis panelinde aktif hareket modunu ve etkin hız çarpanını göstermek.
9. Var olan ve yeni testleri genişleterek regresyon, determinism, FPS eşdeğerliği ve performans davranışını doğrulamak.
10. Aşama 4.7 kapanış raporunu hazırlamak.

## 5. Önerilen alt aşamalar

| Alt aşama | Amaç | Beklenen çıktı |
|---|---|---|
| 4.7.1 — Hareket modu sözleşmesi | Normal/Koşma/Gizlilik modlarını ve varsayılan davranışı tanımlamak | Cihazdan bağımsız MovementMode sözleşmesi |
| 4.7.2 — Hız profilleri | Config ve integrator üzerinden çarpanları uygulamak | 1,0x / 1,5x / 0,5x deterministik hız hesabı |
| 4.7.3 — Klavye bağdaştırıcısı | Shift basılı-tutma, Alt aç/kapa, sol/sağ tuşlar ve öncelik kuralı | Yeni MovementIntent üretimi |
| 4.7.4 — Uçtan uca entegrasyon | Hareket sistemi ve demo akışını bağlamak | Modların gerçek tick akışında çalışması |
| 4.7.5 — Teşhis görünümü | Mod ve etkin hızı görünür kılmak | Salt okunur diagnostics |
| 4.7.6 — Doğrulama ve kapanış | Regresyon, FPS, odak, benchmark ve manuel kontroller | Test kanıtları ve kapanış raporu |

Alt aşamaların kesin dosya sınırları, API imzaları, hata davranışları ve test senaryoları teknik mimari planında belirlenecektir.

## 6. Test ve kabul ölçütleri

### 6.1 Hareket çekirdeği

- Varsayılan MovementIntent Normal modda olmalıdır; önceki çağrılar geriye dönük uyumlu kalmalıdır.
- Normal, Koşma ve Gizlilik hızları tam olarak 1,0x, 1,5x ve 0,5x çarpanlarını üretmelidir.
- Çapraz hareketin hız büyüklüğü aynı moddaki tek eksen hareketini aşmamalıdır.
- Sıfır yön vektörü tüm modlarda sıfır hız üretmelidir.
- Geçersiz mod veya geçersiz hız çarpanı açık ve deterministik biçimde reddedilmelidir.

### 6.2 Klavye

- WASD ve ok tuşları mevcut davranışını korumalıdır.
- Sol/sağ Shift basılı tutulduğu sürece Koşma seçilmelidir.
- Sol/sağ Alt'a ilk basış Gizlilik'i açmalı; sonraki Alt basışı kapatmalıdır.
- Alt'ın basılı tutulması Gizlilik'i tekrar tekrar tetiklememeli; klavye otomatik tekrarı da toggle üretmemelidir.
- Gizlilik açıkken Shift basılı/bırakılması Gizlilik'i kapatmamalıdır.
- Gizlilik kapatıldığında Shift basılıysa Koşma, değilse Normal seçilmelidir.
- Sol/sağ Alt birlikte tutulduğunda tek toggle olmalı; bir Alt bırakılırken diğeri hâlâ basılıysa ikinci toggle oluşmamalıdır.
- Odak kaybında hareket yönü sıfırlanmalı ve toggle Gizlilik durumu güvenli biçimde Normal'e sıfırlanmalıdır; odak geri kazanımında Alt'ın basılı bulunması kendiliğinden toggle etmemelidir.
- Pencere odağı kaybında hareket yönü sıfırlanmalı ve mod Normal olmalıdır.
- Sol/sağ aynı tür değiştiricilerin birlikte basılması hız çarpanını katlamamalıdır.

### 6.3 Zaman ve determinism

- Mod her simülasyon tick'inde örneklenen MovementIntent üzerinden uygulanmalıdır.
- Aynı başlangıç state'i ve aynı tick-indexed intent dizisi aynı sonucu üretmelidir.
- 30/60/120 render FPS eşdeğerliği korunmalıdır.
- Tick pump'ın 8 tick/frame sınırı ve backlog koruma davranışı değişmemelidir.
- Mod geçişleri render kare sayısına değil simülasyon tick sırasına bağlı olmalıdır.

### 6.4 Mimari ve regresyon

- Movement çekirdeği Pygame import etmemelidir.
- Klavye adaptörü Pygame'e bağlı tek katman olarak kalmalıdır.
- Aşama 4.1–4.6 testleri korunmalıdır.
- Tam laboratuvar pytest, Lab CI ve Core Quality Linux/Windows CI başarılı olmalıdır.
- `main` ve `demo_eldoria` değişmeden kalmalıdır.

### 6.5 Görsel ve manuel kabul

- Teşhis paneli Normal/Koşma/Gizlilik modunu ve etkin hızı göstermelidir.
- Gerçek pencerede Shift/Alt davranışı ve öncelik senaryoları test edilmelidir.
- Odak kaybı ve geri kazanımı değiştirici tuşlarla birlikte tekrar doğrulanmalıdır.
- CI veya headless testler gerçek masaüstü kontrolünün yerine sayılmamalıdır.

## 7. Kapsam dışı

- NPC'lerin oyuncuyu görme, duyma, takip etme veya fark etme algoritmaları.
- Gerçek görünmezlik, kamuflaj, saklanma noktası veya görüş konisi sistemi.
- Stamina/enerji tüketimi, koşma limiti veya yorgunluk.
- Gürültü üretimi, ayak sesi veya yüzey bazlı ses.
- İvme, sürtünme, momentum, hızlanma animasyonu veya yavaşlama eğrisi.
- Karakter animasyonları, sprite değişimi veya görsel efekt.
- Çarpışma, obstacle, pathfinding veya ana oyun entegrasyonu.
- Yeni zaman/tick sistemi veya bağımsız accumulator.
- `main` veya `demo_eldoria` dalında değişiklik.

## 8. Riskler ve kontroller

| Risk | Kontrol |
|---|---|
| Hız çarpanının yanlış katmanda uygulanması | Modu intent'te taşı; etkin hızı integrator'da tek yerde hesapla |
| Çarpanların birikmesi | Aynı mod tuşlarını boolean seç; çarpanları çarpma/toplama yoluyla biriktirme |
| Shift/Alt önceliğinin belirsizliği | Tek kural: Gizlilik > Koşma > Normal; birim testleri |
| Odak kaybında Alt/Shift'in takılı kalması | Nötr intent ve Normal mod |
| Render FPS'ye bağlı mod geçişi | Tick başına input örneklemesi; fake-clock FPS testleri |
| Hareket çekirdeğine Pygame sızması | Mod enum'unu movement paketinde; tuş çözümünü input paketinde tut |
| Gelecekte stealth'in NPC algılamasıyla karışması | Bu aşamada yalnızca hız modu; algılama ayrı sistem ve aşama |

## 9. Beklenen teslimatlar

- MovementMode veri sözleşmesi.
- Güncellenmiş MovementIntent, MovementConfig ve MovementIntegrator.
- Güncellenmiş PygameKeyboardAdapter.
- Hareket demosunda mod/hız teşhisi.
- Unit, integration, determinism, FPS ve regresyon testleri.
- Benchmark karşılaştırması.
- Manuel kabul kontrol listesi.
- `reports/PHASE-04.7-CLOSURE-REPORT.md`.

## 10. Onay ve uygulama kapılarının gerçekleşen durumu

1. Kullanıcı hız çarpanlarını ve öncelik kuralını kabul etti.
2. Aşama 4.7 genel planı kullanıcı tarafından onaylandı.
3. Dosya ve API düzeyindeki teknik mimari plan hazırlandı.
4. Teknik plan kullanıcı tarafından onaylandı; uygulama yalnızca onaylı kapsamda yürütüldü.
5. Kod ve test çalışmaları `experiment/hex-world-laboratory` dalında tamamlandı.
6. Hedefli hareket davranışları tam laboratuvar paketi, Lab CI ve Core Quality Linux/Windows doğrulamalarıyla denetlendi.
7. Gerçek masaüstü manuel kabul testleri, kullanıcının kararıyla Aşama 4 genel kapanışına ertelendi.
8. Aşama 4.7 kapanış raporu ve Aşama 4.7.6 teknik kapanış raporu oluşturuldu.

Genel plan veya hız değerlerinin kabulü tek başına teknik planı ya da kod uygulamasını onaylamıyordu; gerekli ayrı teknik plan onayı da alınmış ve uygulanmıştır.

## 11. Dal güvenliği

- Tüm Aşama 4.7 belgeleri ve kodu yalnızca `experiment/hex-world-laboratory` dalında tutulur.
- `main` ve `demo_eldoria` dallarına açık ve ayrı onay olmadan yazma/merge/cherry-pick/rebase/reset yapılmaz.
- Aşama 4.7, Aşama 4'ün son alt aşaması değildir; Aşama 4 genel kapanışı için 4.7 sonuçları da değerlendirilecektir.
- Aşama 5'e geçiş ayrı genel plan ve onay gerektirir.
