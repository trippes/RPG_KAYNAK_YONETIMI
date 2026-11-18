# Aşama 15 — Nihai Mimari, Dokümantasyon ve Entegrasyon Hazırlığı

> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Kaynak Yönetimi RPG  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Hedef entegrasyon dalı:** `demo_eldoria`  
> **Durum:** GENEL PLAN HAZIR — KULLANICI ONAYI BEKLİYOR  
> **Ön koşul:** Aşama 0–14 kapalı  
> **Uygulama durumu:** Başlamadı

## 1. Amaç

Laboratuvarda geliştirilmiş ve testlerle doğrulanmış hex dünya sistemini, ana oyuna kontrollü biçimde aktarılabilecek, sınırları ve etkileri açık bir teknik pakete dönüştürmek.

Aşama 15'in amacı yeni bir oyun özelliği geliştirmek veya ana oyuna kod taşımak değildir. Amaç; laboratuvarın gerçek mimarisini denetlemek, karar ve API sözleşmelerini tamamlamak, laboratuvar ile mevcut oyun arasındaki farkları dosya düzeyinde görünür kılmak ve ayrı bir entegrasyon aşamasının güvenli biçimde planlanabilmesi için gereken kanıtları hazırlamaktır.

Bu aşama tamamlandığında entegrasyonun kendiliğinden başlaması söz konusu değildir. `demo_eldoria` dalına aktarım, Aşama 16 kapsamında ve kullanıcının ayrıca vereceği açık onayla yürütülür.

## 2. Kapsam ve çalışma ilkeleri

- Yalnızca `experiment/hex-world-laboratory` dalında çalışılır.
- `main` ve `demo_eldoria` dalları okunabilir; bu aşamada bu dallara commit, merge veya dosya aktarımı yapılmaz.
- Pygame mevcut çalışma ve çizim teknolojisi olarak korunur. Motor değişimi veya Godot geçişi bu aşamanın konusu değildir.
- Laboratuvarın mevcut test edilmiş davranışı ve Aşama 14 içerik veri sözleşmeleri referans alınır.
- Gerçekleşen mimari, eski hedef belgelerle karşılaştırılır; artık geçerli olmayan hedefler sessizce doğru kabul edilmez.
- Belirsiz, doğrulanmamış veya uyumsuz noktalar varsayımla kapatılmaz; risk/açık karar olarak kaydedilir.
- Bu aşama yeni görsel özellik, yeni oynanış sistemi veya kapsamlı refaktör üretmez.

## 3. İş paketleri

### 15.1 — Gerçekleşen mimari denetimi

- Laboratuvarın güncel kaynak ağacını ve modül sınırlarını envanterlemek.
- Geometry, World, Movement, Physics, Spatial, Camera, Rendering, Entities, Interaction, Simulation, Diagnostics ve Content katmanlarını fiilî kodla karşılaştırmak.
- Bağımlılık yönlerini, Pygame bağımlılık sınırlarını, veri sahipliğini ve authoritative state akışını değerlendirmek.
- Aşama 6–14 kapanış raporları, güncel mimari sözleşme ve uygulama arasında tutarsızlıkları belirlemek.
- Tamamlanmış, kısmen tamamlanmış, kullanılmayan ve entegrasyon öncesi uyarlama gerektiren alanları sınıflandırmak.

**Çıktı:** Gerçekleşen mimari ve hedef mimari karşılaştırma raporu.

### 15.2 — Mimari kararların (ADR) son durumu

- Mevcut ADR kayıtlarını ve aşama kapanışlarında alınmış mimari kararları toplamak.
- Her kararı geçerli, değiştirilmiş, geçersiz veya açık olarak sınıflandırmak.
- Kararın gerekçesini, sonuçlarını ve ilgili kod/test kanıtını ilişkilendirmek.
- Entegrasyonu etkileyen açık kararları ve karar verilmeden ilerlenemeyecek konuları listelemek.

**Çıktı:** Güncel ADR envanteri ve açık karar listesi. Gerekli ADR güncellemeleri yalnızca kanıtlanmış kararları yansıtacak; yeni mimari kararlar kullanıcı onayı olmadan kesinleştirilmeyecektir.

### 15.3 — API, veri akışı ve sürüm sözleşmeleri

- Dışarıdan kullanılabilecek modül/API yüzeylerini ve iç uygulama ayrıntılarını ayırmak.
- Harita, hücre, WorldPoint, entity, spatial index, simulation tick, render snapshot ve content data akışlarını belgelemek.
- Aşama 14 Content Library JSON v1 ve Map Content JSON v1 sözleşmelerini mevcut MAP JSON v1 ve runtime snapshot v1 ile birlikte açıklamak.
- Kimlik, yaşam döngüsü, hata davranışı, sürümleme ve geriye dönük uyumluluk beklentilerini belirginleştirmek.
- Pygame gerektiren adaptörleri ve Pygame'den bağımsız çekirdek API'leri ayırmak.

**Çıktı:** API kataloğu, veri akış diyagramları ve veri/sürüm uyumluluğu özeti.

### 15.4 — Laboratuvar / ana oyun dosya eşleştirmesi

- `demo_eldoria` dalının mevcut yapısını salt okunur biçimde incelemek.
- Laboratuvardaki modülleri ana oyundaki mevcut modül ve sorumluluklarla eşleştirmek.
- Her bileşeni doğrudan aktarılabilir, uyarlama gerektirir, yeniden yazılmalı, ana oyunda karşılığı var veya kapsam dışı olarak sınıflandırmak.
- Aynı sorumluluğu üstlenen eski ve yeni sistemleri, çakışan giriş noktalarını ve olası dosya adı/namespace çakışmalarını belirlemek.
- Aşama 14 içerik modelleri ve renderer adaptörlerinin ana oyundaki olası tüketim noktalarını ayrıca göstermek.

**Çıktı:** Dosya ve modül bazlı eşleştirme tablosu. Bu iş paketi dosya kopyalamaz veya ana oyun dosyalarını değiştirmez.

### 15.5 — Bağımlılık, paketleme ve lisans uyumluluğu

- Laboratuvar ve ana oyunun Python sürüm aralıklarını, build backend'lerini, runtime ve geliştirme bağımlılıklarını karşılaştırmak.
- Pygame sürüm beklentilerini, platform gereksinimlerini ve olası sürüm çakışmalarını belirlemek.
- Paket adı, import yolu, entry point, kaynak dosya ve asset erişimi varsayımlarını incelemek.
- Üçüncü taraf bağımlılıkların lisanslarını ve dağıtım bildirimlerini kontrol etmek; doğrulanamayan lisansları açık risk olarak kaydetmek.
- Kurulum, paketleme ve temiz ortamda çalıştırma gereksinimlerini belirlemek.

**Çıktı:** Bağımlılık/paketleme matrisi ve lisans kontrol özeti.

### 15.6 — Entegrasyon sırası ve geri dönüş tasarımı

- Entegrasyonun bağımsız, küçük ve doğrulanabilir dilimlere ayrılabileceği sırayı önermek.
- Her dilimin ön koşullarını, etkilenecek dosyalarını ve bağımlılıklarını belirtmek.
- Eski sistemlerin ne zaman devreden çıkarılabileceğini ve hangi süre boyunca birlikte tutulmaları gerektiğini değerlendirmek.
- Her adım için geri dönüş noktası, veri yedekleme/koruma ihtiyacı ve başarısızlıkta durdurma ölçütü tanımlamak.
- Büyük birleştirme yerine kontrollü dosya bazlı aktarım/uyarlama yaklaşımını esas almak.

**Çıktı:** Aşama 16 için sıralı entegrasyon ve geri dönüş taslağı.

### 15.7 — Entegrasyon test ve kabul matrisi

- Laboratuvarda mevcut test kanıtlarını entegrasyon öncesi referans olarak sabitlemek.
- Ana oyun testleri, laboratuvar regresyonları, veri şeması uyumluluğu, import/başlatma, platform ve görsel kabul senaryolarını eşleştirmek.
- Kritik dünya davranışları için beklenen sonuçları ve kabul kanıtını tanımlamak.
- Otomatik test ile kullanıcının masaüstünde yapacağı manuel/görsel kabul adımlarını ayırmak.
- Entegrasyon sonrası performans karşılaştırması için ölçülecek temel metrikleri belirlemek.

**Çıktı:** Test matrisi ve entegrasyon kabul kontrol taslağı.

### 15.8 — Hazırlık değerlendirmesi ve entegrasyon kararı paketi

- Önceki iş paketlerinin çıktılarının tutarlılığını incelemek.
- Kritik engelleri, teknik borçları, açık kararları ve kabul edilmiş riskleri tek listede toplamak.
- Entegrasyona hazır, koşullu hazır veya hazır değil sonucunu kanıta dayalı vermek.
- Aşama 16 kapsamını, dosya sınırlarını, sırasını ve kullanıcı onayı gerektiren kararları sunmak.

**Çıktılar:**
- Nihai mimari raporu.
- Entegrasyon/migrasyon planı.
- Dosya eşleştirme tablosu.
- Bağımlılık ve lisans uyumluluk özeti.
- Test/kabul matrisi.
- Açık riskler ve entegrasyon ön koşulları listesi.

## 4. Kapsam dışı

Aşağıdakiler Aşama 15'te yapılmayacaktır:

- `main` veya `demo_eldoria` dallarına yazmak, merge etmek veya kod aktarmak.
- Laboratuvarı ana oyuna entegre etmek; bu Aşama 16'nın konusudur.
- Yeni hex dünya, fizik, hareket, NPC AI, pathfinding, görev, ekonomi veya savaş özelliği geliştirmek.
- Yeni çevresel nesne profilleri, animasyon, ışıklandırma, shader, biyom veya görsel efekt üretmek.
- İzometrik kamera/render dönüşümü veya yeni görsel sanat sistemi uygulamak.
- ELDORIA CONTENT EDITOR masaüstü uygulamasını veya GUI'sini geliştirmek.
- Pygame'den başka oyun motoruna geçmek.
- Sırf belgeyi tamamlamak için geniş çaplı kod refaktörü yapmak.

Aşama 15 bir hazırlık ve kanıtlama aşamasıdır; kendi başına oyunun görsel görünümünü değiştirmez.

## 5. Kabul koşulları

Aşama 15'in kabul edilebilmesi için:

1. Laboratuvarın gerçek mimarisi ile hedef mimari arasındaki farklar dosya/modül düzeyinde açıklanmış olmalı.
2. Kritik ADR kararları ve açık kararlar görünür, gerekçeli ve kanıta bağlı olmalı.
3. Temel API'ler, veri sahipliği ve veri akışları belgelenmiş olmalı.
4. Laboratuvar ile `demo_eldoria` arasında dosya/modül eşleştirme tablosu tamamlanmış olmalı.
5. Python/Pygame ve diğer bağımlılıkların sürüm, paketleme ve lisans etkileri incelenmiş olmalı.
6. Veri şemaları ve geriye dönük uyumluluk riskleri değerlendirilmiş olmalı.
7. Entegrasyon sırası, test matrisi ve geri dönüş stratejisi tanımlanmış olmalı.
8. Açık engeller ve kabul edilmiş riskler listelenmiş olmalı.
9. Laboratuvarın mevcut test/CI durumu yeniden doğrulanmış ve kanıtları rapora eklenmiş olmalı.
10. Kullanıcı nihai mimari ve entegrasyon hazırlık paketini inceleyip kabul etmiş olmalı.

Bu koşulların tamamlanması Aşama 16'yı otomatik başlatmaz. Aşama 16 için ayrıca genel/teknik plan ve açık kullanıcı onayı gerekir.

## 6. Önerilen iş sırası ve onay kapıları

1. Genel planın kullanıcı tarafından onaylanması.
2. 15.1 depo/mimari denetimi ve bulguların raporlanması.
3. Bulgulara göre 15.2–15.7 teknik planının hazırlanması ve kullanıcı onayı.
4. Onaylı teknik plan doğrultusunda dokümantasyon, eşleştirme ve uyumluluk çalışmalarının yürütülmesi.
5. Laboratuvar test/CI kanıtlarının güncel HEAD üzerinde doğrulanması.
6. Nihai hazırlık raporunun ve Aşama 16 önerisinin sunulması.
7. Kullanıcının manuel incelemesi ve Aşama 15 kapanış onayı.

## 7. Başlıca riskler

- Laboratuvar ile ana oyunun farklı mimari varsayımlara veya bağımlılık sürümlerine sahip olması.
- Aynı sorumluluğun iki tarafta farklı veri modelleriyle temsil edilmesi.
- Pygame'e bağlı adaptörlerin Pygame bağımsız çekirdekten yanlışlıkla ayrıştırılamaması.
- JSON şema sürümleri ve mevcut kayıtların uyumluluğunun bozulması.
- Eski sistemlerin kaldırılma zamanının erken veya geç seçilmesi.
- Lisans/dağıtım koşullarının eksik belgelenmesi.
- Entegrasyon sırasında kapsamın genişleyerek görsel veya oynanış geliştirmesine dönüşmesi.

Bu riskler denetim sırasında kanıtla güncellenecek; burada yazılanlar doğrulanmış kusur iddiası değildir.

## 8. Görsel hedefle ilişkisi

Eldoria'nın uzun vadeli hedefi Pygame ile ulaşılabilecek ölçüde modern, izometrik 2.5D RPG/açık dünya sunumudur. Aşama 15 bu görsel hedefi doğrudan gerçekleştiren bir aşama değildir. Bununla birlikte mimari rapor; mevcut kamera, render, procedural drawing, content data ve Pygame bağımlılık sınırlarının ileride izometrik sunum, katmanlı çevre çizimi ve gelişmiş görsel efektler için oluşturduğu imkânları ve sınırlamaları açıkça değerlendirmelidir. Bu değerlendirme yeni görsel sistem uygulamak veya motor değişikliği kararı almak anlamına gelmez.

## 9. Referanslar

- [Master Plan](HEX_WORLD_LAB_MASTER_PLAN.md)
- [Mimari Sözleşme](ARCHITECTURE_SPECIFICATION.md)
- [Geliştirme Kuralları](DEVELOPMENT_RULES.md)
- [Test ve Kabul Ölçütleri](TESTING_AND_ACCEPTANCE_CRITERIA.md)
- [Content Data API](CONTENT_DATA_API.md)
- [Aşama 14 resmî kapanış raporu](../reports/PHASE-14-CLOSURE-REPORT.md)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)

---

**Karar kapısı:** Bu belge yalnızca Aşama 15 genel planıdır. Kullanıcı onayı alınmadan ayrıntılı teknik plan/uygulama başlatılmaz. Aşama 16 entegrasyonu için ayrıca açık onay gerekir.
