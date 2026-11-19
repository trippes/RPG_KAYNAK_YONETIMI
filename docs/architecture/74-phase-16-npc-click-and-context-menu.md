# Aşama 16 — NPC tıklama etkileşimi ve boş aksiyon menüsü

## Kapsam

Bu değişiklik yalnızca `experiment/map-cleanup` dalında yapılmıştır. Lab kaynak dalı, `main` ve `demo_eldoria` değiştirilmemiştir.

## Uygulanan davranış

- NPC seçimi, HexWorldRuntime içindeki canonical NPC entity ID'si ve mevcut axial konumu üzerinden yapılır. Yeni NPC kimliği veya ikinci bir konum kaydı oluşturulmaz.
- Sol tık, harita panelinde tıklanan axial hücrede bulunan NPC'yi seçer ve mevcut GameWindow → DialogueScreen yönlendirmesini tetikler.
- Sağ tık, aynı NPC için boş bir bağlamsal aksiyon menüsü kabuğu açar. Menü yalnızca NPC kimliğini ve başlığını gösterir; herhangi bir eylem tanımlamaz veya çalıştırmaz.
- Sağ tık boş hücrede kullanılırsa açık NPC menüsü kapanır.
- NPC'ye tıklama, click-to-move hedefi oluşturmaz; sağ tık da oyuncuyu hareket ettirmez.
- Menü eylemleri daha sonra NPC'nin türü, rolü ve içerik tanımlarına göre eklenecektir.

## Bilinçli olarak kapsam dışında bırakılanlar

- Diyalog erişim/mesafe kuralı.
- NPC'ye otomatik yaklaşma veya mesafe dışı diyalog davranışı.
- Sağ tık menüsü eylemleri, eylem sağlayıcı/registry sistemi ve NPC rolüne göre eylem filtreleme.
- Kaynak düğümü seçimi, toplama menüsü, toplama miktarı ve etkileşim mesafesi.
- Fizik gövdesi/collider tanımı ve fizik doğrulamasının normal hareket akışına bağlanması.

Bu kararlar için mevcut oyun tasarımında yeterli sözleşme bulunmadığından varsayım üretilmemiştir.

## Test kapsamı

Hex gameplay view testlerine şu kontroller eklenmiştir:
- Sol tıkla NPC seçimi ve diyalog yönlendirme sonucu.
- Sağ tıkla eylemsiz bağlamsal menü açılması.
- Sağ tıkla boş hücrede menünün kapanması.
- NPC tıklamasında click-to-move komutu üretilmemesi.

Bu rapor kod değişikliğinin kapsamını kaydeder; CI sonucu ayrıca doğrulanmalıdır.
