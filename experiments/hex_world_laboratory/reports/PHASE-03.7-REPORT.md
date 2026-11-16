# Aşama 3.7 — Runtime Persistence Uygulama ve Doğrulama Raporu

**Durum:** UYGULAMA VE DOĞRULAMA TAMAMLANDI — AŞAMA 3 GENEL KAPANIŞINA DAHİL EDİLDİ  
**Dal:** `experiment/hex-world-laboratory`  
**Teknik plan:** [PHASE-03.7-TECHNICAL-PLAN.md](PHASE-03.7-TECHNICAL-PLAN.md)

## 1. Amaç

Aşama 3.6'da tanımlanan immutable harita başlangıç verisini değiştirmeden, oyun sırasında oluşan seyrek hücre değişikliklerini ayrı dosyalarda kalıcılaştırmak.

Runtime snapshot yalnızca `terrain_id`, `is_walkable` ve `has_obstacle` alanlarının temel haritadan farklı değerlerini saklar. Harita geometrisi, hücre varlık kümesi, metadata veya oyun nesneleri snapshot'a dahil değildir.

## 2. Teslim edilenler

- Runtime snapshot doğrulayıcısı, serializer, deserializer, hata türleri ve UTF-8 dosya depolaması.
- WorldId, MapId ve canonical harita JSON'undan hesaplanan SHA-256 parmak izini içeren şema v1.
- Deterministik koordinat sıralaması ve sparse override kayıtları.
- Runtime override kümesini dışa aktarma ve tek işlemde değiştirme API'leri.
- Bozuk/uyumsuz dosyanın mevcut runtime durumunu kısmen değiştirmesini engelleyen doğrulama akışı.
- `create` modunda mevcut dosyayı koruma; açık `replace` modunda atomik değiştirme.
- Starting Valley örnek runtime snapshot, şema dokümantasyonu, unit/integration testleri ve benchmark aracı.
- Laboratuvar CI hattına runtime persistence benchmark adımı.

## 3. Test doğrulaması

### Kullanıcının Windows ortamı

```text
python -m pytest -q
288 passed in 2.01s
```

### GitHub Actions — Hex World Laboratory CI

[Run 43843535280](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43843535280)

- Sonuç: başarılı.
- Python 3.12.16, Pygame 2.6.1, pytest 8.4.2.
- Tam test paketi: **288 passed in 0.51s**.
- Harita persistence benchmark: başarılı.
- Runtime persistence benchmark: başarılı.

Bütünleşik doğrulama ve kapanış için son laboratuvar CI koşusu [Run 43844555405](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43844555405) başarılıdır. Ana deponun düzeltilmiş Linux ve Windows Core quality job'ları da [Run 43844555225](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43844555225) kapsamında başarılıdır. Genel kapanış kanıtları [PHASE-03-WORLD-REPORT.md](PHASE-03-WORLD-REPORT.md) içinde tutulur.

## 4. Runtime persistence benchmark

Aşağıdaki değerler CI koşucusundaki tek çalıştırmadan alınmıştır; süre garantisi veya eşik değildir.

| Override | JSON boyutu | Serialize | Deserialize | Save | Load | Tepe izlenen bellek |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 7,706 B | 4.95 ms | 4.62 ms | 1.58 ms | 1.01 ms | 165 KiB |
| 1,000 | 77,007 B | 46.35 ms | 46.23 ms | 8.23 ms | 8.94 ms | 1,604.6 KiB |
| 10,000 | 788,008 B | 495.36 ms | 503.51 ms | 85.20 ms | 96.90 ms | 14,899.4 KiB |

10.000 override için serileştirme/deserileştirme yaklaşık yarım saniye seviyesindedir. Bu ölçüm daha sonraki profiling için referans olabilir; bu aşamada ölçüm dışı optimizasyon yapılmamıştır.

## 5. Korunan tasarım garantileri

- Immutable temel harita verisi runtime değişikliklerinden ayrıdır.
- Runtime override'ları WorldId kapsamında MapId ile ayrılır.
- Snapshot geri yüklemesi birleştirme değil, hedef haritanın override kümesini tam değiştirme işlemidir.
- Temel harita fingerprint uyuşmazlığı runtime mutasyonundan önce reddedilir.
- Harita unload/reload işlemi bellekteki override'ları silmez.
- Dosya yükleme ve doğrulama Pygame/render katmanına bağlı değildir.

## 6. Kapsam sınırları

Bu aşama oyuncu, NPC, envanter, görev, kaynak, bina, oyun nesnesi, tam save slot, autosave, dünya çapında çoklu harita transaction, otomatik harita yükleme/tahliye, offline progression, hareket, fizik, kamera, render veya ana oyun entegrasyonu sağlamaz.

Aşama 3'ün bütünleşik kabul kriterleri ve kalan sınırlar [Genel Aşama 3 Kapanış Raporu](PHASE-03-WORLD-REPORT.md) içindedir.
