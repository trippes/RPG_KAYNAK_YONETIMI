# İçerik Odaklı NPC ve Görev Mimarisi

Durum: Mimari kural
Kapsam: NPC kayıtları, diyaloglar, görev tanımları, görev zincirleri, görev ilerlemesi, ödüller, kayıt/yükleme ve görev günlüğü.
Temel ilke: Yeni oyun içeriği eklemek için mevcut motor, servis veya UI kodunu değiştirmek gerekmemelidir.

## 1. Sorumluluk sınırları

- Oyun motoru genel mekanikleri uygular: görev başlatma, koşul değerlendirme, olayla hedef ilerletme, tamamlama, başarısızlık, ödül dağıtımı ve kayıt/yükleme.
- İçerik paketleri NPC, diyalog, görev, görev zinciri, hedef, ödül, koşul ve bunların ilişkilerini tanımlar.
- UI yalnızca mevcut oyun durumunu görüntüler ve kullanıcı girdisini genel uygulama servislerine iletir. UI içinde NPC veya görev kimliği sabitlenmez.
- Demo içerikleri motorun varsayılanı veya zorunlu sözleşmesi değildir. Silinebilir, değiştirilebilir ve başka içerik paketleriyle değiştirilebilir.
- İçerik verisi doğrudan çalıştırılabilir Python kodu veya keyfî fonksiyon içermez. Tanımlı, doğrulanan eylem ve olay türleri kullanılır.

## 2. NPC kuralları

- Her NPC, içerik paketi kapsamında benzersiz ve kalıcı bir `npc_id` taşır. Görünen ad, rol, konum, fraksiyon, diyalog bağlantısı ve diğer özellikler veridir.
- NPC'nin görev vermesi zorunlu değildir. Bir NPC sıfır, bir veya birden fazla görevle ilişkili olabilir.
- Görev veren NPC ilişkisi tek yönlü ve opsiyonel metadata olarak görev tanımında tutulabilir: `giver_npc_id: string | null`.
- NPC kimlikleri görev ekranına, görev motoruna veya genel servis akışına gömülmez.
- NPC silinmiş, devre dışı veya içerik paketinde bulunmuyor olsa bile eski kayıttaki görev ilerlemesi bozulmamalıdır. UI çözümlenemeyen NPC için güvenli bir genel ifade gösterir; kimliği oyuncuya ham biçimde göstermez.
- NPC'ler arası ilişkiler, diyaloglar ve görev bağlantıları ayrı veri ilişkileridir; bir NPC'nin rolünden görev davranışı çıkarılmaz.

## 3. Görev tanımı kuralları

Her görev, en azından şu kavramları içerik düzeyinde tanımlayabilir:

- Benzersiz `quest_id`, oyuncuya gösterilecek başlık ve açıklama.
- Bir veya daha fazla hedef; her hedefin benzersiz `objective_id`, açıklaması, olay türü, isteğe bağlı hedef kimliği, gereken miktarı ve isteğe bağlı olup olmadığı.
- Ön koşullar ve görünürlük/kabul koşulları.
- Ödüller: deneyim, para, eşya, itibar ve ileride eklenecek genişletilebilir ödül türleri.
- Opsiyonel görev veren NPC, görev zinciri/grup kimliği, etiketler, önem/öncelik ve içerik sürümü gibi metadata.
- Tek seferlik veya tekrar edilebilir olma kuralı; tekrar edilebilir görevlerde sıfırlama ve ödül politikası açıkça tanımlanır.

Görev tanımı, görev ekranının ihtiyaçlarına göre şekillenmez. Görev ekranı bu verileri genel bir görünüm modeliyle sunar.

## 4. Görev ağaçları ve dallanma

- Görev zincirleri doğrusal olmak zorunda değildir. Bir görev birden fazla sonraki görevi açabilir; bir görev birden fazla önceki görevin tamamlanmasını isteyebilir.
- Zincir ilişkileri görev nesnesinin içine sabitlenmiş özel alanlar veya Python if/else bloklarıyla değil, içerik verisindeki bağlantı kayıtlarıyla tanımlanır.
- Bağlantılar en azından kaynak görev, hedef görev ve geçiş koşulunu belirtir. İhtiyaç hâlinde ilişki türü (ardıl, alternatif dal, yan görev, kilit açma) ve dal grubu da veri olarak tutulur.
- Koşullar AND/OR/NOT bileşimlerini destekleyecek şekilde genişletilebilir. Mevcut koşul sistemi korunur; yeni koşul türleri merkezi ve geriye uyumlu biçimde eklenir.
- Görev zinciri doğrulaması eksik görev referanslarını, yinelenen bağlantıları ve döngüleri tespit eder. Döngü yalnızca açıkça desteklenen tekrar mekanizması üzerinden kurulabilir.
- Bir dalın seçilmesi diğer dalları otomatik olarak başarısız saymaz. Bu davranış içerik tanımında açıkça belirtilmelidir.
- Ana görev, yan görev ve bağımsız görev ayrımı içerik etiketi/metadata ile yapılır; motor veya UI belirli görev adlarını tanımaz.
- Bir görevin NPC tarafından verilmesi, zincirin parçası olması veya bir başka görevi açması zorunlu değildir.

## 5. Diyalog ve görev etkileşimi

- NPC ile diyalog bağlantısı NPC içerik tanımında yapılır; her NPC'nin kendine ait diyalog ağacı olabilir.
- Diyalog seçeneklerinin görünürlüğü koşullara bağlıdır. Görev durumu, envanter, itibar, dünya bayrakları ve hedef ilerlemesi koşullarda kullanılabilir.
- Diyalog seçenekleri görev kimliklerine özel sabit servis metotlarını çağırmaz. Bunun yerine doğrulanmış genel eylem kayıtları kullanılır. İlk genel eylemler; görevi kabul etme, görevi teslim etme/tamamlama, bayrak değiştirme, itibar değiştirme ve genel dünya olayı üretme olabilir.
- Eylem kayıtları parametre alabilir (ör. `quest_id`, teslim edilecek gereksinimler); parametreler içerik yüklenirken doğrulanır.
- Eylem sistemi güvenli bir kayıtlı işleyici kataloğu kullanır. İçerik dosyaları keyfî Python fonksiyonu veya metot adı çalıştıramaz.
- NPC konuşması görev başlatmak için tek yol değildir. Keşif, kitap okuma, eşya kullanma, bölgeye girme veya dünya olayı da görev başlatabilir/ilerletebilir.

## 6. Görev ilerlemesi ve olay sistemi

- Hedef ilerlemesi, genel oyun olaylarına abone olarak gerçekleşir: toplama, öldürme, konuşma, konuma ulaşma, eşya teslimi, üretim, keşif ve içerik tarafından tanımlanan özel olaylar.
- Olaylar kararlı bir olay türü ve bağlam verisi taşır. Hedefler bu olayları tür ve isteğe bağlı filtrelerle eşleştirir.
- Görev ekranı ilerlemeyi kendisi hesaplamaz veya görev durumunu değiştirmez; gerçek QuestLog ve hedef ilerlemesini okur.
- Sıralı hedefler, isteğe bağlı hedefler ve paralel hedefler görev tanımındaki kurallara göre çalışır.
- Ödül yalnızca tanımlı tamamlanma politikasına göre bir kez verilir; kayıt/yükleme veya UI yenilemesi ödülü tekrar dağıtmamalıdır.

## 7. Görev günlüğü UI sözleşmesi

- Görev günlüğü aktif oturumun güncel QuestLog verisini okur; açıldığı anda kopyalanmış/sabitlenmiş görev listesine güvenmez.
- Kategoriler görev durumlarından türetilir. Yeni görev türü veya yeni NPC eklemek için QuestLogScreen değişmez.
- Görev ayrıntıları başlık, açıklama, veren NPC (varsa), hedefler, ilerleme, durum, ödül ve zincir ilişkilerini mevcut veriden üretir.
- NPC adı, NPC kayıtlarından `giver_npc_id` ile çözülür. Kayıt bulunamazsa güvenli fallback gösterilir.
- UI, marangoz/kervancı/demirci gibi demo kimliklerini veya görev başlıklarını içermez.
- Pencere/WindowManager mimarisi bu veri modeli için değiştirilmez. Görev günlüğü mevcut pencere sistemi içinde kalır.

## 8. Kayıt, yükleme ve geriye uyumluluk

- Kayıt dosyası oyuncu ilerlemesini ve gerekli içerik referanslarını saklar; içerik tanımlarının tek doğruluk kaynağı içerik paketidir.
- İsteğe bağlı yeni alanlar eski kayıtlarda bulunmayabilir. Eksik alanlar tanımlı varsayılanlarla (ör. `giver_npc_id = null`) yüklenir.
- Bilinmeyen veya artık pakette bulunmayan görev kayıtları, mevcut kayıt politikası çerçevesinde ilerlemeyi kaybetmeden korunur.
- İçerik tanımı ile kayıtlı ilerleme ayrıdır: içerik güncellenirken oyuncu ilerlemesi yalnızca açıkça tanımlanmış migration kurallarıyla taşınır.
- Şema değişiklikleri sürümlenir; eski sürümler için kontrollü migration ve test sağlanır.
- NPC'nin adı değişse bile kararlı kimliği değişmez. Kimlik değişikliği gerekiyorsa alias/migration eşlemesi tanımlanır.

## 9. İçerik doğrulama ve modülerlik

- İçerik yükleme aşamasında benzersiz kimlikler, zorunlu alanlar, referans bütünlüğü, koşul türleri, eylem parametreleri, görev ağacı döngüleri ve ödül değerleri doğrulanır.
- Hatalı içerik, oyunun ortasında sessizce bozulmak yerine anlaşılır bir ContentDefinitionError ile reddedilir.
- Bir içerik paketi NPC, diyalog, görev ve görev zinciri tanımlarını ayrı dosyalarda veya tek pakette taşıyabilir. Dosya düzeni motor sözleşmesini değiştirmez.
- İçerik paketleri birbirinden bağımsız eklenip çıkarılabilir. Paketler arası referanslar açıkça bildirilir ve doğrulanır.
- Yeni içerik eklemek için yalnızca içerik verisi ve gerekirse mevcut genel eylem/olay türlerinin kullanılması yeterli olmalıdır. Yeni mekanik gerekiyorsa genel mekanik bir kez motora eklenir; sonrasında içerik verisiyle tekrar kullanılır.

## 10. Uygulama sırası ve kapsam koruması

1. Mevcut Quest/NPC/diyalog ve kayıt sözleşmelerini koruyarak opsiyonel metadata ve eski kayıt uyumluluğu.
2. Quest giver gösteriminin genel NPC kayıtlarından çözülmesi.
3. Görev zinciri/bağlantı veri modeli ve DAG doğrulaması.
4. Genel görev eylemleri ve olay tabanlı ilerleme; demo görevlerine özel servis metotlarının içerik tanımlarına taşınması.
5. Çoklu NPC/görev/diyalog içerik paketleri ve içerik doğrulama.
6. Görev günlüğünde zincir/ön koşul/veren ilişkilerinin veriye dayalı gösterimi.

Her aşama ayrı test ve küçük commitlerle ilerler. Görev sistemi zaten oyun içinde doğrulandığı için bu çalışma mevcut çalışan davranışları gereksiz yere yeniden yazmaz. WindowManager, ana dünya ekranı ve pencere etkileşim modeli korunur.


## 11. Görev ağacı çalışma zamanı kuralları

- Görev ağacı yalnızca içerik tanımlarındaki kararlı görev kimliklerini ve bağlantıları bilir. NPC, görev başlığı, UI veya demo kimliği içermez.
- Bağlantı türü `UNLOCKS` veya `SIDE` ise hedef görev, bu bağlantıların tüm kaynak görevleri tamamlandığında açılır (AND).
- Aynı `branch_group` içindeki `ALTERNATIVE` giriş bağlantıları OR olarak değerlendirilir; gruptaki tamamlanmış ve seçilmiş yollardan en az biri hedefi açar.
- Bir kaynak görevden aynı dal grubunda birden fazla alternatif hedef çıkıyorsa kaynak tamamlandıktan sonra oyuncu açıkça bir hedef seçer. Seçim yapılmadan hiçbir alternatif hedef açılmaz.
- Tek hedefli alternatif bağlantı seçim istemez; tamamlanan kaynak görev hedefi açar.
- Bir hedefte birden fazla normal giriş bağlantısı ile alternatif gruplar birlikte varsa, tüm normal bağlantılar ve her alternatif grup kendi kuralı doğrultusunda sağlanmalıdır.
- Birleşme noktası için farklı yollardan herhangi birinin yeterli olması isteniyorsa, bu yollar aynı alternatif giriş grubuna bağlanır. Tüm yolların tamamlanması isteniyorsa normal `UNLOCKS` bağlantıları kullanılır.
- Bağlantı kuralları görev tanımının kendi ön koşullarından ayrıdır. Bir görev ancak hem grafik bağlantıları hem de kendi koşul ifadesi doğruysa başlatılabilir.
- Ön koşul ifadeleri `AllConditions` (AND), `AnyConditions` (OR) ve `NotCondition` (NOT) ile iç içe kurulabilir. Atomik koşullar bayrak, itibar, eşya, hedef ilerlemesi ve görev durumunu okuyabilir.
- Kök görevler (giriş bağlantısı olmayanlar) grafik bakımından açıktır; kendi görev koşulları yine uygulanır.
- Oyuncunun alternatif dal seçimi içerik verisi değildir. `QuestGraphProgress` içinde oyuncu ilerlemesi olarak tutulur; dışa/içe aktarılabilir ve yüklenirken mevcut grafik tanımıyla doğrulanır.
- Seçilmiş dal değiştirilemez. Farklı bir hikâye sonucu için içerik açıkça ayrı bir yeniden seçim/geri alma mekaniği tanımlamalıdır.
- `SessionBundle` görev grafiği tanımını ve oyuncu dal ilerlemesini taşır. İçerik paketi her görevi `GameplayService.register_quest_definition()` ile günlüğe tanıtır; ardından `register_quest_graph()` içerik tanımını oturuma bağlar; `available_quests()`, `start_quest()` ve `choose_quest_branch()` aynı çalışma zamanı durumunu kullanır. Görev günlüğü tamamlanan bir görevin çoklu alternatif dallarını gösterir ve oyuncu seçimini doğrudan çalışma zamanına iletir. Dal seçimi oyun kaydına `quest_graph_progress` alanında yazılır. Grafik içeriği save dosyasına kopyalanmaz; yükleme sırasında içerik yeniden kaydedildiğinde bekleyen seçimler bu grafik tanımıyla doğrulanır. Eski kayıtlarda bu alan yoksa boş ilerleme ile devam edilir.

