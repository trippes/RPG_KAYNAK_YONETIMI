# Aşama 3.6 — Resmî Kapanış Raporu

**Durum:** KAPATILDI — TEKNİK UYGULAMA VE DOĞRULAMA TAMAMLANDI  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Laboratuvar kökü:** `experiments/hex_world_laboratory/`  
**Teknik plan:** [PHASE-03.6-TECHNICAL-PLAN.md](../docs/PHASE-03.6-TECHNICAL-PLAN.md)  
**JSON şeması:** [MAP_JSON_SCHEMA_V1.md](../docs/MAP_JSON_SCHEMA_V1.md)

## 1. Kapanış özeti

Aşama 3.6'nın amacı, immutable harita başlangıç verisinin sürümlendirilmiş JSON biçiminde güvenli şekilde serileştirilmesi, doğrulanması, kaydedilmesi ve yeniden yüklenmesiydi.

Planlanan kapsam tamamlandı. GitHub Actions üzerindeki laboratuvar testleri ve benchmark adımı başarılı oldu. Kullanıcı ayrıca Windows yerel geliştirme ortamında tam test paketini çalıştırdı ve **249 testin tamamının 2.93 saniyede geçtiğini** bildirdi.

Bu doğrulamalarla Aşama 3.6 teknik olarak kapatılmıştır.

## 2. Teslim edilen işlevler

- JSON schema v1 için katı alan, tür ve değer doğrulaması.
- Bilinmeyen alanların, yinelenen JSON anahtarlarının ve yinelenen axial hücre koordinatlarının reddedilmesi.
- NaN, Infinity ve geçersiz metadata değerlerinin reddedilmesi.
- Hücreleri ve metadata anahtarlarını deterministik sırayla yazan serializer.
- JSON verisini tüm doğrulamalar tamamlandıktan sonra immutable `HexMapDefinition` nesnesine dönüştüren deserializer.
- UTF-8 dosya okuma/yazma ve kontrollü persistence hata sınıfları.
- Mevcut dosyanın yanlışlıkla üzerine yazılmasını önleyen `create` modu.
- Açıkça istendiğinde geçici dosya ve atomik değiştirme kullanan `replace` modu.
- Örnek başlangıç haritası: `scenarios/maps/starting_valley.json`.
- Şema/API dokümantasyonu ve 100, 1.000, 10.000 hücre ölçümleri için benchmark aracı.

## 3. Doğrulama sonuçları

### GitHub Actions

- İş akışı: Hex World Laboratory CI
- [Başarılı çalıştırma #43839646819](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43839646819)
- Sonuç: **success**
- Python: 3.12.16
- Tam test paketi: **249 passed in 0.45s**
- Benchmark adımı: başarılı

### Kullanıcının Windows ortamı

- Komut: `python -m pytest -q`
- Sonuç: **249 passed in 2.93s**
- Durum: başarılı

İki ortamda da aynı 249 testin tamamı geçti. Yerel süre, kullanıcının kendi geliştirme ortamında alınan sonuçtur; CI süresiyle doğrudan performans karşılaştırması veya başka donanımlar için süre garantisi değildir.

## 4. Benchmark özeti

GitHub Actions Ubuntu koşucusunda alınan ölçümler:

| Hücre sayısı | JSON boyutu | Serileştirme | Deserialization | Dosyaya kaydetme | Dosyadan yükleme | Tepe izlenen bellek |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 20,958 B | 4.835 ms | 3.086 ms | 6.002 ms | 4.176 ms | 321.4 KiB |
| 1,000 | 207,170 B | 50.335 ms | 30.305 ms | 47.571 ms | 40.862 ms | 2,984.1 KiB |
| 10,000 | 2,078,272 B | 518.352 ms | 350.910 ms | 517.840 ms | 437.795 ms | 29,016.9 KiB |

Bunlar tek CI çalıştırmasından alınan yaklaşık ölçümlerdir. Tepe bellek, Python `tracemalloc` tarafından izlenen tahsisleri ifade eder; işletim sisteminin toplam süreç belleği değildir. Bu aşamada otomatik cache, harita yükleme/tahliye politikası veya pasif harita simülasyonu eklenmemiştir.

## 5. Mimari sınırlar

Aşama 3.6 yalnızca immutable harita başlangıç tanımının dosya kalıcılığını sağlar. Aşağıdakiler bu aşamanın kapsamı dışındadır:

- `HexWorldRuntime` değişikliklerinin kaydedilmesi ve geri yüklenmesi — Aşama 3.7.
- Oyuncu, entity, NPC, kaynak, bina veya görev verilerinin kaydı.
- Harita dosyasının otomatik olarak `HexWorld` / `MapRegistry` içine kaydedilmesi.
- Haritalar arası geçiş, hareket, çarpışma, render veya ana oyun entegrasyonu.
- Otomatik harita yükleme/tahliye, cache ve pasif simülasyon.

Ayrıca depo kökündeki ayrı `Core quality` iş akışında laboratuvar paketinin depo kökünden kurulmadan test toplanması nedeniyle görülen `ModuleNotFoundError: No module named 'hex_world_lab'` sorunu bu aşamanın kapsamına alınmamış ve değiştirilmemiştir. Laboratuvarın kendi CI iş akışı başarılıdır.

## 6. Dal ve kapsam güvenliği

- Bütün Aşama 3.6 uygulama ve raporlama çalışmaları `experiment/hex-world-laboratory` dalında tutulmuştur.
- `main` ve `demo_eldoria` dallarına bu aşama kapsamında yazma veya birleştirme yapılmamıştır.
- Aşama 3.7 daha sonra ayrı teknik plan ve onayla tamamlanmıştır; Aşama 3'ün bütünleşik nihai durumu [PHASE-03-WORLD-REPORT.md](PHASE-03-WORLD-REPORT.md) içinde kayıtlıdır.

## 7. Kapanış kararı

**Aşama 3.6 tamamlanmış ve teknik olarak kapatılmıştır.**

Aşama 3.6'nın ardından runtime değişikliklerinin kalıcılaştırılması Aşama 3.7 kapsamında ayrıca uygulanmış; Aşama 3'ün bütünleşik kapanışı [PHASE-03-WORLD-REPORT.md](PHASE-03-WORLD-REPORT.md) içinde belgelenmiştir.

---

**Rapor sonu**


## 8. Birleştirilen uygulama kayıtları

Bu kapanış raporu, önceki `PHASE-03.6-REPORT.md` uygulama raporundaki ayrı ve tekrar eden özeti tek kayıtta toplar. Uygulama raporundan korunan ek ayrıntılar:

### 8.1 Değişen dosya ve modül grupları

- `.github/workflows/hex-world-lab-ci.yml`: persistence benchmark adımı.
- `README.md`: persistence API ve aşama durumu.
- `docs/MAP_JSON_SCHEMA_V1.md`: JSON şema ve API sözleşmesi.
- `scenarios/maps/starting_valley.json`: örnek başlangıç haritası.
- `scripts/benchmark_map_persistence.py`: 100, 1.000 ve 10.000 hücre benchmark aracı.
- `src/hex_world_lab/world/persistence/`: hata sınıfları, validator, serializer, deserializer ve file storage.
- `tests/unit/test_persistence/` ve `tests/integration/test_map_persistence.py`: doğrulama, round-trip ve dosya sistemi testleri.
- Mevcut geometry, world, map registry, runtime ve view modüllerinde değişiklik yapılmadı.

### 8.2 Uygulama sırasında yakalanan hata

İlk test turunda serializer'ın yanlış model türünü beklenmeyen hata sınıfına çevirdiği bir API testi başarısız oldu. Hata düzeltildi; son laboratuvar CI sonucu 249/249 başarılıdır.

### 8.3 Tarihsel kapsam notu

Aşama 3.6 sırasında depo kökündeki ayrı Core Quality iş akışında laboratuvar paketinin depo kökünden kurulmadan test toplanmasına ilişkin `ModuleNotFoundError: No module named 'hex_world_lab'` sorunu not edilmişti. O dönemde laboratuvarın kendi CI iş akışı başarılıydı. Bu not yalnızca Aşama 3.6 tarihsel durumunu açıklar; sonraki aşamaların veya güncel CI durumunun yerine geçmez.
