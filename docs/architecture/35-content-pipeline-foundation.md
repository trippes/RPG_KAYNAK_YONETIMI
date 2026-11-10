# İçerik Hattı — Editör Uyumluluğu ve Veri Sözleşmesi

## Karar

Oyun çekirdeği ve oyuncu arayüzü uygulama kodunda kalır. Oyunun dünyasını
oluşturan içerikler (NPC, item, quest, enemy, world/map, location, structure,
dialogue ve gelecekte eklenecek içerik türleri) harici, sürümlenmiş içerik
paketlerinden yüklenir.

RPG Content Editor bu paketleri oluşturur, düzenler, doğrular, etkinleştirir,
devre dışı bırakır ve kaldırır. Oyun motoru editörün kendisine bağımlı olmaz;
yalnızca yayımlanmış içerik veri sözleşmesini ve runtime adaptörlerini bilir.

## Katmanlar

1. Engine ve UI: Kurallar, simülasyon, rendering, input ve pencere sistemi.
   Bunlar editör içeriği değildir.
2. Content catalog: Paket manifestlerini okur, sürüm ve bağımlılıkları
   doğrular, kayıtları tür + ID anahtarıyla indeksler ve referans bütünlüğünü
   denetler.
3. Runtime adapters: Doğrulanmış NPC/item/quest/enemy/map kayıtlarını
   mevcut domain ve application servislerine dönüştürür. Her domain sisteminin
   kendi davranışını korur.
4. Content Editor: Aynı şemayı üretir ve düzenler; oyun kodunu üretmez veya
   değiştirmez.

## Paket sözleşmesi — schema v1

Catalog root, manifest.json içerir. Bu dosya schema_version ve paket
listesini taşır. Her paket girdisi id, manifest ve isteğe bağlı enabled
alanına sahiptir.

Paket manifesti schema_version, id, version, dependencies ve files
alanlarını taşır. files girdileri kind ve pakete göre göreli path alanlarıyla
bir JSON kaydını tanımlar. Her kayıt benzersiz bir id taşır.
İsteğe bağlı references alanı kind + id çiftlerinden oluşur.

Content kind sabit enum değildir. Böylece yeni içerik türleri catalog katmanını
değiştirmeden eklenebilir; ilgili runtime adapter ve şema doğrulaması ayrıca
geliştirilir. ID'ler tür kapsamında benzersizdir. Referanslar tür + ID ile
çözülür.

Paketler manifestteki sırayı korur; bağımlılıklar önce yüklenir. Devre dışı
paketler kataloğa girmez. Etkin bir paketin bağımlılığı devre dışıysa, eksikse
veya döngü oluşturuyorsa yükleme reddedilir. Kayıt yolları catalog root dışına
çıkamaz. Böylece paket kaldırma/devre dışı bırakma işlemleri açık ve
doğrulanabilir olur.

## Kayıt ve içerik yaşam döngüsü

Oyuncu kayıtları içerik tanımlarının kopyası değildir. Save dosyaları kalıcı
content ID'leri ve oyuncu ilerlemesi gibi runtime state'i saklar. İçerik
paketleri ayrı sürümlenir. Paket kaldırma veya ID değiştirme işlemleri,
kayıt uyumluluğu/migration politikası olmadan sessizce yapılmaz.

Bir içerik referansını kaldırmak isteyen editör önce bağımlı kayıtları bulmalı
ve doğrulama hatalarını göstermelidir. İçerik silme, referansları sessizce
boş bırakmamalıdır. Eski kayıtların ihtiyaç duyduğu içerik için ileride
deprecation/tombstone ve migration politikası tanımlanacaktır.

## Mevcut starter içerik için geçiş kuralı

data/starter_content.json ve application/content_pack.py şu anda açılış
prototipini besleyen özel bir starter-content yoludur. Bu yol henüz genel
content catalog/runtime adapter hattına taşınmış değildir. UI görsel testleri
tamamlanana kadar demo içerik korunur; bu mimari hazırlık çalışması demo
içeriği silmez ve mevcut başlangıç akışını değiştirmez.

UI testlerinden sonra starter/demo verileri ayrı bir development/test pack'e
taşınacak, runtime içerik kodundaki sabit ID ve demo varsayımları temizlenecek.
Sonraki adımda starter loader genel catalog ve domain adapter'larına geçirilir.
Demo paketinin production içerik listesine dahil olması varsayılan olmayacaktır.

## Şimdiki uygulama kapsamı

content paketi şu anda yalnızca catalog/manifest yükleme, paket etkinleştirme,
bağımlılık sıralaması, type-scoped ID tekilliği, path güvenliği ve açık
cross-content referans doğrulaması sağlar. NPC/item/quest/enemy/map kayıtlarını
runtime nesnelerine dönüştürme henüz kapsam dışıdır. Bu ayrım bilinçlidir:
mevcut gameplay sistemleri yeniden yazılmadan, adaptörler kademeli eklenir.

## Kabul kriterleri

- Catalog ve pack schema sürümleri açıkça doğrulanır.
- Paket bağımlılıkları ve döngüler güvenli biçimde denetlenir.
- İçerik türleri genişletilebilir; ID'ler tür kapsamında benzersizdir.
- Referans hedefleri etkin paketler içinde bulunmalıdır.
- Catalog root dışına çıkan dosya yolları reddedilir.
- Demo içeriği bu altyapı çalışmasında silinmez.
- Runtime adapter'ları eklenene kadar mevcut starter akışı değişmeden kalır.
