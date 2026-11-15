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
- Aşama 2 Raporu: reports/PHASE-02-GEOMETRY-REPORT.md

## Kurulum (Windows PowerShell)
Laboratuvar dizinine geç:
```powershell
cd experiments/hex_world_laboratory
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
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

## Mevcut durum
**Aşama 2 — UYGULANDI; TAM LABORATUVAR TESTLERİ KULLANICI ORTAMINDA 49/49 GEÇTİ.** Kullanıcı Windows / Python 3.12.10 ortamında `python -m pytest -q` komutunu çalıştırdığını ve 49/49 sonucunu teyit etti. Geliştirme ortamındaki izole geometri testleri ayrıca Python 3.13.5 / Linux üzerinde 47 test olarak raporlanmıştır.

ADR-003'teki deterministik tie-break ve tolerans politikası nihai kullanıcı değerlendirmesini beklemektedir. Nihai oyun yönelimi henüz seçilmedi. Dünya hücre modeli, hareket, fizik, kamera ve render sonraki aşamalardadır.
