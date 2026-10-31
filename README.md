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
python main.py
python -m pip install -r requirements.txt
python main.py --play
```

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
# service.start_chain(...), service.advance_by(...), service.state()
# ve aktörler için register_actor/start_gathering/start_actor_production,
# register_world_map/place_actor/move_actor,
# market, dialogue, quest ve combat API'leri
# kullanılabilir. Kimlikler ve kaynak kayıtları önce SessionBundle'a eklenir.
```

Production ve facility kayıtları `application` katmanında; kaynak, envanter,
reçete ve node kayıtları `resources` katmanında tutulur. `GameplayService`
başlıca `collect`, `start_production`, `start_chain`, `advance_to`,
`advance_by`, `save`, `load`, `state`, `register_actor`, `start_gathering`,
`start_actor_production`, `register_world_map`, `place_actor`, `move_actor`,
`publish_offer`, `buy_offer`, `cancel_offer`, `register_npc`, `talk_to_npc`,
`start_quest`, `add_combatant` ve encounter işlemlerini sağlar. Bu API'ler
deterministik tick ve candidate restore sözleşmelerini kullanır. Demo içeriği
`application.content_pack.populate_demo_content()` ile yeniden kurulabilir.
Demo görev, NPC, diyalog, kaynak, pazar ve combat tanımları
`data/demo_content.json` dosyasından yüklenir; içerik sözleşmesi için
`docs/architecture/34-content-data-contract.md` belgesine bakın.

Ekonomi sınırı: `resources` fiziksel `ResourceType`, `Quantity`, `Inventory`,
node, reçete ve üretim state'ini taşır. `economy` ise `Currency`/`Money`,
ledger bakiyeleri, fiyat kitabı, market offer'ları, merchant ve trade
transferlerini taşır. Ekonomi fiziksel stoğu kopyalamaz; trade sırasında
`resources.Inventory` sözleşmesini tüketir. Ekonomi snapshot'ı ayrı
`rpg-economy` sözleşmesidir ve birleşik save kapsamına ancak application
katmanındaki açık bir entegrasyonla eklenmelidir.

Güncel ilerleme, tamamlanan fazlar ve yayın hazırlığı için
`docs/architecture/30-master-roadmap.md` belgesine bakın. Güncel proje sürümü
`pyproject.toml` içinde `3.0.0a0` olarak tanımlıdır ve Core 2.1 ile Core 17
seviyesindeki application fazlarını kapsar. UI ve RPG domain genişlemeleri
aynı üst katman sınırları içinde ilerlemektedir. Faz A-C tamamlanmış, güncel
odak Faz D kalite ve yayın hazırlığıdır.

Release-candidate doğrulama kapısı için:

```powershell
python scripts/verify_release.py
```

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
