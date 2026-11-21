# Eldoria — Aşama 3.5 Hedefe Yaklaşma ve Durma Teknik Değerlendirmesi

- **Dal:** `experiment/map-cleanup`
- **İncelenen route commit'i:** `62bc84b7ad41ba5ec0e4492f0591018990e66e60`
- **Tarih:** 21 Kasım 2026
- **Durum:** Teknik bağımlılık nedeniyle ertelendi; güvenli durma garantisi verilmedi.

---

## 1. Mevcut davranış

`ClickMoveRouteController`, oyuncu authoritative runtime hücresi hedef hücre olduğunda hedef hücrenin merkezini waypoint olarak kullanır. Oyuncu ile hedef merkezi arasındaki mesafe `ARRIVAL_TOLERANCE = 0.5` dünya birimine indiğinde route tamamlanır ve idle intent döndürülür.

Bu, oyuncunun hedef hücreye ulaşmasını ve hedef merkezine yakın bir noktada komutun sonlandırılmasını sağlar. Ancak tek başına yüksek hızda hedefi aşmama veya hedef çevresinde salınımı önleme garantisi değildir.

## 2. Teknik bağımlılık

`core/domain/movement/integrator.py` içindeki `MovementIntegrator.step()` incelendi:

- Hız doğrudan `MovementConfig.max_speed * speed_multiplier_for(mode)` olarak hesaplanır.
- Hareketli intent için velocity her adımda `intent.direction.normalized() * speed` olarak yeniden üretilir.
- Önceki `MovementState.velocity` yeni hızı belirlemek için kullanılmaz.
- İvmelenme, frenleme, hedefe kalan mesafeye göre hız sınırlama veya hedefe özel stopping distance desteği bulunmaz.

`ContinuousPlayerMovementController.step()` yalnızca MovementIntent ve fixed delta üzerinden çalışır; hedefe kalan mesafeyi integrator'a aktaracak bir target-aware stopping sözleşmesi yoktur.

Bu nedenle 0.5 birimlik arrival toleransı, fixed-step hareketin bir adımda bu toleransın üzerinden geçmesi halinde oyuncunun hedef merkezinin diğer tarafına geçmesini engelleyemez. Sonraki adımda yön tersine dönerse salınım oluşabilir.

## 3. Alınan karar

Bu alt aşamada:
- Yeni ivmelenme/frenleme fiziği uydurulmadı.
- MovementIntegrator'ın davranışı değiştirilmedi.
- Hareket config'inin max_speed değeri geçici ve örtük biçimde değiştirilmedi.
- Hedefe ulaşıldığına dair yanlış bir garanti verilmedi.

Bu karar Aşama 3 talimatındaki “MovementIntegrator desteklemiyorsa varmış gibi kabul etme; bağımlılığı raporla ve ertele” şartına uygundur.

## 4. Tamamlanması için gereken bağımlılık

Aşağıdaki iki tasarımdan biri ayrı teknik sözleşme ve regresyon testleriyle ele alınmalıdır:

1. **Target-aware displacement cap:** Fixed step displacement, hedefe kalan mesafeyi aşamayacak şekilde ortak hareket controller'ında sınırlandırılır. Statik collision, dinamik aktör çarpışması ve runtime commit sırası korunmalıdır.
2. **Acceleration/braking model:** MovementState velocity geçmişi kullanılarak ivmelenme/frenleme uygulanır; NORMAL/RUNNING/STEALTH modları ve NPC hareketi üzerindeki etkileri ayrı değerlendirilir.

Her iki seçenek de yalnızca click-to-move için değil, ortak integrator kullanan klavye hareketi ve muhtemel diğer aktörler için davranış değişikliği oluşturabilir. Bu nedenle Aşama 3 kapsamı içinde sessizce eklenmemelidir.

## 5. Kabul değerlendirmesi

| Kriter | Durum |
|---|---|
| Hedef hücreye ulaşma | Tamamlandı |
| Hedef merkezine 0.5 dünya birimi toleransında komut bitirme | Tamamlandı |
| Hedefi yüksek hızda aşmama garantisi | Ertelendi |
| Hedef çevresinde salınımı kesin önleme | Ertelendi |
| Acceleration/braking veya target-aware stopping | Mevcut mimaride yok |
| Mevcut 60 Hz fixed-step ve collision sözleşmesini koruma | Korundu |

**Sonuç:** Aşama 3.5 güvenli biçimde tamamlanmış sayılmıyor; teknik bağımlılık olarak ertelendi. Eldoria'nın mevcut hareket fiziğiyle yalnızca 0.5 birim toleranslı varış davranışı sağlanabiliyor. Hedefe yaklaşma hızının düşürülmesi ve kesin durma garantisi, ayrı bir movement-physics kararı gerektiriyor.
