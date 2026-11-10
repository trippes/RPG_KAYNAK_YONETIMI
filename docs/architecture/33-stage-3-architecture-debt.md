# Aşama 3 — Mimari Borcun Daraltılması

Bu belge, 10 Kasım 2026 tarihinde `fix/phase-1-critical-stability` dalında
yapılan mimari borç çalışmasının kapsamını ve bilinçli olarak korunan
uyumluluk sınırlarını kaydeder.

## 3.1 — Legacy kullanım envanteri

`core.compatibility.usage` statik tarayıcısı aşağıdaki kullanım biçimlerini
tanıyacak şekilde genişletildi:

- Doğrudan import ve `as` ile verilen import takma adları.
- Takma ad üzerinden sınıf oluşturma ve kalıtım.
- `import package.module as alias` biçimindeki modül takma adları.
- `import package.module` sonrasında tam nitelikli modül/sınıf çağrıları.

Tarayıcı AST tabanlıdır; kaynak kodu çalıştırmaz. Dinamik import, `getattr`,
runtime'da üretilen isimler ve reflection yoluyla çözülen kullanımları
kesin olarak tespit ettiği iddia edilmez. CI Linux işi raporu her çalıştırmada
çıktıya yazar. Rapor sayıları commit ve kaynak ağacına bağlıdır; tarihsel
belgelerdeki sayılar güncel ölçüm yerine kullanılamaz.

## 3.2 — Tick tekilleştirmesi

`core.time.Tick` tek canonical sınıftır. `time_system.Tick` ve
`time_system.tick.Tick` geriye dönük uyumluluk için aynı sınıfı yeniden
export eder. Böylece iki farklı Tick sınıfının tip kontrolü ve aritmetik
davranış ayrılığı ortadan kalkar.

`core.clock.GameClock` Tick tipini artık doğrudan `core.time` paketinden
alır. Takvim, GameTime, legacy Scheduler ve zaman sabitleri mevcut public
API'lerini korur.

## 3.3 — Position ayrımı

`core.domain.spatial.Position` immutable canonical değer nesnesi olarak
kalır ve yeni simulation/actor/movement kodunun tercih ettiği tiptir.

`core.entity.position.Position`, eski Entity API'sinin mutable davranışını
koruyan bir uyumluluk adaptörüne dönüştürüldü. Adaptör koordinatlarını
canonical immutable Position içinde tutar; `x`, `y`, `move()`,
`set_position()`, `copy()`, `distance_to()` ve `to_dict()` eski
kullanım biçimlerini sürdürür. `to_canonical()` immutable değeri açıkça
verir. Entity'nin public mutable pozisyon davranışı bu aşamada kaldırılmadı.

## 3.4 — Legacy World runtime sınırı

`LegacyWorldRuntime` clock, callback scheduler ve eski event queue
sahipliğini ayrı bir compatibility nesnesinde tutmaya devam eder.
`WorldRuntimeBoundary` canonical `SimulationRuntime` zamanını ilerletir,
World saatini projection olarak eşitler ve eski callback'leri aynı tick'te
çalıştırmak için legacy World runtime'ına sıfır uzunluklu advance uygular.
Legacy World olayları `LegacyEventAdapter` üzerinden canonical event
transport'a aktarılır.

Bu nedenle eski scheduler ve World saat API'si silinmedi: callback kullanan
legacy tüketiciler mevcut olduğu sürece bu sınır gereklidir. Canonical
simulation tick authoritative kaynaktır.

## 3.5 — Entity sahipliği ve projection

Canonical sahiplik `EntityRepository` ve `WorldMembershipService`
üzerindedir. Save/restore canonical membership kayıtlarından kurulur;
`Entity.world_id` ve `World._entities` restore kaynağı değildir.

Bu iki eski alan halen World compatibility projection'ını ve eski public
World sorgularını destekler. Bunların silinmesi bu aşamada güvenli değildir:
önce tüm public tüketicilerin migration'ı tamamlanmalıdır. Canonical sahiplik
kararı bu projection alanlarından alınmaz.

## 3.6 — Bağımlılık sınırları

Canonical `core.domain`, `core.time` ve `core.simulation` katmanlarının
legacy runtime paketlerine bağımlı olmaması mevcut architecture testleriyle
korunur. `GameClock` ve `LegacyWorldRuntime` eski runtime sınırında kalır;
uygulama geçişi `WorldRuntimeBoundary` üzerinden yürür.

Yeni testler Tick kimlik eşitliğini, canonical-backed Position adaptörünü,
scanner alias çözümlemesini ve Entity/World projection sınırını doğrular.

## 3.7 — Kapanış ve kalan borç

Aşama 3'ün güvenli geçiş kapsamı tamamlanmıştır:

- Tick için tek canonical sınıf vardır.
- Legacy Entity Position, canonical immutable değeri kullanan bir adaptördür.
- Legacy API taraması import alias ve modül alias biçimlerini kapsar.
- World runtime ve membership projection'ları canonical servislerin arkasında
  tutulur; silinmeleri için gerekli tüketici göçü açıkça ertelenmiştir.
- CI, legacy kullanım envanterini ve release-candidate doğrulamasını çalıştırır.

Kalan borç, compatibility yüzeyinin tümden kaldırılması değil; dış/legacy
tüketicilerin canonical API'lere taşınmasıdır. Özellikle callback scheduler,
World saat/event API'si, mutable Entity Position ve World membership
projection'ları sonraki major migration kararı olmadan kaldırılmamalıdır.

## CI doğrulaması

Kod değişikliklerini içeren `3648b91d55267d2323585314c8e36bea8cb37282`
commit'inde GitHub Actions Linux/Python 3.11 ve Windows/Python 3.12 işleri
başarılıdır. Release-candidate doğrulaması 880 testin tamamını çalıştırmış,
0 hata bildirmiş; compileall ve application smoke kontrolleri de geçmiştir.
