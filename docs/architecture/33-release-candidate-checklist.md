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

## Gerçek oynanış kontrol listesi

Her Pygame oynanış veya harita değişikliğinden sonra yeni bir oyun oturumunda
bu akış baştan sona uygulanır. Her adım beklenen sonucu vermelidir:

- [ ] `python main.py --play` ile pencere açılır; ana menü ve oyun ekranı
      kararlı biçimde görüntülenir.
- [ ] Oyuncu karakteri oluşturulur veya varsayılan karakterle oyuna başlanır;
      karakter ekranı açılır ve geri dönülebilir.
- [ ] Dünya haritası açılır; Köy, dört orman ve dört maden haritası görünür.
- [ ] Köy yerel haritası açılır; çim zemin, landmark/ev, NPC, duvar ve kapılar
      görünür.
- [ ] Köy duvarının dış tile'larına girilemez; dört kapıdan girilip çıkılabilir.
- [ ] Her orman ve maden haritası arasında seyahat edilebilir.
- [ ] Nehir tile'larına girilemez; nehir yalnızca köprü tile'ından geçilebilir.
- [ ] Orman yerel haritasında ağaç seçilip etkileşim tuşuyla odun toplanır;
      envanter miktarı artar.
- [ ] Maden yerel haritasında Demir Madeni seçilip etkileşim tuşuyla demir
      cevheri toplanır; envanterde `iron_ore` görünür.
- [ ] Köyde Demirci Usta Kemal ile konuşulur; demir cevheri görevi alınır.
- [ ] En az üç demir cevheri toplanır; görev ilerlemesi güncellenir.
- [ ] Cevher demirciye teslim edilir; cevher envanterden düşer ve demir kılıç
      ödülü envantere eklenir.
- [ ] Marangoz, han/pazar ve mevcut NPC diyalogları açılır; uygunsuz
      lokasyonlarda ilgili eylemler devre dışı kalır.
- [ ] Envanter, görev takibi, karakter ve harita ekranları arasında geçiş
      yapılır; ekranlar beklenmedik biçimde kapanmaz.
- [ ] Oyun kaydedilir, oturum yeniden açılır ve kayıt yüklenir; konum,
      envanter, görev ilerlemesi ve ödül korunur.
- [ ] Hatalı etkileşimlerde uygulama kapanmaz; kullanıcıya anlaşılır mesaj
      gösterilir.

Kontrol tamamlandığında tarih, test edilen sürüm ve sonucu release notuna
eklenir. Başarısız bir adım varsa yayın adayı doğrulaması tamamlanmış sayılmaz.

## Donmuş sınır

Bu kapı geçilmeden Core canonical state, scheduler, event transport veya
restore sözleşmesine yeni gameplay state eklenmez. Yeni oynanış özellikleri
application/domain ve Pygame adapter katmanlarında geliştirilir.

## Sürüm adayı sonrası hedef

Doğrulama kapısı yeşil kaldıktan sonra ilk ürün hedefi tek uçtan uca akıştır:

`karakter oluştur → NPC ile konuş → görev al → seyahat et → kaynak topla →
pazarı kullan → combat yap → ödül al → kaydet/yükle`
