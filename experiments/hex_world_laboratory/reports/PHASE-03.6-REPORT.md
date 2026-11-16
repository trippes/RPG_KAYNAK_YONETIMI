# Aşama 3.6 — Harita Dosya Sistemi ve JSON Veri Doğrulama Raporu

**Durum:** UYGULAMA TAMAMLANDI — KULLANICI KABULÜ BEKLİYOR  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Teknik plan:** [PHASE-03.6-TECHNICAL-PLAN.md](../docs/PHASE-03.6-TECHNICAL-PLAN.md)  
**Şema belgesi:** [MAP_JSON_SCHEMA_V1.md](../docs/MAP_JSON_SCHEMA_V1.md)

## 1. Gerçekleştirilen kapsam

- JSON schema v1 alanları, tipleri, zorunlulukları ve bilinmeyen alanların reddedilmesi uygulandı.
- Yinelenen JSON nesne anahtarları, yinelenen axial hücre koordinatları, NaN/Infinity ve geçersiz metadata reddediliyor.
- Model → JSON dönüşümü deterministik hücre ve metadata anahtar sırasıyla çalışıyor.
- JSON → immutable `HexMapDefinition` dönüşümü bütün veri doğrulandıktan sonra tek seferde yapılıyor.
- UTF-8 dosya okuma ve kontrollü persistence hata ailesi eklendi.
- `create` modu mevcut dosyayı ezmiyor; `replace` modu açıkça istendiğinde geçici dosya üzerinden atomik değiştirme kullanıyor.
- `starting_valley.json` örnek haritası eklendi.
- Kullanım ve şema dokümantasyonu eklendi.
- 100, 1.000 ve 10.000 hücreli benchmark aracı CI iş akışına bağlandı.

## 2. Değişen dosyalar

- `.github/workflows/hex-world-lab-ci.yml` — benchmark adımı eklendi.
- `README.md` — persistence API ve aşama durumu belgelendi.
- `docs/MAP_JSON_SCHEMA_V1.md` — JSON şema ve API dokümantasyonu.
- `scenarios/maps/starting_valley.json` — örnek harita.
- `scripts/benchmark_map_persistence.py` — ölçüm aracı.
- `src/hex_world_lab/world/persistence/` — hata, validator, serializer, deserializer ve file storage modülleri.
- `tests/unit/test_persistence/` — validator, serializer/deserializer ve dosya sistemi testleri.
- `tests/integration/test_map_persistence.py` — dosya gidiş-dönüş ve yan etki testleri.

Mevcut geometry, world, map registry, runtime ve view modüllerinde değişiklik yapılmadı.

## 3. Test ve CI sonucu

GitHub Actions — Hex World Laboratory CI:

- Run: [43839500786](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43839500786)
- Sonuç: **success**
- Python: 3.12.16
- Tam test paketi: **249 passed in 0.60s**
- Benchmark adımı: başarılı

İlk test çalıştırmasında serializer'ın yanlış model türünü beklenmeyen hata sınıfına çevirdiği bir API testi yakalandı. Hata düzeltildi ve güncel tam test paketi başarılı oldu.

## 4. Performans ölçümü

Ölçümler GitHub Actions Ubuntu 26.04 / Python 3.12.16 koşucusunda, tek çalıştırma ile alındı. Bunlar kullanıcının Windows bilgisayarındaki süre garantileri değildir; yalnızca aynı test koşusundaki yaklaşık maliyetleri gösterir. Zaman eşiği uygulanmamıştır.

| Hücre | JSON boyutu | JSON serileştirme | Deserialization | Dosya kaydetme | Dosya yükleme | Tepe izlenen bellek |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 20,958 B | 7.184 ms | 4.068 ms | 8.164 ms | 5.537 ms | 321.4 KiB |
| 1,000 | 207,170 B | 66.426 ms | 40.586 ms | 69.641 ms | 60.360 ms | 2,984.1 KiB |
| 10,000 | 2,078,272 B | 740.426 ms | 444.439 ms | 735.998 ms | 583.634 ms | 29,016.9 KiB |

Tepe bellek ölçümü, benchmark sırasında Python `tracemalloc` tarafından izlenen tahsisleri kapsar; işletim sistemi toplam süreç belleği değildir. Ölçümler, 10.000 hücreli başlangıç haritasının yaklaşık 2.08 MB JSON dosyası olarak işlenebildiğini gösteriyor. Bu aşamada önbellek, otomatik harita yükleme/tahliye veya runtime simülasyonu eklenmedi.

## 5. Mimari sınırlar ve kapsam dışı kalanlar

- Yalnızca immutable `HexMapDefinition` başlangıç verisi kalıcılaştırılır.
- `HexWorldRuntime` override verileri kaydedilmez; Aşama 3.7 kapsamındadır.
- Dosya yükleyici `HexWorld` veya `MapRegistry` üzerinde otomatik kayıt oluşturmaz.
- Entity, NPC, kaynak, bina, oyuncu durumu, oyun kaydı ve haritalar arası geçiş sistemi eklenmedi.
- `main` ve `demo_eldoria` dallarına yazılmadı.
- Root `Core quality` workflow'unun laboratuvar paketini depo kökünden kurmadan test toplama sorunu bu aşamanın kapsamına alınmadı; laboratuvarın kendi CI iş akışı bağımsız olarak başarılıdır.

## 6. Kabul durumu

Aşama 3.6'nın planlanan kodu, testleri, örnek verisi, dokümantasyonu ve benchmark aracı uygulandı. Özel laboratuvar CI başarılıdır. Bu rapor teknik kapanış adayıdır; aşama kullanıcı tarafından kabul edilmeden Aşama 3.6 resmen kapanmış sayılmaz.

Aşama 3.7 ve Aşama 4 başlatılmamıştır.
