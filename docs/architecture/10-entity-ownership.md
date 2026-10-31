# Entity Ownership and World Aggregate

## Authoritative model

Core 2.0'da:

- `EntityRepository` entity object'lerinin tek authoritative store'udur.
- `WorldMembershipService` entity-to-world ilişkisinin tek authoritative
  registry'si ve tek writer'ıdır.
- `World` mevcut 1.x davranışı nedeniyle membership projection'ını taşır;
  canonical karar kaynağı değildir.
- `Entity.world_id` canonical mutable state değildir; compatibility döneminde
  read-only projection olarak tutulur.

Bu model `EntityManager.entities`, `World._entities` ve `Entity.world_id`
üçlüsündeki çift yazımı ortadan kaldırır.

FAZ 2 geçişinde `World._entities` ve `Entity.world_id` henüz kaldırılmaz.
Service başarılı işlemlerde bu iki projection'ı günceller. Doğrudan 1.x
`World.add_entity()` çağrıları canonical ownership yolu değildir.

FAZ 7'de `WorldMembershipService`, public `World.add_entity/remove_entity`
yerine açık compatibility projection writer'larını kullanır. Böylece yeni
application kodu public 1.x writer'larına bağlanmaz; `Entity.world_id` ve
`World._entities` yalnızca geriye dönük projection olarak kalır.

`core.foundation.EntityId` ve `core.foundation.WorldId` canonical stable ID
value object'leridir. Mevcut 1.x string ID'leri compatibility adapter ile
taşınır; bu fazda mevcut Entity/World sınıfları bunlara zorla dönüştürülmez.

## Invariants

1. Bir Entity aynı anda en fazla bir World'e ait olabilir.
2. EntityRepository'de olmayan Entity World membership'ine eklenemez.
3. Her membership EntityRepository'de karşılık gelen tek bir Entity ID'ye sahiptir.
4. Add/remove atomik command işlemidir.
5. Başarısız işlem repository, membership veya projection state'inde kısmi değişiklik bırakamaz.
6. World silinmeden önce membership policy uygulanır; orphan entity sessizce bırakılamaz.

## World aggregate sınırı

World içinde kalması gerekenler:

- World ID ve immutable metadata
- Bounds
- Entity ID membership set'i
- World-local domain state

World'ün sahip olmaması gerekenler:

- Global EntityRepository
- Global EventBus
- Application lifecycle
- Gameplay rules
- UI veya persistence

Clock, Scheduler ve EventQueue 2.x'te World'e gömülü state yerine runtime
context tarafından world scope ile yönetilir. 1.x `World` façade'si geçişte
mevcut davranışı korur.

Persistence boundary'de entity records `EntityId`, type, canonical state ve
canonical Position taşır. Membership ayrı `entity_id → world_id` mapping'idir.
`Entity.world_id` ve `World._entities` yalnızca compatibility projection'dır ve
save schema'ya dahil edilmez.

## Phase 9 restore

EntityRepository canonical entity kayıtlarının, WorldMembershipService ise
membership kayıtlarının authoritative sınırıdır. Restore bu iki kaynağı
projection alanlarından bağımsız hazırlar.
