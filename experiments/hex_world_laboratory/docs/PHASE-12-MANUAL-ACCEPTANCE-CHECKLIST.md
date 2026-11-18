# Aşama 12 — Manuel Görsel ve İşlevsel Kabul Kontrol Listesi

> **Durum:** Otomatik doğrulama tamamlandıktan sonra kullanıcı tarafından uygulanacak.
> **Başlatıcı:** Laboratuvar kök dizininde `python -m hex_world_lab`
> **Debug:** F3 collider görünümü; F4 çevresel nesne anchor/bounds görünümü.

## Sahne ve görsel varlıklar

- [ ] Laboratuvar tek başlatıcıyla hatasız açılır.
- [ ] Ağaç, kaya ve çalı sprite'ları sahnede görünür.
- [ ] Ağaç görseli zemin tabanına doğru oturur; havada veya zeminin altında görünmez.
- [ ] Kaya ve çalı görselleri ağaçla aynı genel render sisteminden çizilir.
- [ ] Oyuncu, NPC'ler ve kaynaklar görünür ve mevcut davranışlarını korur.

## Derinlik sıralaması

- [ ] Oyuncu ağacın arkasından geçtiğinde ağaç oyuncunun önünde çizilir.
- [ ] Oyuncu ağacın önünden geçtiğinde oyuncu ağacın önünde çizilir.
- [ ] Kamera pan/zoom sırasında bu sıralama bozulmaz.
- [ ] Ağaç sprite'ının üst kısmı ekrandan kısmen taşarken görünür bölüm aniden kaybolmaz.

## Çarpışma ayrımı

- [ ] Oyuncu ağacın gövdesine çarpar.
- [ ] Ağacın taç/yaprak alanı tek başına fiziksel engel oluşturmaz.
- [ ] Oyuncu kaya collider'ına çarpar.
- [ ] Oyuncu çalının içinden geçebilir.
- [ ] Kamera zoom seviyesi çarpışma sonucunu değiştirmez.

## Debug görünümü

- [ ] F3 collider geometrilerini açıp kapatır.
- [ ] F3 kapalıyken çevresel nesnelerin daire/çokgen collider'ları normal sahnede görünmez.
- [ ] F4 ground anchor ve depth anchor noktalarını/bağlantısını gösterir.
- [ ] F4 visual bounds ve canopy bounds alanlarını gösterir.
- [ ] F4 nesne kimliğini ve dünya koordinatını gösterir.
- [ ] F4 kapatıldığında yardımcı çizgiler ve etiketler kaybolur.
- [ ] F3 ve F4 birbirinden bağımsız çalışır.

## Regresyon

- [ ] Oyuncu hareketi ve mevcut hex sınır davranışı korunur.
- [ ] NPC ve kaynaklar hareket etmez.
- [ ] Yoldaş FOLLOW/WAIT/RETURN yalnızca komut niyeti olarak kalır.
- [ ] Sağ tık NPC menüsü ve mevcut entity seçimi çalışır.
- [ ] Esc laboratuvarı mevcut davranışıyla kapatır.

**Kabul sonucu:** Bu listenin tüm maddeleri kullanıcı tarafından kontrol edilip geçtiğinde Aşama 12 kapatılabilir.
