# Aşama 12 — Manuel Görsel ve İşlevsel Kabul Kontrol Listesi

> Durum: 18 Kasım 2026 — kullanıcı tarafından tamamlandı ve kabul edildi.
> Başlatıcı: python -m hex_world_lab
> Debug: F3 collider; F4 anchor/bounds.

## Prosedürel çizim kalitesi
- [x] Ağaç, kaya ve çalı hazır PNG/JPG/WebP yüklenmeden kod çizicileriyle üretiliyor.
- [ ] Ağaç; gövde, kök, dallar ve farklı tonlarda yaprak kümeleriyle hacimli.
- [ ] Ağaçta ışık ve gölge yüzeyleri ayırt ediliyor; tekdüze primitif görünümünde değil.
- [ ] Kaya çok yüzeyli, hacimli ve ışık/gölge ayrımı belirgin.
- [ ] Çalı ayrı yaprak kümeleri ve alt gölgeyle hacimli.
- [ ] Üç nesne aynı sanat yönüne ve harita ölçeğine uyuyor.
- [ ] Aynı profil/parametreler deterministik görünüm üretiyor.
- [ ] Oyuncu, NPC ve kaynaklar görünür ve mevcut davranışlarını koruyor.

## Zemin, anchor ve derinlik
- [ ] Ağaç zemine doğru oturuyor.
- [ ] Oyuncu ağacın arkasındayken ağaç önde çiziliyor.
- [ ] Oyuncu ağacın önündeyken oyuncu önde çiziliyor.
- [ ] Kaya ve çalı doğru ground/depth anchor ile sıralanıyor.
- [ ] Kamera pan/zoom hizalama ve sıralamayı bozmuyor.
- [ ] Viewport içinde kalan görsel bölüm aniden kaybolmuyor.

## Çarpışma ayrımı
- [ ] Ağaç gövdesi engelliyor; taç/yaprak alanı tek başına engel oluşturmuyor.
- [ ] Kaya engelliyor; çalı içinden geçilebiliyor.
- [ ] Görsel parametre/çizim çözünürlüğü collider geometrisini değiştirmiyor.
- [ ] Kamera zoom çarpışmayı değiştirmiyor.

## Debug ve regresyon
- [ ] F3 collider geometrilerini açıp kapatıyor.
- [ ] F4 ground/depth anchor, visual/canopy bounds, ID ve dünya konumunu gösteriyor.
- [ ] F3 ve F4 bağımsız çalışıyor.
- [ ] Oyuncu hareketi ve hex sınır davranışı korunuyor.
- [ ] NPC/kaynak hareket etmiyor; FOLLOW/WAIT/RETURN yalnızca komut niyeti.
- [ ] Sağ tık NPC menüsü ve Esc davranışı korunuyor.

Aşama 12 manuel kabulü kullanıcı tarafından başarılı olarak bildirildi. Son ağaç/kaya collider hizalaması F3 görünümünde ayrıca kontrol edildi; görsel ve çarpışma alanlarının bütünleşik olduğu onaylandı. Otomatik testler ve Linux/Windows CI da başarılıdır. Aşama 12 resmen kapatılmıştır.
