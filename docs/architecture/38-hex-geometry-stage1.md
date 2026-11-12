# Eldoria — Aşama 1: Altıgen Geometri Çekirdeği

**Durum:** Uygulandı; doğrulama GitHub Actions sonucuna bağlıdır.  
**Dal:** `demo_eldoria`  
**Kapsam:** Bağımsız axial geometri ve saf piksel dönüşüm matematiği.

## Uygulanan API

- `HexCoord(q, r)`: immutable, hashable, sıralanabilir axial koordinat value object'i.
- `HexDirection`: EAST, NORTH_EAST, NORTH_WEST, WEST, SOUTH_WEST, SOUTH_EAST yönleri; offset ve opposite tek kaynaktan gelir.
- `HexCoord.neighbor()`, `neighbors()`, `translated()`, toplama/çıkarma ve `distance_to()`.
- `axial_to_pixel()`: pointy-top hücre merkezini piksele çevirir.
- `fractional_axial_to_hex()`: cube rounding ile kesirli axial koordinatı deterministik hücreye yuvarlar.
- `pixel_to_axial()`: piksel noktasını axial hücreye dönüştürür.

## Matematik ve tip kuralları

- q/r yalnızca int kabul eder; bool ve float reddedilir.
- Negatif axial koordinatlar geçerlidir.
- HexCoord harita sınırı, geçilebilirlik, map ID veya fiziksel mesafe bilmez.
- Altıgen uzaklığı topolojik hücre adımıdır; feet, hareket maliyeti veya hız değildir.
- Pointy-top piksel dönüşümünde hex_size merkezden köşeye uzaklıktır ve pozitif/sonlu olmalıdır.
- Piksel dönüşümü tuple döndürür; genel `Position` API'sine karışmaz.
- Pixel hit-test çağrısından önce kamera/viewport ters dönüşümü yapılmalı; dönen koordinat sonraki aşamada valid-cell maskesiyle doğrulanmalıdır.
- Paylaşılan kenar/köşe eşitliklerinde cube rounding sabit q → r → s önceliğiyle deterministiktir.

## Test kapsamı

`tests/test_foundation/test_hex_coord.py` yön offset'lerini, karşı yön involution'ını, komşuluk simetrisini, immutable/hash davranışını, negatif koordinatları, aritmetiği, uzaklık örneklerini ve üçgen eşitsizliğini sınar.

`tests/test_foundation/test_hex_geometry.py` pointy-top merkez formüllerini, farklı hex size değerlerinde merkez round-trip'ini, kesirli axial rounding'i, kenar eşitliğinin deterministikliğini ve geçersiz girdileri sınar.

## Bilinçli olarak yapılmayanlar

- `Position` değiştirilmedi.
- WorldMap, MapDefinition, LocalMapDefinition, MovementManager, content JSON ve save schema değiştirilmedi.
- Haritalar altıgene dönüştürülmedi.
- Pygame çizimi, kamera, fare input'u ve oyun hareketi bağlanmadı.
- Feet, hücre başına fiziksel mesafe, movement point, hız ve savaş menzili tanımlanmadı.
- NPC, kaynak, nesne ve geçiş koordinatları değiştirilmedi.

Aşama 2'ye geçiş ancak geometri testleri ve mevcut regresyon doğrulaması başarılı olduktan sonra yapılmalıdır.
