Başlangıç İçeriği Veri Sözleşmesi

Oynanış kuralları application/domain katmanında kalır. Başlangıç dünyası, karakter oluşturma ve açılış diyaloğu gibi ilk oyun deneyimine ait tanımlar veri dosyasından yüklenir.

İçerik paketi

Kaynak dizin:

content/demo_eldoria/

Paket manifesti:

content/demo_eldoria/manifest.json

Başlangıç dünyası ve karakter oluşturma tanımları:

content/demo_eldoria/starter_content.json

NPC tanımları:

content/demo_eldoria/npcs.json

Yükleme giriş noktası:

from application.content_pack import load_starter_content, load_npc_definitions, populate_opening_content

"load_starter_content()" başlangıç dünyası tanımını yükler ve doğrular.

"load_npc_definitions()" NPC kayıtlarını yükler, kimlikleri ve alanları doğrular.

"populate_opening_content()" açılış aşamasında etkinleştirilen NPC kayıtlarını yeni oyun oturumuna ekler. Oynanış aşamasındaki NPC kayıtları kaynaklar ve pazarlar hazırlanırken etkinleştirilir.

İçerik kapsamı

Başlangıç paketi şu öğeleri kapsar:

- Başlangıç dünyası ve harita bağlantıları
- Oyuncu karakterinin başlangıç tanımı
- Başlangıç lokasyonları
- NPC tanımları ayrı "npcs.json" dosyasında; açılış ve oynanış aşamasına göre yüklenir
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

Yeni NPC kayıtları mevcut "npcs.json" veri sözleşmesine eklenir. Görevler, diyaloglar, kaynaklar, pazarlar ve karşılaşmalar da aynı paket manifesti üzerinden ayrı veri dosyalarına ayrılacaktır.

Bu paketler başlangıç içeriğine bağımlı olmak zorunda değildir. Her paket kendi kimliklerini, sürümünü ve doğrulama kurallarını taşımalıdır.

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
