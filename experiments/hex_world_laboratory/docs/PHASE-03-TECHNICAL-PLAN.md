# Aşama 3 — Hex Dünya Veri Modeli ve Runtime Teknik Planı

**Durum:** UYGULAMA VE TEKNİK DOĞRULAMA TAMAMLANDI — NİHAİ KULLANICI KABULÜ BEKLİYOR  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Laboratuvar:** `experiments/hex_world_laboratory/`  
**Bağımlı aşama:** Aşama 2 — Hex Geometri Çekirdeği (teknik olarak kabul edildi)

---

## Uygulama durumu ve plan geçmişi

Bu belge ilk onaylandığında 3.7 numarası bütünleşik doğrulama ve kapanış için ayrılmıştı. Aşama 3.6 sonrasında, ayrı teknik plan ve kullanıcı onayıyla runtime değişikliklerinin kalıcılaştırılması da 3.7 olarak eklendi. Bu nedenle runtime persistence'ın uygulama kayıtları `PHASE-03.7-TECHNICAL-PLAN.md` ve `PHASE-03.7-REPORT.md` belgelerinde; ilk plandaki bütünleşik kapanış ise bu belgenin son bütünleşik doğrulama maddesinde izlenir. Bu numaralandırma açıklaması mimari kapsamı değiştirmez.

Aşama 3.1–3.6 ve onaylanan runtime persistence uygulandı. Bütünleşik denetim ve kanıtlar `reports/PHASE-03-WORLD-REPORT.md` belgesinde kayıtlıdır. Teknik kapanış tamamlanmış olsa da kullanıcı nihai kabulü beklenmektedir; Aşama 4'e geçiş izni verilmiş değildir.

## 1. Amaç ve kapsam

Aşama 3'ün amacı, Aşama 2'de doğrulanan hex geometri çekirdeğini gerçek bir dünya ve harita veri modeline dönüştürmektir. Bu aşama; dünya/harita kimliklerini, hücre adreslerini ve verilerini, harita sınırlarını, salt okunur görünümü, kontrollü runtime değişikliklerini ve JSON tabanlı test haritası yüklemeyi tanımlar.

Ortaya çıkacak dünya modeli Pygame'den bağımsız olmalıdır. Geometri ile dünya verisi ayrı sorumluluklar olarak kalacak; dünya modeli çizim, kamera veya kullanıcı arayüzü bilgisi taşımayacaktır.

### 1.1 Aşama sonunda beklenen çıktılar

- Dünya, harita ve hücre adresi kimliklerinin ayrılması.
- Immutable hücre başlangıç verisi ve immutable harita tanımı.
- Açık hücre kümesine dayanan harita sınır politikası.
- Birden fazla haritayı yönetebilen `HexWorld`.
- Salt okunur `HexWorldView` ve kontrollü değişiklik sağlayan `HexWorldRuntime`.
- Sürümü tanımlı JSON test haritası ve doğrulamalı loader.
- Unit ve integration testleri.
- Aşama raporu ve laboratuvar README güncellemesi.

## 2. Onaylanmış tasarım kararları

| Karar alanı | Onaylanan tercih |
|---|---|
| Harita sınırı | Dikdörtgen aralık değil, açıkça tanımlanmış hücre kümesi |
| Harita dışı normal sorgu | `None` döndürür |
| Harita dışı katı sorgu | `UnknownCellError` yükseltir |
| Veri değişmezliği | Immutable harita tanımı + bağımsız ve kontrollü Runtime |
| Test haritası formatı | JSON |
| Geometri kaynağı | Aşama 2'deki `HexLayout` ve geometri API'si |
| Dünya/harita/hücre adresi | Ayrı kimlikler ve bileşik `CellAddress` |

Bu kararlar Aşama 3 uygulamasının bağlayıcı sözleşmesidir. Uygulama sırasında kapsamı veya kararları değiştirmek gerekirse önce gerekçe ve etki analizi sunulmalı, kullanıcı onayı alınmalıdır.

## 3. Mimari model ve sorumluluklar

### 3.1 Kimlik türleri

- **`WorldId`:** Bir dünyayı benzersiz biçimde tanımlar.
- **`MapId`:** Bir dünya içindeki haritayı tanımlar.
- **`CellAddress`:** Bir hücreyi dünya, harita ve axial koordinat bileşimiyle tanımlar.

Bileşik hücre adresi:

```python
CellAddress = (WorldId, MapId, q, r)
```

Aynı `(q, r)` axial koordinatı farklı haritalarda kullanılabilir; harita kimliği adresin parçası olduğundan adres çakışması oluşmaz. Kimliklerin eşitlik, hash ve doğrulama davranışı açık ve test edilebilir olmalıdır. Bir haritanın dünya kimliği ile onu barındıran dünyanın kimliği tutarlı olmak zorundadır.

### 3.2 `HexCellData`

`HexCellData`, bir hücrenin başlangıç/tanım verisini taşır. İlk sürümde alanlar:

- `terrain_id`: Arazi türünü belirten, boş olmayan tanımlayıcı.
- `is_walkable`: Hücrenin başlangıçta geçilebilir olup olmadığı.
- `has_obstacle`: Hücrede başlangıçta engel bulunup bulunmadığı.
- `metadata`: Opsiyonel ek veri.

Hücre verisi immutable olmalıdır. Metadata da yalnızca dış nesnenin değil, iç içe koleksiyonların ve değerlerin değiştirilmesini de engelleyecek şekilde derin değişmezlik/izolasyon sağlamalıdır. Mutable bir girdinin nesneye doğrudan referans olarak saklanması kabul edilmez.

### 3.3 `HexMapDefinition`

`HexMapDefinition`, haritanın değişmeyen tanımını temsil eder. En az şu bilgileri taşır:

- Harita kimliği ve adı.
- Bağlı olduğu dünya kimliği.
- Aşama 2 `HexLayout` geometrisi.
- Dünya koordinatlarındaki harita origin'i.
- Flat-top veya pointy-top yönelimi ve circumradius tabanlı hex boyutu.
- Hücre adresleri ve bunlara karşılık gelen immutable `HexCellData` kayıtları.

Harita sınırı, dikdörtgen bir genişlik/yükseklik alanı olarak değil, haritada gerçekten bulunan axial hücrelerin açık kümesi olarak tanımlanır. Kümede bulunmayan bir koordinat o haritada mevcut değildir. Hücre adreslerinin tekrarlanması veya aynı haritada aynı axial koordinatın birden fazla kez tanımlanması yükleme/kurulum hatasıdır.

Harita tanımı oluşturulduktan sonra kimlik, geometri, origin, hücre kümesi veya hücre başlangıç verileri dışarıdan değiştirilemez.

### 3.4 `HexWorld`

`HexWorld`, bir dünya kimliği altında birden fazla `HexMapDefinition` nesnesini yönetir.

Sorumlulukları:

- Dünya kimliğini taşımak.
- Haritaları `MapId` üzerinden benzersiz biçimde saklamak ve bulmak.
- Haritanın dünya kimliğiyle dünya kimliğinin tutarlılığını doğrulamak.
- Bir harita içindeki hücre adreslerini dünya/harita bağlamında çözümlemek.

Aynı axial koordinatlar farklı haritalarda geçerli olabilir. Bir haritanın kimliği başka bir harita kimliğiyle çakışamaz. Dünya koleksiyonu, dışarıya değiştirilebilir iç sözlük referansı veremez.

### 3.5 `HexWorldView`

`HexWorldView`, dünya verisine salt okunur erişim sağlar.

- Harita ve hücre sorguları sunar.
- İç sözlükleri, mutable koleksiyonları veya runtime'ın değiştirilebilir nesnelerini dışarıya açmaz.
- Döndürülen tanım/veri nesneleri immutable olur veya güvenli salt okunur temsiller olarak sunulur.
- Sorgu sonuçları dünya ve harita kimlikleriyle doğru kapsamda çözülür.

Normal sorgu davranışı:

- Hücre varsa ilgili hücre verisini döndürür.
- Hücre yoksa `None` döndürür.

Katı sorgu davranışı:

- Hücre varsa ilgili hücre verisini döndürür.
- Hücre yoksa `UnknownCellError` yükseltir.

Dünya veya harita kimliği bulunamaması da belirsiz bir sonuç üretmemeli; API sözleşmesinde açık ve tutarlı biçimde ele alınmalıdır.

### 3.6 `HexWorldRuntime`

`HexWorldRuntime`, immutable dünya/harita tanımlarından ayrılmış çalışma zamanı durumunu yönetir.

İlk sürümde runtime üzerinden değiştirilebilecek hücre durumu:

- Arazi türü (`terrain_id`).
- Geçilebilirlik (`is_walkable`).
- Engel durumu (`has_obstacle`).
- Gerekli görülen kontrollü runtime metadata alanları.

Runtime değişiklikleri başlangıç tanımını geriye dönük değiştirmemelidir. Runtime, hücre adresini, harita geometrisini, origin'i, orientation/radius değerlerini veya haritanın hücre varlık kümesini değiştiremez; yeni hücre ekleyemez ve var olan hücreyi haritadan silemez.

Runtime API'si yalnızca açıkça tanımlanmış değişiklik işlemlerini sunmalıdır. İç mutable depolama yapıları çağırana verilmemelidir. View üzerinden yapılan sorgular runtime'ın güncel durumunu gösterebilir; ancak döndürülen nesneler üzerinden doğrudan mutasyon yapılamaz.

## 4. Harita sınırları ve sorgu sözleşmesi

Harita sınırı, `HexMapDefinition` içinde kayıtlı hücre adreslerinin açık kümesidir.

Örnek:

- `(q=0, r=0)` kayıtlıysa hücre haritada vardır.
- `(q=1, r=0)` kayıtlı değilse hücre haritada yoktur.
- Bir koordinatın geometrik olarak başka bir hücrenin komşusu olması, o hücrenin haritada var olduğu anlamına gelmez.

Sorgu API'si en az iki açık davranış sunmalıdır:

1. **İsteğe bağlı sorgu:** Hücre yoksa `None`.
2. **Katı sorgu:** Hücre yoksa `UnknownCellError`.

Bu iki davranış unit testlerle güvence altına alınmalıdır. Harita dışı hücre sorgusu, yanlışlıkla varsayılan arazi veya otomatik hücre oluşturmamalıdır.

## 5. JSON harita formatı ve yükleme

### 5.1 Şema sürümü

JSON dosyası `schema_version` alanı taşımalıdır. Aşama 3 ilk sürümü `1` olacaktır. Desteklenmeyen sürüm, eksik zorunlu alan, hatalı alan türü, geçersiz kimlik, yinelenen axial koordinat veya geçersiz geometri girdisi kontrollü bir yükleme hatası üretmelidir.

Alanların zorunluluğu, türü, değer aralıkları, varsayılanların olup olmadığı ve benzersizlik kuralları loader uygulamasından önce açıkça tanımlanmalıdır. Sessiz veri düzeltmesi veya belirsiz varsayılan kullanımı yapılmamalıdır.

### 5.2 Örnek JSON

Aşağıdaki örnek hedef veri biçimini gösterir; nihai doğrulama kuralları bu belgedeki sözleşmeye göre uygulanacaktır.

```json
{
  "schema_version": 1,
  "world_id": "eldoria_test",
  "map_id": "starting_valley",
  "name": "Başlangıç Vadisi",
  "layout": {
    "orientation": "pointy",
    "radius": 1.0,
    "origin": {
      "x": 0.0,
      "y": 0.0
    }
  },
  "cells": [
    {
      "q": 0,
      "r": 0,
      "terrain_id": "grass",
      "is_walkable": true,
      "has_obstacle": false
    },
    {
      "q": 1,
      "r": 0,
      "terrain_id": "stone",
      "is_walkable": true,
      "has_obstacle": false
    }
  ]
}
```

### 5.3 Loader güvenlik ve bütünlük kuralları

- JSON önce bütünüyle parse ve validate edilmelidir.
- Tüm alanlar ve hücre kayıtları doğrulanmadan `HexWorld` veya `HexMapDefinition` dışarıya sunulmamalıdır.
- Hatalı dosyadan kısmi dünya/harita dönülmemelidir.
- Hata mesajları mümkün olduğunca alanı veya hücre kaydını belirtmelidir.
- Loader Pygame import etmemeli ve çizim/runtime UI bağımlılığı taşımamalıdır.

## 6. Önerilen dosya ve klasör yapısı

Mevcut ağaç uygulama öncesinde yeniden incelenecek; mevcut dosyalar korunacak ve hiçbir dosyanın üzerine gerekçesiz yazılmayacaktır.

```text
experiments/hex_world_laboratory/
├── src/hex_world_lab/
│   ├── geometry/                  # Aşama 2; korunacak
│   └── world/
│       ├── __init__.py
│       ├── identity.py
│       ├── cell.py
│       ├── map_definition.py
│       ├── boundaries.py
│       ├── world.py
│       ├── view.py
│       ├── runtime.py
│       └── loader.py
├── scenarios/
│   └── maps/
│       └── basic_test_map.json
├── tests/
│   ├── unit/
│   │   └── test_world/
│   │       ├── test_identity.py
│   │       ├── test_cell.py
│   │       ├── test_map_definition.py
│   │       ├── test_boundaries.py
│   │       ├── test_world.py
│   │       ├── test_view.py
│   │       └── test_runtime.py
│   └── integration/
│       └── test_world_loading.py
├── docs/
│   └── PHASE-03-TECHNICAL-PLAN.md
└── reports/
    └── PHASE-03-WORLD-REPORT.md
```

Dosya adları önerilen başlangıç düzenidir. Uygulama öncesi gerçek paket ve test yapısıyla karşılaştırılacak; gerekirse yalnızca aynı sorumlulukları daha tutarlı karşılayan isimlendirme, kullanıcıya gerekçesi açıklanarak önerilecektir.

## 7. Alt aşamalar ve uygulama sırası

Her alt aşama kendi testleriyle doğrulanmadan sonraki alt aşamaya geçilmeyecektir.

### 3.1 — Kimlik ve adres sistemi

**İşler**
- `WorldId`, `MapId` ve `CellAddress` türlerini tanımlamak.
- Kimlik doğrulama, eşitlik ve hash davranışlarını belirlemek.
- Hücre adresinin dünya ve harita kimliklerini taşımasını sağlamak.

**Testler**
- Aynı axial koordinatın farklı haritalarda farklı adres olması.
- Kimlik eşitliği ve farklılığı.
- Geçersiz/boş kimliklerin reddedilmesi.
- Adres bileşenlerinin tutarlılığı.

### 3.2 — Hücre veri modeli

**İşler**
- `HexCellData` immutable veri modelini oluşturmak.
- Arazi, geçilebilirlik, engel ve metadata alanlarını doğrulamak.
- Metadata için derin immutability/izolasyon sağlamak.

**Testler**
- Alanların beklenen tür ve değerleri kabul etmesi.
- Doğrudan alan atamasının engellenmesi.
- Girdi metadata'sı sonradan değiştirilse de hücre verisinin etkilenmemesi.
- Döndürülen metadata üzerinden iç durumun değiştirilememesi.

### 3.3 — Harita tanımı ve sınır politikası

**İşler**
- `HexMapDefinition` modelini oluşturmak.
- Aşama 2 `HexLayout` geometrisini kullanmak.
- Origin, orientation, circumradius ve açık hücre kümesini tanımlamak.
- Yinelenen hücre adreslerini reddetmek.

**Testler**
- Hücre kümesinde olan/olmayan koordinatlar.
- Harita tanımının immutable olması.
- Yinelenen axial koordinatların reddedilmesi.
- Geometri ve dünya kimliği tutarlılığı.

### 3.4 — `HexWorld` çoklu harita yönetimi

**İşler**
- Dünya kimliği ve harita koleksiyonunu oluşturmak.
- Haritaları `MapId` ile yönetmek.
- Dünya/harita kimliği tutarlılığını doğrulamak.

**Testler**
- Birden fazla haritanın aynı dünyada bulunması.
- Aynı axial koordinatın farklı haritalarda kullanılabilmesi.
- Yinelenen harita kimliğinin reddedilmesi.
- Başka dünyaya ait haritanın eklenememesi.
- İç koleksiyonun dışarıdan değiştirilememesi.

### 3.5 — View ve Runtime ayrımı

**İşler**
- Salt okunur `HexWorldView` sorgularını oluşturmak.
- Kontrollü runtime durum deposu ve güncelleme API'sini oluşturmak.
- Başlangıç tanımı ile runtime durumunu ayırmak.
- Runtime üzerinden geometri ve hücre varlık kümesinin değişmesini engellemek.

**Testler**
- View üzerinden veri mutasyonunun engellenmesi.
- Runtime değişikliğinin ilgili hücre durumuna yansıması.
- Başlangıç tanımının değişmeden kalması.
- Hücre adresi, geometri ve hücre varlık kümesinin korunması.
- Harita dışı normal/katı sorgu davranışı.

### 3.6 — JSON test haritası ve Loader

**İşler**
- Sürüm 1 JSON şemasını ve doğrulama kurallarını kesinleştirmek.
- `basic_test_map.json` dosyasını oluşturmak.
- JSON'dan dünya/harita modeline dönüşümü uygulamak.
- Kontrollü ve bağlamı açıklayan yükleme hataları sağlamak.

**Testler**
- Geçerli JSON yükleme.
- Eksik alan, yanlış tür, desteklenmeyen sürüm.
- Yinelenen hücre ve geçersiz geometri.
- Bozuk JSON.
- Hata durumunda kısmi dünya/harita üretilmemesi.
- Loader'ın Pygame olmadan import ve kullanım testi.

### Son bütünleşik doğrulama ve kapanış (ilk plandaki 3.7)

**İşler**
- Tüm laboratuvar testlerini çalıştırmak.
- Aşama 2 geometri testlerinin korunduğunu doğrulamak.
- Mimari ve API tutarlılığını gözden geçirmek.
- Aşama raporunu ve README durumunu güncellemek.
- Gerçek test sonuçları, kabul durumu ve bilinen sınırlamaları raporlamak.

**Kapanış şartı**
- Tüm kabul ölçütleri kanıtla karşılanmalı.
- Kullanıcı test/inceleme sonucunu değerlendirmeli.
- Kullanıcı kabulü olmadan aşama tamamlandı olarak işaretlenmemeli ve Aşama 4'e geçilmemelidir.

## 8. Kabul kriterleri

Aşama 3 ancak aşağıdaki maddelerin tamamı doğrulandığında teknik olarak kabul edilebilir:

1. Dünya ve harita kimlikleri ayrı kavramlardır.
2. Hücre adresi `WorldId`, `MapId`, `q`, `r` bileşenlerini içerir.
3. Aynı axial koordinat farklı haritalarda çakışmaz.
4. Harita sınırları açık hücre kümesiyle tanımlanır.
5. Harita dışı normal sorgu `None`, katı sorgu `UnknownCellError` üretir.
6. Hücre verisi ve harita tanımı immutable'dır; metadata dahil derin mutasyon sızıntısı yoktur.
7. View iç mutable depolamayı dışarı açmaz.
8. Runtime kontrollü hücre durumu günceller; geometriyi, adresleri veya hücre varlık kümesini değiştiremez.
9. JSON loader geçerli test haritasını yükler ve hatalı girdileri kontrollü biçimde reddeder.
10. Hatalı JSON'dan kısmi dünya/harita üretilmez.
11. Dünya modeli Pygame'den bağımsız import ve test edilebilir.
12. Aşama 2'nin mevcut 53 testi korunur ve regresyon oluşmaz.
13. Yeni unit ve integration testleri başarılıdır.
14. Aşama raporu ve README gerçek sonuçlarla güncellenmiştir.
15. Kullanıcı teknik sonucu inceleyip kabul etmiştir.

## 9. Kapsam dışı işler

Aşağıdaki işler Aşama 3'e dahil değildir:

- Karakter hareketi ve hareket interpolasyonu.
- Hücre geçişi, çarpışma, fizik ve sınırda karakter davranışı.
- Kamera, render, çizim ve Pygame dünya ekranı.
- NPC, kaynak, ekonomi veya zaman simülasyonu.
- Pathfinding ve navigasyon.
- Harita editörü veya görsel harita üretim aracı.
- Ana oyuna entegrasyon veya `demo_eldoria` dalına aktarım.
- Ağ/çok oyunculu senkronizasyon.
- Kaydetme/yükleme sisteminin ana oyun entegrasyonu.

Bu başlıklar sonraki aşamalarda ayrıca planlanmalıdır.

## 10. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Metadata'nın iç içe mutable kalması | Derin immutability ve girdi/çıktı izolasyon testleri |
| Dünya/harita/hücre kimliklerinin çakışması | Bileşik adres ve kimlik bütünlüğü testleri |
| Hatalı JSON'dan kısmi nesne oluşması | Önce tüm dosyayı doğrulama, sonra atomik nesne oluşturma |
| Runtime'ın geometriyi değiştirmesi | Geometriyi immutable tanımda tutma ve API sınır testleri |
| Aşama 2 regresyonu | Mevcut geometri testlerini değiştirmeden koruma ve tam test koşusu |
| Gereksiz erken karmaşıklık | Yalnızca bu aşamanın tanımlı alanlarını uygulama; kapsam dışını erteleme |
| Loader ile domain modelinin birbirine karışması | JSON parse/validation sorumluluğunu domain nesnelerinden ayırma |

## 11. Geliştirme ve doğrulama kuralları

- Uygulama yalnızca `experiment/hex-world-laboratory` dalında yapılacaktır.
- `main` ve `demo_eldoria` dallarına açık kullanıcı onayı olmadan yazma, merge, cherry-pick, rebase veya reset yapılmayacaktır.
- Her alt aşamadan önce ilgili dosya ağacı ve mevcut API tekrar incelenecektir.
- Her alt aşama sonunda hedefli testler çalıştırılacak; sonuçlar gerçek komut çıktısına dayandırılacaktır.
- Aşama 2 geometri modülleri ve testleri, Aşama 3 gereği olmadıkça değiştirilmeyecektir.
- Bir alt aşamanın onayı sonraki alt aşamaya otomatik onay sayılmayacaktır.
- Test edilmemiş davranış başarılı olarak raporlanmayacaktır.
- Commit öncesi değişen dosyalar gözden geçirilecek; commit sonrası branch HEAD ve dosya içerikleri GitHub üzerinden doğrulanacaktır.
- Plan dışı ihtiyaç çıkarsa uygulamaya devam etmek yerine etki analizi ve onay istenecektir.

## 12. Aşama 3 tamamlanma raporu

Uygulama tamamlandığında `reports/PHASE-03-WORLD-REPORT.md` oluşturulacak. Rapor en az şunları içermelidir:

- Uygulanan mimari ve API özeti.
- Gerçek dosya ağacı ve değişiklik listesi.
- Her alt aşamanın uygulama ve doğrulama sonucu.
- Çalıştırılan test komutları ve gerçek sonuçları.
- Aşama 2 regresyon kontrolü.
- Kabul kriterlerinin tek tek durumu.
- Bilinen sınırlamalar ve ertelenen işler.
- İlgili commit SHA'ları.
- Kullanıcı kabul durumu.

---

**Bu belge yalnızca onaylanmış teknik planı kaydeder. Belgenin kaydedilmesi kod uygulamasına başlama izni değildir. Aşama 3 kod uygulaması için ayrıca açık kullanıcı onayı gereklidir.**
