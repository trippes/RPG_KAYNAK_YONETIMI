# Aşama 17 — İzometrik Ana Oyun Ekranı: Yeniden Temellendirme ve Görsel Dikey Dilim

**Belge türü:** Genel plan taslağı  
**Tarih:** 20 Kasım 2026  
**Çalışma dalı:** `experiment/hex-world-laboratory`  
**Durum:** KULLANICI ONAYI BEKLİYOR — uygulama başlamadı  
**Ürün hedefi:** Karakter yaratma ekranından sonra açılan ana oyun ekranında klasik izometrik aksiyon/RPG dünyası hissini yakalamak.

## 1. Ürün kararı ve başarı tanımı

Eldoria'nın ana oyun ekranı, karakter yaratma tamamlandıktan sonra oyuncuyu düz bir hex ızgarasına veya debug/laboratuvar sahnesine değil; Diablo ve Baldur's Gate gibi izometrik RPG'lerin okunabilir, derinlikli ve yaşayan dünya sunumuna yakın bir oyun sahnesine sokmalıdır.

Referans oyunlar görsel kalite, kamera, dünya okunabilirliği ve etkileşim deneyimi için referanstır. Eldoria kendi sanat yönetimini, varlıklarını ve arayüz kimliğini oluşturacaktır; mevcut oyunların görsel varlıkları kopyalanmayacaktır.

**Başarı, yalnızca izometrik bir ekran görüntüsü üretmek değildir.** Oyuncu karakteri, NPC'ler, arazi, ağaçlar, kayalar, yapılar, gölgeler ve etkileşimler aynı dünya koordinatları ve kamera projeksiyonu içinde çalışmalı; oyuncu bu sahnede hareket edebilmeli ve dünya ile etkileşebilmelidir.

## 2. İncelemeyle doğrulanan mevcut durum

Laboratuvarın önceki aşamaları değerli ve korunacak altyapılar üretmiştir:

- Axial hex topolojisi, sürekli WorldPoint koordinatları ve dünya/ekran dönüşümleri.
- Kamera takibi, zoom, viewport ve fareyle hücre seçimi.
- Immutable render snapshot, görünür alan culling, sprite foot-anchor ve Y-sort.
- Daire/çokgen collider, sürekli hareket/çarpışma, statik engeller ve spatial index.
- Entity kayıt/lifecycle, etkileşim hedefleme ve yoldaş komut verisi.
- Prosedürel ağaç/kaya/çalı/çim/çiçek üretimi.
- Vector VisualDocument, content definition/library ve map placement veri altyapısı.
- Test, benchmark, uzun süreli simülasyon ve Linux/Windows CI altyapısı.

Ancak bu altyapı **izometrik ana oyun görünümünün tamamlandığı anlamına gelmez**. Kaynak incelemesinde laboratuvarın `WorldScreenTransform` sınıfı dünya X/Y koordinatlarını doğrudan ekran X/Y'ye ölçekleyip Y eksenini ters çeviriyor. `PygameWorldRenderer` hex hücrelerini ve dünya öğelerini bu düzlemsel dönüşümle çiziyor. Bu, kamera ve dünya/ekran dönüşümüdür; izometrik/dimetric projeksiyon değildir.

Ana oyunun `WorldTransform` sınıfı da axial koordinatı mevcut hex geometri fonksiyonuyla world-pixel'e, oradan kamera/zoom ile ekrana taşır. `MainScreen` ise içerik tanımlı tile/landmark görünümü ve HexWorldView etrafında kuruludur. Dolayısıyla ana oyunun karakter yaratma sonrası ekranı için gereken izometrik sunum katmanı henüz kanıtlanmış değildir.

Ayrıca aşağıdaki alanlar görsel dikey dilimde birlikte doğrulanmalıdır:
- Gerçek zemin/terrain görünümü ve zemin yüksekliği/elevation gösterimi.
- Karakter ve NPC için nihai sprite/animasyon yönleri.
- Çevre nesnelerinin görsel boyutu ile fiziksel ayak izi ayrımı.
- Ağaç tacı, yapı ve karakterler arasında doğru ön/arka örtüşme.
- Işık, gölge ve atmosfer derinliği.
- Ekrandan dünya koordinatına ve oradan hex/varlık hedeflemesine doğru picking.
- Oyun içi hareket ve çarpışmanın izometrik projeksiyondan bağımsız kalması.
- Bu sahnenin karakter yaratma akışından gerçek ana oyun ekranı olarak açılması.

Bu maddeler ilk teknik denetimde dosya ve test düzeyinde yeniden doğrulanacaktır; henüz uygulanmış kabul edilmez.

## 3. Değişmez mimari kararlar

1. **Hex dünya topolojisi korunur.** İzometrik görünüm, hex dünya modelini kare ızgaraya dönüştürmek veya kaldırmak için gerekçe değildir.
2. **Sunum projeksiyonu ayrı katmandır.** Axial/WorldPoint simülasyon koordinatları ile izometrik ScreenPoint dönüşümü birbirinden ayrılır.
3. **Tek authoritative world position.** Oyuncu/NPC için kamera, render veya projeksiyon ikinci bir konum kaynağı yaratamaz.
4. **Fizik projeksiyondan bağımsızdır.** Collider, hareket ve çarpışma dünya uzayında kalır; izometrik çizim yalnızca bunları sunar.
5. **Foot-anchor ve depth ordering korunur ve genişletilir.** Sıralama yalnızca sprite dikdörtgeninin üst/alt sınırına göre değil, ground-contact anchor ve gerektiğinde elevation/layer ile belirlenir.
6. **Görsel örtüşme açıkça modellenir.** Ağaç tacı/kanopi, gövde, yapı ve karakter çizim ilişkileri tek bir sıralama kuralıyla çözülemezse kontrollü foreground/background pass veya occlusion mask yaklaşımı tasarlanır.
7. **Laboratuvar kazanımları kaybedilmez.** Mevcut fizik, entity, spatial, culling, procedural art ve content modelleri yeniden yazılmadan önce uyumluluk ve kayıp analizi yapılır.
8. **Pygame korunur.** Motor değişikliği ancak ölçülmüş teknik yetersizlik ve kullanıcı onayıyla gündeme gelir.
9. **Ana oyun entegrasyonu erken yapılmaz.** Önce laboratuvarda görsel dikey dilim kabul edilir; ardından ana oyun adaptör/entegrasyon planı hazırlanır.
10. **Her aşama görsel kabul içerir.** Testlerin geçmesi tek başına görsel kabul değildir.

## 4. İzometrik projeksiyon için araştırılacak seçenekler

Teknik plan öncesinde en az iki kamera/projeksiyon alternatifi karşılaştırılacaktır:

- **2:1 dimetric:** Klasik izometrik RPG okunabilirliğine yakın, yatay/dikey eksenler farklı ölçeklenir; sanat üretimi ve tile hizalaması açısından pratik bir adaydır.
- **True isometric / 30° axonometric:** Eksenler eşit ölçekli izdüşürülür; matematiksel olarak tutarlı ancak asset ölçüleri ve ekran alanı bakımından farklı sonuç verir.

Karar yalnızca matematiksel estetiğe göre verilmeyecek. Mevcut hex layout, hareket yönleri, zemin alanı, karakter silueti, ağaç örtüşmesi, zoom, picking ve düşük donanım performansı birlikte değerlendirilecektir.

İlk prototipte dünya uzayı ile ekran uzayı arasında açık bir projection adapter bulunmalıdır. Gerekirse world elevation (Z) ayrı koordinat olarak modellenir; Z, X/Y dünya konumuna gizlice eklenmez.

## 5. Yeni yol haritası

Bu aşama, aşağıdaki yeni görsel/oynanış yol haritasının ilk dikey dilimidir. Alt aşamalar ayrı teknik plan ve onayla yürütülür.

### 17.1 — Görsel hedef ve referans sahne
- Ana oyun ekranı için görsel kabul panosu ve ekran kompozisyonu.
- Kamera açısı, tile/zemin oranı, karakter ölçeği ve çevre yoğunluğu.
- Mevcut laboratuvar ve ana oyun render akışının dosya bazlı denetimi.
- Placeholder ile nihai sanat gereksinimlerinin ayrılması.

### 17.2 — İzometrik/dimetric projeksiyon ve kamera
- Projection contract ve world/elevation/screen dönüşümleri.
- Kamera follow, pan, zoom, viewport ve bounds.
- Mouse picking: screen → projected world → world point → hex/entity.
- Property tests ve görsel eksen/ızgara kalibrasyon sahneleri.

### 17.3 — Zemin, terrain ve yükseklik
- İzometrik zemin yüzeyleri ve terrain materyal sistemi.
- Hücre sınırlarının varsayılan oyuncu görünümünde debug çizgisi olarak kalmaması.
- Arazi geçişleri, kıyılar/yollar ve gerekiyorsa elevation/kenar yüzleri.
- Zemin gölgeleri ve yürünebilir alanların görsel okunabilirliği.

### 17.4 — Çevresel nesneler ve mimari
- Ağaç, kaya, çalı, bitki, yapı, duvar, kapı ve dekor profilleri.
- Ground anchor, fiziksel footprint ve canopy/visual bounds ayrımı.
- Ön/arka katmanlar ve foreground occlusion.
- Prosedürel üretim ile vector content altyapısının görsel kalite hedefiyle değerlendirilmesi.

### 17.5 — Karakterler, NPC'ler ve animasyon
- Oyuncu ve NPC sprite/rig standardı.
- En az sekiz yönlü veya seçilen kamera açısına uygun yön seti.
- Idle, walk ve interaction animasyonları için veri sözleşmesi.
- Foot-anchor, gölge ve depth sorting.
- NPC görünürlüğü ve çevreyle örtüşme testleri.

### 17.6 — Işık, gölge ve atmosfer
- Tutarlı ışık yönü ve ambient renk yaklaşımı.
- Karakter/nesne yer temas gölgeleri.
- Ağaç/çatı örtüşmesi ve çevresel atmosfer.
- Pygame performans bütçesine uygun katmanlı render.

### 17.7 — Oynanışın izometrik dünyaya bağlanması
- Mevcut continuous movement, physics, collision ve spatial query sistemlerinin projeksiyonla bağlantısı.
- Click-to-move veya mevcut hareket kontrolünün picking ile uyumu.
- NPC konumları, etkileşim menzili, hedef seçimi ve yoldaş komutları.
- Render snapshot ile simulation state ayrımının korunması.

### 17.8 — Ana oyun ekranı dikey dilimi
- Karakter yaratma akışından doğrudan izometrik ana oyun sahnesine geçiş.
- Oyuncu, en az iki NPC, çevre nesneleri, zemin, kamera, hareket ve etkileşim.
- Mevcut inventory/character/quest pencerelerinin dünya sahnesini kapatmayan overlay/window yaklaşımıyla çalışması.
- Save/load ve content package akışının yeni sahneyle uyumu.
- Tek başlatıcı ve gerçek ana oyun giriş akışında smoke test.

### 17.9 — Performans, görsel kabul ve entegrasyon kararı
- Temsilî küçük/orta/büyük sahne benchmarkları.
- Culling, cache, draw-call ve bellek ölçümleri.
- Linux/Windows CI ve temiz kurulum.
- Kullanıcı masaüstü görsel kabulü.
- Ana oyun entegrasyonu için özellik koruma matrisi ve rollback planı.

## 6. Görsel kabul ölçütleri

Aşama 17 tamamlanmış sayılabilmesi için tek bir bütünleşik oynanabilir sahne üzerinde aşağıdaki maddeler doğrulanmalıdır:

- [ ] Kamera üstten düz plan görünümü değil, açıkça izometrik/dimetric dünya sunuyor.
- [ ] Zemin hücreleri perspektif/projeksiyonla tutarlı ve kesintisiz bir dünya yüzeyi oluşturuyor.
- [ ] Varsayılan oyuncu görünümünde debug hex çizgileri/koordinat etiketleri kapalı.
- [ ] Oyuncu karakteri placeholder daire değil, ayak ankrajı doğru bir karakter görseliyle temsil ediliyor.
- [ ] En az iki NPC sahnede görünür; oyuncu ve çevre nesneleriyle doğru derinlikte çizilir.
- [ ] Ağaç, kaya ve yapıların görsel alanı ile fiziksel collider alanı uyumlu.
- [ ] Karakter, ağaç gövdesi/kanopi ve yapıların önünden/arkasından geçerken doğru örtüşme oluşur.
- [ ] Kamera takip, pan ve zoom sırasında görüntü titremez; picking doğru hedefi seçer.
- [ ] Hareket ve çarpışma projeksiyon değişiminden etkilenmez.
- [ ] Sahne gerçek oyun akışında karakter yaratma sonrasında açılır.
- [ ] Etkileşim ve temel UI pencereleri dünya sahnesini kaybettirmez.
- [ ] Test, CI, görsel artifact ve kullanıcı manuel kabulü başarılıdır.

## 7. Kapsam dışı ve koruma

- Bu plan Godot geçişi veya yeni motor seçimi değildir.
- Bu plan ana oyun branch'ine doğrudan kod taşıma izni vermez.
- Önceki laboratuvar aşamalarının kaynak kodu, testleri, benchmarkları ve raporları silinmez.
- Aşama 16'nın eski toplu entegrasyon taslağı yeni hedefin ana planı olarak kullanılmaz; yalnızca tarihsel karar kaydı olarak saklanır.
- Savaş, görev, ekonomi ve diyalog sistemlerinin yeniden yazılması bu dikey dilimin kapsamı değildir.
- İzometrik görsel hedefi sağlanmadan yalnızca pencere/menü entegrasyonu aşama başarısı sayılmaz.

## 8. Çalışma sırası ve onay kapıları

1. Kullanıcı bu genel planı onaylar veya kapsamı düzeltir.
2. Aşama 17.1 için gerçek dosya envanteri, görsel referans ve açık teknik karar raporu hazırlanır.
3. Kullanıcı 17.1 teknik planını onaylar.
4. İlk izometrik projection prototype laboratuvar dalında uygulanır.
5. Her alt aşamada test + screenshot artifact + kullanıcı görsel kabulü alınır.
6. Dikey dilim kabul edilmeden ana oyun entegrasyonuna geçilmez.

**Mevcut karar:** Bu belge yalnızca genel plan taslağıdır. Kod değişikliği, entegrasyon, merge veya önceki laboratuvar kodunun silinmesi için yetki vermez.
