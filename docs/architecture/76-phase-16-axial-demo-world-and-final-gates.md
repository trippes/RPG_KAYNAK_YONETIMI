# Aşama 16 — Axial demo dünyası ve son entegrasyon kapıları

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Bu rapor oluşturulurken HEAD: `7823057147cfb4084848cb807e10ace9c9f869e3`

## 1. Bu turda tamamlanan işler

- Eldoria demo paketi için `content/demo_eldoria/hex_maps/starting_valley.json` oluşturuldu.
- Harita schema-v2, pointy-top axial geometri ve 61 geçerli hücre içeriyor.
- Çayır, orman tabanı, açıklık, su ve kaya terrain türleri tanımlandı; su/kaya hücreleri açıkça blocked olarak işaretlendi.
- Harita `manifest.json` içinde `maps: "hex_maps"` ile tanıtıldı. Eski kare harita temizliği tarafından emekli edilmiş `content/demo_eldoria/maps` yolu yeniden kullanılmadı.
- `starter_content.json` içine açık `world.hex_start = {map_id: "starting_valley", q: 0, r: 0}` eklendi.
- Paket sürümü 0.7.1'e yükseltildi.
- `pyproject.toml` wheel paketine axial harita JSON dosyalarını dahil edecek şekilde güncellendi.
- Boş sunum yerleşimi dosyası artık mevcut axial harita kimliğini kullanıyor.
- İçerik yükleyici, başlangıç runtime'ı ve sunum içeriği testleri yeni axial demo sözleşmesine uyarlandı.
- Release verification betiği artık wheel içinden kurulan demo paketinde axial haritanın ve başlangıç koordinatının gerçekten yüklendiğini doğruluyor.
- Eski kare harita sınır denetimi başarılı; yeni axial harita dizini eski kare harita yolu ile karıştırılmıyor.

## 2. Otomatik doğrulama

Workflow run: [44538995615](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44538995615)

- Linux `verify`: başarılı.
- Linux testleri: 2.271 passed, 235 subtests passed.
- Ruff: başarılı.
- Legacy map cleanup boundary: başarılı.
- Compileall, wheel build ve isolated wheel install/content verification: başarılı.
- Windows `verify-windows`: bu rapor hazırlanırken çalışıyordu; sonucu ayrıca teyit edilmelidir.
- 59 pygame `image.tostring` deprecation uyarısı mevcut; test başarısızlığı değildir.

## 3. Hâlâ kapatılmamış entegrasyon kapıları

### 3.1 Fizik gövdesi ve normal hareket akışı

Physics bridge ve actor binding metotları mevcut olsa da normal yön tuşu hareketi ile click-to-move/A* akışı henüz aynı fizik preflight yolunu kullanmıyor.

Bunu güvenli biçimde tamamlamak için oyuncu/NPC collider şekli ve ölçüsü ile statik engellerin shape/transform verisi içerik veya actor metadata'sında açıkça tanımlanmalıdır. Sprite ölçüsünden collider türetilmeyecek; varsayılan yarıçap uydurulmayacak. Bu metadata tanımlandıktan sonra map başına snapshot lifecycle, normal hareket ve A* kenar doğrulaması birlikte bağlanmalıdır.

### 3.2 NPC ve resource demo yerleşimleri

Kullanıcı kararı gereği NPC sağ-tık menüsü boş kalacaktır. Sol tık mevcut diyalog ekranı yönlendirmesini kullanır. Sağ tık için eylem üreticisi/eylem listesi eklenmemiştir; NPC'ler oluşturuldukça role/type bazında doldurulacaktır.

Demo paketinde henüz NPC veya resource-node tanımı/yerleşimi yoktur. NPC diyaloğu, resource seçimi, toplama menzili ve miktar kuralları uydurulmamıştır. Bu içerikler belirlendiğinde mevcut gameplay placement catalog üzerinden eklenecektir.

### 3.3 Manuel Pygame kabul testi

CI headless doğrulamayı yapar; gerçek Pygame penceresinde şu akışlar henüz insan tarafından kabul edilmedi:
- karakter oluşturma sonrası Başlangıç Vadisi'nin görünmesi,
- yön tuşları ve click-to-move,
- blocked su/kaya hücreleri,
- NPC eklendiğinde sol/sağ tıklama,
- ileride authored geçişler eklendiğinde harita geçişi.

## 4. Dal güvenliği

- Yalnızca `experiment/map-cleanup` güncellendi.
- `experiment/hex-world-laboratory` salt kaynak olarak kaldı.
- `demo_eldoria` ve `main` dallarına commit/merge yapılmadı.
- Git karşılaştırmasında `demo_eldoria`, çalışma dalının atasıdır; çalışma dalı demo dalından 389 commit ileridedir ve geride değildir.
- Bu grafik bilgisi tek başına birleştirme onayı değildir. Fizik metadata/entegrasyonu ve manuel Pygame kabul testi kapanmadan çalışma dalı birleştirmeye hazır sayılmaz.

## 5. Sonuç

Axial demo haritası ve açık başlangıç hücresi artık paketin parçasıdır; Linux testleri ve kurulu wheel doğrulaması başarılıdır. Aşama 16'nın tamamı henüz bitmiş değildir. Kalan teknik engel fizik gövde/engel metadata sözleşmesi ve bunun normal hareket/A* akışına bağlanmasıdır. NPC/resource demo içeriği ve gerçek Pygame kabul testi de ayrıca tamamlanmalıdır.
