# Aşama 15 — Kullanıcı İnceleme ve Kabul Kontrol Listesi

Aşama 15 görsel oyun değişikliği yapmaz. Bu kontrol listesi mimari belgelerin doğruluğunu ve A16 hazırlık kararını kullanıcıyla birlikte kabul etmek içindir.

## 1. Doküman incelemesi

- [ ] ADR durum tablosundaki kararların önceki aşamalardaki kararlarımızla uyumlu olduğunu kontrol et.
- [ ] API kataloğunda ana oyun ve laboratuvar sorumluluklarının doğru ayrıldığını kontrol et.
- [ ] Veri akışında sürekli WorldPoint ile hücre tabanlı EntityPosition farkının açık anlatıldığını kontrol et.
- [ ] Veri uyumluluk raporunda MAP v1 / Main Hex Map v2 ve Content JSON v1 ayrımlarını kontrol et.
- [ ] Entegrasyon eşleştirmesinde mevcut ana oyun sistemlerinin korunmasını kontrol et.
- [ ] Pygame / Pygame-CE ve lisans/asset provenance risklerini incele.
- [ ] A16 dilim ve rollback sırasını incele.
- [ ] Test/kabul matrisini incele.
- [ ] Nihai kararın A16 kod entegrasyonunu otomatik başlatmadığını teyit et.

## 2. Kullanıcı kararları

- [ ] Pygame mevcut motor olarak korunuyor; Godot geçişi bu planın dışında.
- [ ] İzometrik 2.5D görsel hedef ayrı gelecek aşama olarak kalıyor.
- [ ] Main'in mevcut hex runtime, renderer ve content safe store sistemleri korunuyor.
- [ ] A16 öncesi Pygame dağıtımı, movement authority, coordinate mapping ve content ownership kararları ayrıca ele alınacak.
- [ ] A16 için ayrı plan ve açık onay gerekecek.

## 3. Kabul sonucu

Kullanıcı notları:

- [ ] Belgeler kabul edildi.
- [ ] Düzeltme gerekiyor.
- [ ] Aşama 15 kapanışı onaylandı.

Not: Bu liste kullanıcı tarafından tamamlanmadan ve son A15 HEAD CI sonuçları doğrulanmadan Aşama 15 resmen kapatılmış sayılmaz.
