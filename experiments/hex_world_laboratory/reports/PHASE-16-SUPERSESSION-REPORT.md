# Aşama 16 — Eski Entegrasyon Taslağının Kapatılması ve Geçersiz Kılınması

**Tarih:** 20 Kasım 2026  
**Dal:** `experiment/hex-world-laboratory`  
**Karar:** KAPATILDI — UYGULAMA BAŞLAMADAN YENİDEN KAPSAMLANDIRILDI  
**Yeni referans:** [Aşama 17 — İzometrik Ana Oyun Ekranı Genel Planı](../docs/PHASE-17-ISOMETRIC-MAIN-GAME-PLAN.md)

## 1. Kapanışın anlamı

Eski Aşama 16, laboratuvar mekaniklerini mevcut demo mimarisine küçük adaptör dilimleriyle aktarmaya yönelik bir entegrasyon taslağı olarak hazırlanmıştı. Aşama 16 için genel/teknik uygulama planı onaylanıp kod uygulaması başlatılmamıştı. Bu nedenle Aşama 16, teknik olarak tamamlanmış bir entegrasyon aşaması değildir.

Kullanıcının 20 Kasım 2026 tarihli ürün yönü kararıyla eski Aşama 16 entegrasyon taslağı kapatılmış ve geçersiz kılınmıştır. Yeni öncelik, karakter yaratma ekranından sonra açılan ana oyun ekranında izometrik RPG sunumunu ve oynanabilir dikey dilimi oluşturmaktır.

## 2. Korunan geçmiş

- Aşamalar 0–15 kendi kapanış raporları, testleri, benchmarkları ve kullanıcı kabulleriyle tarihsel olarak kapalı kalır.
- Aşama 16'nın eski entegrasyon dilimleri ve hazırlık belgeleri silinmez; tarihsel kayıt olarak korunur.
- Laboratuvar kaynak kodu, testleri, asset/content tanımları ve raporları silinmez veya topluca yeniden yazılmaz.
- `main` ve `demo_eldoria` dallarına bu karar kapsamında yazılmaz; merge yapılmaz.

## 3. Neden yeniden planlandı?

Eski entegrasyon taslağı esas olarak paket/bağımlılık, state ownership, koordinat adaptörü, renderer bridge ve content coexistence risklerini çözmeye odaklanıyordu. Bunlar önemlidir; ancak tek başına oyuncunun göreceği ürün hedefini tanımlamıyordu.

Kaynak incelemesi, laboratuvar kamera dönüşümünün dünya X/Y koordinatlarını doğrudan ekran X/Y koordinatlarına taşıdığını ve mevcut render akışının izometrik/dimetric projeksiyon sunmadığını gösterdi. Ana oyunun mevcut `WorldTransform` ve `MainScreen` yapısı da karakter yaratma sonrası hedeflenen izometrik RPG sahnesini henüz sağlamıyor.

Bu nedenle entegrasyon sırası, önce isometrik görsel ve oynanabilir dikey dilim hedefini kanıtlayacak biçimde yeniden kurulmalıdır. Eski entegrasyon taslağındaki güvenlik ilkeleri (tek authoritative state, adapter, schema koruma, rollback, CI ve kullanıcı kabulü) geçerliliğini korur; ancak yeni ürün hedefinin yerine geçmez.

## 4. Yeni karar

Yeni planlama Aşama 17 ile başlar:

- İzometrik/dimetric projeksiyonun seçimi ve teknik sözleşmesi.
- Kamera, picking ve dünya/ekran dönüşümü.
- Zemin, terrain, elevation ve çevre varlıkları.
- Karakter/NPC görselleri, animasyon ve depth/occlusion.
- Işık, gölge ve atmosfer.
- Laboratuvar fizik/hareket/entity sistemlerinin izometrik sunumla birlikte çalışması.
- Karakter yaratma akışından açılan gerçek ana oyun ekranı dikey dilimi.
- Görsel, işlevsel, performans ve CI kabulü.

Ayrıntılı genel plan: [PHASE-17-ISOMETRIC-MAIN-GAME-PLAN.md](../docs/PHASE-17-ISOMETRIC-MAIN-GAME-PLAN.md).

## 5. Kapanış sınırı

**Aşama 16, kod entegrasyonu tamamlandığı için değil; eski entegrasyon yaklaşımı uygulanmadan önce iptal edilip yeni ürün hedefine göre değiştirildiği için kapatılmıştır.** Bu karar herhangi bir mekanik kazanımın tamamlandığı veya ana oyuna aktarıldığı iddiası değildir.

Aşama 17 genel planı kullanıcı onayına sunulmuştur. Onay alınmadan teknik uygulama başlamaz.
