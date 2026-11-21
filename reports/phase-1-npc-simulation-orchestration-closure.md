# Eldoria — Aşama 1 Kapanış Raporu
## Merkezi NPC Simülasyon Orkestrasyonu

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Çalışma dalı:** `experiment/map-cleanup`
- **Aşama:** 1 — Merkezi NPC simülasyon orkestrasyonu
- **Durum:** Tamamlandı
- **Rapor türü:** Teknik kapanış ve doğrulama kaydı

---

## 1. Yönetici özeti

Aşama 1'in amacı, NPC davranış sistemlerinin sabit zaman adımlı oyun döngüsünde dağınık biçimde çağrılması yerine, mevcut davranış sırasını koruyan tek bir merkezi simülasyon giriş noktası üzerinden yürütülmesini sağlamaktı.

Bu aşamada yeni bir NPC yapay zekâsı veya yeni davranış kuralı tasarlanmadı. Devriye, kaçınma ve yoldaş güncelleme sistemleri korunarak tek bir orkestrasyon akışı altında toplandı. NPC kaçınma sistemi için uygun yaşam döngüsü anahtarıyla önbellekleme eklendi. Oyun döngüsü merkezi giriş noktasına yönlendirildi; eski test çiftleri ve uyumluluk senaryoları için kontrollü geri dönüş yolu korundu.

Değişiklikler ilgili regresyon testleriyle kapsandı. Aşamanın son commit'i üzerinde GitHub Actions doğrulamaları Ubuntu ve Windows ortamlarında Python 3.11 ve 3.12 için, ayrıca Pygame headless smoke testi ve kalite kontrolleri için başarılı sonuçlandı.

**Kapanış kararı:** Aşama 1'in tanımlı kapsamı tamamlanmıştır. Aşama 2'ye geçiş için teknik engel bulunmamaktadır.

## 2. Başlangıç problemi ve hedefler

Önceki yapıda NPC simülasyonunun farklı parçaları oyun döngüsünden ayrı ayrı tetikleniyordu. Bu durum:
- NPC güncelleme sırasının birden fazla çağrı noktasında yönetilmesine,
- ortak zaman adımının her alt sisteme ayrı ayrı aktarılmasına,
- sistem yaşam döngüsünün ve tekrar kullanılabilir nesnelerin daha zor izlenmesine,
- ileride algılama, etkileşim ve çarpışma maliyetlerini ölçüp yönetirken tek bir orkestrasyon sınırının bulunmamasına

neden olabilecek bir mimari dağınıklık oluşturuyordu.

Aşamanın hedefleri şunlardı:

1. NPC simülasyonu için tek bir uygulama katmanı giriş noktası oluşturmak.
2. Mevcut güncelleme sırasını değiştirmemek.
3. Sabit zaman adımlı simülasyonun çalışma biçimini korumak.
4. Kaçınma sistemi nesnesinin gereksiz yere tekrar oluşturulmasını önlemek.
5. Oyun döngüsünü merkezi giriş noktasına yönlendirmek.
6. Yeni akışı otomatik testlerle güvence altına almak.
7. Değişiklikleri küçük, izlenebilir commit'lerle dal üzerinde kaydetmek.

## 3. Uygulanan mimari değişiklikler

### 3.1. GameplayService üzerinde merkezi giriş noktası

`application/gameplay_service.py` içinde `advance_npc_simulation(delta_seconds)` metodu eklendi.

Bu metot üç mevcut alt sistemi kanonik sırayla çağırır:

1. NPC devriye güncellemeleri — `advance_npc_patrols`
2. NPC kaçınma güncellemeleri — `advance_npc_avoidance`
3. Yoldaş güncellemeleri — `advance_companions`

Her alt sisteme aynı `delta_seconds` değeri aktarılır. Alt sistemlerden dönen hareket etmiş NPC kimlikleri birleştirilir, tekrarlanan kimlikler tekilleştirilir ve sıralı bir tuple olarak döndürülür.

Bu düzenleme, alt sistemlerin davranış kurallarını GameplayService içine taşımamıştır. GameplayService burada davranışların sahibi değil, mevcut sistemler arasındaki yürütme sırasını yöneten orkestrasyon katmanıdır.

### 3.2. NPC kaçınma sistemi önbelleği

`advance_npc_avoidance()` içerisinde `NPCAvoidanceSystem` nesnesinin her çağrıda yeniden kurulmasını önleyen bir önbellek eklendi.

Önbellek anahtarı şu bileşenlerden oluşur:

- runtime nesnesinin kimliği,
- NPC koleksiyonunun kimliği,
- fizik snapshot/binding nesnesinin kimliği,
- oyuncu aktör kimliği.

Bu bileşenlerden oluşan anahtar değiştiğinde kaçınma sistemi yeniden oluşturulur. Anahtar aynı kaldığında mevcut sistemin `step(delta_seconds)` metodu kullanılır.

Bu yaklaşım, sistemin bağlı olduğu temel runtime ve veri nesneleri değiştiğinde eski sistemin kullanılmaya devam etmesini önlemeyi amaçlar. Önbellekleme yalnızca sistem nesnesinin yaşam döngüsüne uygulanmıştır; NPC davranış kuralları veya algılama sonuçları için yeni bir veri önbelleği getirilmemiştir.

### 3.3. GameWindow oyun döngüsü entegrasyonu

`game_ui/game_window.py` içindeki `_advance_npc_simulation()` merkezi GameplayService giriş noktasını kullanacak şekilde düzenlendi.

Sabit adım accumulator/clock akışı korunmuştur. NPC simülasyonu yine sabit zaman adımı üzerinden ilerler; merkezi çağrı her sabit adımda aynı delta ile yapılır.

Eski test double/adaptörlerinde merkezi metot bulunmadığı durumlar için kontrollü bir geri dönüş yolu bırakılmıştır. Bu yol eski üç çağrıyı aynı sırayla çalıştırır. Böylece üretim akışı merkezileştirilirken mevcut odaklı testlerin ve uyumluluk senaryolarının gereksiz yere kırılması önlenmiştir.

### 3.4. Hafif test nesnelerinde telemetri güvenliği

İlk CI çalıştırmalarında bazı odaklı testlerin `GameWindow` nesnesini normal `__init__` akışını çalıştırmadan oluşturduğu ve `_frame_phase_times` alanının bulunmadığı görüldü.

`step()` başlangıcına bu isteğe bağlı telemetri alanını güvenli biçimde başlatan koruma eklendi. Bu düzeltme oyun davranışını değiştirmez; yalnızca kısmi test nesnelerinde telemetri erişiminin hata üretmesini önler.

## 4. Davranış ve uyumluluk açısından korunanlar

Aşama 1 bir davranış yeniden tasarımı değildir. Özellikle aşağıdaki alanlara müdahale edilmemiştir:

- Devriye davranışının karar kuralları.
- Kaçınma davranışının karar kuralları.
- Yoldaş takip davranışının karar kuralları.
- NPC'lerin hareket/konum çözümleme kuralları.
- NPC gövde çakışmalarının çözüm sırası ve mevcut çağrı noktaları.
- Sabit zaman adımlı simülasyon clock/accumulator yaklaşımı.
- Oyuncu fiziği ve render akışının görevleri.

Çarpışma çözümünü tek merkezde toplama bu aşamanın kapsamına alınmamıştır. Kaçınma sistemi ile GameplayService tarafındaki mevcut overlap çözümünün sorumluluklarını birleştirmek ayrı bir teknik karar ve ayrı test kapsamı gerektirir.

## 5. Değiştirilen dosyalar ve test kapsamı

| Dosya | Değişiklik |
|---|---|
| `application/gameplay_service.py` | Kaçınma sistemi önbelleği ve merkezi `advance_npc_simulation` orkestrasyonu |
| `game_ui/game_window.py` | Sabit adım NPC çağrılarının merkezi giriş noktasına yönlendirilmesi; hafif test nesneleri için telemetri koruması |
| `tests/test_application/test_npc_simulation_orchestration.py` | Alt sistem sırası ve hareket etmiş NPC kimliklerinin birleştirilmesi testi |
| `tests/test_game_ui/test_game_window_rendering.py` | GameWindow sabit adım döngüsünün merkezi servis giriş noktasını kullandığını doğrulayan regresyon testi |

### Eklenen/doğrulanan test senaryoları

**Orkestrasyon sırası testi:** Devriye, kaçınma ve yoldaş sistemlerinin sırasıyla çağrıldığı; aynı delta değerinin iletildiği; dönen NPC kimliklerinin tekilleştirilip sıralı tuple olarak sunulduğu doğrulanır.

**Oyun döngüsü entegrasyon testi:** Merkezi servis giriş noktasının oyun döngüsü tarafından kullanıldığı ve verilen geçen sürenin iki adet 1/60 saniyelik sabit adıma ayrıldığı senaryo doğrulanır.

**Mevcut regresyon kapsamı:** NPC davranışı, kaçınma, yoldaş komutları, GameplayService ve GameWindow test paketleri CI kapsamındaki ilgili testlerle çalıştırılmıştır.

## 6. Commit geçmişi

Aşama 1'in uygulama ve düzeltme zinciri:

1. [`4ad5552` — Centralize NPC simulation orchestration and cache avoidance system](https://github.com/trippes/RPG_KAYNAK_YONETIMI/commit/4ad55527a15e3b5bed10ea5517e508a02b82e18f)  
   GameplayService orkestrasyonu ve kaçınma sistemi önbelleği.

2. [`7832676` — Route fixed-step NPC updates through central simulation entry point](https://github.com/trippes/RPG_KAYNAK_YONETIMI/commit/7832676fb11c570155930d99f63da13b2cdf4520)  
   GameWindow sabit adım akışının merkezi giriş noktasına yönlendirilmesi ve uyumluluk geri dönüşü.

3. [`753c9ef` — Test centralized NPC simulation dispatch from game loop](https://github.com/trippes/RPG_KAYNAK_YONETIMI/commit/753c9ef9c682a695f8941cc3bf91532a68895219)  
   Oyun döngüsü entegrasyon regresyon testi.

4. [`b76ba80` — Test centralized NPC simulation orchestration](https://github.com/trippes/RPG_KAYNAK_YONETIMI/commit/b76ba8024cbbf173ab4bbb7ac83b84b24be7c2a5)  
   Alt sistem sırası ve hareket kimliklerinin birleştirilmesi testi.

5. [`4590a77` — Guard optional frame telemetry for lightweight test instances](https://github.com/trippes/RPG_KAYNAK_YONETIMI/commit/4590a77860a40e2b46dac35553f6685dc231ffae)  
   İlk CI çalıştırmalarında görülen hafif test nesnesi uyumsuzluğunun giderilmesi.

## 7. CI ve otomatik doğrulama sonuçları

Son aşama commit'i `4590a77860a40e2b46dac35553f6685dc231ffae` üzerinde GitHub Actions sonuçları kontrol edilmiştir.

### Eldoria CI

[GitHub Actions — Eldoria CI, run 44875139519](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44875139519)

- Ubuntu / Python 3.11: başarılı
- Windows / Python 3.11: başarılı
- Ubuntu / Python 3.12: başarılı
- Windows / Python 3.12: başarılı
- Pygame headless smoke test: başarılı

### Core quality

[GitHub Actions — Core quality, run 44875139556](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44875139556)

- Değişen runtime entegrasyon dosyalarında Ruff lint: başarılı
- Legacy map cleanup boundary check: başarılı
- Legacy API usage report: başarılı
- Release-candidate verification: başarılı
- Windows verification: başarılı

İlk CI denemesinde yedi hata görülmüştür. Hatalar, bazı testlerin GameWindow kurucusunu çalıştırmadan oluşturulması nedeniyle isteğe bağlı `_frame_phase_times` alanının bulunmamasından kaynaklanmıştır. Yukarıdaki beşinci commit bu durumu güvenli biçimde ele almış; son iki workflow da başarılı tamamlanmıştır.

## 8. Performans ölçümleri: doğru yorum ve sınırlar

Önceki teknik denetimde kaydedilen gözlemsel telemetri, NPC simülasyon aşamasının maliyetinin bazı ölçümlerde belirgin olduğunu göstermiştir:

- Frame ortalama süreleri yaklaşık 15.96–27.69 ms aralığında,
- frame p95 yaklaşık 37–88 ms,
- frame p99 yaklaşık 50–143 ms,
- NPC simülasyon ortalama süreleri yaklaşık 8.97–19.14 ms,
- NPC simülasyon p95 yaklaşık 30.8–77.3 ms,
- NPC simülasyon p99 yaklaşık 41.7–133 ms olarak gözlenmiştir.

Bu değerler farklı gözlem/çalıştırma örneklerinden gelen teşhis verileridir; makine bağımsız performans garantisi veya tek bir kontrollü benchmark sonucu olarak yorumlanmamalıdır. Telemetride NPC simülasyonunun alt sistemleri henüz ayrı ayrı ölçülmemektedir. Ayrıca `avg_fps` değeri ölçülen frame iş süresinden türetilmiştir; gerçek duvar saati/capped FPS ölçümü değildir.

**Önemli:** Aşama 1'in kabul ölçütü merkezi orkestrasyon ve davranış uyumluluğudur. Bu aşama, NPC başına işlem maliyetinde veya FPS'te sayısal iyileşme sağlandığını kanıtlamaz. Kaçınma sistemi nesnesinin yeniden kullanımını sağlar; algılama taraması, mesafe hesapları veya path query maliyetlerini henüz azaltmaz.

## 9. Açık kalan işler ve sonraki aşamalara devredilen konular

Aşağıdaki konular bilinçli olarak Aşama 1 dışında bırakılmıştır:

1. NPC algılama ve çevre taramasının hangi sıklıkta çalıştığının incelenmesi.
2. Tekrarlanan mesafe, komşuluk ve path sorgularının belirlenmesi.
3. NPC-NPC ve NPC-oyuncu etkileşim kontrollerinin maliyet analizi.
4. NPC sayısı arttığında maliyetin 1/10/25/50/100 NPC senaryolarıyla ölçülmesi.
5. NPC mantıksal simülasyonu ile görsel/animasyon güncellemelerinin ayrıştırılması ve görünürlük/LOD politikasının değerlendirilmesi.
6. Çarpışma/overlap çözümünün sorumluluk sınırlarının ayrı bir aşamada incelenmesi.

Bu konulara geçerken mevcut davranışların korunması temel ilkedir. Optimizasyon önerileri önce analiz ve ölçümle gerekçelendirilmeli; davranış semantiğini etkileyebilecek değişiklikler ayrı onay ve regresyon testleriyle ele alınmalıdır.

## 10. Kabul ölçütleri ve kapanış değerlendirmesi

| Kabul ölçütü | Sonuç |
|---|---|
| Merkezi NPC simülasyon giriş noktası mevcut | Karşılandı |
| Devriye → kaçınma → yoldaş sırası korunuyor | Karşılandı |
| Alt sistemlere ortak sabit delta aktarılıyor | Karşılandı |
| Hareket etmiş NPC kimlikleri birleştiriliyor | Karşılandı |
| Kaçınma sistemi uygun anahtarla yeniden kullanılıyor | Karşılandı |
| GameWindow merkezi giriş noktasını kullanıyor | Karşılandı |
| Sabit zaman adımlı döngü korunuyor | Karşılandı |
| Eski test adaptörleri için uyumluluk yolu mevcut | Karşılandı |
| Orkestrasyon ve oyun döngüsü testleri eklendi | Karşılandı |
| Son CI kontrolleri başarılı | Karşılandı |

### Nihai karar

**Aşama 1 — Merkezi NPC Simülasyon Orkestrasyonu kapatılmıştır.**

Bu kapanış, yalnızca bu raporda tanımlanan kapsam ve son CI sonuçları için geçerlidir. NPC algılama optimizasyonu, ölçek benchmark'ı, merkezi çarpışma çözümü veya görsel simülasyon LOD'si tamamlanmış sayılmaz.

Bir sonraki aşama: **Aşama 2 — NPC algılama ve çevre tarama maliyetlerinin azaltılması.** İlk çalışma salt kod incelemesi ve ölçüm olacaktır; davranış kodu, bulgular değerlendirilmeden değiştirilmemelidir.
