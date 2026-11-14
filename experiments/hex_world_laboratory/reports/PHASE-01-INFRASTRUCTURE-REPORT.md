# Aşama 1 — Bağımsız Çalışma ve Test Altyapısı Uygulama Raporu

- **Proje:** Eldoria — Hex World Laboratory
- **Dal:** `experiment/hex-world-laboratory`
- **Aşama:** 1
- **Durum:** UYGULAMA DOSYALARI HAZIR — YEREL DOĞRULAMA BEKLENİYOR
- **Kapsam:** Bağımsız Python paketi, Pygame uygulama kabuğu ve başlangıç testleri.

## 1. Uygulanan işler

- `src/hex_world_lab` bağımsız Python paketi hâline getirildi.
- `python -m hex_world_lab` giriş noktası eklendi.
- Pencere ayarları `AppConfig` veri sınıfında toplandı.
- Pygame başlatma, event loop ve güvenli kapanış akışı oluşturuldu.
- Testlerde sonlu frame çalıştırabilmek için `max_frames` test seam'i eklendi.
- Paket keşfi `src` yerleşimine açıkça yapılandırıldı.
- pytest yapılandırmasına `src` yolu eklendi.
- Paket import ve headless uygulama yaşam döngüsü testleri eklendi.
- Windows PowerShell kurulum, çalıştırma ve test yönergeleri README'ye yazıldı.

## 2. Değişen dosyalar

- `pyproject.toml`
- `README.md`
- `src/hex_world_lab/__init__.py`
- `src/hex_world_lab/__main__.py`
- `src/hex_world_lab/app.py`
- `src/hex_world_lab/config.py`
- `tests/unit/test_package_import.py`
- `tests/integration/test_app_lifecycle.py`

## 3. Mimari sınırlar

Bu aşamada geometri, dünya, hareket, fizik, kamera ve render katmanları oluşturulmadı. Ana oyun modüllerine bağımlılık eklenmedi. Pygame yalnızca laboratuvar uygulama kabuğunda kullanılıyor.

## 4. Kullanıcı makinesinde çalıştırılacak doğrulama

Laboratuvar dizininde:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python -m pytest -q
python -m hex_world_lab
```

Beklenen otomatik test sonucu: 2 testin geçmesi. Pencere testi SDL dummy sürücüsünü kullanır; gerçek pencere açılışı ayrıca son komutla görsel olarak kontrol edilir.

## 5. Doğrulama sınırı

Bu rapor, dosyaların depoya eklenmesini ve yapılandırmanın hazırlanmasını kaydeder. Bu çalışma ortamında kullanıcının Windows makinesinde temiz sanal ortam kurulumu, bağımlılık kurulumu, pytest ve gerçek pencere açılışı çalıştırılamadı. Bu nedenle testler **geçti** olarak raporlanmıyor.

## 6. Kabul durumu

**BEKLEMEDE — KULLANICI MAKİNESİNDE TEST KANITI GEREKLİ.**

Kullanıcı kurulum ve test komutlarını çalıştırıp sonuçları paylaştığında hata varsa düzeltilecek; tüm kabul ölçütleri doğrulanınca Aşama 1 kapanış durumu güncellenecek. Bu rapor Aşama 2'ye geçiş izni değildir.
