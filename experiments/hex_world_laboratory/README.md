# Eldoria Hex World Laboratory

Eldoria'nın canon altıgen dünya mimarisini bağımsız olarak araştırmak, prototiplemek ve doğrulamak için ayrılmış laboratuvar.

## Çalışma ilkeleri
- Kendi giriş noktası, bağımlılıkları ve testleri olacaktır.
- Ana oyunun modülleri bu laboratuvarın bağımlılığı olmayacaktır.
- Deney sonuçları doğrulanmadan `demo_eldoria` dalına aktarılmayacaktır.
- Her aşama öncesinde plan hazırlanır; kullanıcı onayı olmadan uygulamaya geçilmez.
- Laboratuvar çalışmaları yalnızca `experiment/hex-world-laboratory` dalında yürütülür.

## Ana belgeler
- [Master Plan](docs/HEX_WORLD_LAB_MASTER_PLAN.md) — ana yol haritası ve çalışma sözleşmesi.
- [Mimari Sözleşme](docs/ARCHITECTURE_SPECIFICATION.md) — hedef katmanlar ve veri sınırları.
- [Geliştirme Kuralları](docs/DEVELOPMENT_RULES.md) — onay, branch, uygulama ve commit prosedürü.
- [Test ve Kabul Ölçütleri](docs/TESTING_AND_ACCEPTANCE_CRITERIA.md) — doğrulama ve aşama kapıları.
- [ADR Şablonu](docs/decisions/ADR-TEMPLATE.md) — mimari karar kayıt formatı.
- [Aşama 0 Kapanış Raporu](reports/PHASE-00-FOUNDATION-CLOSURE.md) — planlama çıktılarının durumu.

## Mevcut durum
**Aşama 0 — Planlama ve yönetişim belgeleri hazır; kullanıcı kabulü bekleniyor.** Henüz çalışan hareket, geometri, fizik veya render uygulaması yok.
