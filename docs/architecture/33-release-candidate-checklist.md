# Release Candidate Verification

Core ve application altyapısı tamamlandıktan sonra her değişiklik, oyunun
oynanabilir dikey dilimini geliştirmeden önce bu doğrulama kapısından geçer.

## Otomatik kapı

```powershell
python scripts/verify_release.py
```

Bu komut:

1. tüm unittest suite'ini çalıştırır;
2. Core, application, domain, UI ve test kaynaklarını derler;
3. `main.py` ile başlatma smoke testini çalıştırır.

Etkileşimli Pygame oturumu otomatik kapının dışında tutulur. Yeni bir UI veya
oynanış değişikliğinde ayrıca şu manuel kontrol yapılmalıdır:

```powershell
python main.py --play
```

## Donmuş sınır

Bu kapı geçilmeden Core canonical state, scheduler, event transport veya
restore sözleşmesine yeni gameplay state eklenmez. Yeni oynanış özellikleri
application/domain ve Pygame adapter katmanlarında geliştirilir.

## Sürüm adayı sonrası hedef

Doğrulama kapısı yeşil kaldıktan sonra ilk ürün hedefi tek uçtan uca akıştır:

`karakter oluştur → NPC ile konuş → görev al → seyahat et → kaynak topla →
pazarı kullan → combat yap → ödül al → kaydet/yükle`
