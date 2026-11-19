# Aşama 16 — Entegrasyon yeniden denetimi

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Denetlenen HEAD: `23252a35e43e727fce85ad19534c0c15d85d777f`  
Durum: **MİMARİ ENTEGRASYON İLERLEMİŞ; OYUN İÇİ TAMAMLAMA İÇİN 3 ANA KAPI AÇIK**

## 1. Denetim yöntemi

Güncel dal başı ve son commitler, Aşama 16 raporları 73–74, Hex gameplay view, MainScreen, InputMapper, actor binding, physics bridge, A* pathfinder, gameplay placement catalog, world initializer ve demo starter content incelendi. Pygame fare olayları ve Python typed/immutable data yaklaşımı Context7 dokümantasyonuyla karşılaştırıldı.

## 2. CI ve dal bütünlüğü

- Güncel çalışma dalı HEAD: `23252a35e43e727fce85ad19534c0c15d85d777f`.
- Workflow run `44536070259`: Linux ve Windows işleri başarılı.
- Her iki platformda da 2.270 test ve 235 subtest geçti.
- Ruff, legacy map cleanup boundary, compileall, wheel build/isolated install ve release verification başarılı.
- Testlerde 59 pygame.image.tostring deprecation warning mevcut; başarısızlık değil, teknik borç.
- `experiment/hex-world-laboratory`: `9e909a45d1b2dca3d0f97986fde9fc2ad832fd26`, değişmedi.
- `main`: `01dd11e17a345624748b724467a09beb8e309ea0`, değişmedi.
- `demo_eldoria`: `7d53d431d5c3639fd95d273de9043b64483a5125`, değişmedi.
- GitHub API dört dal için de `protected: false` bildiriyor. Bu nedenle branch protection teknik olarak aktif değil; yalnızca çalışma prosedürüyle korunuyor.

## 3. Doğrulanan tamamlanmış altyapı

- Eldoria canonical actor kimliği ile HexWorldRuntime mekânsal sahipliği ayrılmış ve bağlanmış.
- NPC ve resource node domain kimlikleri Hex runtime konumlarına bağlanıyor.
- Container carry/contain geçişlerinde mekânsal kayıt ve custody atomikliği/rollback desteği var.
- Market anchor konumu NPC'nin canonical spatial konumundan okunuyor.
- Hex save/load, içerik tabanlı runtime başlatma, authored map transitions, A* ve click-to-move mevcut.
- Sol tık NPC hücresini seçip mevcut DialogueScreen yönlendirmesini tetikliyor.
- Sağ tık NPC'ye bağlı, eylem içermeyen context-menu kabuğunu açıyor; boş hücre sağ tık menüyü kapatıyor.
- Pygame InputMapper sol ve sağ fare düğmelerini ayrı InputState alanlarına dönüştürüyor. Context7 Pygame dokümantasyonu da MOUSEBUTTONDOWN olayının button alanıyla ayrıştırılmasını destekliyor.

## 4. Açık kalan ana entegrasyon kapıları

### A. Fizik hareket akışına bağlı değil

`ActorHexBindingService.move_with_physics` ve `move_to_with_physics` mevcut. Ancak `HexGameplayView` manuel harekette `move`, click-to-move sırasında `move_toward` çağırıyor. Bu yüzden normal oyuncu hareketi ve A* rotası fizik snapshot doğrulamasından geçmiyor.

Eksik bağımlılıklar:
1. Oyuncu ve NPC için content/actor tanımından gelen typed `BodyDefinition`.
2. Landmark ve diğer statik nesneler için açık collider shape/transform metadata'sı.
3. Map başına physics snapshot üretim, saklama ve invalidation lifecycle'ı.
4. A* komşu kenar doğrulamasının aynı fizik kurallarıyla yapılması.

Sprite ölçüsünden collider veya gövde boyutu türetilmeyecek. Mevcut mantıksal blocked-cell ve occupancy denetimleri çalışıyor; bunlar fizik çarpışmasının yerine geçmiyor.

### B. NPC ve resource etkileşimi kısmi

NPC sol/sağ tıklama altyapısı eklendi. Sağ tık menüsü bilerek boş bırakıldı. Bununla birlikte:
- Menü eylemlerini sağlayan NPC role/type tabanlı registry henüz yok.
- Diyalog erişim mesafesi ve mesafe dışı davranış sözleşmesi tanımlanmadı.
- Resource node seçimi ve `G` gather action gameplay view'a bağlanmadı.
- Gathering range ve quantity/UI akışı tanımlanmadı.

Bunlar tasarım kararı gerektiriyor; varsayımsal mesafe, miktar veya tuş davranışı eklenmemeli.

### C. Yeni axial world content yok

`content/demo_eldoria/starter_content.json` içinde `world.hex_start` bulunmuyor. İçerik paketi için axial map definition ve açık oyuncu başlangıç hücresi de eklenmiş değil. Bu nedenle initializer doğru biçimde runtime başlatmıyor ve MainScreen hazırlık yüzeyinde kalıyor.

Eksik bağımlılıklar:
1. Onaylı schema-v2 axial HexMapDefinition içeriği.
2. Harita sayısı birden fazlaysa uyumlu WorldMapDefinition/topology.
3. `world.hex_start = {map_id, q, r}` açık başlangıç konumu.
4. İstenilen başlangıç NPC/resource/container placement kayıtları.
5. Bu içeriklerle gerçek Pygame manuel kabul testi.

Lab demo haritaları ve senaryoları otomatik olarak taşınmamalı; yeni dünya içeriği Eldoria için ayrıca yazılmalı.

## 5. Ek teknik gözlem

NPC tıklama testi şu anda HexGameplayView davranışını ve MainScreen'in seçili NPC kimliğini diyalog yönlendirmesine aktarmasını doğruluyor. Gerçek oyun içi manuel kabul henüz mümkün değil; çünkü demo pakette axial dünya başlangıç verisi yok. Sağ tık menüsü yalnızca görsel/kimlik kabuğudur, menü etkileşimi veya aksiyon yürütmesi değildir.

Pygame event queue her frame işlenmeye devam etmeli; mevcut InputMapper event listesini tek seferde InputState'e dönüştürüyor ve fare düğmelerini ayrı alanlarda tutuyor. Context7 incelemesi bu yaklaşımın event tabanlı fare input'u için uygun olduğunu doğruladı.

## 6. Önerilen devam sırası

1. Önce yeni axial demo world içeriği ve açık başlangıç koordinatı için içerik sözleşmesini oluşturup onaylamak.
2. Bu içerikle gerçek harita üzerinde hareket, click-to-move, NPC sol/sağ tık ve harita geçişlerini manuel test etmek.
3. Ayrı teknik tasarım olarak typed actor body ve statik obstacle metadata sözleşmesini tamamlamak; ardından normal hareket + A* physics entegrasyonunu yapmak.
4. NPC aksiyon registry ve resource gathering UI'sini ancak NPC/resource içerik kuralları belirlendikten sonra bağlamak.
5. Her aşamada test, Ruff, legacy boundary ve Linux/Windows CI çalıştırmak.

## 7. Sonuç

Aşama 16'ın önemli mimari köprüleri ve otomatik doğrulaması başarılıdır. Fakat **tam oynanabilir entegrasyon henüz tamamlanmamıştır**. En kritik engel yeni axial dünya içeriğinin olmamasıdır; bunun ardından physics wiring ve NPC/resource etkileşim sözleşmeleri kapanmalıdır.

Kapsam kuralı sürüyor: yalnızca `experiment/map-cleanup` üzerinde çalışma; laboratuvar dalını salt kaynak olarak kullan; `main` ve `demo_eldoria` dallarına dokunma; eski kare harita sistemini geri getirme.
