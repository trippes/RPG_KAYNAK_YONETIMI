# Hex World Laboratory — Geliştirme Kuralları

> **Durum:** Yürürlükteki çalışma prosedürü  
> **Üst belge:** [HEX_WORLD_LAB_MASTER_PLAN.md](HEX_WORLD_LAB_MASTER_PLAN.md)

## 1. Temel çalışma ilkesi

Laboratuvarda plansız değişiklik yapılmaz. Her iş; inceleme, kapsam tanımı, uygulama önerisi, açık kullanıcı onayı, uygulama, doğrulama ve raporlama adımlarından geçer.

Kullanıcının yalnızca inceleme veya planlama istemesi dosya değiştirme yetkisi vermez. Onay, yalnızca belirtilen kapsam için geçerlidir.

## 2. Branch güvenliği

- Laboratuvarın tek çalışma dalı `experiment/hex-world-laboratory`dır.
- `main` ve `demo_eldoria` laboratuvar uygulaması sırasında değiştirilmez.
- Her GitHub yazma işleminden önce hedef branch doğrulanır.
- Birden fazla commit gerektiren işlerde her yazma işleminde aynı açık branch adı kullanılır.
- Yazma sonrası branch HEAD ve dosya içeriği yeniden okunarak doğrulanır.
- Yanlış branch veya beklenmeyen HEAD görülürse işlem durdurulur.
- Kullanıcı ayrıca onaylamadıkça merge, cherry-pick, rebase, reset veya branch silme yapılmaz.

## 3. Görev yürütme protokolü

### 3.1 İnceleme
- Master Plan ve ilgili teknik belgeler okunur.
- Mevcut dosya ağacı ve ilgili kod incelenir.
- Aktif branch ve HEAD doğrulanır.
- Var olan davranış ve testler kaydedilir.

### 3.2 Plan
Plan şu bilgileri içermelidir:
- Amaç ve çözülen problem.
- Kapsam içi ve kapsam dışı işler.
- Değişecek/oluşturulacak dosyalar.
- Teknik yaklaşım ve alternatifler.
- Bağımlılık ve mimari etkiler.
- Test ve kabul ölçütleri.
- Riskler ve geri dönüş yaklaşımı.
- Beklenen commit sınırı.

### 3.3 Onay
Kullanıcı planı açıkça onaylamadan uygulama yapılmaz. Onay kapsamı aşan yeni ihtiyaç çıkarsa çalışma durdurulur ve yeni plan sunulur.

### 3.4 Uygulama
- Küçük, mantıksal ve gözden geçirilebilir değişiklikler yapılır.
- İlgisiz dosyalara dokunulmaz.
- Kod biçimi ve mevcut proje standartları korunur.
- Gereksiz soyutlama ve erken optimizasyondan kaçınılır.
- Yeni bağımlılık eklemek için gerekçe yazılır.
- Kullanıcıya ait değişikliklerin üzerine yazılmaz.

### 3.5 Doğrulama
- İlgili testler çalıştırılır.
- Mümkünse tüm laboratuvar testleri çalıştırılır.
- Görsel davranış gerekiyorsa ayrıca görsel kontrol yapılır.
- Performans iddiası için benchmark gerekir.
- Çalıştırılmayan test “geçti” olarak raporlanmaz.

### 3.6 Raporlama ve commit
Rapor; yapılan işi, dosyaları, test komutlarını, sonuçları, bilinen sorunları ve commit SHA'yı belirtir. Commit öncesi diff ve branch kontrolü yapılır; commit sonrası HEAD doğrulanır.

## 4. Mimari disiplin

- Geometry, World, Movement, Physics, Spatial, Camera, Rendering, Entities, Interaction, Simulation ve Diagnostics sorumlulukları korunur.
- Pygame, mümkün olduğunca giriş/çizim adaptörü sınırında kalır.
- Dünya koordinatı, hücre adresi ve ekran koordinatı birbirinin yerine kullanılamaz.
- WorldPosition hareketli varlıkların sürekli fiziksel konumudur; hücre merkezine otomatik snap yapılmaz.
- Hex geometri authoritative kalır.
- Yardımcı grid/spatial hash nihai geometri kararını vermez.
- Render ve kamera simülasyon state'ini değiştiremez.
- Tek bir kuralın birden fazla modülde kopyalanması önlenir.
- Mimari karar değişikliği ADR ve plan güncellemesi gerektirir.

## 5. Kod kalitesi

- Fonksiyon ve sınıflar tek, anlaşılır sorumluluk taşımalıdır.
- İsimler alan dilini yansıtmalı ve tutarlı olmalıdır.
- Tip ipuçları, özellikle koordinat ve geometri verilerinde kullanılmalıdır.
- Sayısal toleranslar rastgele farklı dosyalara dağılmamalıdır.
- Gizli global state ve beklenmeyen yan etkilerden kaçınılmalıdır.
- Hata durumları sessizce yutulmamalıdır.
- Debug kodu üretim davranışını değiştirmemelidir.
- Yeni modül, sorumluluğu ve bağımlılık yönü açıklanmadan eklenmemelidir.

## 6. Test disiplini

- Geometri ve simülasyon çekirdeği pencere açmadan test edilebilir olmalıdır.
- Her hata için mümkünse önce tekrarlanabilir test yazılır.
- Sınır, negatif koordinat, yüksek hız ve zaman adımı senaryoları ihmal edilmez.
- Testler deterministik olmalı; rastgele testlerde seed kaydedilmelidir.
- Görsel kabul testleri otomatik unit testin yerine geçmez.
- Benchmark, doğruluk testlerinin yerine geçmez.
- Başarısız testler çözülmeden aşama kapatılmaz veya açıkça kabul edilmiş istisna olarak kaydedilmez.

## 7. Bağımlılık ve ortam yönetimi

- Laboratuvar kendi `pyproject.toml` ve sanal ortamını kullanır.
- Ana oyun ortamına bağımlı olunmaz.
- Yeni runtime/test bağımlılıkları gerekçe ve sürüm aralığıyla eklenir.
- Kurulum adımları README'de güncel tutulur.
- Platforma özel komutlar açıkça etiketlenir.
- Ortam değişkenleri ve yerel sırlar depoya yazılmaz.

## 8. Belge yönetimi

- Master Plan ana yol haritasıdır.
- Mimari sözleşme katman ve veri sınırlarını açıklar.
- ADR tekil teknik kararları kaydeder.
- Aşama raporları gerçekleşen işi ve kanıtı kaydeder.
- Belgelerde öneri, kabul edilmiş karar ve gerçekleşmiş uygulama birbirinden açıkça ayrılır.
- Eski kararlar silinerek tarihçe kaybettirilmez; yeni ADR eski karara referans verir.

## 9. Yasak/izinsiz işlemler

Açık kullanıcı onayı olmadan:
- `main` veya `demo_eldoria` değiştirilmez.
- Laboratuvar dışındaki dosyalara dokunulmaz.
- Aşama kapsamı genişletilmez.
- Mimari karar sessizce değiştirilmez.
- Deney sonucu doğrulanmadan ana oyuna aktarım yapılmaz.
- Branch geçmişi yeniden yazılmaz.
- Büyük çaplı dosya silme/taşıma veya yeniden adlandırma yapılmaz.

## 10. Görev tamamlanma kontrolü

- [ ] Doğru branch üzerinde çalışıldı.
- [ ] Onaylanan kapsam aşılmadı.
- [ ] Değişen dosyalar listelendi.
- [ ] İlgili testler çalıştırıldı ve sonuçları kaydedildi.
- [ ] Görsel/performans kontrolleri gerekiyorsa yapıldı.
- [ ] Belgeler güncellendi.
- [ ] Commit SHA ve yeni HEAD doğrulandı.
- [ ] Açık sorunlar ve sonraki adım bildirildi.
