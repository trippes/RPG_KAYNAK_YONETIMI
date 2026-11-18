# Aşama 14 — Manuel Kabul Kontrol Listesi

**Amaç:** Content data foundation, beş vektör profil ve mevcut dünya/render davranışında kullanıcı bilgisayarında son doğrulama.  
**Kapsam:** Masaüstü Content Editor yoktur; bu aşamada GUI testi yapılmaz.

## 1. Hazırlık

PowerShell'de laboratuvar klasörüne gir:

```powershell
cd "C:\Users\sabri\Desktop\Yeni klasör (12)\RPG_KAYNAK_YONETIMI\experiments\hex_world_laboratory"
python -m pip install -e ".[test,quality]"
```

Depo farklı klasördeyse yalnızca `cd` yolunu kendi depo konumuna göre değiştir.

## 2. Otomatik yerel doğrulama

```powershell
python -m pytest -q
python -m ruff check src/hex_world_lab/content src/hex_world_lab/rendering/procedural src/hex_world_lab/rendering/environment_assets.py tests/unit/test_content_drawing.py tests/unit/test_content_library_map.py tests/unit/test_content_persistence.py tests/unit/test_content_rendering_adapter.py tests/unit/test_content_architecture_boundary.py scripts/render_phase_14_content.py benchmarks/benchmark_phase_14_content.py
python -m ruff format --check src/hex_world_lab/content src/hex_world_lab/rendering/procedural src/hex_world_lab/rendering/environment_assets.py tests/unit/test_content_drawing.py tests/unit/test_content_library_map.py tests/unit/test_content_persistence.py tests/unit/test_content_rendering_adapter.py tests/unit/test_content_architecture_boundary.py scripts/render_phase_14_content.py benchmarks/benchmark_phase_14_content.py
```

## 3. Vektör profil görsel kanıtı

```powershell
python scripts/render_phase_14_content.py --output artifacts/phase-14-local
```

`artifacts/phase-14-local` klasöründe `tree.png`, `rock.png`, `bush.png`, `grass.png`, `flower.png`, `profile-sheet.png` ve `manifest.json` oluşmalıdır.

Kontrol et:
- Beş profilin tamamı görünür ve transparan arka planlı.
- Ağaç gövde/kök ve taç katmanları ayrı sıralanmış.
- Kaya ve çalı geometrileri bozulmamış.
- Çimen ve çiçek aynı seed ile deterministik.
- Manifest beş profil, anchor ve katman/öğe sayılarını listeliyor.
- Birleşik preview sahnesi beş içerik örneğini doğru ID'lerle tanıyor.

## 4. Eski görsel ve dünya regresyonu

```powershell
python -m hex_world_lab
```

Laboratuvar açıldığında mevcut harita/kamera/oyuncu hareketi davranışını kontrol et. F3 collider debug ve F4 anchor/bounds debug kısayollarının önceki kabul edilmiş davranışları korunmalı. Yeni içerik verisi mevcut demo davranışını değiştirmemeli.

## 5. Performans raporu

```powershell
python benchmarks/benchmark_phase_14_content.py
```

Benchmark `artifacts/phase-14/benchmark.json` üretir. Süreler donanımdan bağımsız kesin eşik değildir; aynı makinede soğuk çizim ve cache hit karşılaştırması için kullanılır.

## 6. Kabul bildirimi

Aşağıdakileri kontrol ettikten sonra Aşama 14 manuel kabulünü bildir:
- [ ] Pytest, Ruff lint ve Ruff format başarılı.
- [ ] Beş profil PNG'si doğru üretildi.
- [ ] Mevcut ağaç/kaya/çalı görünümü önceki kabul edilen görüntülerle aynı.
- [ ] Kamera, harita, hareket ve debug davranışında regresyon yok.
- [ ] İçerik preview manifestinde beş yerleşim doğru.
- [ ] Benchmark JSON üretildi.

Herhangi bir görsel fark veya hata varsa yalnızca ilgili dosya/ekran görüntüsü ve hata çıktısını gönder; kapanış raporu kabul öncesinde güncellenecek.
