# Core 16 — Playable Gameplay Loop

## Kapsam

Core 16, mevcut kaynak, inventory, üretim işi, tesis, kapasite ve canonical
simulation bileşenlerini tek bir application-level API altında koordine eder.
Yeni bir Core state alanı, zaman yöneticisi veya üretim motoru oluşturulmadı.

## GameplayService

`application.gameplay_service.GameplayService`, her işlemde güncel
`SessionHolder.current` bundle'ını çözer. Servis runtime state sahibi değildir;
aktif bundle değiştiğinde eski runtime-only zincir kayıtlarını temizler.

Sağlanan işlemler:

- `collect(node_id, inventory_id, quantity)`
- `start_production(recipe_id, inventory_id, facility_id)`
- `start_chain(chain_id, stages)`
- `advance_to(target_tick)` ve `advance_by(delta)`
- `save(path)` ve `load(path)`
- `inventory(id)` ve deterministik `state()` snapshot'ı

Bilinmeyen kimlikler, aktif dünya eksikliği, yanlış dünya düğümü, uyumsuz tesis
ve kapasite yetersizliği kontrollü hatayla reddedilir.

## Kaynak toplama

Toplama `WorldResourceNodeManager.extract` üzerinden yapılır. Bu API mevcut
`WorldResourceNode.extract_to` atomik işlem sözleşmesini kullanır: önce hedef
inventory snapshot'ı alınır, inventory ekleme veya node güncellemesi başarısız
olursa eski inventory korunur. Gameplay servisi ayrıca düğümün etkin dünyaya
ait olduğunu doğrular.

## Üretim ve zincir

Tek aşamalı üretim mevcut `ProductionFacility.start` ve
`ProductionJobManager.start` üzerinden yürür. Girdiler iş başlangıcında tüketilir,
çıktılar yalnızca tamamlanma event'i işlendiğinde eklenir.

Çok aşamalı üretim mevcut `ProductionChain` kullanılarak yapılır. Her aşama
recipe, inventory ve açık `facility_id` ile tanımlanır. İlk aşamanın çıktısı,
sonraki aşamanın başlangıcında mevcut job sözleşmesiyle tüketilir. Duplicate
completion veya aynı tick'in tekrarı ikinci job/çıktı oluşturmaz.

## Simülasyon zamanı

Servis `ProductionJobManager.advance_to/advance_by` çağırır. Bunlar aynı
`SimulationRuntime` üzerinde ilerler, tick listener'ları çalıştırır ve canonical
dispatcher event'lerini işler. Yeni bir timer veya doğrudan state değişimi yoktur.

## Gözlemleme

`GameplaySnapshotView` immutable dataclass'ları kullanır. Inventory stokları,
node miktarları, tesis rezervasyonları, job durumları ve runtime-only chain
durumları sıralı ve karşılaştırılabilir şekilde döndürülür. Sorgular zaman
ilerletmez, kaynak tüketmez ve iş başlatmaz.

## Persistence sınırı

Mevcut `GameApplication.save/load` ve Core 15 production snapshot sistemi
korunur. Aktif production job'ları, inventory/node/recipe verileri ve tesis
rezervasyon bağlantıları kaydedilip geri yüklenebilir.

Gameplay service nesnesi ve `ProductionChain` orkestrasyon durumu runtime-only
kalmıştır. Save/load sonrasında servis yeni bundle'a bağlanır ve eski chain
registry'sini temizler; aktif tekil production job'ları mevcut persistence
sözleşmesiyle kaldığı yerden devam eder. Zincirlerin otomatik yeniden kurulması
bu aşamada uygulanmamıştır ve sahte devamlılık oluşturulmaz.

## Bilinçli kapsam dışı işler

- Pygame veya UI (Core 16 kapsamı dışında; Faz 3 adapter katmanında uygulanmıştır.)
- otomatik tesis seçimi
- üretim kuyruğu ve önceliklendirme
- oyuncu/karakter/NPC simülasyonu
- para, ücret, enerji piyasası veya ekonomik denge
- chain state persistence

Bu sınırlamalar Core 16 gameplay loop'unun mevcut mimari sınırları içinde
kalmasını sağlar.
