# Çözüm Araştırması: WASD Kontrolü ve Gelişmiş Humanoid Locomotion

Bu analizde Eldoria projesi için *Aşama 2* teknik planına uygun çözümleri detaylandırıyoruz. İki ana sorun üzerinde duruyoruz: (1) Klavye hareketi mimarisini *Z/X altı yön* yerine *W/A/S/D sekiz yön* şeklinde temizlemek, ve (2) Yeni 3B humanoid karakter için gerçekçi yürüyüş/animasyon sistemini tasarlamak. Yanıt, aşağıdaki bölümler halinde ilerliyor:  

- **Kök Neden Analizi:** Mevcut tasarım kusurlarının ve sınırlamaların belirlenmesi.  
- **Önerilen Mimari & Algoritmik Çözüm:** Giriş sisteminden animasyon algoritmalarına kadar matematiksel detaylar.  
- **Uygulama Planı ve Kabul Kriterleri:** Adım adım uygulama akışı ve başarı ölçütleri.  
- **Test Matrisi ve Regresyon Senaryoları:** Fonksiyonel ve performans odaklı test senaryoları.  
- **Performans Ölçüm Planı & Hedefleri:** FPS, bellek ve önbellek davranışını ölçme hedefleri.  
- **Riskler ve Geri Dönüş Stratejisi:** Olası sorunlar, belirsizlikler ve yedekleme planları.  
- **Depo Değişiklikleri Listesi:** `experiment/map-cleanup` dalında yapılacak somut değişiklikler (assumptions [varsayım] olarak işaretlendi).  

## Kök Neden Analizi

**(a) Giriş Kontrol Sistemi Sorunları:** Mevcut kodda iki ayrı giriş hattı bulunuyor: bir yandan `PygameMovementInput` (WASD/ok tuşları vs sürekli hareket), öte yandan `InputMapper/HexGameplayView` (Z/X tuşlarıyla altıgen yönler). Bu durum kafa karıştırıyor. Özellikle W ve D tuşları eski eylemlere atanmış (örneğin `world` veya `dialogue_history`), bu da WASD’yi tam kontrol için kullanımı engelliyor. Sonuç olarak:

- **Çakışan tuş atamaları:** Aynı tuş birden fazla amaca atanmış, istenmeyen etkileşimler oluyor. [varsayım: Mevcut atama tablosu tam bilinmiyor; bir kısım tuşlar eski sistemde farklı işlevde kullanılabilir.]  
- **Altıgen yön kısıtlaması:** Z/X ile yalnızca 6 yönde hareket sunan alt sistem, istenen 8 yönlü kontrolle uyumsuz. Klavye “sekiz yön” hareketi ekran/dünya koordinatlarına doğru dönüştürülmemiş.  
- **Odak ve UI girdi engelleme:** Oyun penceresi odak kaybında veya UI/metin alanlarındayken hareket girdileri düzgün yönetilmiyor olabilir [varsayım: Pencere odak kaybında tuş bırakma/kayıt durumu bilinmiyor].  

**(b) Locomotion ve Animasyon Sorunları:** Yeni 3B rig ve animasyon prototipi “profesyonel” görünmüyor çünkü şunlar eksik:  

- **Adım ve ağırlık aktarımı yok:** Mevcut animatör basit bir döngüyle 8 faz kullanıyor, fakat ayakların gerçek dünya konumu sabitlenmiyor. Bu da “kayma” etkisi yaratıyor ([9]). Ayaklar yerden kalkıp inme ve ağırlık değişimi (pelvis hareketi) ihmal edilmiş.  
- **Düşük çözünürlüklü hareket:** Yalnızca 8 poz örneği kullanmak (örneğin 8 açıda yürüyüş aşamaları) çok kaba hareket üretiyor. Gerçekçi bir yürüyüşte daha fazla ara poz gerekebilir.  
- **Yumuşak geçişler eksik:** Başlangıç, durma ve yön değişimlerinde jelk gibi ani sıçramalar var; geçiş animasyonları (idle→walk, walk→idle, pivot hareketler) eksik. Animasyonlar arasında inersiyal karışım (inertial blending) yapılmamış.  
- **İskeletik sabitleme/IK yok:** Ayaklar zeminle temas ettiğinde sabitlenmıyor (kısmi IK uygulanmamış). Yüksek detaylı IK gibi fiziksel çözümler belki bu projede ağır gelebilir ama basit sabitleme mekanizması dahi yok.  

Bu nedenlerden dolayı mevcut yapı, hem mekanik (kayma, sert geçişler) hem de mimari (eksik kontroller, çakışan tuşlar) anlamda hedeflerden uzak. Bu sorunlar, oyuna gerçek karakterler eklendiğinde daha da belirginleşecektir.

## Önerilen Mimari ve Matematiksel Çözüm

### 1. Giriş Sistemi – WASD ile Sekiz Yönlü Hareket

- **Girdi mimarisini birleştirme:** Yeni sistemde *tek* giriş hattı `PygameMovementInput` üzerinden W/A/S/D ve ok tuşları ile hareket yönünü belirleyecek. Eski Z/X atamaları tamamen kaldırılacak. [varsayım: `PygameMovementInput` içinde tuş durumları tutuluyor; buna W/A/S/D eklenip Z/X ile ilgili tüm mantık silinecek.] Gerekirse W ve D tuşlarına atanmış eski eylemler (ör. `world` menüsü) devre dışı bırakılacak.  
- **Yön vektörünün hesaplanması:** Kullanıcı klavyeden W, A, S, D kombinasyonlarına bastıkça ekranda `(dx,dy)` tarifi elde edilecek (ör. W=(0,-1), A=(-1,0) vb.). Ekran (screen) eksenine göre belirlenen bu `(dx,dy)` çifti dünya eksenlerine dönüştürülecek. İzometrik görüme göre dönüşüm formülü şu örneğe dayanır: 
  ```
  worldX = (screenRight + screenDown)
  worldY = (screenDown - screenRight)
  ``` 
  Yani: `(dx, dy) ⟶ (dx+dy, dy–dx)`. Örneğin yukarı tuşu `(0,-1)` ekran vektörü, dünya vektöründe `(-1,-1)` olur (izometrik haritada kuzeye yukarı ve sola hareket eder). Bu dönüşüm [1†L47-L54] kaynağında anlatıldığı gibidir.  
- **Hız normalizasyonu:** Oluşan dünya yön vektörü `(wx,wy)` uzunluklandırılarak birim vektöre dönüştürülecek. Böylece diyagonal hareketlerde hız artışı önlenir (aşağıdaki formül). Örneğin:
  ```python
  length = sqrt(wx*wx + wy*wy)
  ux, uy = wx/length, wy/length
  dx_world = ux * speed * deltaT
  dy_world = uy * speed * deltaT
  ```
  Bu, [1†L65-L72] kaynağındaki `Math.hypot` kullanımıyla aynı mantıkta, her yönde sabit hız sağlar.  
- **Yön tayini (Facing):** Karakterin karşıya baktığı yön, dünya hız vektöründen hesaplanacak. Yönü 8 bölüme yuvarlamak için [1†L117-L124] formülü kullanılabilir. Bu formüle göre önce ekran koordinatlarında birer açı hesaplanır:
  ```js
  sx = (dx - dy) * (tileWidth/2)
  sy = (dx + dy) * (tileHeight/2)
  angleIndex = (round(atan2(sy, sx)/(PI/4)) + 8) % 8
  ```
  Hesaplanan `angleIndex`, karakter sprite’ının bakış açısını (0=sağ, 1=sağ-altta, … 7=sağ-üstte) belirleyecek. Böylece 8 yönlü döndürme (sekiz sprite/durum) kolayca seçilebilir.  

- **Fareyle hedef tıklama:** Mevcut dünya koordinatlarına tıklayarak hareket sistemi korunacak [varsayım: Sahnedeki izometrik harita için tıklanan ekran pozisyonu inverse matrisle dünya koordinatına çevriliyor (örn. [2†L83-L90]’daki formül).]. Tıklandığında hedef posisine sekiz yön mantığı ile yaklaşım hesaplanacak.  

- **Diğer kontroller:** Klavye basılı tutma/salma (keyup/keydown) ve pencere odağı işlenmeli: Odak kaybı durumunda hareket vektörlerinin sıfırlanması sağlanmalı. Eğer oyun menülerindeyken klavye kullanımı engellenmeli (UI odak kontrolü). Aksi halde karakter “takılıp kalabilir”.  

### 2. Locomotion (Yürüyüş Sistemi)

- **Adım-ankle (foot contact) modeli:** Animasyon döngüsünde ayağın yerde kaldığı (stance) ve havada olduğu (swing) fazlar belirlenecek. Örneğin tipik bir yürüme döngüsü: **contact** (ayak sabit), **down** (ağırlık alt ayağa aktarılıyor), **pass** (boşta kalan ayak öne geçiyor), **up** (boşta kalan ayak kalkışta), ve tekrar **contact**. Bu yaklaşımı Sprita kılavuzu özetler:  
  - **Dikkat edilmesi gereken**: Sabit duran ayak (stance fazındaki ayak) dünya koordinatına göre sabit kalmalıdır. Yani karakter *ileri* ilerlerken sabit ayak sprite içinde geriye doğru kaydırılmalı. Kodda bu, karakterin dünya pozisyonuna göre ayak yerini ayarlamakla sağlanabilir:
    ```python
    # Örnek: ayak dünyada sabitken,
    foot_world_x = char_world_x + foot_local_x
    # Eğer char_world_x artıyorsa, foot_local_x negatif yönde
    ```
    Sprita makalesi bunu vurgular: *“Planted foot should be still relative to world; if character advances 5px, foot moves ~5px backward relative to root”*. Bu şekilde ayaklar zemine sabitlenip kayan gibi görünmesi önlenir.  

- **Animasyon-mesafe senkronizasyonu:** Animasyon hızları ve karakter hareket hızı eşleştirilecek. Örneğin bir adım döngüsü (bir sol ayak + bir sağ ayak adımı) X piksel mesafe kat ediyorsa, karakterin her döngü başına bu mesafeyi ilerlemesi gerekir. Stride (adım) uzunluğu ve süresi hesaplanmalı; biri sabitlendikten sonra diğer ayarlanmalıdır. Aksi halde ya fazla hızlı kayma, ya da yerinde kürek çekme etkisi oluşur.  

- **Yönlü animasyon karışımı (blending):** Sadece ileri yürüyüş animasyonu değil, *diğer* yönlere de geçiş animasyonları kullanılmalı. Basit bir yaklaşımda en az ileri, sağa (strafe), sola, geriye (back) yürüyüş klipleri alınır. Hareket vektörüne göre bu klipler ağırlıklı olarak karıştırılır. Örneğin karakter 45° sağa-doğru yürüyorsa %50 ileri + %50 sağ animasyon karıştırılır. Daha iyi kalite için NECİ (güney-doğu, kuzey-doğu, vb.) yönler için ek animasyonlar ekleyebiliriz. AAA sistemler sekiz yön kullanır: ileri (0°), sağ-ileri (45°), sağ (90°) vb.. Eldoria’da 8 faz yerine 4-5 farklı klip alıp açılarla karıştırmak iyi bir denge olabilir.  

- **Pelvis ve üst gövde hareketi:** Gerçekçi yürüyüş için pelvis (kalça) ve gövde dengesi önemli. Yürüme süresince pelvis hafifçe yukarı-aşağı ve yanlara salınmalı; ağırlık bir ayaktan diğer ayağa geçerken omuzlar/kalça counter-movement yapmalı. Üst gövdenin tamamen hareketsiz olması mekanik hissettirir. Özetle, üst gövde animasyonları adım animasyonlarıyla senkronize edilmeli. 

- **Yön değiştirme ve geçişler:** Karakter dururken, yürümeye başlamadan önce kısa bir başlatma animasyonu (örneğin ağırlık öne kayma), dururken durma animasyonu (son adımda durma pozuna geçiş) ve yön değiştirirken pivot animasyonu uygulanmalı. Ani geçişleri önlemek için animasyonlara *inertial blending* (kademeli karışım) eklenebilir. Örneğin bir dönüş başladığında, yeni yöne geçiş süresince önceki yöne ait animasyon yavaşça solarken yeni yöne ait animasyon yavaşça açığa çıkabilir. Bu, karakter dönüş sırasında titreme yapmadan yumuşak dönecektir.

- **Ayak sabitleme (basit IK):** Tam anlamıyla iki kemikli IK ağır olabilir; fakat basit bir ilke uygulanabilir: her adımın *temas* anında (örn. sol ayak tam yere bastığında) o ayağın dünyada sabit kalması için karakter kökü o an yer değişimi yapmaz. Sadece salınan ayak hareket eder. Böylece ayağın yer kayması önlenir. Yokuş ve engebeli araziye dair tamamen statik bir 2D sprite dünyasında fazla uygulanmayabilir, fakat düz zemin için her adım fazında ayakların sabitlenmesi işe yarar. Eğer ileriye çıkış yokken karakter öne doğru kayan bir animasyon görürsek, o pozisyon düzeltilmeli. (Bu, [7†L42-L51]’de anlatılan raycasting/IK yaklaşımının çok basitleştirilmiş hali gibidir: zemin yoksa karakter pelvisine hiç dokunmuyor, ama ayağını destekleyici şekilde kalça ve ayak rotasyonu simüle ediliyor.)  

- **Yerçekimi/Çarpışma etkileşimi:** Ayakların yerde sabitlenmesi öncelikli; ayak basışlarında çarpışma sistemine uygun bir yüksekliğe getirilmeleri [7†L47-L55] gerekebilir (örn. karakter basitçe ayağı ile “zıplayabilir”). Eldoria 2D izometrik olduğundan genelde zemin sabit kabul edilir. Yokuş/yataylık yoksa pelvis yüksekliği sabit kalabilir. Gelecekte engebeli arazi eklenirse yukarıdaki ağır basit IK akışına bakılabilir.  

### 3. Performans Odaklı Altyapı

- **Sprite önbellekleme:** Mevcut önbellek sistemi devam etmeli. Yeni animasyonlar sprite’larla GPU yerine CPU’da üretiliyor gibi görünse de sonuçta 2D sprite’lar çiziliyor; dolayısıyla önbellekte *doku (texture)* olarak tutup tekrar çizim yapmak hızlı. Aynı animasyon fazı için tek bir sprite üretin, çoklu karakterde tekrar kullanın. Önbellek boyutu sınırları (örn. 32 MB) değiştirilmeden, yeni animasyon fazları için gerekli yeni sprite kayıtları eklenecek.  

- **Çizim optimizasyonu:** [17†L78-L86]’daki gibi tüm ekranı tekrar tekrar tamamen çizmektense *dirty rect* kullanılması önerilir: karede sadece karakterin değişen piksellerini güncelleyin. Ayrıca tüm resimleri `.convert()` edip ekran formatına sokarak SDL blit hızını artırın. Kaynak [17]’de bellek yönetimi, yüzey dönüşümleri ve cümle içinde çizim sayısını azaltma gibi kritik optimizasyonlar anlatılıyor. Eldoria da bu çözümlerden faydalanmalıdır. Örneğin oyunda 50+ NPC varsa, her bir için ayrı 1000 üçgen yerine tek sprite çoğaltmak CPU yükünü düşürür.  

- **LOD (Detay Seviyesi):** Mevcut LOD mekanizması kullanılmalı: uzaktaki NPC’ler için daha düşük çözünürlüklü animasyon/sprite setleri. Bu aşamada yeni animasyonlar eklense de üçgen sayısı önemli ölçüde değişmiyor çünkü sonuçta 2D sprite’a dönüştürülüyor. Yine de, çoklu detay seviyelerini desteklemeye devam edip önbelleğe her LOD için ayrı kayıtlar alınabilir.  

- **Performans ölçümü:** Her aşamada FPS ve çerçeve süreleri izlenecek. Kodda [17]’de verilen profiler önerilerini uygulayarak çekirdek darboğazlar (giriş işlemleri, güncelleme, çizim, vs) izlenecek. Hedef: optimizasyon hedeflerinin bozulmaması. Örneğin önbellek sonrasında elde edilen 0.924 ms/karakter süresi gibi bir performans korunmalı.   

## Uygulama Planı ve Kabul Kriterleri

### Adım 1: Giriş Kontrolünü Yeniden Düzenleme
- **Yapılacaklar:**  
  - `experiment/map-cleanup` dalında `PygameMovementInput`'a geçiş yapın. Z/X tuşlarına bağlı altıgen yön kodlarını (muhtemelen `HexGameplayView` içinde) tamamen kaldırın [varsayım: bu kodun tam yeri bilinmiyor, ama branş adı ve modüllerden tahmin ediliyor].  
  - W/A/S/D tuşlarını sürekli hareket girdisine bağlayın. Önceki W/D atamalarını (örneğin `world` menüsü vs.) temizleyin.  
  - Yeni `InputMapper` yapısını güncelleyin: gelen `(dx,dy)` değerlerini izometrik dönüşümle dünya `(wx,wy)` vektörüne çeviren fonksiyon ekleyin (yukarıdaki formül). Bunun doğruluğu için birim test yazabilirsiniz.  
  - **Kabul Kriteri:** W, A, S, D tuşları tek başına ve kombinasyonları dünya koordinatında sekiz farklı yöne düzgün hareket ettirmeli. Oyunu basit bir sahnede çalıştırdığınızda W tuşuna basıldığında karakter kuzeye (ekranı yukarı doğru) doğru ilerlemeli, D basıldığında doğuya, W+D diagonale, S sola vb. Bu 8 yönden hiçbirinde hız artışı (kayma) olmamalıdır.  

### Adım 2: Karakter Animasyonu ve Yürüyüş Senkronizasyonu
- **Yapılacaklar:**  
  - Mevcut 3B rig ile yürüyüş animasyonunu yeniden gözden geçirin. 8 faz yerine daha fazla ana poz oluşturmayı düşünün. Bir adım döngüsünü belirgin pose’lara bölün (sprita rehberinden ilham alın: contact, passing, vb. pozlar).  
  - Animasyon adımlarını karakterin hareket mesafesiyle eşleştirin. Örneğin bir tam adım (sol-sağ)  X dünya pikseli ilerliyorsa, karakterin bu döngü süresince X mesafe ilerlemesi gerekir. Gerekirse animasyon hızını veya karakter hızını ayarlayın.  
  - Stance (ayak yerde) fazlarında o ayağın dünya konumunu sabit tutun. Kod veya animasyon pivotu ile sabitleme yaparak ayağın kaymasını engelleyin.  
  - İkili ayak animasyonu: Karakter sadece bir ayak üzerinde dururken diğerini ileri doğru sallamalı. Buna uygun referans pozları ekleyin.  
  - **Idle ↔ Walk geçişleri:** Yürümeden önce kısa bir ağırlık kaydırma animasyonu ve duruşa geçiş animasyonu ekleyin. Örneğin karakter hareket etmeyi kestiğinde son adım pozunu yavaşça düz konuma (idle) döndürsün. Başlangıçta ayağını yerden kaldırıp ileri salma açısı gibi bir geçiş olsun.  
  - **Yön Değiştirme:** Kullanıcı yürürken yön değiştirirse döngüyü sıfırlamak yerine mevcut animasyonu koruyun ve yeni yöne göre 8 yönlü karışımı yumuşatın. 90° dönmede pivot animasyonu, 180° için geri yürüme animasyonu gerekebilir.  
  - **Kabul Kriterleri:** Tek oyuncu oynatma modunda:
    - Karakter yürüdüğünde ayaklar yerden kaymamalı; *stance* fazında ayak world pozisyonu sabit kalmalı.  
    - Yavaş başlama ve yavaş durma animasyonları doğal olmalı; ani sıçramalar olmamalı.  
    - Karakter dört ana yönden (ileri, geri, sağa, sola) ve dört diagonale makul yürüyüş animasyonları göstermeli. Örneğin sağa yürürken gövde ve ayaklar sağa doğru sallanmalı.  
    - Adım mesafesi dünya hareketiyle tutarlı olmalı (üstünde referans bir işaretçiyi izleyin – kayma yok). Bunun için [9†L67-L75]’te anlatılan hızı-match testi yapılabilir.  

### Adım 3: Oyun İçi Test ve Entegrasyon
- **Yapılacaklar:**  
  - **Birincil Karakter ile Test:** Yeni sistem sadece oyuncuda etkin olacak şekilde entegre edin. NPC’ler eski sistemde kalsın. Böylece sorun çıkarsa geri dönmek mümkün.  
  - **Yürüyüş ve Dönüş Denemeleri:** Oyun ortamında karakteri W/A/S/D ile sekiz yönde yürütün. Fare tıklayarak hareketi deneyin. Dur-ileride yön değiştir-ileride sıçrama gibi akışları gözlemleyin.  
  - **Animasyon-Girdi Uyumu:** Klavye hareketi devam ederken karakterin animasyonu ileriye taşıyıp taşımadığını, durunca animasyonun sıfırlandığını kontrol edin. (Hareket kesilince adım döngüsü durmalı, arkada kalmamalı.)  
  - **Performans Ölçümü Başlatma:** Yukarıdaki ölçüm betiğini (ör. `benchmark_humanoid_body_3d.py`) kullanarak FPS ve önbellek isabeti ölçün. Bu, sonraki aşamalarda regresyonu yakalamak için baz değer olacak.  
  - **Kabul Kriterileri:** Tüm fonksiyonel testler geçmeli. Karakter *çekici* bir şekilde yürümeli ve dönmeli; 3B hareketi doğal görünmeli. Hareket kontrolleri tutarlı, kesintisiz ve türetilmiş olmalı (örn. W+A önden sol üst çaprazda hareket etsin). Hiçbir durumda animasyon alakasız yönde oynamamalı.  

## Test Matrisi ve Regresyon Senaryoları

Test matrisini hem işlevsel senaryolar hem de performans/regresyon açısından oluşturuyoruz:

- **Girdi Haritalama (Input Mapping):**  
  1. W/A/S/D tek başına basıldığında beklenen dünyasal yönde hareket ediyor mu? (örn. W: kuzeye, D: doğuya, A: batıya, S: güneye).  
  2. Diyagonal kombinasyonlar (W+A, W+D, S+A, S+D) doğrulanmalı. Karakter bu dört çapraz yönden birine kaymalı mı?  
  3. Klavye tuşunu bırakınca karakter duruyor mu? Tuşa bağlı olay akışı bozulmuyor mu?  
  4. Pencere dışına çıkıp geri dönüldüğünde tuşlar sıfırlanıyor mu? (Önceki sistem tuşa basılı kalıyor olabilir.)  
  5. UI veya sohbet/senaryo metin girişi açıkken hareket tuşları yanlış çalışmamalı.  

- **Animasyon ve Locomotion:**  
  1. Karakter yürüdüğünde her adımda bir ayağı yerden kaydırmadan ileri alıyor mu? (Basit bir yerde bir işaretçiyle ayak temas kontrolü yapılabilir.)  
  2. Durduktan sonra yürüyüş döngüsü sıfırlanıyor mu (en az bir idle pozu alıyor mu)?  
  3. Döngü süresi ve mesafesi uyumlu mu? Aynı hıza sabit animasyon (saat gibi) verildiğinde geçerli mesafe kat ediliyor mu?  
  4. Yön değiştirirken (örn. W→D’ ye geçiş) animasyon kalıcı mı? Karakter yere temaslı, açık geçiş yok mu?  
  5. Sekiz yönün her birinde uygun sprite/facing seçiliyor mu? (Test için sprite adları vs.)  
  6. Adım temposu (stride) tutarlılık testi: Referans bir işaret belirleyip karakter defalarca ileri geri yürüsün; ayak hareketleri dünya koordinatında zamanla örtüşmeli.  

- **Performans ve Bellek:**  
  1. 50 karakter, karışık LOD’da test. Beklenen ortalama kare süresi `≤~1 ms` (yaklaşık 1000+ FPS) olmalı. İşlemci ve GPU kaynak kullanımında anormal artış olmamalı.  
  2. Sprite önbellek doluluk/hıt oranı: `hits == frames` olmalı (önbellek hatası olmamalı). Beklenen önbellek boyutu ~1-2 MB aralığında kalmalı.  
  3. Düzenli profil oluşturun (örn. [17†L118-L127]’deki gibi). En ağır işlemler (animasyon oluşturma, draw, update) normal sınırlarda mı? Önbellekten sonrakine göre önceki hazırlık aşaması makul sürede mi tamamlanıyor?  

- **Regresyon Testleri:**  
  - Önceki koddan kalan hareket şemaları eski dallarda çalışmaya devam etmeli. `experiment/map-cleanup` dışında ana/demos dalı bozulmamalı.  
  - Geriye dönme ihtimali için sürüm kontrolü kullanılacak. Her yeni adım kaydedilip testten sonra merge yapılmalı. CI tarafından belirlenen başarısızlık olursa (örn. yanlış yön hesaplama, çakışma hatası) redeployment yapılmadan eski dal geri yüklenmeli.  

## Performans Ölçüm Planı ve Hedefleri

- **Metrikler:** Her veri kümesi için ortalama kare süresi (ms), eşdeğer FPS, önbellek hıt/miss sayıları, bellek kullanımı (MB), GPU/CPU yükü izlenecek. Profilde ayrı “işleme” kısımları (giriş, güncelleme, çizim) ölçülecek. Hedef, *baseline* değerleri aşmamak: daha önce bulunduğumuz 0.924 ms/karakter seviyesinden çok daha yavaş olmamak.  
- **Test ortamı:** Aynı donanımda karşılaştırmalı testler yapılmalı. Her kıyas için hem önbellek “ısınma” (ilk sprite üretim süresi) hem de steady-state değerleri alınmalı. 1, 10, 25, 50 karakter senaryoları raporlanmalı.  
- **Hedefler:**  
  - **Entegre performans:** 50 karakter senaryosunda ortalama kare süresi ~1 ms civarında (≥1000 FPS). Önbellek hıt oranı >99% olmalı. (Elbette bu mikrobenchmark; gerçekte UI vs oyun mantığı vs paralel iş yükleri yavaşlatır, ancak bu tutarlı bir temeldir.)  
  - **Hafıza:** Önbellek 1–2 MB civarında kalmalı, 32 MB sınırının çok altında. Çarpışma ve oyun durum verisi ek yüküne rağmen toplam bellek aşırı artmamalı.  
  - **Draw call sayısı:** Karakter başına ortalama **2000 üçgen** (örnek) diyelim; 50x = 100.000 üçgen GPU’ya gönderiyoruz. Bu kötü durumda bile 1 ms’nin üzerine çıkmamalı. Eğer çıkıyorsa örneğin sprite atlas yöntemiyle batched draw düşünün.  
- **Kayıt:** Tüm ölçümler otomatik kaydedilmeli. CI/CD’ye kare hızı trendi vs zaman eklenecek. Bir sonraki aşamada (evet/koşu, vb.) da bu test yinelenecek.

## Riskler ve Geri Dönüş Stratejisi

- **Çoklu giriş sistemi karmaşası:** `PygameMovementInput`’ı değiştirirken eski hareket sistemi (Z/X altı yön) hattının tam yedeği tutulmalı. Değişikliklerde tek bir commit veya feature branch kullanın. Eğer ana oyunda hata olursa hemen `experiment/map-cleanup` branch’ine dönün. **Geri Dönüş:** Ana dalı bozmamak için birleştirmeden önce kapsamlı test yapılmalı. Hatalıysa, basitçe eski kodu geri çekip yeni olanı dondurabilirsiniz.  
- **Animasyon kalitesi beklentisi:** Yüksek kalite animasyon beklerken bu denli detayı hemen başaramayabiliriz. Bu durumda adım adım iyileştirme (ilk tutarlı animasyon döngüsü, sonra ince ayar) stratejisi kullanılacak. Gerektiğinde taslak model (placeholder) ile ilerlenip, sonradan grafik ekibi yeni animasyon ekleyebilir. **Geri Dönüş:** Elde olmayan (eksik) animasyonlar için başlangıçta geçici durumlar (ör. basit loop) kullanılabilir. Realist animasyonlar oyun içi kameralara göre yavaş yavaş eklenecek.  
- **Performansın bozulması:** Yeni fonksiyonlar çizim/perf iyileştirmelerini aşarsa kaynağa müdahale edebilir. Risk: yeni sistem çizim süresini eskisinden yüksek çıkarsa geri dönebiliriz. Alternatif olarak daha agresif LOD/atlas/dirty-rect önlemleri alınabilir. **Geri Dönüş:** Eğer animasyon sistemi çok ağırsa (örneğin her kare yeni mesh üretiyorsa), gerekirse eskisine (statik sprite) bir alt seviyeyi koruyup kritik diyagramdan yönlü bir geçiş yapılabilir. CI’da profil karşılaştırmaları hata vermeli.  
- **Bilinmeyenler ve Varsayımlar:**  
  - [varsayım] Mevcut animasyon fazlarının tam zamanlaması ve uzatması bilinmiyor; yeni pozlar eklenmeli.  
  - [varsayım] Mevcut `HexGameplayView` gerçek kodu görünmediği için, klavye haritasını nasıl bağladığımıza karar verilmesi gerekiyor.  
  - Geri uyumluluk gereği `experiment/map-cleanup` dalı dışında ana branşa dokunulmayacak; tüm yeni kod bu dalda olacak. Değişiklikleri sıkça commit edip küçük parça parça test edin. Bu, geriye dönme imkânını korur.  
- **Kaynak Zaman ve İş Yükü:** Bu aşama çok zaman alıcı olabilir (özellikle animasyon temizliği). Takım dinamiklerine göre önceliklendirme gerekebilir. Olası çözüm: önce temel yürüyüşü tamamla, sonrasında detaylara in.  

## Eldoria Repo Değişiklikleri ve Adaptasyon

Aşağıdaki özet, `experiment/map-cleanup` dalına yapılacak somut değişiklikleri listeler (dosya adları ve mantıksal değişiklikler [varsayım] olarak verilmiştir):

- **Girdi Sistemi (`input/*`, `HexGameplayView.py`):**  
  - `PygameMovementInput` sınıfı: W/A/S/D tuşlarını sekiz yön hareketine bağlayın. Z/X kodlarını silin. Bu sınıftaki `update` veya `handle_event` fonksiyonlarına isometric dönüşüm ekleyin. [varsayım: Kod yapısı çıkarılmamış, ayıklamak gerekli.]  
  - `InputMapper`/`HexGameplayView`: Eski altıgen yön hesaplamalarını kaldırın. Eğer `HexGameplayView` sadece altıgen sistemi kullanıyorsa, bu dosyayı güncelleyin veya devre dışı bırakın. Dünyasal dönüşümü PygameMovementInput’a taşıyın.  
  - `ui/` veya `dialogue/` modüller: W/D tuş atamalarını kontrol edin, gerekirse silelim. (Bu atamalar yeni sistemle çakışmamalı.)  

- **Locomotion Animasyonu (`scripts/humanoid_body_animation_3d.py`, `character_animator.py`, vs.):**  
  - Yeni yürüyüş animasyon sınıfı: Adım döngüsünü ve fazları yöneten kod ekleyin. Her karakter `orientationIndex = facingFor(dx,dy)` ile yönlenmeli.  
  - Mevcut sahne veya önizleme scriptleri (`preview_humanoid_body_3d.py` vb.) güncellenmeli; yeni animatör/metotlar çağrılmalı. Animasyon hızı artık `deltaMesafe` bazlı ilerlemeli. Örneğin birim zaman yerine gerçek kat edilen mesafeye göre faz artışı (root motion style).  
  - Fade-in/Fade-out (blend) destek fonksiyonu: Geçişlerde önceki ve sonraki animasyonu karıştıracak kod. (Basit Lerp yeterli olabilir.)  
  - Idle ve hareket animasyonları arasındaki geçişler için ek durumlar. (`idle_to_walk`, `walk_to_idle` klipleri).  

- **Performans ve Test Araçları:**  
  - `benchmark_humanoid_body_3d.py`: Yukarıdaki yeni faz mekanizmasını ölçmek için güncelleyin. `sprite_cache_*` istatistiklerini kontrol eden yeni ölçümler ekleyin.  
  - Profiling için `scripts/pygame_profiler.py` (ör. [17†L118-L127]) gibi bir araç ekleyin. Bu, CI işlerinde çağrılabilir.  
  - Otomatik test betikleri: Giriş dönüşümü için küçük birim test (örn. `(dx,dy)->(wx,wy)` beklenen sonucu veriyor mu). Animasyon senkronizasyonu için basit regresyon testi (belirli girdi ↔ çıktı).  

- **Diğer Değişiklikler:**  
  - Mevcut LOD/sprite cache ayarları: Eklenecek yeni animasyon fazları için cache alanı genişletilmeli. `LOD_DISTANCES` veya benzeri sabitler kontrol edilmeli.  
  - Belgeler: Daha önceki aşamada oluşturulan araştırma raporuna bu çözümleri ve parametreleri ekleyin. Böylece yöneticiler ve takım üyeleri süreci takip edebilir.  
  - **CI Yapılandırması:** `experiment/map-cleanup` için eklenen testleri `github actions` konfigürasyonuna dahil edin. Özellikle sekiz yön anahtar, locomotion testleri ve performans profilini barındıran yeni testler eklenmeli.  

Her değişiklik parça parça commit edilecek ve CI onayı beklenecek. Bütünleştirme sırasında eğer işlev kaybı veya performans düşüşü varsa geri çevirme kolay olsun diye adımlar küçük tutulmalı. Aşama 2 tamamlanana kadar ana veya demo dallarına dokunmayın; yalnızca deneysel dal kullanılacak.  

**Özet:** Yukarıdaki adımlar, mevcut input mimarisini sadeleştirerek WASD sekiz yön kontrolünü sağlamayı ve yürüyüş animasyonunu biyomekanik temelli olarak iyileştirmeyi hedefliyor. Bu sayede oyuncu karakteri gerçekçi hareket edecek, performans garanti sınırlarından çıkmadan kaliteli bir sonuç vereceğiz. Sistem, yeniden kullanılabilir görünümler ve önbellek sayesinde ağır matematiksel yükten kaçınacak; platformda yüksek FPS hedeflerimiz korunacak. Aşama 2, ancak bu bütünlüklü entegrasyon ve test sürecinden sonra *görsel ve performans kabul* ile kapatılabilir.  



## Uygulama sırasında doğrulanan mimari düzeltmeler (2026-11-23)

Kaynak kodu incelendiğinde rapordaki bazı varsayımların güncellenmesi gerektiği görüldü:

1. `PygameMovementInput` zaten WASD ve ok tuşlarını okuyordu. Asıl çakışma `InputMapper` içindeki W=`world`, D=`dialogue_history` ve Z/X=eski altıgen yön eylemleriydi. Kısayolları tüm ekranlarda taşımak yerine bağlama duyarlı öncelik uygulandı: normal ekranlarda W ve D eski işlevlerini korur; aktif oyun hareketinde WASD girdisi öncelik kazanır ve aynı karede `world`/`dialogue_history` eylemleri bastırılır. Z/X tuşları artık `InputMapper` tarafından hareket eylemine çevrilmez.
2. Proje dünya koordinatlarını y-aşağı düzleminde saklıyor ve izometrik ekran dönüşümünü `WorldTransform` üzerinden yapıyor. Raporun ilk taslağındaki `(dx+dy, dy-dx)` formülü bu projeksiyonun gerçek ters dönüşümü değildir. Doğru dönüşüm, var olan `WorldTransform.unproject_vector()` fonksiyonudur. WASD girdisi önce ekran yönü olarak okunur, sonra bu fonksiyonla dünya vektörüne çevrilir. Böylece kamera konumu, zoom ve harita topolojisi hareket vektörüne karışmaz.
3. Altıgen `HexDirection` hâlâ harita topolojisi ve hücre geçişleri için gereklidir; kaldırılmamalıdır. Sadece klavyeden Z/X ile tetiklenen iki eski manuel hareket eylemi kaldırılmıştır. Fareyle hedef seçimi, tıklayarak hareket, çarpışma çözümü, harita sınırları ve NPC itiş sistemi korunur.
4. Animator'ın mevcut sekiz fazı zamanla değil, kat edilen mesafeyle ilerliyor; fakat poz üretimi sekiz örneğe kuantize edildiği için hareket görsel olarak kesikli kalıyor. Ayrıca rig eklem dönüşleri destekliyor, ancak gerçek ayak sabitleme için stance sırasında iki kemikli ters kinematik (IK) ve kök hareketine göre ayak hedefi gerekir. Bu iki özellik aynı şey değildir; yalnızca faz sayısını artırmak ayak kaymasını çözmez.
5. Performans kabulü yalnızca önceden ölçülen statik sprite-cache değerleriyle verilemez. Yeni gait sistemi, animasyon açıkken 1/10/25/50 aktör senaryolarında yeniden ölçülmeli; önbellek giriş/çıkışları, bellek tavanı ve kare süresi birlikte raporlanmalıdır.

Bu düzeltmeler, mevcut dünya simülasyonunu ve anatomik rig sözleşmesini koruyarak sonraki locomotion uygulamasının doğru koordinat ve performans varsayımlarına dayanmasını sağlar.


## Uygulama güncellemesi: dünya koordinatlı ayak teması ve IK (2026-11-23)

Bu uygulama diliminde, animasyonun hareket döngüsünden bağımsız bir sprite efekti olmaması için şu altyapı eklendi:

1. `humanoid_locomotion_3d.py`: İki kemikli analitik bacak IK çözücüsü ve stance sırasında dünya koordinatında ayak temas noktası saklayan `HumanoidFootLockSolver3D`.
2. `HumanoidRig.resolve_pose`: Eklemlere yerel öteleme girdisi eklendi. Böylece pelvis sıkışması gibi hareketler iskeletin geri kalanına hiyerarşik olarak aktarılabilir.
3. Gövde mesh skinning ve sprite renderer, yerel eklem ötelemelerini destekleyecek şekilde genişletildi. Öteleme cache anahtarına katılır; sprite cache 192 kayıt ve 32 MB sınırlarıyla kalır.
4. Ana karakter animatörü 16 gait örneğine yükseltildi; idle durumuna nefes, ağırlık aktarımı ve küçük baş/kol hareketleri eklendi. Walk/run/idle geçişleri 8 kademeli kısa bir blend ile yumuşatılır. Kol, dirsek, bilek, göğüs, boyun, baş, kalça, diz ve ayak bileği pozları ortak animasyon çıktısına dahildir.
5. Foot-lock girdisi ana karakterin çizilen dünya pozisyonu, facing yaw ve render ölçeğinden beslenir. Fizik ve dünya konumu runtime'ın yetkisindedir; rig yalnızca sunum pozunu üretir.
6. IK hedefi erişim sınırını aştığında çözücü bunu `reachable` ve hata tanılamasında bildirir. Bu, her koşulda kusursuz ayak kilidi iddiası değildir; görsel kabul ve adım uzunluğu kalibrasyonu gerektirir.

Pygame tarafında sprite üretimi yazılım rasterizasyonudur. Tekrarlanan pozların yüzey cache'inden blit edilmesi ve cache sınırının korunması sürdürülür. Kare süresi ölçümleri, `Clock.get_rawtime()` ile frame-cap beklemesinden ayrılmalı; update/render maliyetleri ayrıca `perf_counter_ns` ile profillenmelidir.

**Açık işler:** NPC'lerin ortak 3B animatöre geçirilmesi; 1/10/25/50 aktör benchmark'ı; sekiz yönde, tıklayarak hareket, ani dönüş ve duruş sırasında gerçek oyun içi görsel doğrulama. Bu aşama görsel kabul yapılmadan kapanmış sayılmaz.


## Uygulama güncellemesi: NPC ortak rig entegrasyonu ve performans aracı (2026-11-23)

NPC'ler de artık sürekli konum verisi bulunan durumlarda ana karakterle aynı `HumanoidBodyAnimator3D`, `DEFAULT_HUMANOID_RIG` ve `HumanoidBodyRenderer3D` hattını kullanır. Her NPC kendi dünya konumunu, facing yönünü ve kat ettiği mesafeyi animatöre verir; fizik ve konum otoritesi yine runtime'dadır. NPC'lerde düşük detaylı gövde mesh'i ve ortak malzeme paleti kullanılır. Sürekli konum verisi bulunmayan aktörler için eski sprite çizimi güvenli geri dönüş olarak korunur.

NPC fazları kimlikten türetilen kararlı başlangıç örnekleriyle dağıtılır; böylece bütün kalabalık aynı karede aynı adımı atmaz. Sprite cache 256 kayıt ve 32 MB bellek tavanı ile sınırlandırılmıştır.

Yeni `scripts/benchmark_humanoid_locomotion_3d.py` aracı 1/10/25/50 aktör senaryolarında update ve render sürelerini, p50/p95 kare maliyetini ve cache hit/miss/bellek kullanımını ayrı raporlar. Bu ölçümler gerçek kullanıcı donanımında da alınmadan performans kabulü verilmez.

**Kalan kabul işleri:** CI doğrulaması, benchmark sonuçlarının değerlendirilmesi, NPC/oyuncu birlikte sahne testi ve kullanıcı görsel kabulü. Dünya temasının her adımda kusursuz olduğu henüz iddia edilmemektedir; IK erişim tanılamaları ve görsel ayak kayması kontrol edilmelidir.


## NPC hareket senkronizasyonu ve tam uzuv pozları (2026-11-23)

NPC sunum katmanı artık runtime'ın zaten sürekli olan konumuna ikinci bir 0.18 saniyelik easing katmanı uygulamaz. Her karede gerçek sunum displacement'ı ölçülür; yön, hız ve gait fazı bu veriden türetilir. Hız 95 dünya birimi/s eşiğini geçtiğinde NPC run, daha düşük hızlarda walk, hareket yoksa idle durumuna geçer. Bu eşik ilk teknik kalibrasyondur ve gerçek oyun hızı/animasyon görüntüsüyle gözden geçirilecektir.

Animasyon pozlarına clavicle ve scapula kontrol noktaları, dirsek fleksiyonu (anatomik Z ekseni), el/avuç, topuk, ayak topu ve parmak ucu eklemleri dahil edildi. Böylece yalnızca ana eklemler değil, kol ve ayak zincirlerinin uç eklemleri de gait/idle pozlarına katılır.


## İlk kalabalık benchmark değerlendirmesi

İlk otomatik benchmark (Linux CI, Python 3.12.16; 120 ölçüm karesi ve 12 ısınma karesi) 974f860 commit'inde şu değerleri verdi:

| Aktör | Update p50 | Render p50 | Birleşik p50 |
|---:|---:|---:|---:|
| 1 | 0.048 ms | 0.139 ms | 0.187 ms |
| 10 | 0.449 ms | 19.687 ms | 20.135 ms |
| 25 | 1.082 ms | 1.718 ms | 2.800 ms |
| 50 | 2.136 ms | 14.708 ms | 16.844 ms |

50 aktörde cache 3.11 MB seviyesinde kaldı; 6,108 hit ve 492 miss görüldü. Render p95 sıçramaları 198 ms'ye kadar çıktığı için bu sonuç kabul edilebilir kararlılıkta değildir. Bu nedenle IK hedef/eklem açıları cache dostu alt piksel toleransında kuantize edildi ve skinned body mesh LRU kapasitesi 16'dan 64'e yükseltildi. Bu yeni ayarlar yeniden benchmark edilmelidir.

Bu ölçümler CI sanal makinesine aittir; kullanıcının düşük donanımlı bilgisayarındaki performansın yerine geçmez.


## Önizleme değerlendirmesi: omuz ve dirsek biyomekaniği

Otomatik üretilen sekiz yönlü sprite sheet görsel kontrolünde, A-pose omuz açıklığının idle ve locomotion pozlarında fazla korunduğu görüldü. Omuzların yerel Y eksenindeki içe/alçalmaya yönelik rotasyonları eklendi; dirsek fleksiyonu da rig limitleriyle uyumlu Z eksenine taşınıp güçlendirildi. Bu düzeltmenin görsel etkisi yeni idle/walk/run önizleme sayfalarında tekrar kontrol edilecek.
