Başlangıç İçeriği Veri Sözleşmesi

Oynanış kuralları application/domain katmanında kalır. Başlangıç dünyası, karakter oluşturma ve açılış diyaloğu gibi ilk oyun deneyimine ait tanımlar veri dosyasından yüklenir.

Başlangıç içerik dosyası

Kaynak dosya:

data/starter_content.json

Yükleme giriş noktası:

from application.content_pack import load_starter_content, populate_opening_content

"load_starter_content()" başlangıç içerik tanımını yükler ve doğrular.

"populate_opening_content()" doğrulanmış başlangıç içeriğini yeni oyun oturumuna kaydeder.

İçerik kapsamı

Başlangıç paketi şu öğeleri kapsar:

- Başlangıç dünyası ve harita bağlantıları
- Oyuncu karakterinin başlangıç tanımı
- Başlangıç lokasyonları
- Açılışta karşılaşılan NPC
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

Yeni görevler, NPC'ler, diyaloglar, kaynaklar, pazarlar ve karşılaşmalar ayrı içerik paketleri olarak tasarlanacaktır.

Bu paketler başlangıç içeriğine bağımlı olmak zorunda değildir. Her paket kendi kimliklerini, sürümünü ve doğrulama kurallarını taşımalıdır.