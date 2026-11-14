# Eldoria Hex World Laboratory

Eldoria'nın canon altıgen dünya mimarisini bağımsız olarak araştırmak, prototiplemek ve doğrulamak için ayrılmış laboratuvar.

## Çalışma ilkeleri
- Kendi giriş noktası, bağımlılıkları ve testleri vardır.
- Ana oyunun modülleri bu laboratuvarın bağımlılığı değildir.
- Deney sonuçları doğrulanmadan `demo_eldoria` dalına aktarılmaz.
- Her aşama öncesinde plan hazırlanır; kullanıcı onayı olmadan uygulamaya geçilmez.
- Laboratuvar çalışmaları yalnızca `experiment/hex-world-laboratory` dalında yürütülür.

## Ana belgeler
- [Master Plan](docs/HEX_WORLD_LAB_MASTER_PLAN.md) — ana yol haritası ve çalışma sözleşmesi.
- [Mimari Sözleşme](docs/ARCHITECTURE_SPECIFICATION.md) — hedef katmanlar ve veri sınırları.
- [Geliştirme Kuralları](docs/DEVELOPMENT_RULES.md) — onay, branch, uygulama ve commit prosedürü.
- [Test ve Kabul Ölçütleri](docs/TESTING_AND_ACCEPTANCE_CRITERIA.md) — doğrulama ve aşama kapıları.
- [ADR Şablonu](docs/decisions/ADR-TEMPLATE.md) — mimari karar kayıt formatı.
- [Aşama 0 Kapanış Raporu](reports/PHASE-00-FOUNDATION-CLOSURE.md) — planlama çıktıları.
- [Aşama 1 Uygulama Raporu](reports/PHASE-01-INFRASTRUCTURE-REPORT.md) — altyapı uygulaması ve doğrulama durumu.

## Kurulum (Windows PowerShell)

Laboratuvar dizinine geç:

```powershell
cd experiments/hex_world_laboratory
```

Sanal ortam oluştur ve etkinleştir:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Geliştirme/test bağımlılıklarını kur:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Python 3.11 veya üzeri gereklidir. Bilgisayarında birden fazla Python sürümü varsa `py -0p` ile kurulu sürümleri görebilirsin.

## Çalıştırma

```powershell
python -m hex_world_lab
```

Pencereyi kapatmak uygulamayı sonlandırır.

## Test

```powershell
python -m pytest -q
```

Pygame yaşam döngüsü integration testi SDL dummy video/audio sürücülerini kullanır; masaüstü penceresi açmadan çalışmalıdır.

## Mevcut durum

**Aşama 1 — Bağımsız paket, minimal Pygame uygulaması ve başlangıç testleri eklendi.** Temiz ortam kurulumu ve yerel test sonuçları kullanıcı makinesinde doğrulanmayı bekliyor. Henüz hex geometri, hareket, fizik, kamera veya render sistemi uygulanmadı.
