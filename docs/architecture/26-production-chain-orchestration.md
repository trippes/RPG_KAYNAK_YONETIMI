# Core 14B — Üretim Zinciri Orkestrasyonu

## 1. Kapsam

Core 14B kapsamında application katmanında runtime-only bir üretim zinciri
orkestrasyonu eklendi. Zincir mevcut `ProductionJobManager`, `Recipe`,
`Inventory` ve `SimulationRuntime` sözleşmelerini kullanır.

Yeni modül:

`application/production_chain.py`

Core, kaynak üretim muhasebesi ve persistence şemaları değiştirilmemiştir.

Core 14C kararı olarak zincirler için kapasite desteği ayrıca ve opt-in
uygulanmıştır; mevcut kapasitesiz job davranışı değişmez.

## 2. Zincir ve aşama kavramları

`ProductionChainStage` şu değerleri taşır:

- `Recipe`
- `Inventory`
- Pozitif `Tick` süresi

`ProductionChain` sıralı stage listesini yönetir. Her aşama için en fazla
bir `ProductionJobManager.start()` çağrısı yapılır. Job ID'leri zincir ve
aşama index'inden deterministik olarak üretilir:

`production_job:<chain_id>:stage:<index>`

Zincir yalnızca orchestration state ve job referanslarını tutar. Kaynak
tüketimi ve çıktı üretimi zincirde tekrarlanmaz.

## 3. Durum geçişleri

Zincir durumları:

- `PENDING`: Henüz başlatılmadı.
- `RUNNING`: Bir aşama çalışıyor.
- `COMPLETED`: Son aşama tamamlandı.
- `FAILED`: Başlangıç, sonraki aşama başlatma veya mevcut job failure
  nedeniyle zincir durdu.
- `CANCELLED`: Aktif aşama iptal edildi.

Temel geçişler:

```text
PENDING --start--> RUNNING
PENDING --start error--> FAILED
RUNNING --stage completed--> RUNNING
RUNNING --last stage completed--> COMPLETED
RUNNING --stage failure--> FAILED
RUNNING --stage start error--> FAILED
RUNNING --cancel--> CANCELLED
```

Terminal durumlar yeniden başlatılamaz ve sonraki aşama başlatmaz.

## 4. Completion tespit mekanizması

Zincir, mevcut canonical dispatcher'a consumer olarak kaydolur. Completion
tespiti polling ile değil, mevcut `SimulationEvent` akışıyla yapılır:

- `ActionCompleted`: ilgili job gerçekten `COMPLETED` ise sonraki stage
  başlatılır.
- `ActionFailed`: zincir `FAILED` olur.
- `ActionCancelled`: zincir `CANCELLED` olur.

İlerleme public olarak `ProductionChain.advance_to()` veya
`advance_by()` üzerinden yapılır. Bu metot mevcut
`ProductionJobManager.advance_to()` çağrısını kullanır. Bir completion
dispatcher çevrimi içinde sonraki job aynı tick'te planlanır; zincir wrapper'ı
mevcut scheduler'ı aynı hedef tick'e bir kez daha ilerleterek job'un
başlangıç event'ini işler. Core dispatcher veya scheduler değiştirilmemiştir.

## 5. Hata ve iptal davranışları

- İlk aşama başlatılamazsa zincir `FAILED` olur ve job oluşturulmaz.
- İlk aşama başarısız olursa sonraki aşama oluşturulmaz.
- Sonraki aşamanın girdisi yetersizse mevcut ilk aşama çıktısı korunur, zincir
  `FAILED` olur ve ikinci job oluşturulmaz.
- Aktif job iptal edilirse mevcut `ProductionJobManager.cancel()` kullanılır;
  girdilerin iadesi job manager'a aittir.
- Zincir iptalinden sonra `advance_to()` yeni iş oluşturmaz.
- Beklenmeyen hata sessizce yutulmaz; zincir failure state'e alınır ve hata
  çağırana iletilir.

## 6. Yinelenmiş completion koruması

Her action ID yalnızca tek stage ile eşleştirilir. Zincir yalnızca mevcut
stage index'iyle eşleşen event'i işler. Önceki stage'in tekrarlanan completion
event'i ve terminal zincirin event'leri yok sayılır. Böylece aynı completion
bildirimi ikinci bir job oluşturamaz.

## 7. Inventory ve job sahipliği

Inventory muhasebesinin tek sahibi mevcut kaynak API'leridir:

- Girdileri `ProductionJobManager.start()` tüketir.
- Çıktıları `ProductionJobManager` completion akışı ekler.
- Zincir inventory üzerinde doğrudan `add()`, `remove()` veya transfer
  yapmaz.
- Aynı inventory kullanan ardışık aşamalar ara ürünü doğal olarak paylaşır.
- Farklı inventory'ler arasında otomatik taşıma uygulanmaz.

## 8. Kapasite entegrasyonu

`application/production_capacity.py::ProductionCapacity`, fiziksel tesis
modeli olmayan bağımsız bir integer slot havuzudur. Her rezervasyon bir veya
daha fazla slot tutar ve toplam rezervasyon kapasiteyi aşamaz.

- `ProductionCapacity.start()` önce rezervasyon yapar, sonra mevcut
  `ProductionJobManager.start()` çağrısını yapar.
- Job başlatma başarısız olursa rezervasyon geri bırakılır ve girdiler mevcut
  job manager tarafından geri alınır.
- Completion, cancellation ve failure event'leri rezervasyonu bırakır.
- `ProductionChain(..., capacity=pool)` aşama geçişinde önceki rezervasyonu
  bırakır, sonraki aşama için yeniden rezervasyon alır.
- Kapasite yetersizliği bekleme kuyruğu oluşturmaz; kontrollü ret politikası
  uygulanır. Bu karar, mevcut scheduler'a yeni kuyruk semantiği eklememek için
  seçilmiştir.
- Aynı havuza bağlı bağımsız zincirler ve job'lar aynı toplam slot sınırını
  paylaşır.

Kapasite bir tesis, iş gücü, enerji veya verimlilik modeli değildir. Bunlar
gelecek aşamalara bırakılmıştır.

## 9. Persistence kapsamı

Zincir ve kapasite havuzu runtime-only'dir ve bu aşamada save/load kapsamına
alınmamıştır.

Yeni persistence alanı, schema sürümü veya migration eklenmemiştir. Mevcut
tekil production job save/load davranışı korunur. Zincir nesneleri
`SessionBundle` içine zorunlu global state olarak eklenmemiştir; caller,
mevcut bundle içindeki `production_jobs` ile zincir oluşturur.

Bu nedenle aktif bir zincirin save/load sırasında zincir orchestration durumu
ve kapasite rezervasyonu otomatik kurulmaz. Restore sonrası kapasite-aware
aktif job'lar için caller, hangi job'ların havuza ait olduğunu bilerek
`ProductionCapacity.attach_existing()` çağırmalıdır. Generic restored job'lar
sessizce kapasiteye atanmaz. Bu açık runtime-only sınır, yeni persistence
şeması değiştirmeden kapasite muhasebesini belirsizleştirmemek için seçilmiştir.

## 10. Test kanıtı

Yeni test dosyası:

`tests/test_application/test_production_chain.py`
`tests/test_application/test_production_capacity.py`

Doğrulanan senaryolar:

- İki aşamalı gerçek runtime zincirinin tamamlanması.
- İlk çıktının ikinci girdisi olarak kullanılması.
- Completion öncesi ikinci job'un başlamaması.
- Yinelenen completion'ın duplicate job oluşturmaması.
- İlk aşama failure.
- Sonraki aşama için yetersiz girdi.
- Aktif zincirin iptali.
- Başlangıç hatasının zinciri `FAILED` yapması.
- Kapasite sınırında ikinci job'un kontrollü reddi.
- Completion, cancellation ve failure sonrası kapasite serbest bırakılması.
- Kapasite paylaşan bağımsız zincirlerin birbirini aşırı tahsis etmemesi.
- Zincir aşamaları arasında kapasite serbest bırakma ve yeniden rezervasyon.
- Mevcut job, gameplay integration, persistence, candidate restore ve
  application save/load testleriyle uyum.

## 11. Bilinen sınırlamalar

- Zincir ve kapasite reservation state'i persistence'a dahil değildir.
- Tesis, bekleme kuyruğu, iş gücü, enerji, yakıt ve verimlilik yoktur.
- Otomatik inventory taşıması yoktur.
- Paralel production chain planlaması yoktur.
- Zincir yalnızca mevcut production job completion event'lerini izler.
- Caller zincirin `advance_to()` akışını kullanmalıdır; doğrudan job manager
  ilerletmek zincir wrapper'ının aynı-tick flush kolaylığını sağlamaz.
- Save/load sonrası capacity-aware aktif job'lar için açık
  `attach_existing()` çağrısı gerekir.

## 12. Değişen katmanlar

Değişiklikler yalnızca application/gameplay katmanı ve test/documentation
alanındadır:

- `application/production_chain.py`
- `application/production_capacity.py`
- `application/__init__.py`
- `tests/test_application/test_production_chain.py`
- Bu belge

`core/` altında değişiklik yapılmamıştır. Yeni üçüncü taraf bağımlılık
eklenmemiştir.

