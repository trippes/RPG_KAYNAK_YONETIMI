Başlangıç İçeriği Veri Sözleşmesi

Oynanış kuralları application/domain katmanında kalır. Başlangıç dünyası, karakter oluşturma ve açılış diyaloğu gibi ilk oyun deneyimine ait tanımlar veri dosyasından yüklenir.

İçerik paketi

İçerik kök dizini:

content/

Etkin paket seçimi:

content/active_package.json

Varsayılan paket dizini bu ayar dosyasında seçilir. Çalıştırırken `--content-package <paket-dizini>` parametresiyle başka bir paket de seçilebilir.

Demo paket dizini:

content/demo_eldoria/

Paket manifesti:

content/demo_eldoria/manifest.json

Harita klasörü ve harita JSON sözleşmesi:

content/demo_eldoria/maps/*.json

docs/content/map-authoring.md

Başlangıç dünyası ve karakter oluşturma tanımları:

content/demo_eldoria/starter_content.json

NPC tanımları:

content/demo_eldoria/npcs.json

Görevler, hedefler, ödüller ve görev diyalogları:

content/demo_eldoria/quests.json

Yükleme giriş noktası:

from application.content_pack import load_starter_content, load_npc_definitions, populate_opening_content

"load_starter_content()" başlangıç dünyası tanımını yükler ve doğrular.

"load_npc_definitions()" NPC kayıtlarını yükler, kimlikleri ve alanları doğrular.

"load_quest_definitions()" görev, hedef, ödül ve görev diyaloğu kayıtlarını yükler ve doğrular.

"load_resource_definitions()" kaynak düğümlerini, miktarlarını ve toplama sürelerini yükler.

"load_character_definitions()" ırk, sınıf, nitelik değiştiricileri ve yetenek tanımlarını yükler.

"populate_opening_content()" açılış aşamasında etkinleştirilen NPC kayıtlarını yeni oyun oturumuna ekler. Oynanış aşamasındaki NPC kayıtları kaynaklar ve pazarlar hazırlanırken etkinleştirilir.

İçerik kapsamı

Başlangıç paketi şu öğeleri kapsar:

- Başlangıç dünyasının kimliği ve başlangıç ayarları; yerel haritalar, dünya konumları ve harita geçişleri ayrı `maps/*.json` tanımlarında tutulur.
- Oyuncu karakterinin başlangıç tanımı
- Harita JSON dosyalarından otomatik keşfedilen başlangıç lokasyonları
- NPC tanımları ayrı "npcs.json" dosyasında; açılış ve oynanış aşamasına göre yüklenir
- Görevler, hedefler, ödüller ve görev diyalogları ayrı "quests.json" dosyasında tanımlanır
- Kaynak düğümleri ve toplama süreleri ayrı "resources.json" dosyasında tanımlanır
- Irk, sınıf ve yetenek tanımları ayrı "characters.json" dosyasında tutulur
- Oyuncu envanteri/hesabı, başlangıç ekonomisi ve tüketilebilir eşya etkileri "gameplay_rules.json" dosyasında tanımlanır
- Açılış diyaloğu
- Karakter oluşturma için gerekli tanımlar

Başlangıç paketi, görev zincirleri, pazar senaryoları, savaş karşılaşmaları ve diğer oynanış testlerinden ayrı tutulur.

Sürümleme ve doğrulama

- İçerik tanımı "schema_version" taşır.
- Desteklenmeyen gelecek sürümler reddedilir.
- Zorunlu bölümler eksikse içerik runtime'a alınmaz.
- Kimlikler içerik tanımı içindeki "ids" alanından alınır.
- İçerik tanımı Core canonical state'e eklenmez.
- Oyun kuralları veri dosyasına taşınmaz; ilgili domain ve application katmanlarında kalır.

Gelecekteki içerik paketleri

Yeni NPC, kaynak ve görev kayıtları ilgili JSON sözleşmelerine eklenir; pazar tanımları başlangıç/paket verisinde NPC ve harita kimlikleriyle ilişkilendirilir. Haritalar manifestte bir klasör olarak tanımlanır ve bu klasördeki bütün JSON dosyaları otomatik keşfedilir. Harita dosyalarını tek tek manifest'e eklemek veya yeni bir harita için Python kodu yazmak gerekmez.

Her paket kendi kimliğini, sürümünü ve doğrulama kurallarını taşır. Harita geçişleri, koordinatlar, NPC/kaynak/görev/pazar ilişkileri ve kayıt uyumluluğu için ayrıntılı sözleşme `docs/content/map-authoring.md` belgesindedir.

NPC veri sözleşmesi

Her NPC kaydı "npcs.json" içindeki "npcs" listesinde bulunur:

- "id": kayıtlar ve görev ilişkileri için kararlı, benzersiz kimlik.
- "name": oyuncuya gösterilecek ad.
- "role": NPC rolü; davranışın kendisini çalıştıran bir kod değildir.
- "faction_ids": NPC'nin bağlı olduğu fraksiyon kimlikleri.
- "location_id": başlangıç dünyasındaki konum kimliği.
- "position": konum içindeki iki tam sayı koordinatı.
- "load_phase": NPC'nin etkinleştirileceği genel yaşam döngüsü aşaması ("opening" veya "gameplay").
- "dialogue_id": varsa NPC ile ilişkili diyalog tanımının kimliği.

NPC kayıtları tek bir genel kayıt işleyicisiyle yüklenir. Yeni NPC eklemek için Python modülü, GameWindow veya GameplayService üzerinde NPC'ye özel kod yazılmaz. "load_phase" yalnızca yükleme zamanını belirler; NPC'nin görev verip vermediği veya pazar işletip işletmediği başka içerik ilişkileriyle tanımlanır.

Görev veri sözleşmesi

Her görev kaydı "quests.json" içindeki "quests" listesinde bulunur:

- "id", "title" ve "giver_npc_id": kararlı görev kimliği, görünen başlık ve görev veren NPC ilişkisi.
- "sequential_objectives": zorunlu hedeflerin sırayla ilerleyip ilerlemeyeceği.
- "objectives": hedef kimliği, açıklaması, türü, hedef kimliği, gerekli miktarı ve isteğe bağlılık durumu.
- "reward": deneyim, para, eşya ve itibar ödülleri.
- "dialogue": görev veren NPC'nin düğüm ve seçeneklerden oluşan diyalog ağı.
- Diyalog eylemleri yalnızca güvenli genel eylem sözleşmelerini kullanır ("accept_quest", "deliver_resource"); içerik JSON'u Python kodu çalıştıramaz.

Yeni görevler bu veri sözleşmesiyle eklenir. Görev tanımı, hedefler, ödüller veya diyalog metinleri için yeni Python görev modülü ya da GameWindow/GameplayService içinde göreve özel kayıt kodu gerekmez. Yeni bir oyun mekaniği gerektiğinde motorun genel yeteneği bir kez geliştirilir; o mekaniği kullanan yeni görevler veriyle tanımlanır.

Kaynak düğümü veri sözleşmesi

"resources.json" içindeki her düğüm; kendi kimliğini, bağlandığı konum ve landmark kimliğini, kaynak türünü, birimini, başlangıç miktarını, kapasitesini, yenilenme oranını ve "gathering_duration_ticks" değerini taşır. Yükleyici landmark ilişkisinin geçerli olduğunu doğrular. Motor, landmark adından veya kimliğinden kaynak türü tahmin etmez.

Karakter tanımı veri sözleşmesi

"characters.json" ırkları, sınıfları ve bunların yeteneklerini tanımlar. Başlangıç karakterinin hangi ırk ve sınıfı kullanacağı "starter_content.json" içinde yalnızca kimlik olarak seçilir. Yeni ırk veya sınıf eklemek için CharacterFactory ya da ana oyun dosyaları değiştirilmez.

Paket seçimi

Motor, etkin paket kimliğini Python kodunda sabitlemez. "active_package.json" varsayılan paket dizinini belirler; çalıştırma sırasında "content_package_path" parametresiyle geçici/alternatif paket seçilebilir. Paket dosyalarının güvenli JSON yüklemesi ve manifest doğrulaması ortak ContentPackageLoader tarafından yapılır.

Eski kayıt geçişi

Sosyal kayıtlarda NPC konumu bulunmayan veya eski varsayılan (0, 0) konumunda kalan kayıtlar, "migrate_save_data" geçişinde etkin içerik paketinin NPC koordinatlarıyla tamamlanır. Geçiş NPC kimliğine özel bir koşul içermez; mevcut konumları olan kayıtları değiştirmez. Yeni paketlerdeki NPC'ler için ayrıca GameApplication içine kayıt düzeltmesi eklenmesi gerekmez.

Başlangıç kimlikleri

Motorun StarterContentIds alanları demo kimliklerini varsayılan olarak taşımaz. Paket içindeki "ids" alanından çözülür; isteğe bağlı çağrı zamanı geçersiz kılmaları ayrıca desteklenir.

Oynanış kuralları veri sözleşmesi

"gameplay_rules.json" oyuncunun aktör, envanter ve ekonomi hesabı kimliklerini; başlangıç para birimi ve miktarını; tüketilebilir kaynakların etkilerini tanımlar. GameplayService bu kayıtları genel yapılandırma olarak alır. Yeni bir iyileştirici yiyecek eklemek için tüketilebilir tanımına yeni bir kayıt eklenir; ekmek/su gibi içerik kimlikleri ve değerleri servis koduna gömülü değildir.
