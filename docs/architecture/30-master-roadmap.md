# RPG Kaynak Yönetimi — Ana Yol Haritası

Bu belge güncel kapsamın tek özetidir. Eski `00–29` belgeleri tasarım kararı
ve faz tarihçesi olarak korunur.

## Tamamlanan ve doğrulanmış temel

- Core 2.0/2.1: canonical state, world/entity ownership, tick, scheduler,
  event transport, dispatcher, restore validation ve atomic activation.
- Application persistence: birleşik save/load, candidate publication ve
  production/facility/actor snapshot'ları.
- Resource gameplay: inventory, node, gathering, recipe, production job,
  chain, capacity, facility ve `GameplayService`.
- Actor gameplay: actor registry, activity lifecycle ve actor persistence.
- Movement gameplay: actor konumu, deterministik lokasyon grafiği/BFS rota,
  canonical scheduler action'ı ve tick tamamlanma geçişi.
- Faz 3 dikey dilim: Pygame oyun döngüsü, ana menü, dünya/envanter/karakter
  ekranları, input/renderer katmanı ve gerçek `GameplayService` toplama/üretim
  akışları.
- Character–Actor entegrasyonu: otomatik actor oluşturma, çift yönlü bağlantı
  doğrulaması, stat okuma, save/load doğrulaması ve lokasyon etkileşimi.
- Ekonomi entegrasyonu: currency ledger, market teklifleri, atomik trade ve
  birleşik save/load persistence.
- Dünya etkileşimleri: kaynakların lokasyonlara bağlanması, lokasyon doğrulamalı
  toplama ve market stok rezervasyonu/teklif iptali.
- Quest/Dialogue/NPC ilk dikey dilimi: sosyal runtime, lokasyon doğrulamalı
  konuşma, ilişki state'i, quest başlatma ve persistence.
- Combat ilk teknik prototipi: deterministic combatant runtime, saldırı, HP,
  status süreleri ve persistence.
- UI ilk genişletmesi: market ekranı, market navigasyonu ve karakter ekranında
  aktif görevler.

## Mevcut durum denetimi — 26 Ekim 2026

Proje şu anda testlerle doğrulanmış, oynanabilir bir application prototipi
durumunda. Temel world/resource/actor/character/economy akışları birbirine
bağlıdır ve güncel tam test suite'i 764 testte hatasızdır.

Core mimari kapsamı tamamlanmış ve hardening testleriyle doğrulanmıştır.
Gameplay, içerik ve UI tarafında yeni özellikler mümkün olmakla birlikte Core
kapanış kriteri değildir. Core persistence state'i scheduler, dispatcher, event
queue ve aktif aksiyonları bilerek içermez; aktif gameplay işleri application
snapshot'larının sorumluluğundadır.

## Güncellenmiş uygulama sırası

### Faz A — Teknik borcun kapatılması — TAMAMLANDI

1. Combat runtime kuralları `combat/` domain paketine taşındı; application
   import’u geriye dönük uyumluluk katmanı olarak bırakıldı.
2. Dialogue, combat ve character creation ekranları gerçek service API’lerine
   bağlandı.
3. Quest objective ilerlemesi collect/talk/kill akışlarına bağlandı; quest
   tamamlanınca currency/item ödülleri dağıtılabiliyor.
4. Social/combat persistence schema/version doğrulaması, duplicate kimlik
   kontrolü ve candidate-load atomikliği güçlendirildi.

### Faz B — Oynanış derinliği — TAMAMLANDI

5. NPC–faction–reputation–relationship akışı tek sosyal modelde birleştirildi.
6. Merchant ekonomisine merchant identity, kısmi satış, teklif süresi,
   expiration ve stok rezervasyonu lifecycle'ı eklendi.
7. Combat encounter yönetimine initiative sırası, turn ilerlemesi, status
   tur geçişi ve encounter persistence eklendi.

### Faz C — İçerik ve kullanılabilirlik — TAMAMLANDI

8. `content_pack.py` ile oynanabilir görev zinciri eklendi: NPC konuşması →
   lokasyon seyahati → lokasyon doğrulamalı toplama → currency/item/reputation
   ödülü.
9. World, market, dialogue, combat ve character creation ekranlarında seyahat,
   seçim, hata/başarı geri bildirimi ve temel keyboard navigation eklendi.
10. `DemoContentIds` ve `populate_demo_content()` ile demo içerik sözleşmesi
    yeniden kurulabilir hale getirildi.

### Faz D — Kalite ve yayın hazırlığı — TAMAMLANDI

11. Application save envelope için explicit legacy v0→v1 migration,
    future-version reject davranışı ve optional domain payload uyumluluğu eklendi.
    Core persistence boundary sürüm doğrulama ile sınırlı tutuldu.
12. End-to-end save/load, UI smoke, failure-injection ve determinism testleri
    eklendi.
13. Combat primitive modülleri ve pygame camera/UI helper iskeletleri gerçek,
    test edilebilir API’lerle dolduruldu; README ve public API envanteri
    güncellendi.

## Bilinçli sınırlar

Yeni gameplay state Core canonical state'e eklenmez. Her sistem kendi
application/domain kaydını taşır, deterministic tick/event sözleşmesini tüketir
ve save/load'a yalnızca doğrulanmış snapshot olarak girer. Otomatik tesis seçimi,
çok iş parçacıklılığı, gerçek zamanlı duvar saati ve ağ çok oyuncululuğu kapsam
dışıdır.

## Güncel doğrulama

Ana test komutu `python -m unittest discover -s tests -t . -p "test_*.py"`'dir.
Faz geçişleri testlerle kanıtlanır; güncel doğrulama 764 test, 0 hata sonucudur.

Bu çalışma kopyasında Git metadata'sı bulunmadığından ilerleme karşılaştırması
commit tarihçesine göre yapılamaz. Bu nedenle bu roadmap'teki durum; mevcut
kaynak kodu, architecture belgeleri ve tekrar üretilebilir test sonucu ile
belirlenir.
