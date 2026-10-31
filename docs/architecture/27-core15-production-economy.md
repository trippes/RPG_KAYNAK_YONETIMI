# Core 15 — Production Economy, Facilities, Labor, Energy & Integration

## 1. Kapsam ve karar özeti

Core 15 uygulaması mevcut `ProductionJobManager`, `ProductionCapacity`,
`ProductionChain`, `Recipe`, `Inventory` ve canonical runtime
sözleşmelerini koruyarak application katmanında tamamlandı.

Ana kararlar:

- Tesisler application/gameplay katmanında tutulur.
- Her tesis kendi mevcut `ProductionCapacity` havuzunun sahibidir.
- İkinci bir kapasite veya rezervasyon muhasebesi oluşturulmaz.
- Tesis seçimi explicit'tir; otomatik tesis seçimi eklenmemiştir.
- Tarifler geriye dönük uyumlu biçimde işlem süresi, tesis türü ve yetenek
  gereksinimi taşıyabilir.
- İş gücü, enerji ve yakıt ayrı ekonomi motorları olarak değil, mevcut
  `Recipe.inputs` içindeki `ResourceType`/`Quantity` girdileri olarak
  tüketilir.
- Tesis ve aktif tesis-job ilişkileri save/load kapsamına alınmıştır.
- Üretim zinciri orchestration state'i runtime-only bırakılmıştır.

## 2. Tesis modeli

`application/production_facility.py` içindeki `ProductionFacility` şu
alanları taşır:

- benzersiz `facility_id`
- `facility_type`
- `active`
- sıralı capability listesi
- tesisin sahibi olduğu `ProductionCapacity`
- aktif job-action ilişkileri

`ProductionFacilityRegistry` tesisleri kararlı ID ile kaydeder. Aynı tesis
ID'si ikinci kez eklenemez. Farklı tesislerin kapasite havuzları bağımsızdır.

Bir tesis:

- aktif olmalıdır,
- tarifin `facility_type` gereksinimiyle eşleşmelidir,
- tarifin tüm `required_capabilities` değerlerini taşımalıdır,
- kapasite rezervasyonu için mevcut `ProductionCapacity` API'sini kullanmalıdır.

Tesisler fiziksel bina, iş gücü, bakım veya enerji simülasyonu değildir.

## 3. Tarif sözleşmesi

`Recipe` mevcut üç argümanlı kullanımını korur. Yeni opsiyonel alanlar:

- `processing_time`: pozitif `Tick`, varsayılan 1.
- `facility_type`: opsiyonel tesis türü.
- `required_capabilities`: opsiyonel, duplicate içermeyen capability listesi.

Mevcut tarifler bu alanları vermeden çalışmaya devam eder.

İş gücü, enerji ve yakıt için ayrı alanlar oluşturulmadı. Bu girdiler mevcut
resource stoklarıyla temsil edilir:

- iş gücü: örneğin `ResourceType("labor")`
- enerji: örneğin `ResourceType("energy")`
- yakıt: fiziksel yakıt resource ID'si

Bunlar normal recipe input'larıdır ve başlangıçta atomik olarak tüketilir.
Ayrı ücret piyasası, enerji üretim sistemi veya yakıt dönüştürme sistemi
Core 15 kapsamına alınmamıştır.

## 4. İşlem süresi ve iş akışı

İşlem süresi deterministik integer tick'tir. Tesis üzerinden başlatılan job,
açık duration verilmezse tarifin `processing_time` değerini kullanır.

Başlatma sırası:

1. Tarif ve tesis uyumu doğrulanır.
2. Tesis aktifliği doğrulanır.
3. Tesis capability'leri doğrulanır.
4. Tesis kapasitesi rezerve edilir.
5. Mevcut `ProductionJobManager.start()` girdileri atomik tüketir.
6. Job mevcut canonical action/scheduler akışına eklenir.
7. Job başlatma başarısızsa kapasite bırakılır ve job manager input rollback
   uygular.

Çıktılar yalnızca mevcut production completion akışında oluşturulur.
Girdiler başlangıçta tüketilir; süreç boyunca kademeli tüketim uygulanmaz.

## 5. Kapasite yaşam döngüsü

- Başlangıçta kapasite rezerve edilir.
- Kapasite yetersizse iş kontrollü biçimde reddedilir.
- Bekleme kuyruğu oluşturulmaz.
- Completion, cancellation ve failure event'lerinde kapasite bırakılır.
- Duplicate event release işlemini ikinci kez etkilemez.
- Tesis registry'si kapasite rezervasyon toplamının tesis kapasitesini
  aşmadığını ve aktif job kayıtlarıyla eşleştiğini doğrular.
- Zincir aşaması tamamlandığında önceki tesis rezervasyonu bırakılır, sonraki
  aşama explicit tesis üzerinden yeni rezervasyon alır.

## 6. Üretim zinciri entegrasyonu

`ProductionChain` artık opsiyonel bir
`ProductionFacilityRegistry` ile kullanılabilir:

```text
ProductionChain(..., facilities=registry)
ProductionChainStage(..., facility_id="smelter-1")
```

Facility-bound chain'lerde her aşamanın tesis ID'si explicit olmalıdır.
Otomatik tesis seçimi sonraki aşamaya bırakılmıştır; böylece seçim
deterministik ve caller tarafından görünür kalır.

Bir aşama:

- uygun olmayan veya inactive tesiste başlatılamaz,
- girdi yetersizliğinde job oluşturmaz,
- failure/cancel sonrası sonraki aşamayı başlatmaz,
- önceki aşamanın çıktısını mevcut inventory üzerinden kullanır.

## 7. Persistence ve restore

Application save envelope'e geriye dönük uyumlu opsiyonel `production`
bölümü eklenmiştir:

- production schema: `rpg-production`, version 1
- facility ID/type/capacity/capabilities/active
- aktif job–facility binding
- kapasite miktarı

Yeni production bölümü olmayan eski save dosyaları geçerlidir. Yeni tesis
save'lerinde:

1. Dosya tamamen okunur ve doğrulanır.
2. Core ve gameplay candidate runtime oluşturulur.
3. Production job'ları ikinci kez input tüketmeden restore edilir.
4. Facility registry oluşturulur.
5. Aktif job–facility bağları candidate runtime'da kapasiteye yeniden
   bağlanır.
6. Tüm ilişkiler doğrulanınca candidate bundle yayımlanır.

Herhangi bir adım başarısız olursa mevcut aktif bundle değiştirilmez.

Üretim zinciri orchestration state'i bu aşamada persistence'a alınmamıştır.
Bu nedenle save/load sonrası zincirin hangi aşamada olduğu otomatik geri
kurulmaz; tesislere bağlı aktif tekil job'lar güvenli biçimde restore edilir.

## 8. Test kapsamı

Yeni tesis testleri:

`tests/test_application/test_production_facility.py`

Kapsanan davranışlar:

- uygun tesiste üretim
- tariften işlem süresi türetme
- inactive/incompatible tesis reddi
- bağımsız tesis kapasite izolasyonu
- explicit tesisli zincir
- aktif tesis job save/load round-trip
- restore sonrası kapasite rezervasyonunun korunması

Mevcut capacity, chain, production, persistence, candidate restore,
application save/load ve architecture testleri de çalıştırılmıştır.

## 9. Bilinçli olarak sonraya bırakılanlar

- Otomatik tesis seçimi
- Bekleme kuyruğu ve önceliklendirme
- İş gücü varlıklarının veya çalışanların simülasyonu
- Enerji üretim/dağıtım sistemi
- Yakıt dönüştürme ve enerji ekonomisi
- Ücret, piyasa, para ve fiyat sistemi
- Tesis bakım, kalite ve verimlilik katsayıları
- Üretim zinciri orchestration state persistence'ı

## 10. Mimari sınır doğrulaması

- `core/` değiştirilmedi.
- Core scheduler, dispatcher, action ve runtime sözleşmeleri değiştirilmedi.
- Core state'e facility, inventory, resource veya economy state eklenmedi.
- Legacy ActionManager ve legacy event queue canonical runtime'a bağlanmadı.
- Yeni harici bağımlılık eklenmedi.
- Mevcut job ve capacity sistemleri yeniden yazılmadı; tesisler onların
  application-level sahibi olarak bağlandı.

