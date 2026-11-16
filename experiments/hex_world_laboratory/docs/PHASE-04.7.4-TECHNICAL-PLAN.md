# Aşama 4.7.4 — Uçtan Uca Entegrasyon Testlerini Güçlendirme Planı

> **Belge türü:** Alt aşama teknik uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK DOĞRULAMASI TAMAMLANDI — ALT AŞAMA KAPATILDI  
> **Üst belge:** `docs/PHASE-04.7-TECHNICAL-PLAN.md`  
> **Başlangıç HEAD:** `0b6dafe4d346c6f61a6fc03282eb81c2fdb68f75`

## 1. Amaç

Aşama 4.7.1–4.7.3 kapsamında hareket modu sözleşmesi, hız profilleri ve klavye adaptörü uygulanmıştır. Mevcut 4.7.4 demo hattı da klavye girdisini gerçek simülasyon tick'lerine, hareket state'ine ve hücre takibine bağlamaktadır.

Bu alt aşamanın amacı üretim kodunu yeniden yazmak değil, mevcut entegrasyonun üç kritik etkileşimini uçtan uca testlerle güvenceye almaktır:

1. Hareket modu değişirken fiziksel konumun hex hücre sınırını kesintisiz geçmesi.
2. Shift basılıyken Alt ile gizliliğin açılıp kapatılması ve gizlilik kapandığında koşmanın demo hattında yeniden etkinleşmesi.
3. Gizlilik açık ve Alt fiziksel olarak basılıyken odak kaybı/geri kazanımı; geri kazanımın sahte toggle üretmemesi.

Bu üç madde mevcut kodun bozuk olduğunu göstermez. Bunlar, adaptör seviyesinde veya daha genel akışlarda zaten kısmen doğrulanan davranışların tam demo hattında açık kabul testlerine dönüştürülmesidir.

## 2. Mevcut durum ve korunacak mimari

Mevcut akış:

`PygameKeyboardAdapter.read_intent()` → `MovementIntent` → `MovementSystem.step()` → `MovementState` → `MovementCellTracker.update()`

Mevcut `tests/integration/test_movement_demo_flow.py` normal/koşma/gizlilik hızlarını ve konum snap olmamasını doğrular. Ancak Shift basılı tutulurken gizlilik toggle'ının kapatılması ve koşmanın yeniden başlaması aynı demo senaryosunda açıkça doğrulanmamaktadır. Hücre takibi testi de mod değişimleri boyunca gerçek bir hücre sınırı geçişini sınamaz.

`tests/unit/test_pygame_keyboard_modes.py` Alt toggle, sol/sağ Alt örtüşmesi, Shift önceliği ve odak kazanımı davranışlarını adaptör seviyesinde kapsar. Bu plan, ilgili odak senaryosunu tam demo akışında da sınar.

Aşağıdaki sözleşmeler değiştirilmeyecektir:

- `WorldPoint` fiziksel konumun tek doğruluk kaynağıdır; hücre takibi konumu snap etmez.
- Sabit simülasyon adımı 1/60 saniyedir; tick kaynağı `DemoTickPump` olarak kalır.
- Normal 1,0x; koşma 1,5x; gizlilik 0,5x hız çarpanları korunur.
- Öncelik Gizlilik > Koşma > Normal'dir.
- Alt toggle, Shift basılı-tutma davranışıdır; tuşların mevcut sol/sağ birleştirme kuralı korunur.
- Render yalnızca görüntüler; simülasyon state'ini değiştirmez.
- Movement çekirdeğine Pygame bağımlılığı eklenmez.

## 3. Kapsam ve dosya sınırı

### Güncellenecek

- `tests/integration/test_movement_demo_flow.py`

Gerekirse testin mevcut yardımcıları aynı dosyada küçük ve yerel biçimde genişletilebilir. Yeni üretim sınıfı, public API veya test altyapısı oluşturulması planlanmamaktadır.

### Değiştirilmeyecek

- `src/hex_world_lab/**` altındaki tüm üretim kodu.
- `tests/unit/**` altındaki adaptör ve hareket çekirdeği testleri.
- `tests/integration/test_movement_demo_fps.py` ve FPS/tick pump davranışı.
- Geometri, dünya modeli, persistence, benchmark ve CI yapılandırmaları.
- Genel/teknik Aşama 4.7 üst belgeleri.

Uygulama sırasında gerçek bir üretim kodu kusuru ortaya çıkarsa bu planın kapsamı dışında tutulur; ayrı bulgu olarak raporlanır ve kullanıcı onayı olmadan düzeltilmez.

## 4. Uygulama ve test senaryoları

### 4.1 Mod değişimleri boyunca hex hücre sınırını geçme

**Hedef:** Normal → Koşma → Gizlilik modları sırasında aktörün fiziksel konumunun kesintisiz ilerlediğini ve `MovementCellTracker` sonucunun fiziksel konumla tutarlı kaldığını doğrulamak.

Senaryo:

1. Demo sabit saat ve kontrollü klavye sağlayıcısıyla başlatılır.
2. Aktör, harita içinde bilinen bir hücre sınırını geçecek şekilde hareket ettirilir.
3. Sınır geçişinden önce ve sonra normal, koşma ve gizlilik modları kontrollü tick'lerde uygulanır.
4. Her tick sonrasında `MovementState.position` fiziksel konum olarak kaydedilir.
5. `current_resolution` hücre çözümlemesi kontrol edilir.

Kabul ölçütleri:

- Seçilen rota en az bir gerçek hex hücre sınırını kesmelidir; yalnızca aynı hücre içinde hareket etmek yeterli değildir.
- Hücre değişimi, fiziksel konumun sürekliliğini değiştirmemelidir.
- Mod geçişi veya hücre değişimi konumu hücre merkezine/kenarına snap etmemelidir.
- Her tick'te tracker'ın koordinatı, aynı fiziksel konumun geometri çözümleyicisiyle bulunan koordinatına eşit olmalıdır.
- Hız farkı yalnızca seçili mod çarpanından kaynaklanmalıdır.
- Test sabit saatle deterministik olmalıdır; gerçek zaman veya uyku kullanmamalıdır.

Test rotası ve sınır noktası mevcut harita geometrisi/API'si üzerinden seçilecek; geometri üretim kodunda değişiklik yapılmayacaktır.

### 4.2 Shift + Alt toggle etkileşiminin tam demo akışı

**Hedef:** Adaptör seviyesinde mevcut olan Shift/Alt etkileşiminin demo tick'leri ve fiziksel hareket üzerindeki etkisini doğrulamak.

Senaryo:

1. D yönü ve Shift ile koşma başlatılır.
2. Alt'a basılır; gizlilik koşmaya üstün gelir.
3. Alt bırakılır; gizlilik toggle açık kaldığı için mod gizlilik olarak kalır.
4. Alt'a ikinci kez basılır; gizlilik kapanır.
5. Shift hâlâ basılı olduğundan koşma yeniden etkinleşir.
6. Son olarak Shift bırakılır; mod normale döner.

Kabul ölçütleri:

- Her durum geçişi yalnızca ilgili simülasyon tick'inde uygulanmalıdır.
- Gizlilik açıkken Shift'in basılı kalması gizliliği bozmamalıdır.
- Gizlilik kapatıldığı tick'te Shift hâlâ basılıysa `MovementState.mode == RUNNING` olmalıdır.
- Koşmaya dönüşte hız vektörü, yapılandırılmış temel hızın 1,5 katını göstermelidir.
- Her adımın konum farkı ilgili tick süresi ve hız çarpanıyla tutarlı olmalıdır.
- Alt'ın bırakılması tek başına toggle'ı kapatmamalıdır.
- Test gerçek demo hattını (`MovementDemo.pump()`) kullanmalıdır; adaptörü doğrudan çağıran unit test yeterli kabul edilmez.

### 4.3 Gizlilik sırasında odak kaybı ve geri kazanımı

**Hedef:** Gizlilik toggle'ı açıkken ve Alt fiziksel olarak basılı durumdayken odak kaybının güvenli nötr duruma geçirdiğini, odak geri geldiğinde sahte Alt basış kenarı üretmediğini doğrulamak.

Senaryo:

1. D yönüyle hareket edilir ve Alt basılarak gizlilik açılır.
2. Alt, kontrollü key provider içinde basılı tutulmaya devam eder.
3. `WINDOWFOCUSLOST` olayı demo'ya gönderilir.
4. Sonraki tick işlenir.
5. `WINDOWFOCUSGAINED` olayı gönderilir; key provider Alt'ın hâlâ basılı olduğunu bildirir.
6. Sonraki tick işlenir.
7. Alt bırakılır ve ardından yeniden basılır; yeni ve gerçek basış kenarı kontrol edilir.

Kabul ölçütleri:

- Odak kaybından sonraki tick'te yön nötr, mod NORMAL ve velocity sıfır olmalıdır.
- Odak kaybı toggle gizlilik state'ini temizlemelidir.
- Odak geri kazanımında Alt hâlâ basılı olsa bile gizlilik kendiliğinden açılmamalıdır.
- Odak geri kazanımı tek başına fiziksel konumu ilerletmemelidir.
- Alt bırakıldıktan sonra yeni bir basış, gizliliği normal toggle kuralıyla açabilmelidir.
- Test gerçek demo olay yönlendirmesini, tick pump'ı ve state güncellemesini kullanmalıdır.

## 5. Test yürütme sırası

1. Yeni/eklenen üç hedefli entegrasyon testi ayrı ayrı çalıştırılır.
2. `tests/integration/test_movement_demo_flow.py` modülü çalıştırılır.
3. Tam laboratuvar test paketi `python -m pytest -q` ile çalıştırılır.
4. Laboratuvar GitHub Actions CI sonucu izlenir.
5. Değişiklik kapsamı test dosyasıyla sınırlı olduğundan Core Quality workflow tetiklenmiyorsa bu durum açıkça raporlanır; tetiklenmişse Linux/Windows sonuçları doğrulanır.
6. Benchmark veya FPS testleri için kod değişikliği gerekmiyorsa tekrar çalıştırma zorunlu değildir; tam pytest içindeki regresyon sonucu kaydedilir.

CI başarısı yerel bilgisayar testinin yerine geçmez. Kullanıcının kararıyla masaüstü manuel kabul kontrolleri Aşama 4.7.4 kapanış şartı olmaktan çıkarılmış ve Aşama 4'ün genel kapanışına ertelenmiştir. Bu nedenle alt aşama teknik doğrulama kapsamında kapatılabilir; masaüstü davranışları Aşama 4 genel kapanışında birlikte kontrol edilecektir.

## 6. Tamamlanma ölçütleri

Aşama 4.7.4 bu plan kapsamında ancak aşağıdaki koşulların tümü sağlanırsa tamamlanmış sayılır:

- Üç senaryonun her biri gerçek `MovementDemo` hattında test edilmiştir.
- Hücre sınırı geçişinde fiziksel konum kesintisizdir ve tracker doğru hücreyi raporlar.
- Shift/Alt toggle etkileşimi koşmaya doğru dönüşü kanıtlar.
- Odak kaybı ve kazanımı stealth toggle'ını güvenli biçimde sıfırlar; sahte toggle oluşmaz.
- Hedefli testler ve tam laboratuvar pytest başarılıdır.
- Laboratuvar CI sonucu başarılıdır.
- Commit yalnızca `experiment/hex-world-laboratory` dalına yazılmıştır.
- Commit SHA, branch HEAD ve değişen dosya listesi GitHub'dan tekrar okunarak doğrulanmıştır.
- Kapanış özeti kullanıcıya sunulmuştur.

**Not:** Yerel bilgisayarda manuel masaüstü kabulü bu alt aşamanın tamamlanma ölçütü değildir. Bu kontroller Aşama 4 genel kapanışında yapılacaktır.

## 7. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Testin hücre sınırını gerçekte geçmemesi | Başlangıç/hedef konumları ve çözümlenen koordinat değişimi açıkça assert edilir |
| Hex sınırındaki kayan nokta belirsizliği | Sınır çizgisi üzerinde değil, sınırın iki yanında güvenli test noktaları kullanılır |
| Alt toggle testinde fiziksel key snapshot'larının yanlış sıralanması | Her basış/bırakış arasında ayrı tick ve açık key-state kurulumu yapılır |
| Focus gain'in sahte basış üretmesi | Alt'ın odak geri geldiğinde hâlâ basılı olduğu snapshot açıkça test edilir |
| Testlerin gerçek zamana bağımlı olması | FakeClock ve deterministik key provider kullanılır |
| Kapsamın üretim koduna kayması | Üretim kodu değişikliği bu planın dışında tutulur |

## 8. Kapsam dışı

- Üretim kodunda refactor veya davranış değişikliği.
- Yeni hareket modu, hız çarpanı veya input semantiği.
- Collision, pathfinding, NPC algısı, gerçek stealth, stamina, ses veya animasyon.
- Kamera, harita geçişi veya ana Eldoria oyununa entegrasyon.
- Manuel masaüstü kabulünün tamamlandığını varsaymak.
- Aşama 4.7.5 teşhis paneli veya 4.7.6 genel kapanış işlerini bu alt aşamaya taşımak.

## 9. Onay kapısı ve dal güvenliği

Kullanıcı bu teknik planı 16 Kasım 2026 tarihinde onaylamıştır. Uygulama ve otomatik teknik doğrulama tamamlanmıştır.

Uygulama sürecinde:

- Yalnızca `experiment/hex-world-laboratory` dalında çalışılır.
- Yazma öncesi branch HEAD ve hedef dosyanın güncel SHA'sı yeniden doğrulanır.
- `main` ve `demo_eldoria` dallarına hiçbir yazma, merge, cherry-pick, rebase veya reset yapılmaz.
- Testler başarısızsa başarısızlık gizlenmez; plan dışı üretim kodu değişikliğine geçilmez.
- Commit sonrasında branch HEAD, commit ve değişen dosyalar GitHub'dan tekrar okunur.
