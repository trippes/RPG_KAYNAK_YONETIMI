# ELDORIA RPG — SERBEST HAREKET SİSTEMİ
## Teknik Mimari Planı ve Geçiş Şeması

**Proje:** Eldoria RPG — Kaynak Yönetimi Oyunu  
**Depo:** trippes/RPG_KAYNAK_YONETIMI  
**Tarih:** 14 Kasım 2026  
**Durum:** Planlandı — uygulama öncesi teknik referans

---

# 1. KARAR ÖZETİ

Eldoria'da oyuncu hareketi tamamen serbest olacaktır.

Bu karar, dünya simülasyonunun hücre veya altıgen tabanlı yapısının kaldırılması anlamına gelmez. Temel mimari prensip:

> Dünya mantıksal hücrelerden oluşabilir; oyuncu bu dünyanın üzerinde fiziksel olarak serbest hareket eder.

Yeni mimari iki konum katmanını ayırır:

MANTIKSAL DÜNYA → Altıgenler, bölgeler, biyomlar ve kaynaklar  
↓  
KOORDİNAT DÖNÜŞÜM KATMANI  
↓  
FİZİKSEL YEREL DÜNYA → Float X/Y, çarpışma, serbest hareket ve kamera

---

# 2. MEVCUT DURUM TEKNİK DENETİMİ

## 2.1 Yerel hareket modeli

Teknik denetimde oynanabilir yerel harita katmanının `game_ui/screens/local_map_screen.py` çevresinde çalıştığı tespit edilmiştir.

Mevcut model:

- 32×32 kare tile haritası kullanır.
- Oyuncu konumunu tam sayı tile koordinatlarıyla temsil eder.
- Klavye hareketi adım/adım gerçekleşir.
- Fare hedefleri kare tabanlı yol bulma ile işlenir.
- Engeller tile seviyesinde değerlendirilir.
- Hareket ile oyun zamanının ilerlemesi birbirine bağlıdır.

Bu model dünya simülasyonu için uygun olsa da gerçek zamanlı RPG keşfi için oyuncu kontrolünü gereksiz biçimde sınırlar.

## 2.2 Dünya ve yerel harita ayrımı

GENİŞ DÜNYA → mantıksal konumlar ve dünya grafiği  
↓  
YEREL HARİTA → kare tile tabanlı oynanabilir yüzey  
↓  
OYUNCU → tile'dan tile'a hareket

Dönüşümün hedefi dünya mimarisini yeniden yazmak değildir. Ana hedef yerel oynanabilir yüzeydeki oyuncu kontrolünü fiziksel koordinat tabanlı hale getirmektir.

## 2.3 Uygulama katmanındaki hareket sistemi

`application/movement.py` içindeki MovementManager mantıksal dünya hareketi için tasarlanmıştır.

**Mimari karar:** MovementManager frame-by-frame oyuncu hareket motoruna dönüştürülmeyecektir. Dünya seviyesi mantıksal hareket sorumluluğunu koruyacaktır.

## 2.4 Actor ve kayıt altyapısı

Konum bilgisi actor ve persistence altyapısında taşınmaktadır.

**Koruyucu ilke:** Serbest hareket için mevcut ortak konum türü aceleyle değiştirilmemeli; fiziksel konum için ayrı bir model veya adaptör değerlendirilmelidir.

---

# 3. HEDEF MİMARİ

INPUT LAYER  
WASD + sürekli tuş durumu  
↓  
FREE MOVEMENT SYSTEM  
Yön + hız + delta time  
↓  
COLLISION SYSTEM  
Engeller + su + sınırlar + çözümleme  
↓  
PHYSICAL POSITION  
Float X/Y  
↙                    ↘  
CAMERA / VIEW        WORLD ADAPTER  
Takip / render       Hücre / biyom / kaynak

| Katman | Sorumluluk |
|---|---|
| Input | Basılı yön tuşlarını belirler |
| Movement | Hız ve delta time ile hedef konumu hesaplar |
| Collision | Fiziksel hareketin geçerliliğini çözer |
| Position | Gerçek dünya koordinatını taşır |
| World Adapter | Fiziksel konumu mantıksal dünya verisiyle ilişkilendirir |
| Camera | Dünya koordinatını ekran koordinatına dönüştürür |
| Renderer | Nesneleri doğru çizim sırasıyla ekrana çizer |

---

# 4. YENİ KONUM MODELİ

Yerel oynanabilir dünyada konum ondalıklı koordinat kullanmalıdır.

Örnek:

WorldPosition
- x = 421.75
- y = 286.40

Bu konum bir hücre merkezine bağlı değildir ve her frame küçük miktarlarda değişebilir.

Dünya simülasyonu gerektiğinde fiziksel konumu mantıksal konuma dönüştürür:

Fiziksel konum (421.75, 286.40)  
↓  
Yerel alan / hücre dönüşümü  
↓  
Mantıksal konum: Hex(q, r) veya ilgili dünya konumu

---

# 5. SERBEST HAREKET ALGORİTMASI

Her frame:

1. Basılı tuşları oku.
2. Yön vektörünü oluştur.
3. Vektörü normalize et.
4. Hız × delta time hesapla.
5. Çarpışmayı çöz.
6. Geçerli yeni konumu uygula.

Temel ilke:

`direction = normalize(x, y)`  
`displacement = direction × speed × delta_time`

Hareket frame sayısına değil geçen zamana bağlı olmalıdır.

---

# 6. ÇARPIŞMA MİMARİSİ

Eski soru:

> Bu tile'a girebilir miyim?

Yeni soru:

> Oyuncunun fiziksel gövdesi bu engelle kesişiyor mu?

İlk sürüm çarpışma şekilleri:

- Rect
- Circle
- WorldBoundary

İlk geçişte mevcut engel verileri silinmeyecektir:

Blocked Tile  
↓  
Tile dünya sınırları  
↓  
Collision Rect  
↓  
Collision System

Çarpışma çözümleme:

1. X eksenindeki hareketi dene.
2. Çarpışma varsa X hareketini sınırlandır.
3. Y eksenindeki hareketi dene.
4. Çarpışma varsa Y hareketini sınırlandır.
5. Geçerli son konumu uygula.

---

# 7. KAMERA VE RENDER

`game_ui/camera.py` serbest keşif için genişletilecektir.

Oyuncu dünya konumu  
↓  
Kamera hedefi  
↓  
Kamera konumu  
↓  
world_to_screen()  
↓  
Ekran çizimi

İlk sürüm hedefleri:

- Kamera oyuncuyu takip eder.
- Kamera harita sınırlarının dışına çıkmaz.
- Dünya nesneleri dünya koordinatlarında tutulur.
- Çizimden önce kamera ofseti uygulanır.

Y ekseni çizim sırası:

Nesnenin ayak noktası Y değeri küçük → önce çiz.  
Nesnenin ayak noktası Y değeri büyük → sonra çiz.

---

# 8. DÜNYA SİMÜLASYONU VE ZAMAN

Yeni ilke:

FİZİKSEL HAREKET  
Gerçek zamanlı / frame tabanlı

ayrı

DÜNYA SİMÜLASYONU  
Tick / faaliyet / oyun kuralları

Yürümek her frame canonical simulation tick ilerletmemelidir.

---

# 9. SİSTEM DURUM MATRİSİ

## Korunacak

- Dünya haritası mimarisi
- Mantıksal dünya konumları
- Altıgen/hücresel dünya matematiği
- Kaynak ve ekonomi sistemleri
- NPC ve görev domain sistemleri
- MovementManager'ın dünya seviyesi mantıksal sorumlulukları
- Actor/activity mimarisinin genel yapısı
- Kayıt sisteminin genel yapısı

## Yeniden tasarlanacak

- LocalMapScreen içindeki tile-adım oyuncu hareketi
- Sürekli hareket için input akışı
- Yerel fiziksel çarpışma
- Yerel kamera entegrasyonu
- Hareket ile simülasyon zamanı arasındaki doğrudan bağ

## Uyarlanacak

- Actor'ın oynanabilir yerel konum temsili
- Position persistence
- Kaynaklarla etkileşim mesafesi
- NPC fiziksel konumları
- Harita geçiş bölgeleri
- Yerel harita render akışı

---

# 10. UYGULAMA YOL HARİTASI

## AŞAMA A — SÖZLEŞME VE VERİ MODELİ

Fiziksel konum sözleşmesi, mantıksal/fiziksel konum ayrımı ve persistence stratejisi belirlenecek.

**Başarı kriteri:** Core konum sistemi bozulmadan yerel serbest konum modeli tanımlanmalıdır.

## AŞAMA B — INPUT VE HAREKET ÇEKİRDEĞİ

Sürekli tuş durumu, yön vektörü, normalizasyon ve delta time tabanlı hız uygulanacak.

**Başarı kriteri:** Oyuncu hücre merkezine bağlı olmadan akıcı hareket etmelidir.

## AŞAMA C — ÇARPIŞMA SİSTEMİ

Collision shape sözleşmesi, statik engeller, dünya sınırları ve eksen bazlı çözümleme uygulanacak.

## AŞAMA D — MEVCUT HARİTA ADAPTÖRÜ

Tile → dünya koordinatı ve blocked tile → collision region dönüşümü yapılacak.

## AŞAMA E — KAMERA VE RENDER

Kamera takibi, world-to-screen dönüşümü, harita sınırları ve Y koordinatına göre çizim sırası uygulanacak.

## AŞAMA F — DÜNYA ENTEGRASYONU

Physical → logical position adapter, biyom sorgusu, kaynak etkileşim mesafesi ve harita geçiş bölgeleri uyarlanacak.

## AŞAMA G — PERSISTENCE VE REGRESYON

Başlangıç konumu, hareket sonrası kayıt, yükleme, dünya değişimi ve mevcut sistem regresyonları test edilecek.

---

# 11. TEST STRATEJİSİ

## Birim testleri

- Yön vektörü hesaplama
- Diyagonal normalizasyon
- Delta time hareket mesafesi
- Çarpışma tespiti
- Çarpışma çözümleme
- Koordinat dönüşümü

## Entegrasyon testleri

- Input → Movement → Position
- Movement → Collision
- Position → Camera
- Position → World Adapter
- Save → Load → Position restore

## Manuel test senaryoları

1. Oyuncu uzun süre W tuşuna basılı tutar.
2. Oyuncu dört diyagonal yönde hareket eder.
3. Oyuncu bir engele çapraz yaklaşır.
4. Oyuncu harita sınırına ulaşır.
5. Oyuncu hareket ederken kamera takip edilir.
6. Oyuncu kaydedilir ve oyun yeniden açılır.
7. Kaynak ve etkileşim alanlarına serbestçe yaklaşılır.

---

# 12. RİSKLER VE KORUYUCU İLKELER

- Core Position türü ayrı model veya adaptör değerlendirilmeden değiştirilmemelidir.
- MovementManager dünya seviyesi mantıksal hareket sorumluluğunu korumalıdır.
- Fiziksel render/movement döngüsü ile canonical simulation tick ayrılmalıdır.
- İlk geçişte tile verileri collision ve render adaptörleri aracılığıyla korunmalıdır.
- Aşama A–G sırası korunmalı; her aşama test edilmeden sonraki aşamaya geçilmemelidir.

---

# 13. NİHAİ MİMARİ KARAR

1. Oyuncu tamamen serbest hareket eder.
2. Oyuncu konumu fiziksel dünyada float X/Y ile temsil edilir.
3. WASD sürekli hareket sağlar.
4. Hareket delta time tabanlıdır.
5. Diyagonal hız normalize edilir.
6. Çarpışma fiziksel alanlar üzerinden çözülür.
7. Dünya mantığı fiziksel konumu gerektiğinde hücresel/altıgen konuma dönüştürür.
8. Fiziksel hareket canonical simulation tick'lerinden bağımsızdır.
9. Dünya mimarisi korunur; oynanabilir yerel hareket katmanı dönüştürülür.
10. Geçiş küçük, test edilebilir ve kontrollü aşamalar halinde yapılır.

---

# 14. SONUÇ

Bu belge Eldoria'yı hücreler arasında hareket eden bir prototipten, hücresel dünya mantığı üzerinde özgürce keşif yapılabilen bir RPG'ye dönüştürmek için teknik yol haritasıdır.

Temel hedef:

ALTIGEN / MANTIKSAL DÜNYA  
+  
SERBEST FİZİKSEL HAREKET  
+  
BAĞIMSIZ ÇARPIŞMA VE KAMERA  
=  
ELDORIA'NIN HEDEF KEŞİF MİMARİSİ

Bu belge uygulama aşamasında referans mimari plan olarak kullanılacaktır. Kod değişikliklerine Aşama A kapsamındaki mevcut sınıf ve veri sözleşmelerinin ayrıntılı doğrulamasından sonra başlanmalıdır.
