# Aşama 3.7 — Runtime Değişikliklerinin Kalıcılaştırılması Teknik Planı

**Belge türü:** Teknik uygulama planı — onay bekliyor  
**Durum:** PLAN HAZIRLANDI — KOD UYGULAMASI BAŞLAMADI  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Laboratuvar kökü:** `experiments/hex_world_laboratory/`  
**Planın dayanağı:** Aşama 3 ana planı, Aşama 3.5 runtime/view tasarımı, Aşama 3.6 JSON persistence ve kapanış raporları  
**Ön koşullar:** Aşama 3.1–3.6

---

## 1. Amaç ve problem tanımı

Aşama 3.6, bir haritanın değişmeyen başlangıç tanımını (`HexMapDefinition`) JSON dosyasına kaydedip yeniden yüklemeyi sağladı. Ancak oyun çalışırken `HexWorldRuntime` üzerinden yapılan arazi, yürünebilirlik ve engel değişiklikleri henüz diske kaydedilmiyor.

Aşama 3.7'nin amacı, bu çalışma zamanı değişikliklerini güvenli, sürümlendirilmiş ve doğrulanabilir bir dosya biçiminde saklamak; oyun yeniden açıldığında aynı temel harita üzerine geri uygulamaktır.

Bu aşama **tam oyun kayıt sistemi değildir**. Yalnızca mevcut runtime modelinin desteklediği üç hücre alanı kalıcılaştırılır:

- `terrain_id`
- `is_walkable`
- `has_obstacle`

Temel harita dosyası değişmeden kalır. Runtime dosyası yalnızca temel veriden farklı olan alanları içerir.

## 2. Temel mimari kararlar

### 2.1. Temel harita ve runtime verisi ayrı dosyalarda kalacak

Aşama 3.6'nın `HexMapDefinition` JSON biçimi değiştirilmez. Runtime verisi için ayrı bir JSON şeması ve ayrı persistence API'si oluşturulur.

Bunun sonuçları:

- Başlangıç haritası tek bir kaynak dosyada korunur.
- Oyun sırasında değişen alanlar küçük bir delta dosyasına yazılır.
- Runtime kaydı silinse bile temel harita bozulmaz; dünya başlangıç hâline döndürülebilir.
- Runtime dosyası olmayan harita, tüm hücreleri temel tanımlarıyla kullanır.

### 2.2. Kayıt bir harita kimliğine bağlı olacak

Her runtime snapshot yalnızca bir `WorldId + MapId` çiftine ait olacaktır. Bir dosya birden fazla haritanın runtime verisini taşımayacaktır.

Aynı axial koordinat farklı haritalarda bulunabileceğinden her override kaydının koordinatı, dosyanın dünya ve harita kimliği bağlamında yorumlanır.

### 2.3. Temel harita parmak izi kullanılacak

Runtime snapshot, üretildiği temel haritanın SHA-256 parmak izini taşıyacaktır.

Parmak izi, Aşama 3.6 serializer'ının deterministik çıktısı olan temel harita JSON metninin UTF-8 baytları üzerinden hesaplanır. Runtime override'ları bu girdiye dahil edilmez.

Yükleme sırasında dosyadaki parmak izi mevcut temel haritanın parmak iziyle eşleşmelidir. Böylece aynı `WorldId/MapId` kimlikleri korunmuş olsa bile temel harita hücreleri veya geometrisi değiştirilmişse eski runtime verisinin yanlış haritaya uygulanması engellenir.

Parmak izi bir güvenlik imzası değildir; yanlış veya uyumsuz temel haritayı tespit eden bütünlük/uyumluluk kontrolüdür.

### 2.4. Snapshot kapsamı

İlk sürümde snapshot bir harita için tam runtime durumunu temsil eder; yalnızca o haritaya ait mevcut override'ları içerir. Snapshot geri yüklenirken o haritanın önceki runtime override kümesi, doğrulama başarılı olduktan sonra snapshot içeriğiyle bütünüyle değiştirilir.

Bu yaklaşım, aynı harita için eski ve yeni override kayıtlarının istemeden birleşmesini önler. Kısmi güncelleme/merge davranışı bu aşamada sunulmaz.

### 2.5. Kayıt ve geri yükleme için harita yüklenmiş olmalı

Kaydetme ve geri yükleme işlemleri hedef `HexMapDefinition` nesnesine ihtiyaç duyar. Bu nedenle hedef harita `MapRegistry` içinde kayıtlı ve yüklü olmalıdır.

- Harita kayıtlı değilse mevcut `UnknownMapError` davranışı korunur.
- Harita kayıtlı ancak yüklenmemişse mevcut `MapNotLoadedError` davranışı korunur.
- Harita yüklenmiş ancak snapshot içindeki hücre temel haritada yoksa snapshot reddedilir.

Harita unload edildiğinde mevcut runtime override'ları bellekte korunmaya devam eder; bu davranış Aşama 3.5 sözleşmesidir. Disk kaydı unload öncesinde, harita yüklüyken yapılır. Bu aşama otomatik unload öncesi kayıt mekanizması eklemez.

---

## 3. Runtime JSON şeması v1

Önerilen dosya adı örneği: `starting_valley.runtime.json`

Örnek:

```json
{
  "schema_version": 1,
  "kind": "hex_world_runtime_snapshot",
  "world_id": "eldoria",
  "map_id": "starting_valley",
  "base_map_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "overrides": [
    {
      "q": 2,
      "r": -1,
      "terrain_id": "burned_grass",
      "is_walkable": true
    },
    {
      "q": 4,
      "r": 0,
      "has_obstacle": true
    }
  ]
}
```

### 3.1. Üst seviye alanlar

| Alan | Tür | Kural |
|---|---|---|
| `schema_version` | integer | Yalnızca 1; boolean kabul edilmez |
| `kind` | string | Tam olarak `hex_world_runtime_snapshot` |
| `world_id` | string | Boş olamaz; hedef dünyanın kimliğiyle eşleşmeli |
| `map_id` | string | Boş olamaz; hedef haritanın kimliğiyle eşleşmeli |
| `base_map_sha256` | string | 64 küçük harfli hexadecimal karakter; temel harita parmak iziyle eşleşmeli |
| `overrides` | array | Hücre başına sıfır veya bir override kaydı |

Bilinmeyen üst seviye alanlar reddedilir. Yinelenen JSON nesne anahtarları ve standart dışı `NaN/Infinity` sabitleri reddedilir.

### 3.2. Override kaydı

| Alan | Tür | Kural |
|---|---|---|
| `q`, `r` | integer | Boolean olamaz; axial koordinatı belirtir |
| `terrain_id` | string | İsteğe bağlı; boş veya whitespace olamaz |
| `is_walkable` | boolean | İsteğe bağlı |
| `has_obstacle` | boolean | İsteğe bağlı |

Kurallar:

- Her override en az bir değiştirilebilir alan içermelidir.
- `q/r` çifti dosya içinde benzersiz olmalıdır.
- Hücre, temel haritada gerçekten bulunmalıdır.
- Alanın değeri temel haritadaki değerle aynıysa kayıt içinde bulunmamalıdır. Serializer bu tür değerleri normalize ederek dışarıda bırakır; deserializer ise gereksiz/eşit değerleri şema ihlali olarak reddeder.
- `null`, alanı sıfırlamak için kullanılmaz. Bir alanın override edilmemesi, o alanın temel harita değerini kullanması demektir.
- `metadata`, hücre adresi, geometri, hücre varlığı veya başka bir oyun nesnesi bu şemaya yazılamaz.
- Hücreler deterministik biçimde `(q, r)` sırasıyla yazılır.

Boş `overrides` listesi geçerli bir snapshot'tır ve hedef haritanın runtime override kümesini boşaltır.

---

## 4. Python API tasarımı

Aşama 3.5'in runtime sınıfının özel sözlük alanına persistence modülünden doğrudan erişilmeyecektir. Runtime ile persistence arasında kontrollü bir snapshot sınırı kurulacaktır.

### 4.1. Runtime snapshot arayüzü

`HexWorldRuntime` üzerinde harita bazında snapshot alıp atomik biçimde geri yüklemeye yarayan kontrollü metotlar planlanır:

- `export_map_overrides(map_id)`: Haritanın mevcut override kayıtlarını değiştirilemez, deterministik bir snapshot olarak döndürür. Harita unload edilmiş olsa da bellekte tutulan override'lar okunabilir; ancak bu aşamadaki dosya kaydetme API'si temel harita parmak izi için yüklü tanım ister.
- `replace_map_overrides(map_id, overrides)`: Önceden doğrulanmış override kümesini hedef haritanın mevcut override kümesinin yerine koyar. Girdi doğrulaması ve normalizasyon tamamlanmadan mevcut kayıtlar değiştirilmez.

Bu metotlar diğer haritaların override'larına dokunamaz. `HexWorld.remove_map` davranışı korunur ve ilgili runtime kayıtlarını temizlemeye devam eder.

Runtime sınıfının mevcut `set_terrain`, `set_walkable`, `set_obstacle`, reset ve clear API'leri geriye dönük uyumlu kalmalıdır.

### 4.2. Persistence API

Önerilen dış API:

- `runtime_to_payload(runtime, map_definition)`
- `serialize_runtime(runtime, map_definition)`
- `deserialize_runtime_payload(payload, map_definition)`
- `save_runtime_file(runtime, map_definition, path, mode="create")`
- `load_runtime_file(path, map_definition)` — doğrulanmış snapshot verisini döndürür; tek başına runtime'ı değiştirmez.
- `restore_runtime_file(runtime, map_definition, path)` — dosyayı okur, tüm kontrolleri yapar ve tek atomik işlemle hedef haritanın runtime override kümesini değiştirir.

`load_runtime_file` ile `restore_runtime_file` ayrımı bilinçlidir: yalnızca okuma/doğrulama yapmak isteyen kod, runtime üzerinde yan etki oluşturmaz.

Kaydetme API'sinde `create` varsayılanı mevcut dosyayı ezmez. `replace` yalnızca açıkça istendiğinde mevcut dosyanın yerini atomik olarak alır. Aşama 3.6'nın dosya güvenliği ilkeleri korunur.

---

## 5. Modül ve dosya yerleşimi

Mevcut `world/persistence/` paketi genişletilecektir. Önerilen dosyalar:

```text
src/hex_world_lab/world/
  runtime.py                         # Snapshot dışa/içe aktarma sınırı
  persistence/
    __init__.py                      # Yeni runtime API dışa aktarımları
    runtime_errors.py                # Runtime persistence hata ailesi
    runtime_validator.py             # Snapshot şeması ve temel harita uyumluluğu
    runtime_serializer.py            # Runtime → payload/JSON
    runtime_deserializer.py          # Payload → doğrulanmış immutable snapshot
    runtime_file_storage.py          # UTF-8 dosya okuma/yazma ve atomik kayıt

tests/unit/test_world/
  test_runtime.py                    # Snapshot API ve atomik değiştirme testleri

tests/unit/test_persistence/
  test_runtime_validator.py
  test_runtime_serializer.py
  test_runtime_file_storage.py

tests/integration/
  test_runtime_persistence.py

scenarios/runtime/
  starting_valley.runtime.json       # Küçük örnek runtime snapshot

docs/
  RUNTIME_JSON_SCHEMA_V1.md

reports/
  PHASE-03.7-REPORT.md               # Uygulama ve doğrulama raporu; uygulama sonunda

scripts/
  benchmark_runtime_persistence.py   # Gerekli görülürse ölçüm aracı
```

Bu planın kendisi `reports/PHASE-03.7-TECHNICAL-PLAN.md` konumunda tutulur.

Dosya listesi uygulama öncesi mevcut depo durumuna göre tekrar doğrulanacaktır. Gereksiz modül veya test dosyası oluşturulmayacaktır. Var olan `file_storage.py` güvenli yazma ilkeleri mümkün olduğunca ortak bir iç yardımcıyla yeniden kullanılacak; Aşama 3.6 harita dosyası API'sinin davranışı değiştirilmeden korunacaktır.

---

## 6. Doğrulama ve hata yönetimi

Yeni hata sınıfları `MapPersistenceError` ailesiyle uyumlu olmalıdır. Önerilen sınıflar:

- `RuntimePersistenceError`
- `RuntimeJSONDecodeError`
- `RuntimeValidationError`
- `RuntimeSchemaVersionError`
- `RuntimeBaseMapMismatchError`
- `RuntimeWorldMismatchError`
- `RuntimeMapMismatchError`
- `RuntimeFileWriteError`

Mevcut genel dosya hataları (`MapFileNotFoundError`, `MapFileAccessError`, `MapFileAlreadyExistsError`) uygun olduğu yerde yeniden kullanılabilir; hata adları ve sorumlulukları uygulama sırasında tutarlı hâle getirilir.

Aşağıdaki durumlar kontrollü biçimde reddedilmelidir:

1. Bozuk JSON veya yinelenen JSON anahtarı.
2. Eksik zorunlu alan, bilinmeyen alan veya yanlış tür.
3. Desteklenmeyen şema sürümü ya da yanlış `kind`.
4. Geçersiz SHA-256 biçimi veya temel harita parmak izi uyuşmazlığı.
5. WorldId/MapId uyuşmazlığı.
6. Aynı koordinatın birden fazla kez bulunması.
7. Temel haritada bulunmayan hücreye override yazılması.
8. Boş terrain kimliği, boolean yerine sayı/string kullanılması veya `null` alan.
9. Hiç alan içermeyen override kaydı.
10. Temel değerle aynı olan gereksiz override.
11. Dosya erişim/yazma hataları.

### 6.1. Kısmi uygulamayı engelleme

Geri yükleme işlemi iki aşamalı olacaktır:

1. Dosya tamamen okunur; JSON ayrıştırılır; şema, kimlik, parmak izi, koordinatlar ve alan değerleri doğrulanır. Bütün override kayıtları geçici ve değiştirilemez bir snapshot'a dönüştürülür.
2. Tüm doğrulamalar başarılıysa runtime'ın hedef harita override kümesi tek işlemde değiştirilir.

Herhangi bir doğrulama hatasında runtime'ın önceki durumu byte/değer düzeyinde aynı kalmalıdır. İlk birkaç hücre uygulanıp sonraki hücrede hata alınması kesinlikle kabul edilmez.

---

## 7. Test planı

### 7.1. Runtime birim testleri

- Bir haritanın override snapshot'ını dışa aktarma.
- Snapshot'ın değiştirilemez olması ve runtime iç sözlüğünü dışarı sızdırmaması.
- Yalnız hedef MapId kayıtlarının dışa aktarılması.
- Snapshot ile mevcut override kümesini atomik değiştirme.
- Başarısız girdide önceki override kümesinin korunması.
- Boş snapshot ile hedef haritanın override'larını temizleme.
- Diğer haritaların runtime verisinin etkilenmemesi.
- Var olan runtime mutation/reset davranışlarının korunması.

### 7.2. Validator ve serializer testleri

- Geçerli boş ve dolu snapshot.
- Üç desteklenen alanın ayrı ayrı ve birlikte kaydı.
- Deterministik JSON çıktısı ve sıralı hücreler.
- Aynı temel değere sahip alanların serializer tarafından yazılmaması.
- Duplicate koordinat, bilinmeyen alan ve eksik alan reddi.
- Boolean/integer ayrımı ve geçersiz `null` değerleri.
- NaN/Infinity, hatalı hash ve desteklenmeyen sürüm reddi.
- WorldId/MapId ve base fingerprint uyuşmazlıkları.
- Temel haritada bulunmayan hücreye override reddi.
- Metadata veya desteklenmeyen alanların snapshot'a sızmaması.

### 7.3. Dosya sistemi testleri

- UTF-8 snapshot kaydetme/yükleme.
- `create` modunun var olan dosyayı ezmemesi.
- `replace` modunun açıkça istendiğinde dosyayı değiştirmesi.
- Hatalı JSON ve bulunamayan dosya için kontrollü hatalar.
- Yazma hatasında geçici dosya temizliği.
- Aynı dizinde geçici dosya ve atomik replace davranışı.
- Dosya kaydetme/yükleme sonrası payload eşitliği.

### 7.4. Entegrasyon testleri

- Runtime değiştir → snapshot kaydet → yeni HexWorld oluştur → temel haritayı yükle → runtime snapshot'ını geri yükle → `HexWorldView` üzerinden aynı hücre durumunu doğrula.
- Snapshot olmadan yüklenen haritanın temel değerleri göstermesi.
- Aynı WorldId/MapId fakat değiştirilmiş temel harita ile restore işleminin fingerprint hatası vermesi.
- Bir haritanın snapshot'ının başka haritaya uygulanamaması.
- Hatalı snapshot'ın runtime'da kısmi değişiklik bırakmaması.
- Bir haritanın restore işleminin başka haritanın runtime'ına dokunmaması.
- Unload/reload sırasında bellekteki override'ların mevcut Stage 3.5 sözleşmesine uygun kalması.
- Remove map işleminin runtime override'larını temizlemesi.
- Aşama 3.6 map persistence testlerinin değişmeden başarılı kalması.

### 7.5. Tam regresyon

Uygulama sonunda laboratuvar kökünde:

```powershell
python -m pytest -q
```

Tam test paketi çalıştırılır. Hedef, yeni testlerle birlikte tüm laboratuvar testlerinin geçmesidir; kesin test sayısı uygulama sonunda raporlanır. Ayrıca GitHub Actions Hex World Laboratory CI başarılı olmalıdır.

---

## 8. Performans ve bellek yaklaşımı

Bu aşamada amaç her frame'de dosya yazmak değildir. Runtime değişiklikleri bellekte kalır; disk snapshot'ı açıkça çağrılan save işlemi sırasında oluşturulur.

Performans ilkeleri:

- Yalnızca override içeren hücreler serileştirilir.
- Bir hücre için yalnızca temel veriden farklı alanlar yazılır.
- Snapshot üretimi hedef MapId ile sınırlıdır; diğer haritalar taranmaz.
- JSON hücre sırası deterministik tutulur.
- Restore sırasında doğrulama geçici snapshot üzerinde yapılır, sonra tek seferde uygulanır.
- Harita yükleme/tahliye, simülasyon ve cache politikaları bu aşamada eklenmez.
- Büyük snapshot'larda bellek ve süre ölçülür; ölçüm olmadan karmaşık optimizasyon yapılmaz.

Önerilen benchmark boyutları:
- 100 override hücresi
- 1.000 override hücresi
- 10.000 override hücresi

Her boyutta JSON dosya boyutu, serialize/deserialize, dosya save/load süresi ve Python `tracemalloc` tepe tahsisi raporlanır. Tek koşunun ölçümleri süre garantisi sayılmaz; CI'da keyfî katı zaman eşiği konmaz.

---

## 9. Aşama 3.7 kapsamı dışındakiler

Bu aşama aşağıdakileri **uygulamayacaktır**:

- Oyuncu karakteri, envanter, görev, NPC, entity, kaynak, bina veya üretim verisi kaydı.
- Tam oyun save slot sistemi veya çoklu kayıt yuvası.
- Birden fazla haritayı kapsayan dünya geneli save manifest/transaction sistemi.
- Otomatik periyodik kayıt, autosave veya çökme kurtarma.
- Her runtime değişikliğinde anlık disk yazımı.
- Runtime dosyası yoksa otomatik dosya üretimi.
- Harita yükleme/tahliye/cache ve pasif dünya simülasyonu.
- Offline progression.
- Hareket, pathfinding, çarpışma, render, Pygame veya ana oyun entegrasyonu.
- Bina içleri, kapılar ve haritalar arası geçiş.
- Ağ/çok oyunculu eşzamanlama veya çatışma çözümü.

Bunlar daha sonra ayrı tasarım ve onay gerektirir. Özellikle birden fazla haritanın tek oyun kaydında atomik olarak saklanması, bu aşamadaki harita başına snapshot yaklaşımından ayrı bir üst katman konusudur.

---

## 10. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Runtime dosyası farklı temel haritaya uygulanır | SHA-256 temel harita parmak izi |
| Restore sırasında kısmi değişiklik oluşur | Önce tam doğrulama, sonra tek atomik runtime değiştirme |
| Aynı hücre iki kez kaydedilir | Duplicate axial koordinat reddi |
| Dosya büyür ve temel harita tekrar tekrar yazılır | Yalnız sparse override delta'sı |
| Persistence kodu runtime iç sözlüğüne bağlanır | Kontrollü export/replace API'si |
| Aşama 3.6 dosya davranışı bozulur | Mevcut API regresyon testleri ve uyumluluk |
| Yanlış haritaya snapshot yüklenir | WorldId, MapId ve fingerprint doğrulaması |
| Platformda atomik dosya işlemi farklı davranır | Aynı dizinde temp file; platform testleri; kontrollü hata |
| Gereksiz karmaşıklık/performance yükü oluşur | Harita başına snapshot; frame döngüsünde disk I/O yok; ölçüm temelli optimizasyon |

---

## 11. Uygulama sırası

Uygulama onaylanırsa aşağıdaki sırayla ilerlenir:

1. **Depo ve sözleşme doğrulaması:** Dal HEAD'i, mevcut runtime/persistence dosyaları ve testler yeniden okunur.
2. **Runtime snapshot sınırı:** Runtime'a immutable export ve atomik replace API'leri eklenir; hedefli birim testleri yazılır.
3. **Şema ve validator:** Runtime JSON v1 alanları, kimlik, fingerprint ve hücre doğrulaması uygulanır.
4. **Serializer/deserializer:** Deterministik çıktı ve yan etkisiz snapshot oluşturma uygulanır.
5. **Dosya depolama:** Güvenli create/replace ve kontrollü okuma/yazma uygulanır.
6. **Entegrasyon:** Yeni HexWorld üzerinde temel harita yükleme ve runtime restore gidiş-dönüşü kanıtlanır.
7. **Regresyon ve benchmark:** Tam test paketi, CI ve ölçümler çalıştırılır.
8. **Raporlama:** `PHASE-03.7-REPORT.md` sonuçlarla hazırlanır; GitHub'da yalnız onaylı dal ve kapsam içinde kaydedilir.
9. **Kullanıcı kabulü:** Sonuçlar sunulur. Aşama 3 bütünü doğrulanmadan Aşama 4'e geçilmez.

Herhangi bir uygulama öncesinde dal ve hedef dosyaların güncel SHA'ları yeniden doğrulanır. Çalışma yalnızca `experiment/hex-world-laboratory` dalında yapılır. `main` ve `demo_eldoria` dallarına açık onay olmadan yazılmaz, merge veya cherry-pick yapılmaz.

---

## 12. Kabul ölçütleri

Aşama 3.7 ancak aşağıdaki koşulların tamamı sağlandığında teknik olarak tamamlanmış sayılır:

1. Runtime override snapshot'ı yalnızca bir WorldId/MapId haritasını temsil eder.
2. Snapshot yalnızca temel veriden farklı olan üç izinli alanı içerir.
3. Temel harita SHA-256 parmak izi doğrulanır.
4. JSON şema v1 katı biçimde doğrulanır.
5. Kaydetme deterministik ve güvenli dosya yazımıyla yapılır.
6. Restore önce tüm snapshot'ı doğrular; hata durumunda runtime'ın hiçbir kısmını değiştirmez.
7. Başarılı restore sonrası `HexWorldView` beklenen güncel hücre değerlerini döndürür.
8. Bir haritanın restore işlemi başka haritanın verisini değiştirmez.
9. Aşama 3.5 runtime davranışı ve Aşama 3.6 map persistence regresyon testleri geçer.
10. Tam laboratuvar test paketi ve özel GitHub Actions CI başarılıdır.
11. Benchmark sonuçları raporlanır; performans iddiaları ölçüm sınırlarıyla birlikte sunulur.
12. Kod, dokümantasyon ve rapor yalnızca onaylı deney dalında bulunur.

## 13. Onay sınırı

Bu belge yalnızca Aşama 3.7 teknik planıdır. GitHub'a kaydedilmesi kod uygulaması için izin anlamına gelmez.

**Bu plan onaylanmadan hiçbir Python kaynak kodu, test, CI iş akışı veya örnek runtime snapshot dosyası oluşturulmayacak/değiştirilmeyecektir.** Planın onaylanması hâlinde uygulama, burada tanımlanan dosya ve kapsam sınırları içinde ayrıca başlatılacaktır.

Aşama 3.7'nin tamamlanması da Aşama 3'ün otomatik olarak kapandığı anlamına gelmez. Aşama 3 kapanışından önce bütün alt aşamalar, bütünleşik davranış ve kabul ölçütleri ayrıca doğrulanacaktır.

---

**Teknik plan sonu**
