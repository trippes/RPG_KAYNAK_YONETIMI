# Eldoria — Karakter Anatomisi, İskelet ve Rig Sistemi Genel Geliştirme Planı

**Belge türü:** Üst seviye teknik geliştirme planı  
**Durum:** Aşama 1 statik iskelet görsel kabulü ve CI doğrulaması tamamlandı; Aşama 2 ilk hacim prototipi geliştiriliyor  
**Hedef dal:** `experiment/map-cleanup`  
**Korunan dallar:** `main` ve `demo` — bu çalışma kapsamında kesinlikle değiştirilmez  
**İlgili mevcut belge:** `reports/asama-3-5-karakter-iskeleti-teknik-mimari-plani.md`  
**Uygulama yaklaşımı:** Aşama kapılarıyla ilerleyen, görsel ve otomatik test doğrulamasını birlikte kullanan kontrollü yeniden tasarım

---

## 1. Amaç ve genel karar

Eldoria'nın mevcut prosedürel karakter rig'i, eklemli uzuv hareketini ve sekiz yönlü önizlemeyi gösterebilen bir ilk altyapı sunmaktadır. Bununla birlikte paylaşılan görsellerde karakterin anatomik bütünlüğü henüz yeterli değildir. Başlıca sorunlar omuz kuşağının gövdeye bağlanması, göğüs-bel-pelvis oranları, uzuvların eklem bölgelerindeki mekanik birleşimler, yan görünüm derinliği ve yürüyüşte ayak-zemin ilişkisidir.

Bu nedenle geliştirme, tek tek görsel yamalarla sürdürülmeyecektir. İskelet geometrisi, vücut hacmi, yön projeksiyonu, animasyon biyomekaniği ve modüler görünüm aynı genel tasarım altında ele alınacaktır.

**Ana hedef:** Oyuncu ve NPC'lerin ortak kullanabileceği; anatomik olarak tutarlı, sekiz yönde okunabilir, doğal hareket üretebilen ve ileride kıyafet/zırh/saç/silah/aksesuar katmanlarıyla genişletilebilen bir karakter altyapısı oluşturmak.

Bu çalışma Pygame tabanlı mevcut oyun mimarisini sürdürür. Blender dokümantasyonunda kullanılan armature, kemik hiyerarşisi, rest pose, eklem kısıtları, IK ve deformasyon ilkeleri kavramsal referans olarak alınır; Blender çalışma zamanı veya Godot entegrasyonu hedeflenmez.

## 2. Kapsam ve değişmez sınırlar

### Kapsama dahil

- Anatomik referanslara dayalı iskelet ve kemik hiyerarşisinin yeniden tasarımı.
- Tutarlı nötr/rest pose ve karakter oranları.
- Omuz kuşağı, göğüs kafesi, pelvis, kol ve bacak zincirlerinin modellenmesi.
- Üç boyutlu yerel koordinatlarda poz hesaplama ve iki boyutlu Pygame ekranına projeksiyon.
- Hacimli, birbirine doğal bağlanan vücut parçalarının çizimi.
- Sekiz yönün ve yakın/uzak uzuv sıralamasının tutarlı hâle getirilmesi.
- Idle, walk ve run animasyonlarının biyomekanik açıdan geliştirilmesi.
- Gerçek oyun hareket mesafesiyle senkronize adım fazı ve ayak teması.
- Modüler görünüm/ekipman bağlantı noktaları.
- Oyuncu ve NPC entegrasyonu, regresyon ve görsel kabul testleri.

### Kapsam dışı / korunacak alanlar

- Bu plan kendi başına yeni fizik veya çarpışma sistemi geliştirmez.
- Runtime'ın dünya konumu, hareket otoritesi, hız/ivme, NPC itişi, ayrışma, mekânsal indeks, rota ve tıklayarak hareket davranışları rig tarafından devralınmaz.
- Karakter rig'i dünya konumunu veya çarpışma sonucunu değiştiremez; yalnızca görsel poz ve çizim üretir.
- İlk hedef tam 3B modelleme veya gerçek zamanlı 3B motor değildir. Üç boyutlu yerel iskelet geometrisi, mevcut Pygame çizim katmanında kontrollü 2B projeksiyonla sunulur.
- Eski karakter çizim sistemi, yeni sistem bütün kabul kapılarını geçmeden kaldırılmaz.

## 3. Genel teknik mimari

Sorumluluklar aşağıdaki şekilde ayrılacaktır. Dosya adları uygulama öncesinde gerçek import ve paket yapısıyla doğrulanır; bu tablo yeni dosyaların kesin olarak mevcut olduğu iddiası değildir.

| Katman | Sorumluluk | Temel kural |
|---|---|---|
| Anatomik iskelet modeli | Kemikler, eklemler, rest pose, ebeveynlik ve yerel dönüşümler | Pygame bağımsız, saf veri/hesaplama |
| Poz ve kısıt sistemi | Yerel eklem pozları, hareket sınırları, IK/temas çözümleri | Dünya konumunu değiştirmez |
| Animasyon sistemi | Idle/walk/run ve ilerideki aksiyon pozları | Gerçek hareket ilerlemesiyle senkronize olabilir |
| Projeksiyon/yön sistemi | 3B yerel koordinatları sekiz yön için ekrana dönüştürme | Anatomiyi ekranda zorla hizalamak yerine doğru projekte et |
| Rig renderer | Hacimli vücut parçaları, örtüşme ve çizim sırası | İskelet ve poz verisini tüketir; poz üretmez |
| Görünüm/ekipman katmanı | Ten, saç, kumaş, zırh, silah ve aksesuar | İskelet matematiğinden ayrı veri |
| Oyun entegrasyonu | Oyuncu/NPC örneklerini runtime hareket durumuna bağlama | Runtime hareket ve konum otoritesi olarak kalır |

### Koordinat sözleşmesi

Yeni model için sağ-sol (X), ön-arka/derinlik (Y) ve yukarı-aşağı (Z) eksenleri açıkça tanımlanacaktır. İşaret yönleri, açı birimleri, karakterin ileri ekseni, kök noktası ve ayak tabanı ankrajı tek bir sözleşmede sabitlenip test edilecektir.

Ekran projeksiyonu tek noktada yapılır. Omuzları veya uzuvları ekranda aynı yüksekliğe zorlayan özel düzeltmeler, anatomik modelin yerine geçemez. Yakın/uzak uzuv görünürlüğü ve çizim sırası yön/projeksiyon katmanında çözülür.

### Anatomik zincir ilkesi

- Gövde: pelvis → alt/üst omurga veya gövde segmentleri → göğüs kafesi → boyun → baş.
- Omuz kuşağı: göğüs kafesine bağlı sol/sağ köprücük kemiği ve omuz kökü; kürek kemiği hareketi ilk sürümde sadeleştirilmiş kontrol/poz katkısı olarak temsil edilebilir.
- Kol: omuz → üst kol → dirsek → ön kol → bilek → el; el gerektiğinde avuç ve parmak gruplarına ayrılabilir.
- Bacak: kalça → uyluk → diz → baldır → ayak bileği → topuk/ayak ucu; ayak tabanı temasını tanımlamak için topuk ve parmak ucu referansları tutulur.

Anatomik doğruluk hedeflenirken gereksiz kemik sayısı artırılmaz. Her kemik ve eklem, poz üretimi, deformasyon, temas veya gelecekteki ekipman bağlantısı açısından somut bir sorumluluğa sahip olmalıdır.

---

## 4. Aşamalı geliştirme yol haritası

## Aşama 1 — Anatomik iskelet ve hareket hiyerarşisinin yeniden tasarımı

**Amaç:** Mevcut basit iki boyutlu eklem düzeninden, anatomik referanslara dayalı ve derinlik eksenini destekleyen tutarlı bir iskelet modeline geçmek.

### İşler

1. Mevcut iskelet, renderer, animator ve çağıran API'ler tekrar incelenir; mevcut testler ve gerçek oyun yön adları doğrulanır.
2. Karakterin nötr duruşu belirlenir. Başlangıç rest pose'u, omuz ve kalça zincirlerinin rahatça ayrışabildiği dengeli bir A-pose olarak değerlendirilir.
3. Kök/pelvis, omurga, göğüs kafesi, boyun ve baş oranları anatomik referanslarla belirlenir.
4. Omuz kuşağı göğüs kafesine bağlanır; köprücük kemiği ve omuz kökü açıkça modellenir. Kürek kemiği etkisi, ilk sürümün karmaşıklığına göre sadeleştirilmiş eklem veya kontrol dönüşümü olarak ele alınır.
5. Kol zinciri dirsek, bilek ve el ayrımını; bacak zinciri diz, ayak bileği ve ayak referanslarını içerir.
6. Her eklem için yerel eksen, ebeveyn, rest transform ve izin verilen hareket aralıkları tanımlanır.
7. Üç boyutlu yerel koordinat dönüşümleri ve ayak tabanı ankrajı saf matematik katmanında uygulanır.
8. Eski modelle uyumluluk gerekiyorsa geçici adaptör tasarlanır; eski sistem bu aşamada kaldırılmaz.

### Testler ve çıkış kapısı

- Hiyerarşi döngüsüz ve bütün ebeveyn bağlantıları geçerli olmalı.
- Rest pose sabit, deterministik ve simetrik temel oranlara sahip olmalı.
- Sol/sağ eklem zincirleri aynalanabilir ve anatomik olarak tutarlı olmalı.
- Omuz kökleri göğüs kafesine bağlı olmalı; ekran Y koordinatını zorla eşitleyen renderer yamalarına ihtiyaç duyulmamalı.
- Dirsek ve diz hareket sınırları tanımlanmalı ve sınır dışı pozlar güvenli biçimde ele alınmalı.
- Önden, yandan ve çapraz referans projeksiyonlarında iskeletin anatomik sırası korunmalı.

**Aşama kabulü:** Saf iskelet testleri başarılı ve kullanıcı nötr iskelet önizlemesini görsel olarak onaylamış olmalı. Bu onay olmadan vücut hacmi üretimine geçilmez.

## Aşama 2 — Vücut anatomisi, hacim ve doğal parça birleşimleri

**Amaç:** İskeleti, mekanik eklemli parçalardan oluşan bir manken yerine bütünlüklü ve hacimli bir insan siluetine dönüştürmek.

### İşler

1. Göğüs kafesi, karın, bel ve pelvis ayrı anatomik hacimler olarak tasarlanır.
2. Omuz-göğüs-köprücük kemiği geçişi yeniden kurulur; omuzlar yalnızca iki nokta arasındaki çubuk veya daire olarak çizilmez.
3. Üst kol, dirsek, ön kol ve bilek hacimleri eklem hareketinde birbirinden kopmayacak biçimde tasarlanır.
4. Uyluk, diz, baldır ve ayak bileği geçişleri doğal siluet oluşturur.
5. Baş, boyun, el, avuç, topuk ve ayak ucu için okunabilir biçimler belirlenir.
6. Parçaların birleşiminde örtüşme, derinlik ve kontur kuralları uygulanır; eklem daireleri nihai karakter görünümünde gereksiz yere görünür kalmaz.
7. Renk/palet, ışık-gölge ve kontur dili tek bir görsel stile bağlanır. Eldoria'nın hedeflenen stiline uygun düşük poligon/prosedürel 2.5D sunum korunur.
8. Vücut geometrisi iskelet pozunu izler; geometri ve animasyon verisi birbirine gömülmez.

### Testler ve çıkış kapısı

- Nötr pozda baş, boyun, omuz, gövde, pelvis ve uzuvlar kopuksuz bir siluet oluşturmalı.
- Kollar kaldırıldığında veya bacaklar açıldığında eklem boşluğu oluşmamalı.
- Farklı pozlarda gövde oranları bozulmamalı.
- Ön, yan ve çapraz statik görsellerde insan anatomisi okunmalı.
- Kullanıcı özellikle omuz-göğüs-pelvis bütünlüğünü ve genel silueti onaylamalı.

**Aşama kabulü:** Statik karakter görünümü sekiz yöne geçmeden önce temel anatomik kaliteyi sağlamalı.

## Aşama 3 — Sekiz yön, projeksiyon, derinlik ve çizim sırası

**Amaç:** Aynı anatomik karakterin sekiz yönde aynı kişi olarak okunmasını ve yakın/uzak uzuvların doğru görünmesini sağlamak.

### İşler

1. Kamera/karakter yön sözleşmesi mevcut oyun yönleriyle eşleştirilir.
2. 3B yerel iskelet noktaları sekiz yön için tutarlı biçimde projekte edilir.
3. Baş, göğüs kafesi ve pelvis yönleri birbiriyle uyumlu tutulur; başın gövdeden bağımsız dönmesi yalnızca tanımlı hareketle yapılır.
4. Doğu/batı profillerinde karakterin derinliği kaybolmaz; ön-arka eksen ekran genişliğine doğru katkı verir.
5. Yakın ve uzak kol/bacakların örtüşmesi, gövdenin önünde/arkasında kalması ve çizim sırası yön bilgisine göre belirlenir.
6. Omuz, kalça ve ayak hizaları anatomik modelden gelir; tekil yönlerde ekran koordinatlarını zorla eşitleyen yamalar kullanılmaz.
7. Sekiz yönlü statik turnaround ve hareket önizlemesi oluşturulur.

### Testler ve çıkış kapısı

- Sekiz yönün tamamı doğru ve benzersiz yönelime sahip olmalı.
- Ön/arka ve yan/çapraz görünümlerde uzuv örtüşmeleri tutarlı olmalı.
- Karakter yön değiştirirken ayak ankrajı ve kök konumu sıçramamalı.
- Baş-gövde yön ilişkisi tutarlı olmalı.
- Kullanıcı sekiz yönlü statik ve hareketli önizlemeyi onaylamalı.

**Aşama kabulü:** Sekiz yönün tamamında anatomi ve perspektif kabul edilmeden animasyonun son biçimine geçilmez.

## Aşama 4 — Biyomekanik animasyon, gerçek hareket senkronizasyonu ve ayak teması

**Amaç:** Uzuv salınımı yapan bir kukla yerine ağırlık aktarımı ve ayak teması okunabilen doğal bir hareket sistemi oluşturmak.

### İşler

1. Idle, walk ve run için ayrı poz hedefleri ve geçişler tasarlanır.
2. Yürüyüşte karşılıklı kol-bacak salınımı, pelvis dönüşü, göğüs karşı dönüşü ve hafif ağırlık aktarımı eklenir.
3. Koşuda adım frekansı/genliği, gövde eğimi ve uçuş/temas fazları ayrı ele alınır.
4. Animasyon fazı yalnızca duvar saatine göre ilerlemez; runtime'dan gelen gerçek hareket mesafesi/hız bilgisiyle sürülür.
5. Duran karakterde adım fazı ilerlemez; yavaş hareket daha yavaş adım, hızlı hareket daha hızlı adım üretir.
6. Ayak temasında stance (yere basma) ve swing (havada ilerleme) evreleri ayrılır.
7. Temas evresinde ayak dünya/zemin referansına göre sabitlenir; mümkün olan ölçüde ters kinematik veya kısıtlı hedef çözümü kullanılır.
8. Yön değişiminde faz korunur; hareket durduğunda poz kontrollü idle durumuna geçer.
9. İvme, yavaşlama ve yön değişiminde animasyon hızı runtime hareketiyle tutarlı olur.

### Testler ve çıkış kapısı

- Hareket yokken adım fazı ilerlememeli.
- Aynı mesafe farklı frame parçalanmalarında aynı toplam gait fazını üretmeli.
- Yürüme ve koşma adım ritmi gerçek hızla tutarlı olmalı.
- Ayak basışında gözle görülür kayma kabul sınırının altında olmalı.
- Yön değişiminde ayak ankrajı veya animasyon fazı sıçramamalı.
- Oyuncunun normal hareketi ve NPC itişi sırasında görsel hareket runtime pozisyonundan kopmamalı.
- Kullanıcı idle/walk/run önizlemesini ve gerçek oyun hareketini onaylamalı.

**Aşama kabulü:** Mesafe tabanlı animasyon ve ayak teması doğrulanmadan yeni rig oyuncu/NPC'lere yaygın biçimde entegre edilmez.

## Aşama 5 — Modüler görünüm, kıyafet ve ekipman altyapısı

**Amaç:** Aynı anatomik iskeletin farklı karakter görünümlerini ve ekipmanları desteklemesini sağlamak.

### İşler

1. Skin/görünüm tanımı iskelet ve animasyondan ayrılır.
2. Ten, saç, sakal, kumaş ve temel kıyafet katmanları tanımlanır.
3. Gövde, omuz, ön kol, el, bacak ve ayak için kıyafet/zırh bağlantı bölgeleri oluşturulur.
4. Silah, kalkan ve aksesuarlar için el/bilek ve gövde ankrajları belirlenir.
5. Pelerin, kemer, çanta ve benzeri parçalar için uygun takip/ikincil hareket noktaları tasarlanır; ilk sürümde fizik simülasyonu zorunlu değildir.
6. Görünüm katmanlarının yakın/uzak uzuvlarla doğru örtüşmesi sağlanır.
7. Oyuncu ve NPC aynı rig'i kullanırken farklı skin/palet/ekipman verisi taşıyabilir.

### Testler ve çıkış kapısı

- Ekipman eklenmesi iskelet hiyerarşisini değiştirmemeli.
- Farklı görünüm verileri aynı animasyon/rig altyapısıyla çalışmalı.
- Ekipman ankrajları yön ve poz değişiminde karaktere bağlı kalmalı.
- Katman sırası sekiz yönde tutarlı olmalı.
- En az bir temel kıyafet ve bir elde taşınan ekipman örneği görsel olarak doğrulanmalı.

**Aşama kabulü:** Modüler görünüm örnekleri sekiz yönde kontrol edilmeden oyun entegrasyonunun sonlandırılması kabul edilmez.

## Aşama 6 — Kontrollü oyun entegrasyonu, geçiş ve eski sistemin kaldırılması

**Amaç:** Kabul edilmiş rig'i mevcut oyun akışına güvenli biçimde bağlamak ve eski karakter çizim sistemini yalnızca kanıtlanmış geçişten sonra emekliye ayırmak.

### İşler

1. Önce tek bir kontrollü karakter örneği oyun görünümüne bağlanır.
2. Runtime hareket durumundan gerçek hareket vektörü/mesafesi animator'a aktarılır; rig runtime'a veri yazmaz.
3. Oyuncu entegrasyonu doğrulanır; ardından NPC'lere ortak altyapı uygulanır.
4. Mevcut karakter türü/palet farklılıkları ve depth sorting korunur.
5. Gerekirse geçiş süresince eski/yeni renderer seçimi veya geri dönüş yolu tutulur.
6. Hareket, çarpışma, NPC itişi, ayrışma, rota takibi, tıklayarak hareket ve kamera davranışları regresyon testlerinden geçirilir.
7. Görsel ve performans kontrolleri yapılır; çok sayıda NPC çiziminde gereksiz hesaplama/cache maliyetleri ölçülür.
8. Yeni sistem tam kabul edildiğinde eski sprite factory/renderer bağımlılıkları kaldırılır.
9. Teknik mimari planı, uygulama günlüğü ve test kayıtları güncellenir.

### Testler ve çıkış kapısı

- Oyuncu ve NPC aynı rig altyapısını kullanmalı.
- Runtime konum/hareket/çarpışma davranışı değişmemeli.
- İki dakikadan uzun hareket testinde titreme, takılma, teleport veya faz sıçraması olmamalı.
- NPC itişi, duvara itme, ayrışma, harita sınırı ve tıklayarak hareket regresyonları geçmeli.
- Tam ilgili unittest paketi ve CI başarılı olmalı.
- Eski sisteme çalışma zamanı bağımlılığı kalmadığı doğrulanmalı.
- Kullanıcı gerçek oyun içi görsel kabul vermeli.

**Aşama kabulü:** Kullanıcı görsel kabulü, otomatik testler ve oyun içi regresyonlar tamamlanmadan eski sistem silinmez.

---

## 5. Ortak doğrulama ve kullanıcı kabul yöntemi

Her aşama aynı teslim düzeniyle tamamlanır:

1. **Teknik inceleme:** Değiştirilecek dosyalar, çağıranlar ve bağımlılıklar incelenir.
2. **Uygulama:** Yalnızca o aşamanın kapsamındaki değişiklikler yapılır.
3. **Otomatik test:** Projenin mevcut test altyapısı kullanılır. Projede pytest kurulu olduğu varsayılmaz; doğrulamada mevcut unittest komutları esas alınır.
4. **Görsel önizleme:** İlgili aşamanın görsel çıktısı kullanıcıya gösterilir/yerel ortamda çalıştırılır.
5. **Kabul raporu:** Değişen dosyalar, test sonucu, bilinen sınırlamalar ve kalan işler yazılır.
6. **Kapı kararı:** Kullanıcı onayı olmadan sonraki aşamaya geçilmez.

Otomatik test başarısı tek başına anatomik veya sanatsal kabul sayılmaz. Görsel kabul de hareket/çarpışma regresyon testlerinin yerine geçmez.

## 6. Dal ve Git çalışma politikası

Bu planın ve bütün uygulama değişikliklerinin tek hedefi:

`experiment/map-cleanup`

Kesin kurallar:

- `main` dalına commit, merge, cherry-pick, push veya doğrudan dosya değişikliği yapılmaz.
- `demo` dalına commit, merge, cherry-pick, push veya doğrudan dosya değişikliği yapılmaz.
- Yeni bir dal oluşturulmaz ve başka dala geçilmez.
- Bütün rapor ve kod değişiklikleri yalnızca `experiment/map-cleanup` dalına yazılır.
- Yerel doğrulama için kullanıcıya verilecek pull komutları yalnızca `origin experiment/map-cleanup` hedefini kullanır.
- Her aşama ayrı, açıklayıcı commit(ler) ile kaydedilir.
- Dal hedefi veya dosya içeriği konusunda belirsizlik varsa yazma işlemi yapılmadan önce tekrar doğrulanır.

## 7. Mevcut durum ve başlangıç noktası

Bu belge yazıldığı sırada:

- Saf iskelet modeli, rig renderer ve rig animasyonu için bağımsız modüller oluşturulmuş durumda.
- Bu ilk model 19 eklem ve 14 kemik içeriyor; mevcut iskeletin koordinat yaklaşımı henüz bu genel planda tarif edilen üç eksenli anatomik modele eşdeğer değildir.
- Rig'in oyun görünümüne tam entegrasyonu tamamlanmış kabul edilmemektedir.
- Kullanıcı tarafından daha önce dört test grubunda 34/34 test başarısı bildirilmiştir; bu sonuç o test koşusuna aittir ve yeni mimari değişikliklerin doğrulaması olarak kullanılamaz.
- Paylaşılan son önizlemede tunik ve vücut hacmi önceki sürüme göre gelişmiş olmakla birlikte omuz-göğüs bağlantısı, gövde oranları, mekanik eklem geçişleri ve yan profil derinliği hâlâ geliştirme gerektirmektedir.
- Görsel kabul verilmemiştir.
- Yeni planın ilk uygulama adımı Aşama 1 öncesi teknik inceleme ve anatomik iskelet şemasının kesinleştirilmesidir. Doğrudan oyun entegrasyonu yapılmayacaktır.

## 8. Araştırma ve tasarım referansları

Aşağıdaki Blender kaynakları, gerçek zamanlı 3B motor kullanma kararı olarak değil; karakter rigging kavramları için teknik referans olarak kullanılacaktır:

- Blender Manual — [Rigify Bone Positioning](https://docs.blender.org/manual/en/latest/addons/rigify/bone_positioning.html)
- Blender Manual — [Inverse Kinematics](https://docs.blender.org/manual/en/latest/animation/armatures/posing/bone_constraints/inverse_kinematics/introduction.html)
- Blender Manual — [Bone Roll](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/bone_roll.html)

Anatomik oranlar ve eklem hareketleri uygulama sırasında ayrıca insan iskeleti/anatomi referanslarıyla kontrol edilmelidir. Bu belge, her kemik için klinik anatomi ölçüsü iddiasında bulunmaz; oyun karakteri için tutarlı stilize anatomi hedefler.

---

## 9. Karar kaydı

- Karakter geliştirmesi tekil görsel yamalar yerine bu altı aşamalı genel plana göre yürütülecektir.
- Mevcut iskelet ve renderer, teknik inceleme tamamlanmadan nihai temel kabul edilmeyecektir.
- Üç boyutlu yerel iskelet koordinatları ve sekiz yönlü 2B projeksiyon yaklaşımı araştırılacak ve Aşama 1'de kesinleştirilecektir.
- Omuz hizası, ekran koordinatına zorla müdahale edilerek değil, anatomik omuz kuşağı ve doğru projeksiyonla çözülecektir.
- Gerçek hareket mesafesine bağlı animasyon ve ayak temas kontrolü Aşama 4'ün zorunlu gereksinimidir.
- Oyuncu/NPC entegrasyonu Aşama 6'ya kadar kontrollü ve sınırlı tutulur.
- `main` ve `demo` dalları bu çalışma boyunca değiştirilmeyecektir.

## 10. Uygulama durumu kaydı — 2026-11-22

**Aşama 1 durumu:** İlk anatomik iskelet modeli ve matematik altyapısı uygulandı; aşama henüz kabul edilmedi.

Eklenen/ güncellenen bileşenler:

- `game_ui/world_rendering/humanoid_rig_3d.py`: Pygame bağımsız 3B humanoid hiyerarşisi, quaternion tabanlı ebeveyn dönüşümleri, eklem limitleri, kemik uzunlukları ve ortografik projeksiyon.
- `tests/test_game_ui/test_humanoid_rig_3d.py`: 18 unittest metodu.
- `scripts/preview_humanoid_rig_3d.py`: Ön, yan ve üç çeyrek debug görünüşü.
- `pyproject.toml`: pytest keşif ve Ruff yapılandırması.
- `.github/workflows/eldoria-ci.yml`: Yeni rig modülü, testleri ve önizleme betiği Ruff kapsamına eklendi.
- `reports/asama-1-anatomik-iskelet-uygulama-raporu.md`: Aşama 1 uygulama kaydı.

**Korunan sınırlar:** Eski 2B iskelet, rig renderer, animator, oyuncu/NPC sprite hattı ve runtime hareket/konum/çarpışma sistemi değiştirilmedi.

**Doğrulama durumu:** Depo testleri bu işlem ortamında çalıştırılmadı. Son commit için erişilebilen birleşik commit-status ve PR workflow sorguları sonuç döndürmedi; bu nedenle GitHub Actions başarısı iddia edilmemektedir. Yerel test, Ruff ve görsel kabul beklenmektedir.

**Sonraki işlem:** Kullanıcının yerel ortamında hedefli unittest/pytest ve Ruff doğrulaması; ardından üç görünüşlü önizlemenin görsel değerlendirmesi. Aşama 1 kabul edilmeden Aşama 2'ye geçilmez.


## 11. Görsel kabul kaydı — 2026-11-22

Kullanıcı, düzeltilmiş üç görünüşlü iskelet önizlemesini inceledi ve mevcut iskelet oranları ile A-Pose duruşunu bu aşama için uygun buldu. Bu karar **statik iskelet/önizleme kabulüdür**; oyun içi karakter animasyonlarının doğal görünümüne ilişkin nihai kabul değildir. Kullanıcı, animasyonları oyun içinde gördükten sonra son değerlendirmeyi yapacağını açıkça belirtti.

Önizlemedeki ilk kadraj taşması giderildi; rig anatomik koordinatları değiştirilmedi. Yan görünüşte kolların üst üste düşmesi mevcut ortografik izdüşümün beklenen sonucudur ve tek başına anatomik hata sayılmamıştır.

Aşama 1'in görsel kabul kapısı karşılanmıştır. Son kod değişikliğinden sonra Eldoria CI yeniden çalıştırılmaktadır; teknik doğrulama başarılı olmadan Aşama 1 tamamen kapatılmış ve Aşama 2 başlatılmış sayılmayacaktır. Oyun içi animasyon kabulü Aşama 4 ve Aşama 6 görsel kabul kapılarında yeniden yapılacaktır.


## 11. Aşama 1 kabul ve Aşama 2 başlangıç kaydı — 2026-11-22

Aşama 1 statik iskelet önizlemesi kullanıcı tarafından kabul edildi. Kabul, iskelet geometrisi ve A-Pose rest pose'un statik görünümüyle sınırlıdır; oyun içi animasyonların nihai kabulü Aşama 4 ve Aşama 6'da yapılacaktır. Son Aşama 1 kod düzeltmeleri için Eldoria CI ve Core Quality başarılı tamamlanmıştır.

Aşama 2 kapsamında ilk bağımsız 3B hacim prototipi oluşturulmuştur:
- `humanoid_body_3d.py`: iskelet eklemlerine bağlanan parametrik ellipsoid ve segment hacimleri.
- `humanoid_body_renderer_3d.py`: üçgen mesh'i derinlik sıralaması ve ortografik projeksiyonla Pygame yüzeyine çizer.
- `preview_humanoid_body_3d.py`: ön, üç çeyrek ve yan statik görünüş önizlemesi.
- `test_humanoid_body_3d.py`: hacim envanteri, deterministik mesh, poz takibi ve geçersiz geometri testleri.

Bu ilk prototip, Aşama 2'nin tamamlandığı veya görsel olarak kabul edildiği anlamına gelmez. Kas hacimleri, omuz-göğüs geçişi, eklem örtüşmeleri, siluet, yüzey normalleri ve farklı pozlarda kopma/boşluk kontrolleri görsel ve teknik incelemeyle iyileştirilecektir. Eski 2B karakter renderer'ı ve runtime entegrasyonu değiştirilmemiştir.


## 12. Aşama 2 anatomik hacim ve performans iyileştirmesi — 2026-11-22

Kullanıcının kalite kararı: Karakter daha gerçekçi ve anatomik olarak inandırıcı görünecek; ancak görsel kalite için optimizasyondan ödün verilmeyecek. Düşük poligonlu 2.5D yaklaşımı ve düşük donanım hedefi korunacaktır.

İlk hacim önizlemesinin ardından Aşama 2 prototipinde şu iyileştirmeler yapıldı:

- Göğüs kafesi, bel, karın ve üst sırt hacimleri daha belirgin anatomik kütleler olarak ayrıştırıldı.
- Köprücük kemiği hacimleri göğüs ve omuz zinciri arasına eklendi.
- Üst kol, ön kol, uyluk ve baldır için birbirinden farklı, kademeli kesit profilleri tanımlandı; bütün uzuvların aynı kalınlıkta silindir görünmesi azaltıldı.
- Düşük poligon mesh üretiminde tekrarlanan daire ve enlem trigonometrisi örnekleri LRU önbelleğine alındı.
- Rig ve poz aynı kaldığında üretilen değişmez yerel üçgen mesh'i 16 girdilik LRU önbelleğinde saklanıyor. Aynı animasyon pozunu paylaşan karakter örnekleri bu geometriyi yeniden kullanabilir.
- Cache anahtarı rig tanımı ve normalize edilmiş poz girdilerinden oluşur; runtime dünya konumu, kamera açısı veya karakterin oyun içi konumu cache'e dahil edilmez. Renderer'ın projeksiyon ve derinlik sıralaması mevcut sorumluluğunda kalır.

Bu tur yalnızca bağımsız hacim modeli ve testlerini etkiler. Eski 2B karakter renderer'ı, oyun runtime hareket/konum/çarpışma sistemi ve NPC davranışları değiştirilmemiştir.

Yeni test kapsamı: anatomik kesit profillerinin varlığı ve geçerliliği, trigonometrik örnek önbelleği ve aynı rig/poz için immutable mesh nesnesinin yeniden kullanılması. GitHub Actions doğrulaması tamamlanmadan bu turun teknik kabulü verilmiş sayılmaz; statik önizleme de kullanıcı tarafından yeniden incelenecektir.


## 13. Aşama 2 — bağlı gövde yüzeyi ilk mimari uygulaması — 2026-11-22

Kullanıcının bağlayıcı kalite kararı: Anatomik gerçekçilik artırılacak; ancak düşük donanım ve çok sayıda NPC hedefi nedeniyle optimizasyondan ödün verilmeyecek. Küçük ve birbirinden kopuk görsel yamalarla ilerlemek yerine yüzey/topoloji yaklaşımı önce tasarlanıp uygulanacaktır.

### Kod incelemesinden doğrulanan başlangıç sorunu

Önceki `HumanoidBodyModel` gövdeyi pelvis, karın, bel, göğüs, sırt ve boyun için bağımsız ellipsoid/segment parçalarıyla kuruyordu. Renderer bütün üçgenleri tek listede topluyor, üçgen başına ışık hesabı yapıyor ve derinliğe göre sıralıyordu. Bu yöntem eklem/gövde birleşimlerinde üst üste eklenmiş parça görünümüne yol açıyor; anatomik yüzey akışını tanımlamıyordu.

### Uygulanan ilk mimari değişiklik

- `BodySurfaceDefinition` eklendi. Anatomik landmark'lara bağlı, sıralı kesit istasyonları tanımlıyor.
- `connected_torso` yüzeyi pelvis → alt omurga → üst omurga → göğüs → boyun istasyonları arasında tek bir paylaşılan halka topolojisiyle üretiliyor.
- Sol/sağ kol yüzeyleri omuz → dirsek → bilek; bacak yüzeyleri kalça → diz → ayak bileği landmark zincirlerini takip eden bağlantılı tüp yüzeyleri olarak üretildi.
- Kesit halkaları her istasyonda yerel zincir teğetine göre yönlendiriliyor; böylece yüzey yalnızca dikey gövde eksenine değil, bükülen kol/bacak zincirlerine de uyum sağlıyor.
- Komşu istasyonlar arasında yumuşatılmış interpolasyon ve kontrollü düşük poligon kesitleri kullanılıyor.
- Gövde artık beş ayrı kapalı hacmin üst üste bindirilmesiyle oluşturulmuyor. Tunik/pantolon/ten malzeme bantları aynı yüzeyin istasyonları üzerinden atanıyor.
- Daire örnekleri mevcut önbellekten paylaşılıyor; yüzey topolojisi ve üçgenleri aynı rig/poz için mevcut sınırlı mesh cache üzerinden tekrar kullanılabiliyor.
- İlk geometri bütçesi bilinçli olarak 8 kesit kenarı ve 3 ara bölümleme düzeyine indirildi. Testte bir temel karakterin toplam mesh'i en fazla 1.300 üçgenle sınırlandırıldı. Bu bir başlangıç geometri bütçesidir; hedef FPS veya ölçülmüş çizim süresi iddiası değildir.
- 50 karakter için bu üst sınır yaklaşık 65.000 üçgenlik geometri yüküne karşılık gelir. Pygame'in CPU tabanlı çokgen çizim maliyeti ayrıca benchmark edilmelidir; gerekirse uzak NPC LOD/sprite fallback ve görünürlük culling'i uygulanacaktır.
- Baş, omuz başı, köprücük kemiği, el ve ayak prototipleri şimdilik ayrı parça olarak duruyor. Gövde ve ana kol/bacak zincirleri bağlantılı yüzeylere taşındı. Bu, tüm vücudun tek mesh olduğu veya skinning'in tamamlandığı anlamına gelmez.

### Bu değişikliğin sınırları

- Henüz lineer blend skinning veya dual-quaternion skinning eklenmedi.
- Omuz, dirsek, kalça ve diz çevresinde deformasyon kalitesi henüz animasyon pozlarıyla doğrulanmadı.
- Üçgen derinlik sıralaması ve yüzey gölgelendirme mimarisi henüz performans profiliyle ölçülmedi. 1.300 üçgen sınırı yalnızca geometri bütçesidir; 50 NPC'de kabul edilebilir FPS anlamına gelmez.
- Gerçek zamanlı oyun entegrasyonu, runtime hareket/konum, çarpışma ve NPC davranışları değiştirilmedi.

### Sonraki uygulama dilimi

1. Omuz kuşağı ve kol zincirleri için eklem çevresinde ortak halka/bağlantı topolojisi.
2. Kalça, uyluk, diz ve baldır için aynı yaklaşım.
3. El/avuç ve ayak/topuk geometrisinin anatomik landmark'lara bağlanması.
4. Rig transformlarıyla uyumlu skinning seçimi ve ağırlıklandırma; CPU maliyetini ölçerek karar verme.
5. Sekiz yön ve ekstrem pozlarda golden-image/eklem boşluğu testleri.
6. NPC sayısı arttığında üçgen sayısı, mesh-cache hit rate, çizim süresi ve bellek ölçümleri.

Aşama 2 kabul edilmedi. Bu commit yalnızca gövde topolojisinin ilk mimari düzeltmesidir; görsel önizleme ve CI doğrulaması beklenir.


## 14. Aşama 2 — skinning, ayak yüzeyi, sekiz yön ve performans altyapısı — 2026-11-22

Bu uygulama diliminde bağlantılı yüzey prototipi animasyon pozlarına hazırlanmış ve performans doğrulama araçları eklenmiştir.

### Skinning ve deformasyon

- `MeshTriangle` artık her köşesi için en fazla iki eklemden oluşan skin weight verisi taşıyor.
- Ağırlıklar normalize ediliyor; bağlı yüzeylerde istasyonlar arası yumuşatılmış kesit interpolasyonuyla uyumlu biçimde dağıtılıyor.
- Ellipsoid parçaları tek eklem etkisiyle, segment parçaları uç eklemler arasında ağırlıklandırılıyor.
- Poz dönüşümünde rig'in global quaternion dönüşümleri kullanılarak Linear Blend Skinning (LBS) uygulanıyor. Her eklemin bind-pose global dönüşümü ile güncel global dönüşümü arasındaki delta, ilgili eklemin bind pivotu çevresinde köşeye uygulanıyor.
- Dual-quaternion skinning bu aşamada seçilmedi. Mevcut rig ve düşük poligon bütçesinde LBS daha basit, ölçülebilir ve yeterli başlangıç yaklaşımıdır. Omuz/bilek gibi büyük bükülmelerde hacim kaybı görsel testte belirginleşirse alternatif yeniden değerlendirilecektir.
- Bind-pose mesh'i ayrı 4 kayıtlı cache'te tutuluyor; skinned poz mesh'i ayrı 16 kayıtlı cache'te tutuluyor. Böylece her yeni animasyon pozunda trigonometrik örnekleme ve temel topoloji yeniden üretilmiyor.
- Yüzey kesitlerinde önceki halkadan taşınan paralel-transport çerçevesi kullanılıyor. Bu, sabit dünya referansına bağlı ani kesit burulmalarını azaltır.

### El ve ayak

- Ayaklar tek oval hacim olmaktan çıkarıldı; topuk → tarak → parmak ucu landmark'ları arasında bağlantılı yüzey olarak üretiliyor.
- Bilek → avuç bağlantısı ayrı bir skinned yüzeyle kuruldu; avuç hacmi düşük poligon ellipsoid olarak korunuyor. Parmakların ayrı eklemleri mevcut rig'de bulunmadığından bu aşamada bağımsız parmak animasyonu iddia edilmiyor.

### Sekiz yön ve renderer

- Önizleme artık N, NE, E, SE, S, SW, W ve NW olmak üzere sekiz yönü aynı ekranda gösteriyor.
- Renderer testleri sekiz yaw açısının tamamında çizim yapılmasını kontrol ediyor.
- Her üçgenin yüz normali mesh oluşturulurken bir kez hesaplanıyor; her karede tekrar vektör çarpımı ve karekök yapılmıyor.
- `build_mesh` ve renderer `detail_level=high|medium|low` seçeneklerini destekliyor. High/medium/low topoloji bütçeleri sırasıyla 1.248 / 744 / 528 üçgen olarak test sözleşmesine sabitlendi.
- LOD varyantları aynı anatomik landmark ve skinning düzenini koruyup kesit kenarı/bölüm sayısını azaltıyor. Uzaklık veya ekrandaki piksel boyutuna göre LOD seçimi henüz oyun runtime'ına bağlanmadı; çağıran sistem açıkça detail_level seçmelidir.
- Renderer hâlâ üçgenleri derinliğe göre sıralayıp Pygame polygon çağrılarıyla çiziyor. Bu yüzden 50 NPC için performans garantisi verilmemektedir.

### Geometri ve performans ölçümü

- Temel modelin otomatik testteki üst sınırı karakter başına 1.300 üçgendir.
- Yeni `scripts/benchmark_humanoid_body_3d.py`, 1/10/25/50 karakter senaryolarında kare süresini, eşdeğer FPS'i, LOD dağılımını ve toplam üçgen sayısını raporlar.
- Benchmark'ın 50 karakterlik karma LOD senaryosu 5 high + 10 medium + 35 low karakter kullanır; geometri bütçesi 32.160 üçgen/kare olur. Aynı 50 karakterin tamamı high olsaydı 62.400 üçgen/kare olurdu. Bu yalnızca geometri sayısı karşılaştırmasıdır, FPS ölçümü değildir.
- Benchmark sabit FPS eşiği uygulamaz; makine ve Pygame sürümüne bağlı sonuçları ölçer. CI'da bir karelik tanılama çalışmasıyla benchmark'ın çalışması ve üçgen bütçesinin korunması kontrol edilir.
- Yüzey normalinin önceden hesaplanması ve bind-pose mesh cache'i çizim/mesh üretimindeki tekrarları azaltır; ekran dışı culling, uzak NPC LOD ve render verisi cache'i henüz tamamlanmamıştır.

### Yeni otomatik kontroller

- Her üçgen köşesinde 1–2 geçerli eklem etkisi.
- Her köşede toplam skin weight = 1.
- Dirsek pozu değiştiğinde kol yüzeyinin deforme olması.
- Sıfır poz girdisinin bind-pose geometrisini koruması.
- Farklı pozlarda bind-pose geometri cache'inin yeniden kullanılması.
- Üçgen normallerinin sonlu ve normalize olması.
- Sekiz yönde renderer çizim testi.
- Bir karakter için 1.300 üçgen sınırı.

### Bilinen sınırlamalar ve sonraki teknik kapı

- LBS eklenmiş olsa da omuz ve kalça çevresinde gerçek anatomik deformasyon kalitesi statik A-Pose ve testlerle tek başına kanıtlanmış değildir; dirsek hareketi için otomatik geometri testi vardır, görsel ekstrem poz incelemesi beklenir.
- Gövde, kollar, bacaklar ve ayaklar ayrı bağlantılı yüzey adalarıdır; bütün vücut tek kapalı manifold mesh değildir. Omuz ve kalça birleşimleri görsel önizlemede ayrıca incelenmelidir.
- El/parmak anatomisi basit tutulmuştur.
- 8 yönlü statik turnaround ve 1/10/25/50 NPC benchmark çıktısı henüz kullanıcı görsel kabulü veya gerçek hedef makine performans ölçümü değildir.
- Runtime oyun entegrasyonu, dünya konumu, hareket, çarpışma, kamera ve NPC davranışları değiştirilmemiştir.

Aşama 2 henüz kabul edilmedi. Sonraki kapı: CI doğrulaması, sekiz yönlü yeni önizleme, dirsek/omuz/kalça/diz bükülme pozları ve benchmark sonuçlarının incelenmesi. Bunlar tamamlanmadan yeni rig oyun karakterlerine entegre edilmez.


## 15. Aşama 2 — LOD geometri bütçesi ve el yüzeyi — 2026-11-22

- Bilek ile avuç arasında bağlantılı, iki eklem ağırlıklı el yüzeyi eklendi; avuç hacmi ayrı düşük poligon parça olarak kalıyor. Parmak eklemleri rig'de bulunmadığı için parmak animasyonu kapsam dışı.
- Ayaklar topuk → tarak → parmak ucu yüzey zinciri olarak tanımlandı.
- Yüksek, orta ve düşük detay varyantları aynı anatomik landmark ve skinning verisini koruyup halka kenarı/bölüm sayısını azaltıyor.
- Kesin geometri bütçeleri otomatik testte sabitlendi: high 1.248, medium 744, low 528 üçgen/karakter.
- Renderer'a açık `detail_level` seçimi eklendi. Runtime mesafe/piksel boyutu tabanlı otomatik LOD seçimi henüz yapılmadı.
- 50 NPC benchmark senaryosunda 5 high + 10 medium + 35 low dağılımı kullanılıyor; toplam teorik geometri 32.160 üçgen/kare. Bu sayı performans/FPS garantisi değildir.
- Aşama 2 kabul edilmedi; GitHub Actions ve hedef makine benchmark sonuçları doğrulanmalıdır.
