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

Aşama 5'in son GitHub laboratuvar CI doğrulaması **584 passed** sonucunu verdi. Kullanıcının Windows bilgisayarındaki son tam test çalıştırması henüz bekleniyor.

Özel GitHub Actions laboratuvar iş akışı tam test paketini ve harita/runtime persistence benchmark'larını başarıyla çalıştırdı. Ana `Core quality` iş akışının Linux ve Windows job'ları da laboratuvar paketi kurulum düzeltmesinden sonra başarılı oldu. Run bağlantıları genel kapanış raporunda kayıtlıdır.

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

**Aşama 0–3:** Tamamlandı ve teknik olarak kabul edildi. Dünya kimlikleri, hücre/harita modeli, çoklu harita kaydı, View/Runtime ayrımı ve map/runtime JSON persistence dahildir.

**Aşama 4:** Sürekli hareket sistemi kullanıcı tarafından kabul edilerek kapatıldı.

**Aşama 5:** 5.1–5.7 fizik çekirdeği ve otomatik doğrulamaları tamamlandı. Son denetimde Pygame kabul demosu da CollisionAwareMovementSystem'e bağlandı; demo için yeni regresyon testleri eklendi. Laboratuvar 584 ve Core Quality Linux/Windows 2.047'şer test sonuçları bu son demo entegrasyonundan önceki kod sürümüne aittir. Kullanıcının bilgisayarında güncel tam test paketi ve nihai görsel kabul bekleniyor; aşama henüz kapatılmadı.

### Mimari sınırlar

- Kayıtlı harita kataloğu ile belleğe yüklenmiş harita tanımları ayrıdır.
- Kayıtlı her harita aynı anda bellekte veya simülasyonda tutulmaz.
- Runtime override'ları harita unload/reload sırasında bellekte korunur; disk kaydı açık persistence API'siyle yapılır.
- Otomatik harita yükleme/tahliye, cache politikası ve offline progression henüz uygulanmadı.
- Kamera, nihai render, NPC/kaynak simülasyonu, oyun nesnesi sistemi ve ana oyuna entegrasyon sonraki aşamaların kapsamındadır. Sürekli hareket Aşama 4'te, fizik/çarpışma Aşama 5'te laboratuvar içinde uygulanmıştır.

ADR-003 sınır davranışı: eşit mesafede karakterin önceki hücresi korunur; sınır geçilip diğer hücre daha yakın hâle geldiğinde yeni hücre seçilir. Önceki hücre bilgisi verilmezse deterministik cube-rounding yedek kuralı kullanılır.
