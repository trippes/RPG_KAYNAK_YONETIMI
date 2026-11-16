# Aşama 3.6 — Harita Dosya Sistemi ve JSON Veri Doğrulama Teknik Planı

**Durum:** KULLANICI ONAYI ALINDI — UYGULAMA VE DOĞRULAMA TAMAMLANDI (249 TEST)
**Kapanış raporu:** [PHASE-03.6-CLOSURE-REPORT.md](../reports/PHASE-03.6-CLOSURE-REPORT.md)  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Laboratuvar kökü:** `experiments/hex_world_laboratory/`  
**Ön koşul:** Aşama 3.1–3.5  
**Planın dayanağı:** `PHASE-03-TECHNICAL-PLAN.md`, `PHASE-03.5-TECHNICAL-PLAN.md` ve mevcut dünya modeli

---

## 1. Amaç

Aşama 3.6'nın amacı, mevcut immutable harita başlangıç tanımını kalıcı, sürümlendirilmiş ve doğrulanabilir bir dosya biçiminde saklamaktır.

Bu aşamanın sonunda laboratuvar:

1. Bir `HexMapDefinition` nesnesini tanımlı JSON şemasına göre serileştirebilmeli.
2. JSON içeriğini doğrulayıp yeniden `HexMapDefinition` nesnesine dönüştürebilmeli.
3. Harita tanımını UTF-8 JSON dosyasına güvenli biçimde kaydedebilmeli.
4. Kaydedilmiş haritayı dosyadan okuyabilmeli.
5. Hatalı, eksik, tutarsız veya desteklenmeyen dosyaları kontrollü hatalarla reddedebilmeli.
6. Yükleme başarısız olduğunda kısmi harita veya kısmi dünya kaydı oluşturmamalı.
7. Kaydet-yükle gidiş-dönüşünde başlangıç verisinin kayıpsız korunduğunu testlerle kanıtlamalı.

Bu aşama yalnızca **haritanın immutable başlangıç tanımını** kapsar. Oyun sırasında oluşan runtime değişikliklerinin kalıcı kaydı Aşama 3.7'nin konusudur.

## 2. Mevcut mimariyle uyum ve korunacak sözleşmeler

Aşama 3.6 yeni bir dünya modeli kurmayacak; mevcut sınıfları dosya katmanına bağlayacaktır.

| Mevcut bileşen | Aşama 3.6'daki rolü |
|---|---|
| `WorldId`, `MapId` | JSON kimlik alanlarının tipli kimlik nesnelerine dönüştürülmesi |
| `AxialCoord` | Hücrelerin `(q, r)` adreslerinin temsil edilmesi |
| `HexLayout` | Orientation, circumradius ve origin bilgisinin tek geometri kaynağı olması |
| `HexCellData` | Hücre başlangıç verisinin ve metadata'nın doğrulanması |
| `HexMapDefinition` | Deserializer'ın üreteceği immutable harita tanımı |
| `MapRegistry` | Yüklenmiş haritanın daha sonra dünyaya kaydedilmesi; dosya katmanının doğrudan registry yönetmemesi |
| `HexWorldRuntime` | Bu aşamada dosyaya yazılmaması ve değiştirilmemesi |
| `HexWorldView` | Bu aşamada değiştirilmemesi |

Bağlayıcı ilkeler:

- Geometri hesabı yalnızca Aşama 2 geometri API'sinden yapılır; JSON katmanı ikinci bir hex matematiği uygulamaz.
- Harita sınırı, mevcut tasarımdaki gibi açık hücre kümesidir. JSON'da yalnızca gerçekten var olan hücreler listelenir.
- Aynı `(q, r)` koordinatı farklı haritalarda kullanılabilir; benzersizlik yalnızca tek bir harita içindeki hücre listesi için aranır.
- `HexMapDefinition` ve `HexCellData` immutable kalır.
- Metadata'nın iç içe JSON değerleri korunur; mutable JSON girdileri doğrudan model nesnelerine referans olarak verilmez.
- Persistence modülü Pygame'e ve ana oyun modüllerine bağımlı olmaz.
- Bu aşama kayıtlı harita kataloğu, otomatik yükleme/tahliye veya bellek yönetimi politikası eklemez.

## 3. Kapsam ve kapsam dışı

### 3.1 Dahil

- JSON şema v1 sözleşmesinin kesinleştirilmesi.
- Model → JSON dönüşümü (serializer).
- JSON → model dönüşümü (deserializer).
- Ayrı veri doğrulama katmanı (validator).
- UTF-8 dosya okuma ve güvenli dosya yazma.
- Kontrollü persistence hata türleri.
- Test haritası JSON dosyası.
- Unit, integration ve regresyon testleri.
- Kullanım ve format dokümantasyonu.
- Aşama 3.6 kapanış raporu.

### 3.2 Hariç

- `HexWorldRuntime` override kayıtlarının kalıcılaştırılması.
- Oyuncu, NPC, kaynak, eşya veya bina nesnelerinin saklanması.
- Harita editörü veya oyun içi harita oluşturma aracı.
- Haritalar arası kapı/geçiş sistemi ve iç mekân üretimi.
- Otomatik harita yükleme, cache, tahliye veya offline simülasyon.
- Ana oyuna entegrasyon veya `main` / `demo_eldoria` dallarında değişiklik.
- Ağ üzerinden senkronizasyon, sıkıştırma, veritabanı veya alternatif dosya biçimi.
- Genel amaçlı save-game sistemi.

## 4. JSON şema v1 sözleşmesi

### 4.1 Önerilen dosya biçimi

Aşağıdaki örnek şema v1'in hedef yapısını gösterir:

```json
{
  "schema_version": 1,
  "world_id": "eldoria",
  "map_id": "starting_valley",
  "name": "Başlangıç Vadisi",
  "layout": {
    "orientation": "pointy_top",
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
      "has_obstacle": false,
      "metadata": null
    },
    {
      "q": 1,
      "r": 0,
      "terrain_id": "stone",
      "is_walkable": true,
      "has_obstacle": false,
      "metadata": {
        "surface": "rocky",
        "tags": ["natural", "rough"]
      }
    }
  ]
}
```

Bu sözleşme mevcut modelin alanlarına göre düzenlenmiştir. `orientation` değerleri mevcut enum değerleriyle birebir eşleşir: `flat_top` ve `pointy_top`.

### 4.2 Alan kuralları

| Alan | Zorunlu | Tür / kural |
|---|---:|---|
| `schema_version` | Evet | Tam sayı; yalnızca `1` desteklenir |
| `world_id` | Evet | Boş olmayan string |
| `map_id` | Evet | Boş olmayan string |
| `name` | Evet | Boş veya yalnızca whitespace olmayan string |
| `layout` | Evet | Nesne |
| `layout.orientation` | Evet | `flat_top` veya `pointy_top` |
| `layout.radius` | Evet | Sonlu, sıfırdan büyük sayı |
| `layout.origin` | Evet | Nesne |
| `layout.origin.x`, `y` | Evet | Sonlu sayılar |
| `cells` | Evet | Hücre nesnelerinden oluşan dizi; boş dizi geçerlidir |
| `cells[].q`, `r` | Evet | Boolean olmayan tam sayılar |
| `cells[].terrain_id` | Evet | Boş olmayan string |
| `cells[].is_walkable` | Evet | Boolean |
| `cells[].has_obstacle` | Evet | Boolean |
| `cells[].metadata` | Evet | JSON null veya string anahtarlı JSON nesnesi |

Şema v1'de nesne seviyelerinde tanınmayan alanlar reddedilecektir. Böylece yazım hataları sessizce yutulmaz ve sürüm yükseltme gerektiren alanlar yanlışlıkla mevcut sürümde kabul edilmez. İleriye dönük yeni alanlar, yeni bir şema sürümü veya açıkça onaylanmış geriye uyumluluk kuralı ile eklenir.

### 4.3 Metadata kuralları

- Metadata, mevcut `HexCellData` sözleşmesine uygun JSON değerlerinden oluşur.
- İzin verilen değerler: null, string, boolean, integer, sonlu float, string anahtarlı nesne ve dizi.
- Nesne anahtarları string olmalıdır.
- NaN ve sonsuz sayılar reddedilir.
- Döngüsel Python nesneleri JSON girdisi olamayacağı için serializer/model sınırında reddedilir.
- `metadata: null` ile `metadata: {}` farklı değerler olarak korunur.
- JSON dizileri modelin immutable tuple temsiline dönüştürülebilir; serializer bunları tekrar JSON dizisi olarak yazar.
- Metadata'nın sırası anlamsal değildir; deterministik çıktı için nesne anahtarları sıralanır.

### 4.4 Hücre kuralları

- Aynı dosyanın `cells` dizisinde aynı `(q, r)` çifti birden fazla kez bulunamaz.
- Negatif axial koordinatlar geçerlidir.
- Hücre listesi boş olabilir.
- Hücrelerin bitişik olması veya dikdörtgen alan oluşturması zorunlu değildir.
- Hücre sırası semantik değildir. Serializer deterministik çıktı için hücreleri önce `q`, sonra `r` artan sırasıyla yazar.
- `q` ve `r` alanlarında JSON boolean değerleri integer gibi kabul edilmez.

## 5. Katman mimarisi ve sorumluluklar

Persistence katmanı `world/persistence/` altında bağımsız bir paket olacaktır.

### 5.1 `map_validator.py`

Sorumluluklar:

- Parse edilmiş JSON değerinin en üst seviyede nesne olduğunu doğrulamak.
- Zorunlu alanları ve alan türlerini kontrol etmek.
- Tanınmayan alanları reddetmek.
- Şema sürümünü kontrol etmek.
- Kimlik, layout, origin, hücre ve metadata kurallarını doğrulamak.
- Yinelenen hücre koordinatlarını tespit etmek.
- Hataları alan yolu ve mümkün olduğunda hücre indeksiyle raporlamak.

Validator dosya sistemi kullanmaz, `HexWorld` oluşturmaz ve Pygame import etmez. Doğrulama sonucu ya geçerli, tipli bir ara temsil ya da kontrollü validation hatası üretir.

### 5.2 `map_serializer.py`

Sorumluluklar:

- Yalnızca geçerli `HexMapDefinition` kabul etmek.
- Model alanlarını şema v1 JSON nesnesine dönüştürmek.
- Orientation değerlerini mevcut enum değerlerinden almak.
- Metadata'yı JSON uyumlu biçime dönüştürmek.
- Hücreleri deterministik sırada yazmak.
- JSON metnini deterministik biçimde üretmek (UTF-8, sabit girinti politikası, sabit anahtar sırası ve son newline politikası belgelenir).

Serializer dosya yazmaz ve runtime/view üzerinden veri toplamaz. Girdi modelini değiştirmez.

### 5.3 `map_deserializer.py`

Sorumluluklar:

- JSON parse edilmiş içeriği validator üzerinden geçirmek.
- Kimlikleri `WorldId` ve `MapId` nesnelerine dönüştürmek.
- Orientation değerini `HexOrientation` enum'una dönüştürmek.
- Origin'i `WorldPoint`, layout'u `HexLayout` olarak oluşturmak.
- Her hücreyi `AxialCoord` ve `HexCellData` nesnesine dönüştürmek.
- Bütün doğrulamalar başarıyla tamamlandıktan sonra tek bir `HexMapDefinition` döndürmek.

Deserializer, başarısızlıkta kısmi hücre listesi veya kısmi harita döndürmez. Dünya registry'sine kayıt yapmaz; model oluşturma ile dünya yaşam döngüsü birbirinden ayrıdır.

### 5.4 `file_storage.py`

Sorumluluklar:

- UTF-8 dosya okuma.
- JSON metnini güvenli parse etme için gerekli parser seçeneklerini uygulama.
- Serializer çıktısını dosyaya yazma.
- Dizin ve dosya erişim hatalarını kontrollü persistence hatalarına dönüştürme.
- Geçici dosya ve atomik değiştirme işlemlerini yönetme.
- Oluşturma ve mevcut dosyanın üzerine yazma davranışlarını açıkça ayırma.

Dosya katmanı `HexWorld` veya `MapRegistry` yönetmez. Harita kimliğinden otomatik ve kontrolsüz dosya yolu türetmez; çağıranın verdiği hedef yolu kullanır. Uygulamada izin verilen harita dizini sınırı belirlenirse path traversal ile bu dizinin dışına çıkılması engellenir.

### 5.5 `errors.py`

En az aşağıdaki hata ailesi planlanır:

- `MapPersistenceError`: Persistence işlemlerinin temel hata sınıfı.
- `MapFileNotFoundError`: Kaynak dosya bulunamadı.
- `MapFileAccessError`: Okuma/yazma veya erişim hatası.
- `MapJSONDecodeError`: JSON sözdizimi geçersiz.
- `MapValidationError`: JSON içeriği şema/model kurallarına aykırı.
- `UnsupportedMapSchemaVersionError`: Şema sürümü desteklenmiyor.
- `MapFileAlreadyExistsError`: Yalnızca oluşturma modunda hedef dosya zaten mevcut.
- `MapFileWriteError`: Güvenli yazma işlemi tamamlanamadı.

Hata mesajları kaynak istisnayı zincirleyebilir; ancak kullanıcıya dosya yolu, alan yolu veya hücre indeksi gibi teşhis için gereken bağlamı sunmalıdır. Ham traceback normal API sonucu olarak kullanılmaz.

## 6. Yükleme işlem akışı ve atomiklik

Dosyadan harita yükleme şu sırayı izler:

1. Dosya yolu ve erişim kontrol edilir.
2. Dosya UTF-8 metin olarak okunur.
3. JSON parse edilir; yinelenen nesne anahtarları reddedilir.
4. En üst seviye ve şema sürümü doğrulanır.
5. Bütün alanlar ve hücre kayıtları doğrulanır.
6. Tipli model bileşenleri oluşturulur.
7. Tek bir immutable `HexMapDefinition` oluşturulur.
8. Nesne çağırana ancak bütün adımlar başarılıysa döndürülür.

Bu akışta `HexWorld` veya `MapRegistry` üzerinde yan etki oluşmaz. Çağıran, başarılı sonucu daha sonra `register_map` / `load_map` yaşam döngüsüne dahil edebilir.

Bir hata 5.000'inci hücrede ortaya çıksa bile ilk 4.999 hücreyi içeren kısmi bir harita döndürülmez.

## 7. Güvenli dosya kaydetme

### 7.1 Yazma protokolü

Mevcut sağlam dosyanın başarısız yazma nedeniyle bozulmasını önlemek için aynı dizinde geçici dosyaya yazıp atomik değiştirme yaklaşımı kullanılacaktır:

1. Model JSON metnine dönüştürülür.
2. Hedef dizin doğrulanır; hedef dosya politikası kontrol edilir.
3. Aynı dizinde benzersiz bir geçici dosya oluşturulur.
4. UTF-8 içerik geçici dosyaya yazılır, flush edilir ve mümkün olan platformlarda dosya sistemi senkronizasyonu uygulanır.
5. Yazma başarılıysa geçici dosya `os.replace` benzeri atomik değiştirme işlemiyle hedefe alınır.
6. Hata durumunda geçici dosya temizlenmeye çalışılır; mevcut hedef dosya değiştirilmeden kalır.
7. Başarı/başarısızlık sonucu kontrollü biçimde bildirilir.

Atomik değiştirme garantisinin dosya sistemi ve platform sınırları olduğu belgelenir. Geçici dosya hedefle aynı dosya sistemi/dizin içinde tutulur. Platform desteklemediği bir garantiyi sistem varmış gibi iddia etmez.

### 7.2 Açık overwrite politikası

- `create`: Hedef mevcutsa reddeder; yanlışlıkla üzerine yazmaz.
- `replace`: Çağıran açıkça istediğinde mevcut dosyanın yerini alır.
- Varsayılan davranış sessiz overwrite değildir.
- Kaydetme işlemi başarısız olursa mevcut sağlam dosya korunmalıdır.

### 7.3 Yazma sonrası doğrulama

Serializer çıktısı kendi sözleşmesine göre deterministik ve geçerli olmalıdır. Testlerde dosyaya yazılan içerik tekrar okunup deserializer'dan geçirilecektir. Üretim kaydetme yolunda gereksiz ikinci tam harita kopyası oluşturulması zorunlu tutulmaz; doğrulama maliyeti performans ölçümleriyle değerlendirilir.

## 8. Önerilen dosya yapısı

Uygulamadan önce mevcut repository ağacı tekrar incelenecek ve aynı sorumluluğu zaten karşılayan dosyalar varsa yeni kopyalar oluşturulmayacaktır.

Hedeflenen yapı:

```text
experiments/hex_world_laboratory/
├── src/hex_world_lab/
│   └── world/
│       ├── ... mevcut dünya modülleri ...
│       └── persistence/
│           ├── __init__.py
│           ├── errors.py
│           ├── map_validator.py
│           ├── map_serializer.py
│           ├── map_deserializer.py
│           └── file_storage.py
├── scenarios/
│   └── maps/
│       └── starting_valley.json
├── tests/
│   ├── unit/
│   │   └── test_persistence/
│   │       ├── test_validator.py
│   │       ├── test_serializer.py
│   │       ├── test_deserializer.py
│   │       └── test_file_storage.py
│   └── integration/
│       └── test_map_persistence.py
├── docs/
│   └── PHASE-03.6-TECHNICAL-PLAN.md
└── reports/
    └── PHASE-03.6-REPORT.md
```

Test fixture'ları ve bozuk JSON örnekleri testlerin altında tutulabilir; üretim harita dizinine geçersiz dosyalar konulmaz. Gerçek klasör yerleşimi uygulama öncesi kontrol edilerek gereksiz taşıma yapılmaz.

## 9. Test ve kabul planı

### 9.1 Validator testleri

- Geçerli minimum JSON.
- Geçerli boş hücre listesi.
- Eksik zorunlu alanların her biri.
- Yanlış üst seviye ve nested türler.
- Bilinmeyen alanlar.
- Desteklenmeyen ve boolean olarak verilmiş şema sürümü.
- Geçersiz orientation.
- Sıfır, negatif, NaN/Infinity radius ve origin.
- Boolean olarak verilmiş q/r.
- Yinelenen `(q, r)`.
- Boş/whitespace kimlik, harita adı ve terrain id.
- Boolean yerine string/integer verilmesi.
- Metadata'da geçersiz anahtar/değer ve sonlu olmayan sayı.
- JSON nesnesinde yinelenen anahtar.
- Hata konumunun alan yolu ve hücre indeksiyle raporlanması.

### 9.2 Serializer testleri

- Modelden beklenen şema v1 alanları üretilir.
- Her iki orientation doğru yazılır.
- Origin ve radius korunur.
- Negatif axial koordinatlar korunur.
- Boş ve düzensiz hücre kümeleri korunur.
- Metadata null/boş nesne/iç içe nesne/dizi ayrımı korunur.
- Hücre sırası deterministiktir.
- Aynı model aynı JSON metnini üretir.
- Serializer girdi modelini değiştirmez.

### 9.3 Deserializer testleri

- Geçerli JSON doğru model türlerine dönüşür.
- WorldId, MapId, layout ve hücre alanları korunur.
- Metadata derin immutable model sözleşmesine uygun oluşturulur.
- Hatalı herhangi bir hücrede kısmi harita döndürülmez.
- Deserializer registry veya runtime üzerinde yan etki oluşturmaz.

### 9.4 File storage testleri

- UTF-8 dosya oluşturma ve okuma.
- Türkçe harita adları ve metadata metinleri.
- Dosya bulunamadı ve erişim hataları.
- Create modunda mevcut dosyanın korunması.
- Replace modunda kontrollü güncelleme.
- Yazma/replace hatasında önceki dosyanın korunması.
- Geçici dosyanın hata sonrası temizlenmesi.
- Hedef dizin yok veya yazılamaz olduğunda kontrollü hata.
- Path traversal girişimlerinin izin verilen depolama sınırını aşamaması (depolama kökü API'de sınırlandırılmışsa).

### 9.5 Integration ve regresyon testleri

- `HexMapDefinition → JSON → dosya → JSON → HexMapDefinition` gidiş-dönüş testi.
- Orijinal ve yeniden yüklenen haritanın kimlik, ad, layout, hücre koordinatları, hücre alanları ve metadata bakımından eşdeğerliği.
- İki farklı MapId için aynı axial koordinatların bağımsız kalması.
- Hatalı dosyanın `HexWorld` / `MapRegistry` durumunu değiştirmemesi.
- Pygame import edilmeden persistence paketinin kullanılabilmesi.
- Önceki geometri, world, registry, runtime ve view testlerinin regresyona uğramaması.

### 9.6 Performans ve kaynak kullanımı

En az üç harita boyutu ölçülecek: küçük, orta ve büyük fixture. Kesin hücre sayıları uygulama öncesi mevcut donanım ve test düzeni dikkate alınarak belirlenecek; keyfî bir performans garantisi yazılmayacak.

Ölçülecek değerler:
- Serializer süresi.
- Deserializer süresi.
- Dosya yazma/okuma süresi.
- Tepe bellek kullanımı mümkün olan test ortamında ölçülebiliyorsa.
- Hücre sayısı ve JSON dosya boyutu.

Optimizasyon ancak ölçümle doğrulanmış darboğaz varsa yapılır. Büyük harita yüklenirken gereksiz tam kopyalar ve aynı verinin birden fazla kez tutulması önlenir.

## 10. Uygulama alt aşamaları

| Alt aşama | Çalışma | Çıktı |
|---|---|---|
| 3.6.1 | Şema v1 ve persistence hata sözleşmesi | Kesin alan/tür/benzersizlik kuralları |
| 3.6.2 | Validator ve JSON parse güvenliği | Doğrulama testleri |
| 3.6.3 | Serializer ve deterministik JSON üretimi | Model → JSON |
| 3.6.4 | Deserializer ve immutable model oluşturma | JSON → model |
| 3.6.5 | UTF-8 file storage ve atomik kayıt | Dosyaya yazma/okuma |
| 3.6.6 | Test haritası, entegrasyon, regresyon ve ölçüm | Gidiş-dönüş kanıtı |
| 3.6.7 | Dokümantasyon ve kapanış raporu | Aşama 3.6 kapanışı için aday |

Alt aşamalar sırayla yürütülür. Herhangi bir alt aşamanın kapsamı veya mimari kararı değiştirilmek zorunda kalırsa önce kullanıcıya gerekçe ve etki sunulur.

## 11. Riskler ve azaltma yöntemleri

| Risk | Etki | Önlem |
|---|---|---|
| Şema/model alanlarının ayrışması | Veri kaybı veya hatalı yükleme | Alan eşleştirme testleri ve tek şema sözleşmesi |
| Yinelenen JSON anahtarlarının sessiz kabulü | Yanlış veri okunması | Parser seviyesinde duplicate-key reddi |
| Yinelenen hücre koordinatları | Hücre verisinin üzerine yazılması | Model oluşturulmadan önce koordinat benzersizliği kontrolü |
| Metadata'nın dönüştürülürken değişmesi | Kaydet-yükle kaybı | null/boş nesne/dizi ve nested değer testleri |
| Kısmi harita yüklenmesi | Dünya bütünlüğünün bozulması | Önce tam doğrulama, sonra tek model oluşturma |
| Kaydetme sırasında süreç/disk hatası | Mevcut dosyanın bozulması | Aynı dizinde geçici dosya ve atomik replace |
| Çok büyük dosya | Aşırı bellek/süre | Ölçüm, açık ve yapılandırılabilir kaynak sınırları; sessiz truncation yok |
| Platformlar arası atomiklik farkı | Yanlış güvence | Platform garantilerini belgeleme ve hata senaryolarını test etme |
| Runtime verisinin başlangıç tanımına karışması | Save mimarisinin bulanıklaşması | 3.6'da yalnızca HexMapDefinition; runtime persistence 3.7 |

## 12. Kabul kriterleri

Aşama 3.6 ancak aşağıdakilerin tümü sağlanırsa tamamlanmış sayılır:

1. Şema v1 alanları, türleri, zorunlulukları ve reddetme kuralları belgelenmiş ve test edilmiş olmalı.
2. Geçerli `HexMapDefinition` kayıpsız JSON'a serileştirilebilmeli.
3. Geçerli JSON yeniden immutable `HexMapDefinition` oluşturabilmeli.
4. JSON dosyası UTF-8 olarak yazılıp okunabilmeli.
5. Create/replace davranışları açık ve test edilmiş olmalı.
6. Yazma hatasında önceki sağlam hedef dosya korunmalı.
7. Yinelenen anahtar ve hücre koordinatları reddedilmeli.
8. Desteklenmeyen şema sürümü ve bilinmeyen alanlar reddedilmeli.
9. Geçersiz geometri, kimlik, hücre alanı ve metadata reddedilmeli.
10. Hatalı dosyadan kısmi harita veya dünya kaydı oluşmamalı.
11. Runtime override'ları bu aşamada kaydedilmemeli veya değiştirilmemeli.
12. Persistence paketi Pygame'den bağımsız olmalı.
13. Önceki laboratuvar testleri korunmalı; tam laboratuvar test paketi başarılı olmalı.
14. GitHub Actions Hex World Laboratory CI başarılı olmalı.
15. Performans ölçümleri ve sonuçları raporlanmalı.
16. Yalnızca laboratuvar dalında değişiklik yapılmış olmalı.
17. Dosyalar ve commit GitHub üzerinden tekrar doğrulanmalı.
18. Aşama 3.6 kapanış raporu hazırlanmalı ve kullanıcı tarafından kabul edilmeli.

## 13. Değişiklik ve onay sınırları

Bu belge yalnızca Aşama 3.6'nın teknik planıdır. Planın kaydedilmesi kod uygulama izni değildir.

Uygulamaya geçmeden önce ayrıca açık kullanıcı onayı alınacaktır. Uygulama onaylandığında:

- Önce aktif branch HEAD ve değiştirilecek dosyaların güncel blob SHA değerleri doğrulanır.
- Yalnızca `experiment/hex-world-laboratory` dalında çalışılır.
- `main` ve `demo_eldoria` dallarına yazılmaz.
- Aşama 3.1–3.5 davranışları korunur; kapsam dışı refactor yapılmaz.
- Her alt aşama için hedefli testler ve uygun regresyon testleri çalıştırılır.
- Sonunda tam laboratuvar test paketi ve özel CI çalıştırılır.
- Commit, dosya listesi, blob SHA ve branch HEAD GitHub üzerinden doğrulanır.
- Uygulama raporu ile planlanan ve gerçekleşen kapsam karşılaştırılır.

## 14. Aşama 3.7 ile sınır

Aşama 3.6 yalnızca immutable harita başlangıç tanımını kaydeder.

Aşama 3.7 için ayrı plan hazırlanarak şu sorumluluklar ele alınacaktır:

- `HexWorldRuntime` seyrek override verilerinin kalıcılaştırılması.
- Runtime kayıtlarının ilgili WorldId/MapId ve hücre adresleriyle ilişkilendirilmesi.
- Başlangıç harita dosyası ile runtime değişiklik dosyasının ayrılması.
- Runtime değişikliklerinin doğrulanarak yeniden uygulanması.
- Harita silme, sürüm uyumu, bozuk kayıt ve kısmi yükleme davranışları.

Aşama 3.7 tasarımı Aşama 3.6'nın uygulama sonuçları görülmeden kesinleştirilmiş sayılmaz.

---

**Plan belgesi sonu — Aşama 3.6 uygulaması için ayrıca kullanıcı onayı gerekir.**
