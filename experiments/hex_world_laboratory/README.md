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

Son yerel Windows tam test doğrulaması: **288 passed in 2.01s**.

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

**Aşama 0–2:** Tamamlandı ve teknik olarak kabul edildi.

**Aşama 3.1–3.6:** Dünya kimlikleri, hücre/harita modeli, çoklu harita kaydı, View/Runtime ayrımı ve harita JSON persistence uygulandı.

**Aşama 3.7:** Runtime persistence uygulandı; sparse override kayıtları, SHA-256 temel harita uyumluluk kontrolü, atomik geri yükleme ve benchmark'lar eklendi.

**Aşama 3 genel teknik kapanışı:** Bütünleşik denetim ve raporlama tamamlandı. Son test paketi 288 testten oluşuyor. Kullanıcı nihai kabulü bekleniyor; Aşama 4 başlamadı.

### Mimari sınırlar

- Kayıtlı harita kataloğu ile belleğe yüklenmiş harita tanımları ayrıdır.
- Kayıtlı her harita aynı anda bellekte veya simülasyonda tutulmaz.
- Runtime override'ları harita unload/reload sırasında bellekte korunur; disk kaydı açık persistence API'siyle yapılır.
- Otomatik harita yükleme/tahliye, cache politikası ve offline progression henüz uygulanmadı.
- Hareket, çarpışma/fizik, kamera, render, NPC/kaynak simülasyonu, oyun nesnesi sistemi ve ana oyuna entegrasyon bu aşamanın kapsamı dışındadır.

ADR-003 sınır davranışı: eşit mesafede karakterin önceki hücresi korunur; sınır geçilip diğer hücre daha yakın hâle geldiğinde yeni hücre seçilir. Önceki hücre bilgisi verilmezse deterministik cube-rounding yedek kuralı kullanılır.
