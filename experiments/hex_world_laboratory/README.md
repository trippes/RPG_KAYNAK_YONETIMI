# Eldoria Hex World Laboratory

Eldoria'nın canon altıgen dünya mimarisini ana oyundan bağımsız araştırmak, prototiplemek ve doğrulamak için kullanılan laboratuvar.

## Çalışma ilkeleri

- Kendi Python paketi, giriş noktası, bağımlılıkları ve test altyapısı vardır.
- Ana oyunun modülleri laboratuvarın çalışma zamanı bağımlılığı değildir.
- Deneyler doğrulanmadan `demo_eldoria` dalına aktarılmaz.
- Her yeni aşama ve kapsam değişikliği için teknik plan ve kullanıcı onayı gerekir.
- Laboratuvar uygulamaları yalnızca `experiment/hex-world-laboratory` dalında tutulur.

## Ana belgeler

- [Master Plan](docs/HEX_WORLD_LAB_MASTER_PLAN.md)
- [Mimari Sözleşme](docs/ARCHITECTURE_SPECIFICATION.md)
- [Geliştirme Kuralları](docs/DEVELOPMENT_RULES.md)
- [Test ve Kabul Ölçütleri](docs/TESTING_AND_ACCEPTANCE_CRITERIA.md)
- [Hex Koordinat Sözleşmesi](docs/HEX_COORDINATE_CONVENTION.md)
- [Aşama 3 Teknik Planı](docs/PHASE-03-TECHNICAL-PLAN.md)
- [Aşama 4 Genel Planı](docs/PHASE-04-GENERAL-PLAN.md)
- [Aşama 4 Teknik Planı](docs/PHASE-04-TECHNICAL-PLAN.md)
- [Aşama 5 Genel Planı](docs/PHASE-05-GENERAL-PLAN.md)
- [Aşama 5 Teknik Planı](docs/PHASE-05-TECHNICAL-PLAN.md)
- [Aşama 6 Genel Planı](docs/PHASE-06-GENERAL-PLAN.md)
- [Aşama 6 Teknik Planı](docs/PHASE-06-TECHNICAL-PLAN.md)
- [Aşama 6 Görsel Kabul Kontrol Listesi](docs/PHASE-06-MANUAL-ACCEPTANCE-CHECKLIST.md)
- [Aşama 3.6 Teknik Planı](docs/PHASE-03.6-TECHNICAL-PLAN.md)
- [Aşama 3.7 Runtime Persistence Teknik Planı](reports/PHASE-03.7-TECHNICAL-PLAN.md)
- [Harita JSON Şema v1](docs/MAP_JSON_SCHEMA_V1.md)
- [Runtime JSON Şema v1](docs/RUNTIME_JSON_SCHEMA_V1.md)

## Aşama raporları

- [Aşama 0 — Temel Kapanış](reports/PHASE-00-FOUNDATION-CLOSURE.md)
- [Aşama 1 — Altyapı](reports/PHASE-01-INFRASTRUCTURE-REPORT.md)
- [Aşama 2 — Geometri](reports/PHASE-02-GEOMETRY-REPORT.md)
- [Aşama 3.6 — Harita JSON Persistence](reports/PHASE-03.6-REPORT.md)
- [Aşama 3.7 — Runtime Persistence](reports/PHASE-03.7-REPORT.md)
- [Aşama 3 — Genel Dünya Modeli Kapanış Raporu](reports/PHASE-03-WORLD-REPORT.md)
- [Aşama 4 — Sürekli Hareket Kapanış Raporu](reports/PHASE-04-CLOSURE-REPORT.md)
- [Aşama 5 — Gövde Modeli, Çarpışma ve Fizik Kapanış Raporu](reports/PHASE-05-CLOSURE-REPORT.md)
- [Aşama 6 — Otomatik Doğrulama Günlüğü](reports/PHASE-06-VALIDATION-LOG.md)
- [Aşama 6 — Kapanış Raporu (Kabul Edildi)](reports/PHASE-06-CLOSURE-REPORT.md)

## Kurulum (Windows PowerShell)

Laboratuvar dizinine geç:

```powershell
cd experiments/hex_world_laboratory
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Python 3.12 önerilir. Paket Python 3.11 ve üzerini destekleyecek şekilde tanımlanmıştır.

## Çalıştırma

```powershell
python -m hex_world_lab
```

960×640 Pygame laboratuvar penceresini açar. Dünya veri modeli ve geometri çekirdeği çizim katmanından bağımsızdır.

## Test

```powershell
python -m pytest -q
```

Son kullanıcı tarafından bildirilen yerel tam test sonucu **588/588 başarılıdır**. Bu sayı, son Pygame demo entegrasyonunu da kapsayan yerel çalıştırma sonucudur; GitHub Actions CI sonucu olarak sunulmaz.

Aşama 6 son otomatik doğrulamasında GitHub Actions Laboratuvar CI 681/681 testle başarılıdır; tüm benchmark adımları tamamlanmıştır. Aynı commit için Core Quality Linux ve Windows job'ları başarılıdır. Run bağlantıları ve alt aşama kanıtları reports/PHASE-06-VALIDATION-LOG.md içinde kayıtlıdır.

## Harita ve runtime persistence

Harita başlangıç tanımları JSON Schema v1 ile saklanır. Oyun sırasında değişen hücre alanları ayrı runtime snapshot dosyalarında tutulur. Runtime snapshot yalnızca `terrain_id`, `is_walkable` ve `has_obstacle` değişikliklerini içerir ve temel haritanın canonical SHA-256 parmak izini doğrular.

Örnek API:

```python
from pathlib import Path
from hex_world_lab.world.persistence import load_map_file, save_map_file

map_definition = load_map_file(Path("scenarios/maps/starting_valley.json"))
save_map_file(map_definition, Path("my_map.json"), mode="create")
```

Varsayılan `create` modu mevcut dosyayı ezmez. Değiştirme için açıkça `mode="replace"` kullanılmalıdır. Runtime snapshot API'si ve şema ayrıntıları ilgili teknik belgelerde açıklanır.

## Mevcut durum

**Aşama 0–5:** Tamamlandı ve kabul edildi. Aşama 3 dünya/runtime ve persistence; Aşama 4 sürekli hareket; Aşama 5 gövde, hex/nesne çarpışmaları, kayma, CCD ve 60 TPS entegrasyonunu kapsar. Aşama 5 son kullanıcı bildirimiyle 588/588 yerel test ve başarılı masaüstü kabulüyle kapatılmıştır.

**Aşama 6 — TAMAMLANDI VE KABUL EDİLDİ:** Kamera ve dünya-ekran dönüşümünün 6.1–6.5 teknik uygulaması tamamlandı. Son otomatik doğrulama 681/681 test, Linux/Windows Core Quality ve benchmark adımlarında başarılıdır. Kamera, zoom, yumuşak takip, harita bounds politikası, Pygame renderer, pencere resize ve fareyle hex seçimi entegre edildi. Kullanıcı 17 Kasım 2026 tarihinde tüm masaüstü/görsel kontrollerin başarılı olduğunu bildirdi; Aşama 6 resmen kapatıldı. Kontrol adımları docs/PHASE-06-MANUAL-ACCEPTANCE-CHECKLIST.md içindedir. Aşama 7'nin 7.1–7.8 uygulaması, 703/703 otomatik testi, Linux/Windows CI, benchmark ve kullanıcı görsel kabulü tamamlanmış; aşama 17 Kasım 2026 tarihinde kapatılmıştır. Aşama 8'in 8.1–8.8 teknik uygulaması, 729/729 test, Linux/Windows Core Quality, tüm benchmarklar ve kullanıcı görsel/regresyon kabulü tamamlanmıştır. Aşama 8 resmen kapatılmıştır; Aşama 9–13 henüz başlatılmamıştır.

### Mimari sınırlar

- Kayıtlı harita kataloğu ile belleğe yüklenmiş harita tanımları ayrıdır.
- Kayıtlı her harita aynı anda bellekte veya simülasyonda tutulmaz.
- Runtime override'ları harita unload/reload sırasında bellekte korunur; disk kaydı açık persistence API'siyle yapılır.
- Otomatik harita yükleme/tahliye, cache politikası ve offline progression henüz uygulanmadı.
- Kamera, nihai render, NPC/kaynak simülasyonu, oyun nesnesi sistemi ve ana oyuna entegrasyon sonraki aşamaların kapsamındadır. Sürekli hareket Aşama 4'te, fizik/çarpışma Aşama 5'te laboratuvar içinde uygulanmıştır.

ADR-003 sınır davranışı: eşit mesafede karakterin önceki hücresi korunur; sınır geçilip diğer hücre daha yakın hâle geldiğinde yeni hücre seçilir. Önceki hücre bilgisi verilmezse deterministik cube-rounding yedek kuralı kullanılır.


## Aşama 7 — Render ve görsel doğrulama

**Durum:** TAMAMLANDI VE KABUL EDİLDİ — 7.1–7.8, 703/703 otomatik test, Linux/Windows CI, benchmark ve kullanıcı görsel kabulü 17 Kasım 2026 tarihinde tamamlandı.

- [Aşama 7 Genel Planı](docs/PHASE-07-GENERAL-PLAN.md)
- [Aşama 7 Teknik Mimari Planı](docs/PHASE-07-TECHNICAL-PLAN.md)
- [Manuel Görsel Kabul Kontrol Listesi](docs/PHASE-07-MANUAL-ACCEPTANCE-CHECKLIST.md)
- [Uygulama ve Doğrulama Raporu](reports/PHASE-07-IMPLEMENTATION-VALIDATION-REPORT.md)
- [Görsel test sahneleri — GitHub Actions artifact](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44045118838/artifacts/14311276474)

Aşama 7 kapanış raporu: [PHASE-07-CLOSURE-REPORT.md](reports/PHASE-07-CLOSURE-REPORT.md). Aşama 8'in teknik uygulaması tamamlandı; kullanıcı görsel kabulini bekliyor. Dünya görsel zenginleştirmesi Aşama 7'nin geriye dönük eksik işi değildir.


## Aşama 8 — Mekânsal indeksleme ve performans karşılaştırması

**Durum:** TAMAMLANDI VE KABUL EDİLDİ — 8.1–8.8, 729/729 test, Linux/Windows Core Quality, benchmarklar ve kullanıcı masaüstü/görsel kabulü 17 Kasım 2026 tarihinde tamamlandı.

- [Aşama 8 Genel Planı](docs/PHASE-08-GENERAL-PLAN.md)
- [Aşama 8 Teknik Mimari Planı](docs/PHASE-08-TECHNICAL-PLAN.md)
- [Uygulama ve Doğrulama Raporu](reports/PHASE-08-IMPLEMENTATION-VALIDATION-REPORT.md)
- [Manuel Görsel/Kabul Kontrol Listesi](docs/PHASE-08-MANUAL-ACCEPTANCE-CHECKLIST.md)
- [Spatial İndeks Seçim ADR'si](docs/ADR-008-SPATIAL-INDEX-SELECTION.md)
- [Aşama 8 Kapanış Raporu](reports/PHASE-08-CLOSURE-REPORT.md)
- [Benchmark raporları — GitHub Actions artifact](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44054382282)

Aşama 8, kullanıcının manuel kontrolleri kabul etmesi üzerine 17 Kasım 2026 tarihinde resmen kapatılmıştır. Sıradaki planlı aşama Aşama 9 — Varlıklar ve etkileşimlerdir.
