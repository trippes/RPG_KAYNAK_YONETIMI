# Aşama 5 — Gövde Modeli, Çarpışma ve Fizik Genel Planı

> Belge türü: Aşama genel planı  
> Proje: Eldoria — Hex World Laboratory  
> Çalışma dalı: experiment/hex-world-laboratory  
> Durum: UYGULAMA VE OTOMATİK TEKNİK DOĞRULAMA TAMAMLANDI — NİHAİ MASAÜSTÜ KABULÜ BEKLİYOR  
> Tarih: 16 Kasım 2026  
> Ön koşul: Aşama 4 kapatıldı ve kullanıcı tarafından kabul edildi.

---

## 1. Amaç

Aşama 5'in amacı, Aşama 4'te tamamlanan sürekli hareket sistemini hex dünya üzerindeki fiziksel engellerle tutarlı biçimde etkileştirmektir.

Oyuncu ve ileride NPC gibi hareketli varlıklar; ağaç, kaya, duvar ve diğer engellerin içinden geçmemeli, engellere temas ettiklerinde kararlı biçimde durmalı veya temas yüzeyi boyunca kayabilmelidir. Fiziksel gövde ile görsel sprite birbirinden ayrılmalı; konum, zemin teması ve gövde yüksekliği kavramları birbirine karıştırılmamalıdır.

Nihai çarpışma doğruluğu gerçek hex polygon ve kenar geometrisine dayanacaktır. AABB yalnızca olası çarpışma adaylarını hızlıca toplamak için kullanılabilir; nihai çarpışma kararı veremez.

## 2. Devralınan mimari sözleşmeler

Aşama 5 aşağıdaki tamamlanmış sistemleri yeniden yazmadan kullanmalıdır:

1. Aşama 2 Geometry: WorldPoint, HexLayout, HexOrientation, world_to_axial, hex_polygon ve hex_edges.
2. Aşama 3 World: WorldId, MapId, CellAddress, HexCellData, MapRegistry, HexWorld ve HexWorldRuntime.
3. Aşama 4 Movement: MovementState, MovementConfig, MovementIntent, MovementIntegrator, MovementMode ve MovementSystem.
4. Aşama 4 zaman sözleşmesi: simülasyon tick hızı 60 TPS; hareket adımı 1/60 saniye.
5. Laboratuvar bağımsızlığı: fizik ve çarpışma çekirdeği Pygame'den bağımsız ve saf Python ile test edilebilir olmalıdır.

WorldPoint hareketli varlığın kesintisiz ve yetkili dünya konumu olarak kalır. Axial koordinat dünya topolojisi ve hücre sorguları içindir; ScreenPosition fiziksel konum olarak kullanılmaz.

## 3. Kapsam içi işler

### 3.1 Fiziksel gövde modeli

- Hareketli varlığın fiziksel gövdesini sprite verisinden ayırmak.
- Gövde şekli, boyutu, yerel offset'i ve zemin ankrajını tanımlamak.
- İlk uygulama için daire collider'ı; engeller için daire ve dışbükey polygon collider'ı kullanmak.
- Aynı fizik sözleşmesinin ileride oyuncu, NPC ve hareketli dünya varlıklarınca kullanılabilmesini sağlamak.

### 3.2 Zemin bağlantısı ve gövde yüksekliği

- WorldPoint ile fiziksel zemin/ayak ankrajı arasındaki ilişkiyi tanımlamak.
- Sprite pivotu ile collider merkezinin aynı olmak zorunda olmadığını güvence altına almak.
- Gövde yüksekliği kavramını tanımlamak; bu aşamada 2D zemin düzlemindeki çarpışma ile görsel derinlik/örtüşme davranışını birbirine karıştırmamak.
- Kamera ve nihai render katmanını bu aşamada geliştirmemek.

### 3.3 Hex çarpışma geometrisi

- Flat-top ve pointy-top hex hücrelerin mevcut geometri API'sinden gerçek polygon/kenar sınırlarını kullanmak.
- Hücre engeli, harita sınırı ve nesneye özel engel geometrisini birbirinden ayırmak.
- Tek hücre engeli, bitişik engeller, dar geçitler ve harita kenarları için tutarlı sınırlar üretmek.

### 3.4 Çarpışma tespiti

- Broadphase ile olası çarpışma adaylarını hızlıca toplamak.
- Narrowphase ile gerçek daire/polygon geometrileri arasındaki teması hesaplamak.
- AABB kullanılırsa bunu yalnızca broadphase ile sınırlamak.
- Geometrik tolerans, temas normali, nüfuz derinliği ve temas noktası sonuçlarını açık sözleşmelerle taşımak.

### 3.5 Çarpışma çözümü

- Engelin içine giren hareketi engellemek.
- Temas yüzeyine paralel hareketi koruyarak duvar boyunca kaymayı sağlamak.
- Köşe ve birden fazla eşzamanlı temas durumlarını kararlı çözmek.
- Titreşim, köşeye kilitlenme, geri sıçrama ve sonsuz çözüm döngülerini önlemek.

### 3.6 Sürekli çarpışma ve tunneling

- Hız, gövde boyutu ve tick süresine göre tunneling riskini ölçmek.
- Gerekli durumlarda swept collision / time-of-impact yaklaşımını uygulamak.
- Tek tick içinde ince engelin bir tarafından diğer tarafına geçilmesini önlemek.
- Çoklu çarpışma ve maksimum çözüm adımı için güvenli sınırlar tanımlamak.

### 3.7 Entegrasyon ve teknik doğrulama

- Çarpışma çözümünü 60 TPS hareket akışına bağlamak.
- Normal, koşma ve gizlilik hız profillerinde aynı çarpışma kurallarını korumak.
- Geometri, dünya ve hareket sistemlerinin mevcut testlerini regresyona karşı korumak.
- Pygame penceresi gerektirmeyen otomatik doğrulamaları tamamlamak.

## 4. Alt aşamalar ve sıralama

| Alt aşama | Başlık | Ana çıktı |
|---|---|---|
| 5.1 | Fiziksel gövde ve collider sözleşmeleri | Gövde tanımı, collider şekilleri ve doğrulama testleri |
| 5.2 | Zemin ankrajı ve gövde yerleşimi | Ground anchor, yerel offset ve yükseklik sözleşmesi |
| 5.3 | Hex ve nesne engel geometrisi | Hex sınırları ve statik engel tanımları |
| 5.4 | Broadphase ve narrowphase | Aday toplama ve kesin temas sorguları |
| 5.5 | Temas çözümü ve kayma | Nüfuz düzeltme, duvar kayması ve çoklu temas |
| 5.6 | Sürekli çarpışma ve tunneling | Swept testler ve güvenli hareket çözümü |
| 5.7 | Sistem entegrasyonu ve teknik kapanış hazırlığı | Bütünleşik otomatik doğrulama ve teknik rapor girdileri |

Her alt aşama kendi teknik kabul ölçütlerini ve otomatik testlerini geçmeden sonraki alt aşamaya başlanmayacaktır. Alt aşamalar sırasında masaüstü görsel kabul testi yapılması zorunlu değildir.

## 5. Test ve doğrulama yöntemi

Alt aşamalar boyunca kapsamına göre şu doğrulamalar uygulanacaktır:

- Birim testleri ve sayısal geometri sınır testleri.
- Hareket, dünya ve fizik entegrasyon testleri.
- Flat-top ve pointy-top regresyon testleri.
- Mimari bağımlılık ve Pygame bağımsızlığı kontrolleri.
- Farklı hız, tick ve engel boyutlarında tunneling testleri.
- Ölçüm temelli performans testleri.
- GitHub Actions Linux ve Windows CI / Core Quality doğrulamaları.

Test edilmemiş davranış başarılı olarak raporlanmayacaktır. Kullanıcı bilgisayarında yapılacak görsel testler bu alt aşama doğrulamalarının yerine geçmez.

## 6. Nihai görsel kabul

5.1–5.7 alt aşamalarının kodlaması ve teknik doğrulamaları tamamlandıktan sonra Aşama 5'in nihai kabul süreci yürütülecektir.

Laboratuvar uygulaması kullanıcı bilgisayarında açılarak en az şu davranışlar görsel olarak kontrol edilecektir:

1. Oyuncu sprite'ı ile fiziksel collider'ın doğru ayrılması ve hizalanması.
2. Tek hücrelik engeller ve bitişik engeller.
3. Ağaç/kaya/duvar benzeri farklı collider biçimleri.
4. Engellerin içinden geçememe.
5. Duvar boyunca doğal kayma.
6. Dar geçitlerden geçebilme.
7. Köşelerde takılma veya titreşim olmaması.
8. Birden çok temasın kararlı çözülmesi.
9. Normal, koşma ve gizlilik modlarında tutarlı çarpışma.
10. Flat-top ve pointy-top haritalarda doğru davranış.
11. Harita sınırlarının beklenen davranışı.
12. Normal açılış ve kapanış.

Görsel testlerde bulunan kusurlar giderilecek ve ilgili kontroller tekrar edilecektir. Görsel kabul, bütün alt aşamalar tamamlandıktan sonra tek bir bütünleşik süreç olarak yürütülecektir.

## 7. Kapsam dışı işler

Ayrıca onaylanmadıkça Aşama 5 kapsamında geliştirilmez:

- Kamera, zoom, pan ve dünya-ekran dönüşümü.
- Nihai sprite çizimi, animasyon, y-sort ve sanat varlıkları.
- Yol bulma ve NPC yapay zekâsı.
- Görev, ekonomi, savaş veya etkileşim kurallarının yeniden tasarımı.
- Tam Entity/Component sisteminin kurulması.
- Multiplayer/ağ senkronizasyonu.
- Ana oyuna veya demo_eldoria dalına entegrasyon.
- Godot'a geçiş.

Bu aşamada yalnızca fiziksel gövde ile görsel varlık arasındaki gerekli veri sınırı tanımlanır; nihai görsel derinlik ve örtüşme sistemi sonraki aşamalara bırakılır.

## 8. Aşama kapanış koşulları

Aşama 5 ancak aşağıdakilerin tamamı sağlandığında kapatılabilir:

1. 5.1–5.7 alt aşamaları tamamlanmış ve belgelenmiş olmalıdır.
2. Birim, entegrasyon ve regresyon testleri başarılı olmalıdır.
3. Linux ve Windows CI / Core Quality kontrolleri geçmelidir.
4. Mimari sınırlar ve Pygame bağımsızlığı doğrulanmalıdır.
5. Performans ölçümleri ve bilinen sınırlar raporlanmalıdır.
6. Kullanıcı bilgisayarında nihai görsel kabul tamamlanmalıdır.
7. reports/PHASE-05-CLOSURE-REPORT.md oluşturulmalı ve gerçek kanıtları içermelidir.
8. Teknik plan ve raporlar nihai durumla tutarlı olmalıdır.
9. Kullanıcı nihai sonucu kabul etmelidir.

## 9. Dal ve değişiklik güvenliği

- Bütün çalışma yalnızca experiment/hex-world-laboratory dalında yapılır.
- main ve demo_eldoria dallarına ayrı ve açık kullanıcı onayı olmadan yazılmaz, merge veya cherry-pick yapılmaz.
- Kod uygulaması başlamadan önce teknik planın onayı alınır.
- Her alt aşamadan önce gerçek dosya ağacı ve API tekrar incelenir.
- Commit öncesi dal ve değişen dosyalar; commit sonrası HEAD ve dosya içerikleri doğrulanır.
- Plan dışı mimari değişiklik gerekirse önce gerekçe ve etki analizi sunulur.
- Görsel testler bütün alt aşamalar tamamlanmadan nihai kabul yerine kullanılamaz.

---

Bu genel plan Aşama 5'in kapsamını ve kabul yöntemini tanımlar. Ayrıntılı teknik plan, modül/API sözleşmelerini, algoritmaları, test matrisini ve alt aşama kapılarını belirler. Teknik planın onaylanması kod uygulamasına ayrıca izin verilmesini gerektirir.


## 10. 16 Kasım 2026 — Uygulama ve otomatik doğrulama durumu

5.1–5.7 alt aşamalarının uygulaması tamamlandı. 5.7 bütünleşik hareket/çarpışma sistemi, harita sınırı entegrasyonu, harita kapsamı doğrulaması ve benchmark p95 düzeltmesi dâhil teknik incelemede bulunan düzeltmeler de çalışma dalına işlendi.

Otomatik doğrulama kanıtları:

- Hex World Laboratory CI: run `43932344855` — **584 test geçti**; harita persistence, runtime persistence, hareket ve bütünleşik çarpışma benchmark adımları başarılı.
- Core Quality: run `43932344956` — Linux **2.047 test geçti**, Windows **2.047 test geçti**; iki platformda release-candidate verification başarılı.
- Bütünleşik çarpışma benchmark'ı (GitHub Linux runner, 10 tick/batch): 1 aktör 198.492 µs/actor-tick; 10 aktör 190.8413 µs; 100 aktör 194.7613 µs; 1.000 aktör 196.2149 µs. Bu ölçüm render, input polling, NPC mantığı ve dünya simülasyonunu kapsamaz; kullanıcının bilgisayarında FPS garantisi değildir.
- BLOCKED harita sınırı artık gerçek çarpışma engellerine dönüştürülür; OPEN davranışı ayrıca test edilir. Collision-aware movement sistemi farklı harita kimliklerini karıştırmayı reddeder.

Son denetimde Pygame kabul demosunun eski hareket sistemiyle çalıştığı görüldü. Demo artık CollisionAwareMovementSystem'e bağlandı; fiziksel engeller ve collider görselleştirmesi eklendi, bu entegrasyon için yeni regresyon testleri yazıldı. Başlangıç evi de beş ayrı duvar collider'ı ve kapı boşluğu olan basit bir yapı iskeleti olarak eklendi; duvar/çatı çizgileri nihai sanat varlığı değildir. Önceki CI sonuçları bu son demo entegrasyonunu kapsamaz. Bu nedenle kullanıcının bilgisayarındaki tam pytest çalıştırması son demo değişikliğini de doğrulayacak; başarılı olursa yalnızca masaüstü/görsel kabul kalacaktır. Herhangi bir kusur bulunursa kapanıştan önce düzeltilir ve ilgili test tekrarlanır.

### Kullanıcının yapacağı son kontroller

1. Laboratuvar kök dizininde `python -m pytest -q` komutunu çalıştırmak ve başarılı sonucu bildirmek.
2. `python -m hex_world_lab` ile Pygame laboratuvarını açmak.
3. Tek hücre ve bitişik engellerde oyuncunun engelin içinden geçmediğini doğrulamak.
4. Daire oyuncu collider'ı ile ağaç/kaya/duvar temsili engellerin temasını kontrol etmek.
5. Başlangıç evi iskeletinin duvarlarına çarpışmayı, kapı boşluğundan geçişi ve evin çevresinden dolaşmayı kontrol etmek.
6. Duvar boyunca kaymayı ve dar geçitlerden geçişi kontrol etmek.
7. Köşe ve birden fazla temas durumunda takılma/titreşim olmadığını kontrol etmek.
8. Normal, koşma ve gizlilik hızlarında çarpışmayı kontrol etmek.
9. Flat-top demo haritasında çarpışmayı kontrol etmek; pointy-top geometri doğrulaması tam pytest paketi içindeki otomatik testlerle yapılır.
10. BLOCKED sınırda harita dışına çıkılamadığını, OPEN sınırda çıkışın mümkün olduğunu doğrulamak.
11. Pencerenin normal açılıp kapanmasını doğrulamak.

Bu liste tamamlanıp kullanıcı sonucu onayladıktan sonra `reports/PHASE-05-CLOSURE-REPORT.md` gerçek yerel sonuçlarla hazırlanacak ve Aşama 5 kapatılacaktır.
