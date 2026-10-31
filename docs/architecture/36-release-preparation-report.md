# Yayın Hazırlığı Raporu

## Uygulanan kapılar

- Sürüm `3.0.0rc1` olarak release candidate seviyesine alındı.
- `rpg-kaynak-yonetimi` komut satırı giriş noktası eklendi.
- Beklenmeyen masaüstü hataları `logs/eldoria.log` dosyasına kaydediliyor.
- Mevcut save dosyası üzerine yazılmadan önce `<save>.bak` oluşturuluyor.
- Save yazımı atomic replace davranışını koruyor.
- İçerik JSON dosyaları paket veri dosyası olarak tanımlandı.
- Yayın araçları `requirements-release.txt` içine ayrıldı.
- `--version` ile paket sürümü doğrulanabiliyor.

## Yayın öncesi komutlar

```powershell
python scripts/verify_release.py
python main.py --version
python main.py --play
```

Dağıtım artefaktı üretimi için `requirements-release.txt` kurulmalı ve
`python -m build` çalıştırılmalıdır. Bu çalışma ortamında build doğrulaması
`setuptools.build_meta` bulunmadığı için tamamlanamadı; kaynak doğrulama kapısı
başarılıdır.

İlk komut headless otomatik kapıdır. İkinci komut gerçek pencere, navigasyon,
save/load ve ilk dikey dilimin manuel kontrolüdür.
