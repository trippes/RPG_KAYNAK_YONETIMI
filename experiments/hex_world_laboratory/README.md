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
- [Aşama 1 Uygulama Raporu](reports/PHASE-01-INFRASTRUCTURE-REPORT.md) — altyapı uygulaması ve doğrulama kanıtları.

## Kurulum (Windows PowerShell)

Laboratuvar dizinine geç:

```powershell
cd experiments/hex_world_laboratory
```

Sanal ortam oluştur ve etkinleştir:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Geliştirme/test bağımlılıklarını kur:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Bu aşamanın Windows doğrulaması Python 3.12.10 ile yapılmıştır. Pygame 2.6.1 için hazır Windows wheel paketi bu ortamda başarıyla kurulmuştur. Farklı Python sürümlerinde paket wheel kullanılabilirliği değişebileceğinden, laboratuvar için doğrulanmış sürüm olan Python 3.12 tercih edilir.

## Çalıştırma

```powershell
python -m hex_world_lab
```

960×640 Pygame penceresi açılır. Pencereyi kapatmak uygulamayı sonlandırır.

## Test

```powershell
python -m pytest -q
```

Pygame yaşam döngüsü integration testi SDL dummy video/audio sürücülerini kullanır; masaüstü penceresi açmadan çalışmalıdır.

## Mevcut durum

**Aşama 1 — TAMAMLANDI VE KULLANICI MAKİNESİNDE DOĞRULANDI.** Bağımsız Python paketi, minimal Pygame uygulaması ve başlangıç testleri hazırdır. Kullanıcının Windows ortamında pytest sonucu 2 passed olarak doğrulanmış; gerçek 960×640 Pygame penceresi açılmış ve hatasız kapatılmıştır. Doğrulanan ortam Python 3.12.10, Pygame 2.6.1 ve pytest 8.4.2'dir.

Henüz hex geometri, dünya, hareket, fizik, kamera veya render sistemi uygulanmadı. Aşama 2 için ayrıca plan ve kullanıcı onayı gereklidir.
