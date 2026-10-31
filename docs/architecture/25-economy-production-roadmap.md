# Core 14 Ekonomi ve Üretim Sistemi — Tarihsel Yol Haritası

> **Belge durumu:** Bu dosyanın ilk bölümleri Core 14A denetimi sırasında
> yazılmış tarihsel durum ve öneri kaydıdır. Güncel uygulanmış kapsam değildir.
> Core 14B–14D, Core 15, Core 16 ve Core 17 sonradan uygulanmıştır; güncel
> doğruluk kaynağı sırasıyla `26-production-chain-orchestration.md`,
> `27-core15-production-economy.md`, `28-core16-playable-gameplay-loop.md`,
> `29-core17-world-actors-activities.md` ve `30-master-roadmap.md` belgeleridir.

Bu belge Core 14A denetiminin sonucudur. Mevcut davranışları kod ve test
kanıtına göre ayırır; önerilen gelecek tasarımını uygulanmış özellik olarak
sunmaz. Bu ifade yalnızca belgenin oluşturulduğu Core 14A anını anlatır.

## 1. Mevcut sistemin gerçek durumu

Ekonomi paketi (`economy/`) mevcut olsa da Core 14A kapsamındaki gerçek
üretim davranışı `resources/` paketindedir. `resources` gameplay katmanıdır;
`core/` katmanına bağımlı değildir ve yalnızca mevcut
`SimulationRuntime`/action sözleşmesini tüketir.

Mevcut yapı şunları destekler:

- `ResourceType`, `Quantity` ve `ResourceUnit` ile kaynak tanımı.
- Dünya kaynak düğümleri ve tick tabanlı yenilenme.
- Envanter içi stok yönetimi ve atomik envanterler arası transfer.
- Girdi/çıktı tanımlayan immutable `Recipe` kayıtları.
- Anında üretim (`produce`) ve tick süreli üretim işleri
  (`ProductionJobManager`).
- Canonical simulation action/scheduler üzerinden deterministik işler.
- Inventory, node, recipe ve production job kayıtlarının gameplay snapshot
  içinde save/load edilmesi.

Mevcut sistemde piyasa, fiyat, para akışı, tesis, iş gücü, enerji, yakıt,
kapasite limiti veya üretim verimliliği uygulanmış bir ekonomi sözleşmesi
bulunmamaktadır.

## 2. Kaynak ve üretim API'leri

### Kaynak türleri ve miktarlar

`resources/resource.py` içindeki `ResourceType` kararlı bir kimliktir.
`Quantity` negatif olmayan integer değer ve `ResourceUnit` taşır.
Desteklenen birimler `item`, `kg` ve `liter`'dir.

`resources/inventory.py` içindeki `Inventory`:

- Aynı kaynak ve birimdeki stokları toplar.
- Aynı kaynak için farklı birimi reddeder.
- Yetersiz veya bulunmayan pozitif stok çıkarımını reddeder.
- Tamamen tüketilen stoğu kayıttan kaldırır.
- Kararlı sıralı immutable snapshot üretir.

### Transfer

`resources/transfer.py::transfer_resources` iki envanter arasında tek kaynak
ve miktar taşır. Birimler önceden doğrulanır; kaynak çıkarma veya hedef
ekleme hata verirse iki snapshot da geri yüklenir.

### Reçeteler

`resources/recipe.py::Recipe` kaynak türü ve miktar çiftlerinden oluşur.
Reçete immutable'dır, boş girdi/çıktıyı ve duplicate kaynakları reddeder,
girdileri/çıktıları deterministik sıralar ve kararlı bir recipe ID taşır.

Reçete belirli bir envanteri değil, `ResourceType` değerlerini referans alır.

### Anında üretim

`resources/production.py::produce` mevcut tek inventory üzerinde çalışır.
Önce tüm girdiler ve birimler doğrulanır; sonra girdiler tüketilir ve çıktılar
aynı inventory'ye eklenir. Hata olursa önceki snapshot geri yüklenir.

### Süreli üretim işleri

`resources/jobs.py::ProductionJobManager` bir işi tek bir `Inventory`, bir
`Recipe`, pozitif bir `Tick` süresi ve deterministik action ID ile başlatır.

- Başlangıçta girdiler bir kez tüketilir.
- Action mevcut `SimulationRuntime` içine planlanır.
- Başlangıç tick'inde iş `RUNNING` olur.
- Bitiş tick'inde çıktılar aynı inventory'ye eklenir.
- İptal girdileri bir kez iade eder ve çıktı üretmez.
- Çıktı yazma hatası işi `FAILED` yapar; inventory atomic kalır.
- Tekrarlanan completion callback ikinci çıktı üretmez.

Üretim süresi doğrudan simülasyon tick'i cinsindedir. Duvar saati veya timer
kullanılmaz.

## 3. Testlerle doğrulanmış özellikler

İlgili kanıt testleri:

- `tests/test_resources/test_value_objects.py`: kaynak kimliği, birim ve
  miktar doğrulaması.
- `tests/test_resources/test_inventory.py`: ekleme, çıkarma, birim uyuşmazlığı
  ve stok bütünlüğü.
- `tests/test_resources/test_transfer.py`: başarılı transfer ve atomic rollback.
- `tests/test_resources/test_production.py`: reçete, tüketim, üretim, birim
  kontrolü ve rollback.
- `tests/test_resources/test_jobs.py`: başlatma, tick geçişi, tamamlanma,
  iptal, failure, action çakışması ve scheduler sırası.
- `tests/test_resources/test_gameplay_integration.py`: node → inventory →
  üretim → çıktı → yenilenme → snapshot akışı.
- `tests/test_resources/test_persistence.py`: recipe/node/job/inventory
  serialization, active job restore ve reference doğrulamaları.
- `tests/test_application/test_candidate_restore.py` ve
  `test_game_application_save.py`: birleşik save/load ve failed restore
  sonrasında aktif bundle'ın korunması.
- `tests/test_resources/test_core13_world_cycle.py`: Core 13 dünya referansı,
  atomik çıkarma, batch/small-step eşdeğerliği ve load sonrası yenilenme.

Core 14A tarihindeki `python -m unittest` sonucu: **634 test, 0 hata**. Komut bazı
legacy script testlerinin stdout çıktısını da üretmektedir; bu başarısızlık
değildir. Güncel sonuç için aşağıdaki denetim kanıtına bakınız.

## 4. Eksik veya doğrulanmamış özellikler

Aşağıdakiler mevcut kod veya testlerde uygulanmış özellik olarak
doğrulanmamıştır:

- Tesis veya üretim hattı kapasitesi.
- Aynı tesis için eşzamanlı iş kotası.
- İş gücü, enerji, yakıt, bakım veya üretim kaybı.
- Verimlilik katsayısı, kalite veya yan ürün kuralları.
- Üretim işinin hedef inventory'sini kaynak inventory'sinden ayırma.
- Farklı inventory'ler arasında iş çıktısının otomatik taşınması.
- Üretim zinciri graph'i, bağımlılık çözümleme veya zincir orkestratörü.
- Pazar, fiyat, para, ticaret veya ekonomik denge.
- Üretim emri önceliği, kuyruk politikası veya tesis rezervasyonu.
- Çıktı kapasitesi dolu olduğunda bekleme/başarısızlık politikası.

## 5. Çok aşamalı üretim zinciri için önerilen tasarım

Cevher → külçe → alet örneği mevcut API'lerle sınırlı biçimde mümkündür:
ilk reçete cevher girdisi ve külçe çıktısı, ikinci reçete külçe girdisi ve alet
çıktısı taşır. İkinci iş, ilk iş tamamlanıp çıktı inventory'ye eklendikten
sonra başlatılmalıdır.

Bu, reçetelerin `ResourceType` referanslaması sayesinde mümkündür; ancak
sistem iki işi otomatik bağlamaz. Henüz zincir yöneticisi veya bağımlılık
graph'i yoktur.

Önerilen yön:

- Zincir orkestrasyonunu ayrı gameplay/application katmanında tutmak.
- Ara ürünler için mevcut `ResourceType` ve `Inventory` sözleşmesini
  kullanmak.
- Bağımlılıkları resource ID ve job ID referanslarıyla ifade etmek.
- Completion event'i ile sonraki job başlatma sınırını açıkça tanımlamak.
- Core state'e zincir veya ekonomi alanı eklememek.

Bu bölüm öneridir; uygulanmış özellik değildir.

## 6. Üretim kapasitesi ve tesisler için olası tasarım

Tesis kavramı mevcut değildir. İleride ayrı bir gameplay katmanı şu minimum
state'i taşıyabilir:

- Immutable facility ID, desteklenen recipe ID'leri ve eşzamanlı kapasite.
- Aktif job ID'leri ve kapasite rezervasyonları.
- Job başlatma öncesi recipe/facility/slot doğrulaması.
- Tamamlanma, iptal ve failure durumlarında slotun atomik serbest bırakılması.

İş gücü, enerji ve yakıt sonradan eklenebilir; fakat tüketim zamanı,
rezervasyon, iade ve failure sözleşmeleri önce belirlenmelidir. Bu mantığı
mevcut `ProductionJobManager` içine doğrudan eklemek yerine ayrı bir
gameplay servisi daha düşük riskli bir seçenek olarak değerlendirilmelidir.

## 7. Simülasyon tick'leriyle uyum

Mevcut `SimulationRuntime.advance_to()` ve `CanonicalScheduler` monoton
integer tick kullanır. `ProductionJobManager` action'ı başlangıç tick'inde
başlatır ve completion tick'inde tamamlar. Aynı tick'teki işler scheduler
sequence sırasına göre işlenir.

İleride:

- Zincir adımları yalnızca önceki completion event'inden sonra ilerlemeli.
- Aynı tick'teki ara ürün tüketimi açık event sırasına bağlanmalı.
- Büyük ve küçük `advance_to` adımları aynı sonucu üretmeli.
- Duvar saati, timer ve kontrolsüz rastgelelik kullanılmamalı.
- Kapasite rezervasyonları canonical zaman sıralamasına bağlı state geçişleri
  olmalı.

## 8. Persistence uyumluluğu

Birleşik save sistemi `GameSaveDocument` içinde Core document ile
`GameplaySnapshot`'ı taşır. Mevcut şemalar değiştirilmemelidir:

- Dış envelope: `rpg-game-save`, version 1.
- Gameplay snapshot: `rpg-gameplay`, version 1.
- Core persistence: mevcut Core sözleşmesi.

Yeni ekonomi alanları için öneri:

- Runtime servisleri canonical/persistence state içine konulmamalı.
- Facility, order, reservation ve chain kayıtları immutable record olmalı.
- ID referansları yükleme sırasında doğrulanmalı.
- Candidate restore tamamlanmadan aktif bundle değiştirilmemeli.
- Yeni alanlar için gerekirse açık migration boundary yazılmalı; eski şema
  sessizce değiştirilmemeli.
- Core/gameplay simulation tick eşitliği korunmalı.

Bu, mevcut `SessionHolder.publish`, `GameplaySnapshot.restore` ve
`GameApplication.load` aday akışıyla uyumludur.

## 9. Core 14B, 14C ve 14D için önerilen sıra

### Core 14B — Üretim zinciri temelleri

Mevcut API'leri kırmadan iki veya daha fazla reçetenin aynı inventory'de
ardışık çalıştığını kanıtlayan testler ve küçük bir application-level
orchestration sözleşmesi eklenmeli. Bu aşamada tesis veya yeni save şeması
eklenmemeli.

### Core 14C — Tesis ve kapasite

Üretim emrinin tesisini ve kapasite rezervasyonunu tanımlayan ayrı gameplay
state tasarlanmalı. Eşzamanlı işler, slot doluluğu, iptal, failure ve restore
senaryoları test edilmeden iş gücü/verimlilik eklenmemeli.

### Core 14D — Persistence ve ekonomik genişleme

Facility/order/reservation state için schema uyumluluğu, candidate restore ve
round-trip testleri eklenmeli. Bundan sonra enerji, yakıt, iş gücü, verimlilik
veya pazar gibi ekonomik sistemler küçük sözleşmeler halinde ele alınmalı.

## 10. Riskler ve mimari sınırlar

- `ProductionJobManager` işi tek bir inventory'ye bağlar; farklı inventory
  akışı ayrıca tasarlanmalıdır.
- Atomic tüketim aynı stok için güvenli başlangıç sağlar; tesis kapasitesi ve
  öncelik politikası yoktur.
- Runtime dispatcher consumer sırası yeni orkestrasyon tarafından açıkça
  korunmalıdır.
- Core katmanı gameplay kaynaklarını bilmemelidir.
- Core state'e ekonomi veya üretim runtime'ı eklenmemelidir.
- Save schema ve migration sözleşmeleri gerekçesiz değiştirilmemelidir.
- `economy/` paketi ayrıca denetlenmeden Core 14 üretim sözleşmesinin kanıtı
  sayılmamalıdır.

## Denetim kanıtı

Komut:

```text
python -m unittest
```

Core 14A tarihsel sonucu: **634 test başarılı, 0 başarısız**.

Bu bölüm, o tarihteki denetim kapsamını kaydeder. Güncel uygulama ve test
sonucu bu dosyadan türetilmemelidir.

## Güncel doğrulama

Güncel tam test komutu:

```text
python -m unittest discover -s tests -t . -p "test_*.py"
```

Son doğrulama: **672 test başarılı, 0 başarısız**. Uygulanmış production,
facility, gameplay ve actor API'leri ilgili Core 14B–17 belgelerinde
tanımlıdır.

## Core 14C/14D güncellemesi

Core 14B sonrasında application katmanında `ProductionChain` ile sıralı
üretim orkestrasyonu uygulanmıştır. Core 14C incelemesi, job süresinin zaten
pozitif integer `Tick` olarak belirlendiğini ve aynı runtime'da birden fazla
job'un çalışabildiğini; ancak kapasite rezervasyonunun bulunmadığını
doğrulamıştır.

Core 14C için fiziksel tesis modeli yerine opt-in bir
`application.ProductionCapacity` integer slot havuzu uygulanmıştır. Bu havuz
yalnızca kapasite-aware başlatılan job ve zincirleri sınırlar; mevcut
`ProductionJobManager` davranışı kapasitesiz kullanımda değişmez. Başlatma
öncesi rezervasyon, başlatma hatasında rollback ve completion/cancel/failure
sonrası release test edilmiştir. Kapasite yetersizliği için bekleme kuyruğu
yerine kontrollü ret seçilmiştir.

Zincir ve kapasite runtime-only kalmıştır. Yeni persistence schema alanı
eklenmemiştir; restore sonrası kapasite-aware aktif job'lar için açık
`ProductionCapacity.attach_existing()` çağrısı gerekir. Ayrıntılı karar ve
test kanıtı `docs/architecture/26-production-chain-orchestration.md` içinde
yer alır.

