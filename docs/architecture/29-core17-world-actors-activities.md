# Core 17 — World Actors, Activities & Simulation Integration

## Aktör modeli

`WorldActor` application katmanında tutulan, Core Entity’den ayrı bir gameplay
kaydını temsil eder. Aktör; kararlı `actor_id`, doğrulanmış `world_id`, rol,
aktiflik ve en fazla bir aktif faaliyet kimliği taşır. Core canonical state’e
aktör alanı eklenmemiştir.

`WorldActorRegistry`, bağlı `WorldManager` üzerinden dünya ilişkilerini
doğrular. Duplicate aktör kimlikleri reddedilir; snapshot’lar aktör kimliğine
göre sıralıdır. Aktör nesneleri dışarıya doğrudan mutable referans olarak
verilmez, `ActorView` döndürülür.

## Faaliyet yaşam döngüsü

Faaliyet durumları:

`PENDING → RUNNING → COMPLETED`

Hata yolları:

`PENDING/RUNNING → FAILED`

`PENDING/RUNNING → CANCELLED`

Bir aktör aynı anda en fazla bir aktif faaliyet yürütebilir. Terminal faaliyet
durumları yeniden başlatılamaz. Duplicate action event’leri terminal kaydı
değiştirmez.

## Tick ve dispatcher entegrasyonu

`ActorActivityManager`, yeni scheduler oluşturmaz. Üretim faaliyetlerini mevcut
`ProductionJobManager` action kimliğine bağlar ve aynı canonical dispatcher
event’lerini dinler. Üretim tamamlanınca önce mevcut job çıktıyı üretir, sonra
aktör faaliyeti `COMPLETED` olur. İptal ve hata durumlarında aktörün faaliyet
bağı temizlenir.

Kaynak toplama mevcut node→inventory işlemi atomik ve anında sonuçlandığı için
sahte bir süreli scheduler kullanılmaz. Toplama faaliyeti aynı tick içinde
`RUNNING` ve `COMPLETED` olur.

## Gameplay entegrasyonu

`GameplayService` şu ek application API’lerini sağlar:

- `register_actor`
- `actor` ve `actors_state`
- `set_actor_active`
- `start_gathering`
- `start_actor_production`
- `cancel_activity`
- `activity` ve `activities_state`

Servis her çağrıda güncel `SessionHolder.current` bundle’ını çözer. Aktif dünya,
aktör aktifliği, dünya ilişkisi, node, inventory, tarif, tesis ve kapasite
kuralları mevcut sahipleri tarafından doğrulanır.

## Çoklu aktör davranışı

Birden fazla aktör aynı registry’de bulunabilir. Aynı node üzerindeki stok
sınırlarını `WorldResourceNode` korur; aynı tesis üzerindeki kapasite sınırını
`ProductionFacility` korur. Başarısız bir aktör faaliyeti diğer aktörlerin
durumunu değiştirmez. Eşit zamanlılık veya çok iş parçacıklı yürütme eklenmemiştir.

## Persistence ve restore

Save belgesine geriye dönük uyumlu, opsiyonel `rpg-actors` v1 bölümü eklenmiştir.
Aktör kimliği, dünya, rol, aktiflik ve faaliyet kayıtları saklanabilir. Aktif
üretim faaliyetleri mevcut production job kimliği ve action kimliği üzerinden
restore edilir; girdiler ikinci kez tüketilmez ve tamamlanmış işler yeniden
çalıştırılmaz.

Restore aday session üzerinde yapılır. Dünya, aktör, faaliyet, node, inventory,
tesis ve production job referansları doğrulanmadan aktif bundle yayımlanmaz.
Eski save dosyalarında actor bölümü yoksa boş aktör registry’si oluşturulur.

`GameplayService` ve `ProductionChain` orkestrasyon nesneleri kalıcı değildir.
Aktör faaliyetlerinin production chain state’i otomatik olarak yeniden
oluşturulmaz; zincir persistence’ı bu aşamanın kapsamı dışındadır.

## Sınırlamalar

- Hareket, konum güncellemesi ve yol bulma yoktur.
- NPC karar verme veya davranış ağacı yoktur.
- Aktör başına tek aktif faaliyet politikası uygulanır.
- Otomatik tesis seçimi ve üretim kuyruğu yoktur.
- Savaş, beceri, ekonomi ve kullanıcı arayüzü yoktur.

Bu sınırlamalar sonraki aşamalara bırakılmıştır.
