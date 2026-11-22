# Eldoria — Aşama 2: Vücut Anatomisi ve Hacim Prototipi

**Durum:** Parametrik hacim prototipi ve kontrollü oyuncu animasyon entegrasyonu uygulandı; CI başarılı, oyun içi görsel kabul bekliyor.  
**Hedef dal:** `experiment/map-cleanup`  
**Bağımlılık:** Aşama 1 statik iskelet ve A-Pose kabulü

## 1. Amaç

Aşama 1'de kabul edilen 3B anatomik iskeletin üzerine, eklem pozlarını takip eden ve birbirine örtüşen hacimli vücut parçaları kurmak. Bu prototip yalnızca sunum geometrisidir; iskelet, animasyon, runtime dünya konumu ve çarpışma otoritesi değildir.

## 2. İlk uygulama

- `game_ui/world_rendering/humanoid_body_3d.py`: `BodyPartDefinition`, `MeshTriangle`, `HumanoidBodyModel`; ekleme bağlı ellipsoid ve iki eklem arasında uzanan segment mesh üretimi.
- `game_ui/world_rendering/humanoid_body_renderer_3d.py`: mesh üçgenlerini kamera derinliğine göre sıralar, ortografik projeksiyon uygular ve basit yönlü aydınlatma ile Pygame yüzeyine çizer.
- `scripts/preview_humanoid_body_3d.py`: ön, üç çeyrek ve yan görünüş statik önizlemesi.
- `tests/test_game_ui/test_humanoid_body_3d.py`: parça envanteri, deterministik geometri, poz takibi, bilateral parça kapsamı ve geçersiz giriş testleri.

## 3. Model kapsamı

İlk hacim envanteri pelvis, karın, göğüs, boyun, baş, omuz başları, üst kol, dirsek, ön kol, el, uyluk, diz, baldır ve ayak hacimlerini içerir. Gövde ve eklem hacimleri kasıtlı olarak kısmen örtüşür; amaç statik siluette ve poz değişiminde görünür boşlukları azaltmaktır.

## 4. Bilinen sınırlamalar

- Bu sürüm düşük poligonlu ilk hacim prototipidir; anatomik kas grupları ve ince siluet düzeltmeleri tamamlanmamıştır.
- Omuz-göğüs-köprücük kemiği geçişinin görsel kalitesi kullanıcı önizlemesiyle değerlendirilecektir.
- Mesh parçaları ayrı hacimlerdir; henüz tek, sürekli deformasyon yüzeyi değildir. Aşama 2 içinde örtüşme ve çizim sırası iyileştirilecek.
- Baş yüzü, parmaklar, ayak tabanı ayrıntıları ve kıyafet katmanları bu ilk prototipin hedefi değildir.
- Eski 2B renderer ve oyun runtime entegrasyonu değiştirilmemiştir.

## 5. Kabul ölçütleri

1. Ön, yan ve üç çeyrek görünüşlerde insan silueti okunmalı.
2. Omuzlar göğüs kafesine doğal bağlanmalı; üst kol başlangıcında boşluk görünmemeli.
3. Göğüs, karın, bel ve pelvis hacimleri birbirinden ayırt edilebilmeli ve tek gövde gibi birleşmeli.
4. Dirsek, diz, bilek ve ayak bileği birleşimlerinde belirgin kopma olmamalı.
5. Poz değiştiğinde mesh ilgili rig eklemlerini takip etmeli ve rest geometriyi değiştirmemeli.
6. Kullanıcı statik hacim görünümünü kabul etmeli. Animasyon kalitesine ilişkin nihai kabul sonraki aşamalarda yapılacak.

## 6. Sonraki işler

- İlk CI sonuçlarını incele.
- Kullanıcı önizlemesini al; anatomi oranları ve siluet için geri bildirimleri uygula.
- Farklı omuz/dirsek/kalça/diz pozları için debug pozları ve eklem birleşimi kontrolleri ekle.
- Gerekirse gövde hacimlerini daha organik bir yüzey veya örtüşen düşük poligon kabuklarla iyileştir.


## 18. Kontrollü oyuncu animasyon prototipi — 2026-11-22

### Uygulama

- `game_ui/world_rendering/humanoid_body_animation_3d.py` içinde `HumanoidBodyAnimator3D` eklendi. Animator, yürüyüş/koşu fazını duvar saatinden değil, ölçülen gerçek dünya hareket mesafesinden ilerletir.
- Tam gait çevrimi için yürüyüş mesafesi 56 dünya pikseli, koşu mesafesi 84 dünya pikseli olarak tanımlandı. Pozlar sprite cache tekrar kullanımını artırmak amacıyla çevrim başına 8 deterministik örneğe kuantize edilir.
- Hareket mesafesi sıfır olduğunda gait fazı ilerlemez. Yön değişimi fazı sıfırlamaz; idle durumunda yürüyüş pozu çizilmez.
- `HexGameplayView`, yeni 3B body renderer'ı yalnızca oyuncu karakterinde kullanır. NPC'ler mevcut sprite renderer hattında kalır; bu aşamada toplu NPC geçişi yapılmamıştır.
- Oyuncunun katettiği mesafe öncelikle runtime'ın sürekli dünya konumundan salt-okunur biçimde ölçülür. Sürekli konum bulunmayan durumlarda mevcut görsel konum interpolasyonu yedek kaynak olarak kullanılır.
- Ekran yönü, `WorldTransform.unproject_vector` ile rig'in +Y ileri eksenine çevrilir. Renderer'ın üçgen sayısı, ölçülen hareket mesafesi ve sprite cache sayaçları `render_stats` üzerinden izlenebilir.
- Runtime dünya konumu, hareket otoritesi, hız/ivme, çarpışma, NPC itişi, ayrışma, rota ve kamera davranışları bu entegrasyon tarafından devralınmaz veya değiştirilmez.

### Otomatik doğrulama

- Mesafe tabanlı faz ilerlemesi, idle duruş, yön değişiminde fazın korunması, yürüyüş/koşu çevrim mesafesi, kuantize pozların tekrarlanabilirliği ve rig eklem sınırları için testler eklendi.
- Oyun görünüm testleri, oyuncunun 3B body renderer ile çizildiğini, 1.264 üçgenlik high mesh kullanımını, cache kaydını ve hem sürekli runtime hareketinde hem de click-to-move sırasında mesafeye bağlı gait ilerlemesini doğrular.
- GitHub Actions, commit `d40e89910325de6970259ab5c43e36ee5f03509e` üzerinde başarılı tamamlandı: Ubuntu/Windows, Python 3.11/3.12 test matrisindeki dört test işi ve Pygame headless smoke işi başarılıdır. Unit test, pytest, Ruff, benchmark tanılama ve izometrik render smoke adımları geçti.
- CI çalışması: https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/45067478077

### Bilinen sınırlar ve sıradaki kapı

- Bu prototip henüz ayak kilitleme/IK, gerçek stance-swing temas çözümü veya animasyon sırasında kayma kabulünü kanıtlamaz.
- Gait pozları sekiz örneğe kuantize edilmiştir; görsel akıcılık ve cache hit/miss davranışı gerçek oyun ekranında incelenmelidir.
- NPC'ler henüz yeni 3B renderer'a geçirilmemiştir.
- Animasyonlu 1/10/25/50 karakter benchmark'ı henüz yapılmamıştır; önce oyuncu üzerinde görsel kabul, ardından animasyon sırasında cache ve kare süresi ölçümü yapılacaktır.
- Aşama 2 kapatılmamıştır. Kullanıcı oyun ekranında yürüme, durma ve yön değiştirmeyi görsel olarak değerlendirdikten ve animasyonlu performans ölçümü hedefleri karşıladıktan sonra kabul kararı verilecektir.
