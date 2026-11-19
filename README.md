# RPG Kaynak Yönetimi

Bu proje, deterministik zaman ve olay akışı üzerine kurulu, kaynak üretimi,
aktör faaliyetleri ve genişletilebilir RPG sistemleri içeren bir oyun altyapısıdır.

`GameApplication` Core ve application state'inin bileşim köküdür. Eski `Game`
API'si uyumluluk katmanında korunur. Çalışan alt sistemler:
- dünya ve aktif dünya yönetimi;
- varlıkların merkezi kayıt ve dünya içi yerleşimi;
- zaman ve süreli aksiyonlar;
- tüm oyun ile dünya olayları için ortak olay kuyruğu.
- kaynak toplama, üretim zincirleri, tesis kapasitesi ve aktör faaliyetleri;
- karakter, hareket, ekonomi, görev ve combat için application-level sözleşmeler.

`main.py` varsayılan olarak smoke oturumu başlatır. Güncel oynanabilir dikey dilimi
Pygame ile açmak için:

```powershell
python -m pip install -e .
python main.py --play
```

Temiz bir Windows ortamında kurulum ve giriş noktası doğrulaması:

```powershell
python -m venv .venv-clean
.\.venv-clean\Scripts\python.exe -m pip install --upgrade pip
.\.venv-clean\Scripts\python.exe -m pip install .
.\.venv-clean\Scripts\rpg-kaynak-yonetimi.exe --version
.\.venv-clean\Scripts\python.exe main.py --play
```

Kurulum sonrasında beklenen sürüm `3.0.0rc1` olmalıdır. Kontrol tamamlandıktan
sonra geçici `.venv-clean` klasörü kaldırılabilir.

Yayın adayı sürümü `3.0.0rc1`'dir. Kurulumdan sonra aynı uygulama şu giriş
noktasıyla da başlatılabilir:

```powershell
rpg-kaynak-yonetimi --play
```

Beklenmeyen masaüstü hataları `logs/eldoria.log` dosyasına yazılır. Var olan
bir save slotunun üzerine yazılırken önce `<slot>.bak` yedeği oluşturulur.

Kod içinden application-level gameplay API kullanımı:

```python
from application import GameplayService
from main import oyun_olustur

game = oyun_olustur("Eldoria")
service = GameplayService(game)

# service.collect(...), service.start_production(...),
# service.start_chain(...), service.advance_by(...), service.state(),
# actor, market, dialogue, quest ve combat API'leri kullanılabilir.
# Kimlikler ve kaynak kayıtları önce SessionBundle'a eklenir.
```

Production ve facility kayıtları `application` katmanında; kaynak, envanter,
reçete ve node kayıtları `resources` katmanında tutulur. `GameplayService`
başlıca `collect`, `start_production`, `start_chain`, `advance_to`,
`advance_by`, `save`, `load`, `state`, `register_actor`, `start_gathering`,
`start_actor_production`, `publish_offer`, `buy_offer`, `cancel_offer`,
`register_npc`, `talk_to_npc`, `start_quest`, `add_combatant` ve encounter
işlemlerini sağlar. Bu API'ler
deterministik tick ve candidate restore sözleşmelerini kullanır. Başlangıç dünyası, karakter oluşturma ve açılış diyaloğu seçili içerik
paketinden yüklenir. Aktif paket `content/active_package.json` ile seçilir.
Schema-v2 axial harita dosyaları, paket manifestindeki `maps` alanıyla belirtilen
klasörden keşfedilir. Yeni harita içerik sözleşmesi için
`docs/content/hex-map-authoring.md` belgesine bakın. Genel içerik paketi
sözleşmesi `docs/architecture/34-content-data-contract.md` içinde açıklanır.

Ekonomi sınırı: `resources` fiziksel `ResourceType`, `Quantity`, `Inventory`,
node, reçete ve üretim state'ini taşır. `economy` ise `Currency`/`Money`,
ledger bakiyeleri, fiyat kitabı, market offer'ları, merchant ve trade
transferlerini taşır. Ekonomi fiziksel stoğu kopyalamaz; trade sırasında
`resources.Inventory` sözleşmesini tüketir. Ekonomi snapshot'ı ayrı
`rpg-economy` sözleşmesidir ve birleşik save kapsamına ancak application
katmanındaki açık bir entegrasyonla eklenmelidir.

Güncel ilerleme, tamamlanan fazlar ve yayın hazırlığı için
`docs/architecture/30-master-roadmap.md` belgesine bakın. Güncel proje sürümü
`pyproject.toml` içinde `3.0.0rc1` olarak tanımlıdır ve Core 2.1 ile Core 17
seviyesindeki application fazlarını kapsar. UI ve RPG domain genişlemeleri
aynı üst katman sınırları içinde ilerlemektedir. Faz A-C tamamlanmış, güncel
odak Faz D kalite ve yayın hazırlığıdır.

Release-candidate doğrulama kapısı için test araçlarını runtime bağımlılıklarından ayrı kurun:

```powershell
python -m pip install -r requirements-test.txt
python scripts/verify_release.py
```

Bu doğrulama tüm testleri ve smoke kontrolünü çalıştırmanın yanında wheel üretir,
izole bir hedefe kurar ve kurulu içerik paketinin manifest, asset catalog ve
scene-placement sözleşmelerini kaynak kod ağacının dışından yükleyebildiğini
doğrular. Eski kare harita dosyaları ve demo harita kataloğu pakete dahil değildir.

Dağıtılabilir wheel/sdist üretimi için yayın araçlarını kurup:

```powershell
python -m pip install -r requirements-release.txt
python -m build
```

Sürüm kontrolü:

```powershell
python main.py --version
```

Kapının kapsamı ve Core sınırı `docs/architecture/33-release-candidate-checklist.md`
belgesinde tanımlıdır.

## Harita Sistemi Temizliği

`experiment/map-cleanup` dalında eski kare harita gameplay sistemi ve eski
yedi haritalı Hex demo/portal akışı kaldırılmıştır. Kare map catalog/schema/
loader, eski WorldMap location graph, kare movement ve map UI bileşenleri ile
bunlara bağlı demo NPC, resource, quest, dialogue ve market içerikleri artık
aktif paket veya normal gameplay tarafından kullanılmaz.

Korunan altyapı, sonraki entegrasyonun hedefi olan axial Hex map/world
definition, HexWorldRuntime, occupancy, movement rules, pathfinding ve
session-scoped runtime owner bileşenleridir. Bu bileşenler eski demo portalı
değildir. Yeni gameplay haritası ve içerikleri laboratuvar mimarisi entegre
edildikten sonra ayrıca oluşturulacaktır; eski kare koordinatlar axial
koordinatlara dönüştürülmez.

Kapsam ve teknik kararlar için [genel plan](docs/architecture/51-map-system-cleanup-general-plan.md),
[teknik plan](docs/architecture/52-map-system-cleanup-technical-plan.md),
[başlangıç envanteri](docs/architecture/57-legacy-map-system-removal-inventory.md)
ve [kapanış/bağımlılık raporu](docs/architecture/58-legacy-map-runtime-dependency-graph.md)
belgelerine bakın. Bu dalın temizliği `demo_eldoria`, `main` veya
`experiment/hex-world-laboratory` dallarına kendiliğinden aktarılmaz.
