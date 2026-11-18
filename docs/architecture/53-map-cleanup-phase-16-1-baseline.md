# Harita Sistemi Temizliği — Aşama 16.1 Baseline ve Characterization Raporu

| Alan | Değer |
|---|---|
| Çalışma dalı | `experiment/map-cleanup` |
| İncelenen HEAD | `1705497305339675df25928c7272eb9b10aba7a2` |
| Kaynak dal başlangıcı | `demo_eldoria` @ `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Aşama | 16.1 — teknik baseline tamamlandı; manuel görsel doğrulama bekliyor |
| Kod/veri değişikliği | Yok — bu rapor yalnızca envanter ve mevcut davranış kaydıdır |

## 1. CI ve doğrulama baseline'ı

İncelenen HEAD için GitHub Actions Core quality çalışması:

- Run: [#44411974271](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44411974271)
- Linux `verify`: **success** (Python 3.11)
- Windows `verify-windows`: **success** (Python 3.12)
- Sonuç: workflow tamamlandı, iki iş de başarılı.

Workflow'un `scripts/verify_release.py` kapısı aşağıdakileri yürütür:

1. `python -m pytest -q`
2. `compileall` ile Core/application/game UI/test modüllerini derleme kontrolü.
3. Wheel oluşturma ve izole hedefe kurma.
4. Kurulu paketten içerik yükleme doğrulaması.
5. `python main.py` application smoke.

Paket doğrulaması özellikle 9 kare harita, 7 altıgen harita, altıgen dünya bağlantıları, 6 asset ve 14 placement bekliyor. Bu sayılar mevcut release sözleşmesinin parçasıdır; tek kare easter egg hedefiyle uyumsuz hâle gelmeleri, ancak içerik ve gameplay migration tamamlandıktan sonra ele alınabilir.

Sınırlar:
- Bu rapor hazırlanırken GitHub Actions'ın mevcut HEAD için yeşil olduğu doğrulandı; yerel Windows testleri bu oturumda çalıştırılmadı.
- Workflow dosyasında Ruff adımı bulunmuyor. Teknik plandaki Ruff kabul ölçütü, CI'a eklenmeden otomatik olarak sağlanmış sayılamaz.
- Pygame `--play` görsel kabulü CI'ın headless kapısında yoktur; kullanıcı tarafından ayrıca yapılmalıdır.

## 2. Depo ve içerik envanteri

GitHub recursive tree yanıtı 607 ağaç girdisi içeriyor (yanıt `truncated=false`). İçerik paketindeki 16 map JSON'un gerçek `schema_version` alanları okundu:

| Şema | Adet | Harita kimlikleri |
|---|---:|---|
| v1 kare | 9 | `village`, `forest`, `south_forest`, `west_forest`, `east_forest`, `north_mine`, `south_mine`, `west_mine`, `east_mine` |
| v2 axial hex | 7 | `hex_forest_demo`, `hex_clearing_demo`, `hex_northeast_demo`, `hex_northwest_demo`, `hex_west_demo`, `hex_southwest_demo`, `hex_southeast_demo` |

Diğer içerik:
- `content/active_package.json`: schema v1; aktif paket `demo_eldoria`.
- `content/demo_eldoria/manifest.json`: schema v1; `maps`, `world_map`, `asset_catalog`, `map_placements` ve `presentation_assets` yollarını bildiriyor.
- `content/demo_eldoria/world.json`: schema v1; yalnızca yedi hex haritasını axial dünya koordinatlarında yerleştiriyor.
- `content/demo_eldoria/placements/`: iki hex placement JSON'u.
- `asset_catalog.json`, `presentation_assets.json`: split ve legacy birleşik sunum verisi birlikte mevcut.

Dokuz kare harita 32×32 boyutunda. `village` haritası başlangıç noktası `(16, 29)` tanımlıyor. Kare geçiş grafında sekiz çift yönlü bağlantı bulunuyor; köy dört orman haritasına, her orman da bir maden haritasına bağlanıyor.

## 3. Mevcut çalışma zamanı davranışı — kritik bulgu

### 3.1 Normal oynanabilir akış bugün kare harita üzerinde

- `application/content_pack.py` içindeki `populate_opening_content`, paket içindeki `map_definitions` verisini kullanıyor.
- `_validate_content_references`, NPC, kaynak, market ve başlangıç konumu referanslarını kare harita tanımları üzerinden doğruluyor.
- `_register_opening_content`, dokuz kare haritadan `WorldMap` ve `LocalMapDefinition` kayıtlarını oluşturuyor; oyuncuyu `village` konumuna yerleştirip `(16, 29)` başlangıç koordinatını veriyor.
- `game_ui/screens/main_screen.py`, aktif aktörün `location_id` ve `Position(x, y)` verisini okuyarak kare grid çiziyor, dört yönlü hareket/yerel yol bulma ve JSON geçişlerini yürütüyor.
- `game_ui/screens/map_screen.py`, legacy `WorldMap` konum grafını gösteriyor.

### 3.2 Hex görünümü bugün bağımsız ve geçici bir demo runtime'ı

- `MainScreen` içindeki `hex_portal` eylemi, H tuşuyla `HexWorldView.enter()` çağırıyor.
- `HexWorldView.enter()`, mevcut aktör kimliğini kullanıyor; fakat mevcut kare konumunu dönüştürmüyor. Yeni `HexWorldRuntime` kurup oyuncuyu `hex_forest_demo` haritasında `(0, 0)` hücresine yeniden kaydediyor.
- `HexWorldView.leave()`, hex runtime'ını tamamen atıyor ve kare aktör durumuna dönüyor.
- Mevcut `test_leave_keeps_legacy_actor_location_and_position` testi, kare aktörün `village` konumunun ve kare koordinatının hex görünümünden çıkışta değişmediğini doğruluyor.
- Sonuç: hex görünümdeki hareket, ana actor/gameplay konumunun authoritative kaydı değildir; H ile tekrar girişte runtime yeniden oluşturulduğundan hex konumu da kalıcı değildir.

Bu, A15 entegrasyon readiness raporundaki movement state ownership blocker'ının doğrudan kod kanıtıdır.

## 4. İçerik bağımlılıkları — kare haritalar henüz kaldırılamaz

Mevcut starter içerik kare harita sistemine sıkı bağlıdır:

- Açılış ve gameplay NPC kayıtlarının tamamı `village` konumuna ve kare `(x, y)` koordinatlarına bağlıdır.
- `resources.json` içinde 22 kaynak node'u bulunuyor; bunların konum/landmark referansları kuzey, güney, doğu, batı ormanları ve maden haritalarına dağılıyor.
- `starter_content.json` market konumunu `village_id` ile tanımlıyor.
- Kare haritaların geçiş hedefleri birbirlerine bağlı.
- Save restore, aktörün `location_id` değerini aktif paket harita kataloğunda arıyor; konumu ilgili local map ölçüleriyle doğruluyor. Dokuz haritadan sekizini kaldırmak, eski save'lerdeki konum referanslarını ve gameplay kayıtlarını bozabilir.
- `pyproject.toml` bütün `maps/*.json` dosyalarını paketliyor.
- `scripts/verify_release.py` izole wheel içinden tam dokuz kare harita bekliyor.
- `tests/test_world/test_demo_local_map_content.py`, dokuz haritayı, dünya koordinatlarını, sekiz bağlantıyı, kaynak landmark'larını ve başlangıç haritasını açıkça doğruluyor.

Dolayısıyla kare haritalardan birini bugün seçip diğer sekizini silmek, yalnızca harita dosyası temizliği değildir; starter gameplay, NPC/kaynak/market içerikleri, aktör hareketi, save/restore, UI ve paketleme sözleşmelerini birlikte değiştiren bir migration olur.

## 5. Mimari sahiplik özeti

| Sorumluluk | Mevcut sahip | Baseline sonucu |
|---|---|---|
| Kare harita tanımı/yükleme | `world/map_definition.py`, `map_loader.py`, `map_catalog.py` | Dokuz kare harita ve geçiş grafı için kullanılıyor |
| Hex map tanımı | `application/hex_map_definition.py` | Yedi schema-v2 haritayı okuyor |
| Hex dünya topolojisi | `application/world_map_definition.py` + `world.json` | Yedi hex haritasını axial yerleşim ve geçişlerle doğruluyor |
| Paket keşfi | `application/content_loader.py` | v1 haritaları `map_definitions`, v2 haritaları `hex_map_definitions` içine ayırıyor |
| Normal UI | `MainScreen` | Şu an kare runtime state'ini kullanıyor |
| Hex UI | `HexWorldView` | Ayrı/atılabilir geçici runtime oluşturuyor |
| Save/restore | `GameApplication`, actor persistence ve content package | Aktör konumlarını kare map ID'leri ve ölçüleriyle doğruluyor |
| Genel Core World/Clock | `core/world/World`, `WorldManager`, `LegacyWorldRuntime` | Kare harita kataloğuyla aynı şey değil; kare harita temizliği gerekçesiyle silinemez |

## 6. 16.1 çıkış kararı

**Teknik baseline ve CI karakterizasyonu tamamlandı.** Ancak 16.1'in manuel oynanış/görsel kısmı henüz tamamlanmadı; kullanıcı `python main.py --play` ile mevcut kare başlangıç akışını, H geçişini, kare haritaya dönüşü ve kayıt/yükleme davranışını doğrulamalı.

### Kritik sıralama bağımlılığı

Ürün hedefi "ana oyun hex, tek kare easter egg" iken mevcut uygulama "ana oyun kare, H ile girilen geçici hex demo" durumundadır. Hex runtime şu anda NPC, kaynak toplama, diyalog, market, görev, aktör konumu ve save/restore sistemlerinin authoritative sahibi değildir.

Bu nedenle güvenli sıra şudur:

1. Hex runtime'ın ana gameplay state'iyle entegrasyonu ayrı ve açıkça tanımlanmış entegrasyon işi olarak tamamlanmadan, mevcut dokuz kare haritadan sekizini kaldırma.
2. NPC/kaynak/market/quest/placement/save referanslarının hex dünyaya taşınması veya yeni sahiplik sözleşmeleri belirlenmeden tek kare easter egg haritasını kesin seçme.
3. Tek kare easter egg'in mevcut kare gameplay'den ayrılması ve giriş/çıkış sözleşmesi doğrulanmasından sonra kalan kare map graph/catalog/runtime kodunu küçültme.
4. `demo_eldoria` ve laboratuvar dalları bu temizlik sırasında değiştirilmez; entegrasyon için ayrı onay ve dal stratejisi gerekir.

Bu bulgu, başlangıçtaki "temizlik önce, hex entegrasyonu sonra" sırasının mevcut kod durumunda tek kare easter egg hedefiyle çakıştığını gösteriyor. Kod silmeden önce teknik planın sıralaması yeniden kararlaştırılmalıdır.

## 7. Kullanıcı kabulü bekleyen kontroller

- [ ] Windows'ta `python main.py --play` başlatılır; başlangıçta kare köy haritası göründüğü doğrulanır.
- [ ] H ile hex görünüm açılır; oyuncunun hex başlangıç hücresi `(0, 0)` olduğu görülür.
- [ ] Hex görünümde hareket edilir; H ile çıkışta kare oyuncu konumunun değişmediği doğrulanır.
- [ ] H ile tekrar girişte hex oyuncusunun yeniden başlangıç hücresine döndüğü doğrulanır.
- [ ] Save/load ile kare actor konumunun korunduğu doğrulanır.

Manuel kontroller tamamlanmadan 16.1 tamamen kapatılmış sayılmaz.
