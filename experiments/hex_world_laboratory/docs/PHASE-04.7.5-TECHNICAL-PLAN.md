# Aşama 4.7.5 — Teşhis Paneli Teknik Planı

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Ön koşul:** Aşama 4.7.4 kodu ve GitHub CI doğrulamaları başarılıdır.  
> **Durum:** KULLANICI ONAYI BEKLİYOR — bu belge kod uygulama izni değildir.

## 1. Amaç

Mevcut Pygame hareket demosunun salt okunur teşhis paneline seçili hareket modunu, hız çarpanını ve o mod için teorik hızı eklemek; gerçek anlık hız bilgisini ayrı tutmak. Panel, simülasyon davranışını değiştirmeden operatörün Normal/Koşma/Gizlilik geçişlerini gözlemlemesini sağlayacaktır.

## 2. Mevcut durum

`application/movement_demo.py` içinde `MovementDemo`, `MovementConfig(max_speed=movement_speed)` nesnesini doğrudan `MovementSystem` oluştururken veriyor. `_draw_diagnostics()` şu bilgileri gösteriyor: dünya, harita, konum, gerçek velocity, hücre, son tick, render FPS, kare başına tick ve bekleyen tick/zaman borcu.

`MovementState.mode` son işlenmiş tick'in modunu taşır. `MovementConfig.speed_multiplier_for(mode)` etkin mod çarpanını verir. Demo temel hızı `AppConfig.movement_speed` üzerinden yapılandırılabilir; varsayılanı 60 dünya birimi/saniyedir.

## 3. Kapsam

1. Demo'nun kullandığı `MovementConfig` tek ve tutarlı bir referans olarak tutulacak.
2. Teşhis paneline aşağıdaki bilgileri ekle:
   - `Mode`: `NORMAL`, `RUNNING` veya `STEALTH`.
   - `Multiplier`: ilgili mod çarpanı, iki ondalık basamakla.
   - `Mode speed`: temel hız × mod çarpanı, bir ondalık basamakla ve dünya birimi/saniye anlamında.
3. Mevcut `Velocity` satırı gerçek anlık hız vektörünü ve büyüklüğünü göstermeye devam edecek. Aktör dururken teorik mod hızı gerçek hareket hızıymış gibi sunulmayacak.
4. Mod bilgisi yalnızca son işlenmiş `MovementState` snapshot'ından okunacak.
5. `render()` ve teşhis çizimi salt okunur kalacak; tick, movement state, cell tracker veya input üzerinde değişiklik yapmayacak.
6. `MANUAL-MOVEMENT-DEMO-CHECKLIST.md` içine mod/hız paneli ve tuş davranışları için manuel kontrol maddeleri eklenecek.

## 4. Dosya sınırları

### Güncellenecek
- `src/hex_world_lab/application/movement_demo.py`
- `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md`
- İlgili render/diagnostics test dosyaları (mevcut test yerleşimine göre).

### Yeni dosya
- Bu teknik plan belgesi.

Başka üretim modülü, movement çekirdeği, klavye adaptörü, tick pump, dünya/geometri/persistence kodu değiştirilmeyecek. Gerekmedikçe yeni bağımlılık eklenmeyecek.

## 5. Tasarım ve davranış

### 5.1 Tek config kaynağı

`MovementDemo` oluşturulurken bir `MovementConfig` üretilecek ve aynı nesne hem `MovementSystem` kurulumunda hem teşhis hesaplamasında kullanılacak. Temel hız veya çarpanlar için ikinci, kopya bir sabit tanımlanmayacak.

### 5.2 Teşhis satırları

Önerilen gösterim:

- `Mode: NORMAL | multiplier: 1.00x | mode speed: 60.0`
- `Mode: RUNNING | multiplier: 1.50x | mode speed: 90.0`
- `Mode: STEALTH | multiplier: 0.50x | mode speed: 30.0`

Bu sayılar yalnızca temel hız 60 olduğunda örnektir. Farklı `movement_speed` konfigürasyonlarında değerler config üzerinden hesaplanmalıdır.

### 5.3 Panel yerleşimi

Mevcut panelin satır tabanlı çizimi korunacak. Yeni mod satırı panel yüksekliğine dahil edilecek; dar pencere genişliğinde satırın panel dışına taşmaması için mevcut genişlik/ölçü yaklaşımı gözden geçirilecek. Bu alt aşama kapsamına genel UI ölçekleme veya yeni panel tasarımı girmez.

### 5.4 Salt okunurluk

Teşhis hesapları yalnızca `state` ve config değerlerini okur. Render çağrısı simülasyon ilerletmez. Var olan render immutability testleri korunup mod değişimi ve render tekrarlarıyla güçlendirilecek.

## 6. Test ve kabul ölçütleri

1. Normal, Koşma ve Gizlilik modlarında panelin doğru mod adını gösterdiği doğrulanır.
2. Varsayılan 60 hızda teorik hızlar sırasıyla 60.0, 90.0 ve 30.0 olarak gösterilir.
3. Farklı temel hızda (ör. 40) değerler 40.0, 60.0 ve 20.0 olarak hesaplanır; sabit 60 varsayımı bulunmaz.
4. Aktör dururken seçili mod ve teorik mod hızı görünür; gerçek velocity/speed sıfır kalır.
5. Gerçek hareket sırasında Velocity satırı gerçek hız vektörünü göstermeyi sürdürür.
6. `render()` çağrıları state, tick sayısı, hücre çözümlemesi ve hareket konumunu değiştirmez.
7. Var olan uygulama yaşam döngüsü, hücre çizimi ve hareket modu entegrasyon testleri regresyona uğramaz.
8. Tam laboratuvar pytest, Lab CI ve Core Quality Linux/Windows başarılı olur.
9. Gerçek Pygame penceresinde kullanıcı manuel kontrol listesindeki mod ve teşhis satırı maddelerini doğrular; headless CI masaüstü kabulünün yerine geçmez.

## 7. Manuel kontrol listesi ekleri

- Normal modda panel `NORMAL / 1.00x` gösterir.
- Sol veya sağ Shift ile `RUNNING / 1.50x` gösterir.
- Shift bırakıldığında Normal'e döner.
- Sol veya sağ Alt ile `STEALTH / 0.50x` gösterir.
- Shift + Alt birlikteyken Gizlilik görünür.
- Hareket tuşları bırakıldığında Velocity sıfır olurken seçili mod satırı doğru kalır.
- Temel hız yapılandırması değiştiğinde Mode speed doğru orantılı değişir.
- Pencere odağı kaybında mod Normal ve yön/hız sıfır olur.
- Pencereyi kapatmak uygulamayı mevcut şekilde sonlandırır.

## 8. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Teorik mod hızı gerçek hızla karıştırılır | Mode speed ve Velocity ayrı satırlar olarak korunur |
| Temel hız iki yerde tanımlanır | Aynı MovementConfig nesnesi kullanılır |
| Render simülasyonu değiştirir | Sadece snapshot/config okuma; render immutability testi |
| Yeni satır panelden taşar | Panel yüksekliği satır sayısına göre hesaplanır; manuel pencere kontrolü |
| Sabit 60 hızı yanlış gösterilir | Farklı temel hızla test |

## 9. Kapsam dışı

- NPC algısı, gizlenme/ görünmezlik veya ses sistemi.
- Stamina, animasyon, hızlanma/yavaşlama.
- Genel UI tasarım sistemi, dinamik ölçekleme veya pencere sistemi.
- Yeni grafik/telemetri kütüphanesi.
- Ana Eldoria oyununa entegrasyon.
- `main` veya `demo_eldoria` dalında değişiklik.

## 10. Uygulama kapısı

Bu belge kullanıcı onayına sunulur. Açık onay gelmeden kod veya manuel kontrol listesi değiştirilmez. Onay sonrası yalnızca bu kapsam uygulanır; hedefli testler, tam pytest ve GitHub CI çalıştırılır. Masaüstü manuel kabul kullanıcı tarafından gerçek pencerede yapılır. Tüm yazmalar yalnızca `experiment/hex-world-laboratory` dalına yapılır.
