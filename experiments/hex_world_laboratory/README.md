# Eldoria Hex World Laboratory

Eldoria'nın canon altıgen dünya mimarisini bağımsız araştırmak ve doğrulamak için laboratuvar.

## Çalışma ilkeleri
- Kendi giriş noktası, bağımlılıkları ve testleri vardır.
- Ana oyunun modülleri çalışma zamanı bağımlılığı değildir.
- Deneyler doğrulanmadan demo_eldoria dalına aktarılmaz.
- Her aşama öncesi plan ve kullanıcı onayı gerekir.
- Laboratuvar çalışmaları yalnızca experiment/hex-world-laboratory dalındadır.

## Ana belgeler
- Master Plan: docs/HEX_WORLD_LAB_MASTER_PLAN.md
- Mimari Sözleşme: docs/ARCHITECTURE_SPECIFICATION.md
- Geliştirme Kuralları: docs/DEVELOPMENT_RULES.md
- Test ve Kabul Ölçütleri: docs/TESTING_AND_ACCEPTANCE_CRITERIA.md
- Hex Koordinat Sözleşmesi: docs/HEX_COORDINATE_CONVENTION.md
- ADR Şablonu: docs/decisions/ADR-TEMPLATE.md
- Aşama 0 Raporu: reports/PHASE-00-FOUNDATION-CLOSURE.md
- Aşama 1 Raporu: reports/PHASE-01-INFRASTRUCTURE-REPORT.md
- Aşama 2 Raporu: reports/PHASE-02-GEOMETRY-REPORT.md\n- Aşama 3.6 Teknik Planı: docs/PHASE-03.6-TECHNICAL-PLAN.md\n- Harita JSON Şema v1: docs/MAP_JSON_SCHEMA_V1.md\n- Aşama 3.6 Uygulama Raporu: reports/PHASE-03.6-REPORT.md

## Kurulum (Windows PowerShell)
Laboratuvar dizinine geç:
```powershell
cd experiments/hex_world_laboratory
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```
Python 3.12.10, Pygame 2.6.1 ve pytest 8.4.2 Windows ortamında önceki aşamada doğrulanmıştır. Python 3.12 önerilir.

## Çalıştırma
```powershell
python -m hex_world_lab
```
960x640 Pygame penceresi açılır. Geometri çekirdeği henüz bu pencereye bağlı değildir.

## Test
```powershell
python -m pytest -q
```
Geometri çekirdeği saf Python'dur ve Pygame yüklemeden import edilebilir.

## Harita JSON persistence

Aşama 3.6 kapsamında harita başlangıç tanımları JSON şema v1 ile kaydedilip yüklenebilir. API ve alan sözleşmesi için [MAP_JSON_SCHEMA_V1.md](docs/MAP_JSON_SCHEMA_V1.md) belgesine bakın.

```python
from pathlib import Path
from hex_world_lab.world.persistence import load_map_file, save_map_file

map_definition = load_map_file(Path("scenarios/maps/starting_valley.json"))
save_map_file(map_definition, Path("my_map.json"), mode="create")
```

Varsayılan `create` modu mevcut dosyanın üzerine yazmaz. Değiştirme için açıkça `mode="replace"` verilmelidir. Runtime override'ları bu dosyaya dahil değildir; ayrı Aşama 3.7 kapsamındadır.

## Mevcut durum
**Aşama 2 — TAMAMLANDI VE TEKNİK OLARAK KABUL EDİLDİ.** Geometri çekirdeğinin önceki doğrulaması 53 testti.

**Aşama 3.1–3.5 — UYGULANDI. Aşama 3.6 — UYGULAMA VE ÖZEL CI DOĞRULAMASI TAMAMLANDI; KULLANICI KABULÜ BEKLİYOR.** Son doğrulama 249 testin başarılı olduğunu ve 100 / 1.000 / 10.000 hücre benchmark adımının tamamlandığını gösterir. Ayrıntılar: [Aşama 3.6 Raporu](reports/PHASE-03.6-REPORT.md).

ADR-003 sınır davranışı: eşit mesafede karakterin önceki hücresi korunur; sınır geçilip diğer hücre daha yakın hâle geldiğinde yeni hücre seçilir. Önceki hücre bilgisi verilmezse deterministik cube-rounding yedek kuralı kullanılır.

Aşama 3.6 yalnızca immutable harita başlangıç verisini kapsar. Runtime persistence, hareket, fizik, kamera, render ve ana oyuna entegrasyon bu aşamanın dışındadır.
