# Aşama 16 — Ana Oyun Hex Gameplay View

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **ANA OYUN PYGAME EKRANI HEX RUNTIME VIEW'A BAĞLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilim: [Axial Gameplay Placement Catalog](69-phase-16-gameplay-placement-catalog.md)

## 1. Hedef

Eski kare harita ekranı geri getirilmeden, ana oyunun kalıcı gameplay yüzeyini session-scoped `HexWorldRuntime` verisine bağlamak. Presentation, simülasyonun konum/kimlik otoritesi olamaz.

## 2. Yeni HexGameplayView

`game_ui/world_rendering/hex_gameplay_view.py` eklendi. Mevcut ana oyun sunum katmanlarını bir araya getirir:

- `HexTerrainRenderer`: axial map cell terrain çizimi.
- `HexCharacterRenderer`: oyuncu/NPC foot-anchor çizimi.
- `DepthSorter`: entity çizim sırası.
- `HexCamera`: player-follow ve edge-scroll.
- `WorldTransform`: axial → world pixel → screen pixel ve zoom dönüşümü.

View yalnızca runtime snapshot/read API'lerini kullanır. Entity ID, map-local position, movement profile veya occupancy üretmez; oyuncunun konumu `HexWorldRuntime` üzerinden okunur. Render sırasında domain state değiştirilmez.

## 3. Ana ekran ve input

`MainScreen` artık aktif session'da Hex runtime ve player spatial kaydı varsa `HexGameplayView` kullanır. Runtime veya player placement henüz yoksa eski kare haritaya dönmek yerine açık hazırlık mesajını gösterir.

Klavye yönleri altı axial komuta bağlandı:
- Sağ/sol: East/West
- Yukarı/aşağı: North-East/South-East
- Z/X: North-West/South-West

Fare tekerleği yalnızca presentation zoom değerini değiştirir. Zoom sınırlandırılmıştır; simulation coordinates etkilenmez. Runtime veya player kaydı yokken hareket komutu gönderilmez.

## 4. Sınırlar ve henüz yapılmayanlar

Bu dilim gameplay view ve input bağlantısını tamamlar; henüz yeni dünya verisi oluşturmaz.

Mevcut `demo_eldoria` package'ında axial map, world-map placement veya oyuncu başlangıç hücresi tanımı bulunmadığı için yeni oyun otomatik olarak canlı harita başlatmaz. MainScreen hazırlık görünümünde kalır. Herhangi bir q/r başlangıç koordinatı, map ID, NPC konumu veya resource konumu uydurulmamıştır.

Ayrıca bu ilk view diliminde mouse ile hedef seçme/pathfinding, NPC etkileşim seçimi, world transition, authored sprite/asset layer ve 2.5D elevation/depth content pipeline kapsam dışıdır. Bunlar ayrı ve testli dilimlerdir.

## 5. Test kapsamı

- Altı klavye yönünün doğru `HexDirection` değerlerine yönlendirilmesi.
- Fare tekerleğinin yalnızca zoom'u değiştirmesi ve zoom sınırları.
- Runtime yokken movement çağrısı yapılmaması.
- Pygame Surface üzerinde axial map ve player render smoke testi.
- Render sonrasında player `EntityPosition` değerinin değişmediğinin doğrulanması.
- MainScreen'in Hex runtime bulunmayan eski/test service doubles ile uyumluluğu.

## 6. CI doğrulaması

- Doğrulanan HEAD: `5fd38fedf5deeda7d5e994b9cd40309bb700d5cd`
- GitHub Actions: [#44528895988](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44528895988)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.249 test + 235 subtest başarılı**.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Release-candidate verification: iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 7. Sonraki teknik kapı

Sıradaki iş, yeni axial world package'ı için **world runtime başlangıç composition** katmanıdır: package map registry + world-map topology + açık player start position + mevcut NPC/resource/container placement catalog → session-owned HexWorldRuntime ve actor binding.

Bu composition, `starter_content.json` içinde açık `hex_start` verisi bulunmadan runtime/player position üretmemelidir. Mevcut package bu alanı içermediğinden canlı dünya başlangıcı hâlâ içerik tasarımını beklemektedir.
