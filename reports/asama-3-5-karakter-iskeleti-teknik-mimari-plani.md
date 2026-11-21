# Aşama 3.5 — Karakter İskeleti ve Rig Sistemi Teknik Mimari Planı

**Durum:** Uygulama öncesi teknik sözleşme  
**Kapsam:** Aşama 3.5 karakter görselleştirme iyileştirmesi  
**Hedef dal:** `experiment/map-cleanup`  
**Temel karar:** Mevcut hareket, çarpışma ve dünya konumlandırma sistemleri korunurken prosedürel kare-sprite karakter çiziminden eklem tabanlı karakter rig altyapısına kontrollü geçiş.

---

## 1. Amaç

Mevcut karakter animasyonu sınırlı sayıda önceden çizilmiş sprite karesinin değiştirilmesine dayanıyor. Bu yaklaşım hareket ediyor olsa da uzuvların birbirinden bağımsız ve eklem ilişkileri içinde hareket etmesini yeterince desteklemiyor.

Bu çalışmanın amacı, oyuncu ve NPC'lerin ortak kullanabileceği, eklem hiyerarşisine dayalı, yön ve hareket durumuna göre poz üretebilen bir karakter iskeleti altyapısı kurmaktır.

İlk hedef özelleştirilebilir karakter editörü veya nihai sanat kalitesi değildir. Öncelik; doğru matematiksel iskelet, güvenilir dönüşüm/hiyerarşi, test edilebilir animasyon ve mevcut oyun döngüsüne gerileme oluşturmadan entegrasyondur.

## 2. Tasarım ilkeleri

1. **Tek gerçek konum kaynağı:** Karakterin dünya konumu ve hareket otoritesi mevcut oyun/runtime sisteminde kalır. Rig, fizik veya hareket sistemi değildir.
2. **Sunum katmanı ayrımı:** İskelet modeli Pygame'e bağımlı olmayacak; çizim Pygame renderer katmanında yapılacaktır.
3. **Hiyerarşik dönüşüm:** Bir eklemin dönüşümü üst ekleminden miras alınır. Pozlar yerel uzayda tanımlanır; dünya/ekran koordinatına dönüşüm ayrı yapılır.
4. **Ortak oyuncu/NPC altyapısı:** Oyuncu ve NPC aynı iskelet tanımını ve renderer altyapısını kullanır. Görsel farklılıklar ileride görünüm/skin verisiyle sağlanabilir.
5. **Aşamalı geçiş:** Eski sprite factory ve renderer, yeni rig doğrulanmadan kaldırılmaz.
6. **Deterministik test edilebilirlik:** İskelet geometrisi ve animasyon pozu mümkün olduğunca saf veri/hesaplama olarak test edilir; testler pencere veya gerçek zamanlı oyun döngüsü gerektirmez.
7. **Ölçek ve ayak ankrajı:** Rig yerel, normalize bir koordinat sisteminde tanımlanır. Kamera ölçeği bütün vücuda eşit uygulanır; karakterin dünya konumuna bağlanan referans noktası ayak tabanı/zemin ankrajıdır.
8. **Geleceğe açık görsel parçalar:** Gövde ve uzuv çizimleri, ileride kıyafet, zırh, saç, silah ve aksesuar katmanlarıyla değiştirilebilecek biçimde ayrıştırılır.

## 3. Kapsam

### 3.1 Bu çalışmaya dahil

- İskelet eklemlerinin ve kemik bağlantılarının veri modeli.
- Üst-alt eklem ilişkileri ve yerel dönüşüm hesaplaması.
- Nötr/rest pozunun tanımlanması.
- Sekiz yön için karakterin yöneliminin temsil edilmesi.
- Idle, walk ve run hareket durumları için eklem pozu üretimi.
- Pygame üzerinde eklemli vücut parçalarının çizilmesi.
- Oyuncu ve NPC render akışına kontrollü entegrasyon.
- Birim testleri, renderer testleri ve mevcut hareket/çarpışma regresyon kontrolleri.

### 3.2 Bu çalışmaya dahil değil

- Karakter oluşturma/özelleştirme ekranı.
- Kullanıcı tarafından kıyafet, zırh, saç, ten rengi veya vücut oranı seçimi.
- Ekipmanların görsel olarak karaktere takılması.
- Nihai piksel-art/illüstrasyon üretimi veya profesyonel karakter modelleme.
- Yeni fizik, çarpışma, hitbox, hareket hızı veya NPC itiş sistemi.
- Savaş/hasar animasyonlarının tam seti; yalnızca mimarinin sonraki durumlara genişletilebilir olması hedeflenir.

## 4. Hedef modül mimarisi

| Modül | Sorumluluk | Bağımlılık sınırı |
|---|---|---|
| `character_skeleton.py` | İskelet tanımı, eklemler, kemik bağlantıları, hiyerarşi ve rest pose verisi | Pygame ve oyun ekranlarından bağımsız |
| `character_rig_animation.py` | Hareket durumuna, yöne ve animasyon fazına göre eklem yerel pozlarını üretmek | İskelet modelini kullanır; çizim yapmaz |
| `character_rig_renderer.py` | Pozlanmış iskeleti katmanlı vücut parçaları olarak Pygame'e çizmek | Pygame ve iskelet/poz verisini kullanır |
| `character_animation.py` | Mevcut animasyon seçimi/state API'si ile yeni rig animasyonu arasındaki uyumluluğu yönetmek | Mevcut çağıranları gereksiz yere kırmamalı |
| `hex_gameplay_view.py` | Oyuncu ve NPC için rig/animator/renderer örneklerini oluşturup çizim akışına bağlamak | Dünya konumu ve hareket otoritesini devralmaz |

Dosya adları uygulama sırasında mevcut paket düzeni ve import kurallarıyla doğrulanmalıdır. Gereksiz yeni alt paket oluşturulmamalıdır.

## 5. İskelet modeli sözleşmesi

### 5.1 Koordinat sistemi

- İskelet geometrisi karaktere özgü normalize yerel uzayda tanımlanır.
- Modelin kök noktası karakterin gövde/pelvis merkezine yakın, sabit bir referans olarak belirlenir.
- Ekran çiziminde dünya konumu için ayak tabanı ankrajı kullanılır; kök noktasından ayak ankrajına olan fark rig tanımında açıkça tutulur.
- Yerel koordinatlarda sağ/sol ve yukarı/aşağı yönleri tek bir tutarlı eksen sözleşmesiyle tanımlanır ve test edilir.
- Kamera zoom'u ve render ölçeği yalnızca son dönüşüm aşamasında uygulanır.

### 5.2 Eklem ve kemik hiyerarşisi

İskelet en az şu anatomik noktaları temsil etmelidir:

- Gövde: pelvis, omurga/gövde merkezi, göğüs, boyun, baş.
- Kollar: sol/sağ omuz, dirsek, el bileği/el.
- Bacaklar: sol/sağ kalça, diz, ayak bileği/ayak.

Kemikler eklemler arasındaki bağlantıları ve uzunlukları temsil eder. Her eklem sabit ve benzersiz bir kimliğe sahip olmalı; ebeveyn ilişkileri döngü oluşturamamalıdır. Eksik ebeveyn, yinelenen kimlik, geçersiz uzunluk ve geçersiz sayısal değerler model oluşturulurken yakalanmalıdır.

Çocuk eklemin konumu ebeveynin dünya dönüşümünden hesaplanır. Animasyon, rest pose değerlerini ezmek yerine poz verisi üretir; böylece aynı iskelet tanımı farklı karakter örneklerinde tekrar kullanılabilir.

### 5.3 Poz verisi

- Rest pose değişmez referanstır.
- Animasyon pozu eklem bazında yerel açı/konum değişiklikleri taşır.
- Animasyon fazı (zaman ilerlemesi) animator tarafından yönetilir.
- Yön değişimi, yürüyüş fazını gereksiz yere sıfırlamamalıdır.
- Idle/walk/run durum geçişleri açık ve deterministik olmalıdır.

## 6. Yön sistemi

Mevcut oyunun sekiz yönlü karakter sunumu korunacaktır. Yön adlandırması ve sıralaması mevcut projedeki yön enum/değerleriyle eşleştirilmelidir; yeni ve ikinci bir yön standardı yaratılmamalıdır.

Rig, sekiz yönde tutarlı görünmelidir. İlk sürümde yönler için ayrı sanat varlıkları zorunlu değildir; vücut parçalarının derinlik sıralaması, örtüşme ve uzuv görünürlüğü yön bilgisine göre renderer tarafından ele alınabilir.

Yön değişimi sırasında:
- karakterin dünya konumu değişmez;
- ayak ankrajı sabit kalır;
- animasyon fazı korunur;
- yakın/uzak kol ve bacakların çizim sırası doğru uygulanır.

## 7. Animasyon sözleşmesi

İlk animasyon kümesi:

- **Idle:** Ağırlık merkezi ve gövde çok hafif doğal hareket eder; ayaklar zemine sabit görünür.
- **Walk:** Kollar ve bacaklar karşılıklı salınım yapar; diz ve dirsekler eklemli hareket eder; ayakların zemine basma/kalkma döngüsü tutarlı olur.
- **Run:** Walk döngüsünden daha yüksek frekans/genlik ve uygun gövde eğimi kullanılır; ayak kayması önlenir.

Animasyon sistemi:
- sabit FPS varsayımına bağlanmamalı, delta-time/faz temelli çalışmalıdır;
- farklı karakter örnekleri arasında animasyon durumu paylaşmamalıdır;
- aynı input için aynı pozu üretebilmelidir;
- gelecekte attack, interact, hit, death gibi durumlara genişletilebilir olmalıdır.

## 8. Renderer sözleşmesi

Yeni renderer yalnızca iskelet çizgileri ve eklem noktaları göstermemelidir. İlk doğrulama aşamasında bile gövde, baş, üst/alt kol, el, üst/alt bacak ve ayak gibi ayrı, dolu/şekilli parçalar çizilmelidir.

- Parçalar eklem noktalarına bağlanmalı ve eklem hareketini takip etmelidir.
- Gövde parçaları arasında belirgin kopukluk veya eklem boşluğu oluşmamalıdır.
- Yakın/uzak uzuv sırası yöne göre belirlenmelidir.
- Çizim sırası ileride kıyafet ve ekipman katmanları eklenmesine izin vermelidir.
- Sprite/render ölçeği ve mevcut ayak pivotu davranışı korunmalıdır.
- Debug iskeleti yalnızca geliştirme/test aracı olarak kalabilir; nihai karakter görünümünün yerine geçemez.

## 9. Mevcut sistemle entegrasyon ve korunacak davranışlar

Yeni rig yalnızca görsel sunum katmanına bağlanır. Aşağıdakiler değiştirilmeyecektir:

- oyuncu ve NPC dünya koordinatlarının sahibi olan runtime;
- hareket, hız, ivme, yavaşlama ve yön değiştirme hesapları;
- çarpışma, NPC itişi, ayrışma ve mekânsal indeks/occupancy kuralları;
- tıklayarak hareket ve rota takibi;
- kamera/dünya koordinatı dönüşümünün otoritesi;
- karakterlerin derinlik sıralaması için kullanılan mevcut dünya konumu semantiği.

Rig çizimi karakterin konumunu güncelleyemez, çarpışma sonucu üretemez veya runtime konumuna geri yazamaz. Render pivotu yalnızca sunum dönüşümüdür.

Oyuncu ve NPC aynı iskelet/renderer altyapısını kullanır; karakter türü/palet gibi mevcut görsel farklılıklar geçiş süresince korunur.

## 10. Uygulama sırası ve kapılar

### Paket 0 — Sözleşme ve mevcut durum doğrulaması
- Bu mimari belgeyi referans al.
- Mevcut yön enum/değerlerini, animator çağrılarını, render pivotunu ve test beklentilerini tekrar doğrula.
- Bu paket kod davranışını değiştirmez.

**Çıkış kapısı:** Değiştirilecek gerçek dosyalar ve mevcut API sınırları doğrulanmış olmalı.

### Paket 1 — Saf iskelet modeli
- `character_skeleton.py` oluştur.
- Eklemler, kemikler, hiyerarşi, rest pose ve yerel/dünya dönüşüm hesaplarını uygula.
- Pygame import etme.
- `tests/test_game_ui/test_character_skeleton.py` (veya testlerin mevcut gerçek paket düzenine uygun karşılığı) ekle.

**Çıkış kapısı:** Hiyerarşi, dönüşüm, doğrulama ve ayak ankrajı testleri geçmeli. Henüz oyun ekranına bağlanmamalı.

### Paket 2 — Rig renderer
- `character_rig_renderer.py` oluştur.
- Ayrı vücut parçalarını pozlanmış eklemlere göre çiz.
- Renderer testleriyle parça bağlantısı, ölçek ve ankrajı doğrula.

**Çıkış kapısı:** Sekiz yönün her birinde görsel iskelet bütünlüğü doğrulanmalı.

### Paket 3 — Rig animasyonu
- `character_rig_animation.py` oluştur.
- Idle/walk/run pozlarını delta-time/faz temelli üret.
- Yön değişiminde fazı koru; durum değişiminde tanımlı geçiş davranışı uygula.

**Çıkış kapısı:** Uzuv bağımsızlığı, döngü sürekliliği, ayak kayması ve deterministik poz testleri geçmeli.

### Paket 4 — Kontrollü oyun entegrasyonu
- Önce tek bir karakter örneğinde yeni rig'i bağla.
- Ardından oyuncu ve NPC'lere ortak altyapıyı uygula.
- Mevcut palet/görsel ayrımlarını koru.
- Eski renderer ile yeni renderer arasında gerekirse geçici bir seçim/geri dönüş yolu tut.

**Çıkış kapısı:** Oyun içi manuel testler ve hareket/çarpışma regresyon testleri geçmeli.

### Paket 5 — Eski sistemin emekliye ayrılması
- Yeni sistem tüm kabul ölçütlerini karşıladıktan sonra eski sprite factory/renderer bağımlılıklarını kaldır.
- Kullanılmayan kod ve testleri temizle.
- Mimari/uygulama raporunu güncelle.

**Çıkış kapısı:** Eski sisteme çalışma zamanı bağımlılığı kalmadığı doğrulanmalı; tam test paketi ve CI başarılı olmalı.

## 11. Test stratejisi ve kabul ölçütleri

### Birim testleri
- Eklemler benzersiz kimliklerle tanımlanır.
- Hiyerarşi döngüsüzdür; hatalı ebeveyn ilişkileri reddedilir.
- Kemik uzunlukları ve sayısal değerler geçerlidir.
- Çocuk eklemler ebeveyn dönüşümünü doğru miras alır.
- Rest pose değişmez kalır.
- Ayak ankrajı tanımlı ve dönüşümde korunur.
- Sekiz yönün tamamı tanınır.
- Animator idle/walk/run için geçerli poz üretir.
- Yön değişiminde faz korunur; karakter örnekleri birbirini etkilemez.

### Renderer testleri
- Tüm temel vücut parçaları çizilir.
- Kol ve bacak eklemleri bağımsız hareket edebilir.
- Parçalar eklem noktalarında bağlı kalır.
- Ölçek değişimi vücut oranlarını bozmaz.
- Ayak ankrajı ekran dönüşümünde sabit kalır.
- Sekiz yönde yakın/uzak uzuv sıralaması tutarlıdır.

### Entegrasyon ve manuel kabul
- Oyuncu ve NPC aynı rig altyapısıyla çizilir.
- Idle/walk/run oyun içinde doğru çalışır.
- Yön değiştirme sırasında karakter sıçramaz.
- Hareket sırasında ayaklar zeminde kaymaz veya karakter dünya konumundan kopuk görünmez.
- Kamera zoom'u karakter oranlarını bozmaz.
- Eski hareket, çarpışma, NPC itişi, ayrışma ve tıklayarak hareket davranışları değişmeden kalır.
- En az iki dakikalık sürekli hareket testinde titreme, takılma, teleport veya animasyon fazı sıçraması görülmez.

## 12. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Render pivotunun değişmesiyle karakterin zeminde kayması | Ayak ankrajını model sözleşmesine dahil et; dönüşüm testleri yaz |
| Rig'in runtime konumuna müdahale etmesi | İskelet/renderer API'sine dünya konumu yazma sorumluluğu verme |
| Sekiz yönlü görünümde uzuvların yanlış örtüşmesi | Yön bazlı katman sırası ve sekiz yön testleri |
| Animasyon geçişinde poz sıçraması | Rest pose + yerel pose ayrımı; faz/state geçiş testleri |
| Oyuncu ve NPC'nin farklı davranması | Ortak rig/renderer ve ayrı örnek durumları |
| Büyük geçişin mevcut sistemi kırması | Paketli uygulama, geçici geri dönüş yolu, eski sistemi en son kaldırma |
| Pygame'e aşırı bağımlı matematik modeli | Saf iskelet modelini Pygame'den bağımsız tutma |

## 13. Özelleştirme için gelecekteki genişleme noktaları

Bu aşamada uygulanmayacak; ancak mimari aşağıdaki genişlemeleri engellememelidir:

- görünüm/skin tanımı ile vücut parçalarının değiştirilmesi;
- kıyafet, zırh, pelerin, saç ve aksesuar katmanları;
- elde silah/kalkan gibi ekipman ankrajları;
- farklı vücut oranları veya ırk/karakter tipleri;
- ekipmana ve animasyon durumuna bağlı ek görsel katmanlar.

Bu özellikler iskelet matematiğine gömülmemeli; ileride ayrı görünüm/ekipman verileri ve renderer katmanlarıyla sağlanmalıdır.

## 14. Uygulama çalışma kuralı

Her paket öncesinde ilgili mevcut dosyalar ve çağıranlar tekrar incelenir. Uygulama, bu belgedeki sözleşmeyi ve gerçek kod tabanının mevcut API'lerini birlikte izler. Belgeyle kod arasında çelişki bulunursa sessizce varsayım yapılmaz; önce gerçek durum tespit edilir, gerekiyorsa bu belge gerekçesiyle güncellenir.

Her paket sonunda:
1. Değişen dosyalar ve gerekçeleri raporlanır.
2. İlgili testler çalıştırılır.
3. Test sonucu ve kalan riskler açıkça yazılır.
4. Sonraki pakete geçiş kapısı sağlanmadan entegrasyon genişletilmez.

**İlk kodlama adımı:** Yalnızca `character_skeleton.py` ve ona ait saf birim testlerini uygulamak. Eski karakter görselleştirme sistemi bu adımda değiştirilmez veya kaldırılmaz.

---

## 15. Uygulama günlüğü

- **Paket 1 — Saf iskelet modeli:** Uygulandı. Kullanıcı tarafından yerel ortamda çalıştırılan `tests.test_game_ui.test_character_skeleton` test paketi 11/11 başarılı oldu.
- **Paket 2 — Rig renderer:** İlk bağımsız uygulama eklendi: `game_ui/world_rendering/character_rig_renderer.py`. Renderer, mevcut sekiz yön adını kullanır; normalize eklem koordinatlarını ayak referansından ekran koordinatına dönüştürür; gövdeyi, başı ve ayrı uzuv parçalarını Pygame çizim ilkelleriyle oluşturur.
- **Paket 2 testleri:** `tests/test_game_ui/test_character_rig_renderer.py` eklendi. Yerel doğrulama bekleniyor.
- **Entegrasyon durumu:** Henüz `hex_gameplay_view.py`, mevcut sprite factory veya mevcut animasyon sistemi değiştirilmedi. Oyuncu/NPC entegrasyonu Paket 4'e bırakılmıştır.
- **Paket 2 — Rig renderer doğrulaması:** Kullanıcının yerel ortamda çalıştırdığı iskelet, rig renderer ve mevcut karakter renderer testleri toplam 21/21 başarılı oldu.
- **Paket 3 — Rig animasyonu:** İlk bağımsız sürüm eklendi: `game_ui/world_rendering/character_rig_animation.py`. Idle/walk/run durumları için delta-time tabanlı, örnek başına bağımsız eklem pozları üretir; yön değişiminde fazı, durum değişiminde normalize edilmiş döngü fazını korur. Yürüyüş/koşuda karşılıklı kol-bacak salınımı ve ayak yönünü yatay tutan ayak bileği telafisi bulunur.
- **Paket 3 testleri:** `tests/test_game_ui/test_character_rig_animation.py` eklendi. Kullanıcının yerel ortamda çalıştırdığı dört test grubu (iskelet, rig renderer, rig animasyonu ve mevcut karakter renderer) toplam **33/33 başarılı** oldu.
- **Entegrasyon durumu:** Oyun görünümü, mevcut sprite factory ve mevcut animasyon API'si değiştirilmedi. Rig animasyonu henüz oyun içinde kullanılmıyor.
