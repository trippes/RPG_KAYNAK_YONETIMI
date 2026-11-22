# Eldoria — Aşama 2: Vücut Anatomisi ve Hacim Prototipi

**Durum:** İlk parametrik hacim prototipi oluşturuldu; CI ve görsel kabul bekliyor.  
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
