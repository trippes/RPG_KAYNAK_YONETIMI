# Aşama 16 — Aşama 0: Entegrasyon Öncesi Hazırlık

Tarih: 19 Kasım 2026  
Çalışma dalı: `experiment/map-cleanup`  
Durum: **AŞAMA 0 TAMAMLANDI — İLK PACKAGE/RUNTIME SPIKE LINUX VE WINDOWS'TA BAŞARILI**  
Kod entegrasyonu: **SONRAKİ DİLİME GEÇİŞE HAZIR; ANA OYUN RUNTIME BAĞLANTISI HENÜZ YAPILMADI**

## 1. Dal ve HEAD doğrulaması

| Dal | Denetim anındaki HEAD | Kullanım |
|---|---|---|
| `experiment/map-cleanup` | `2d459e46978d93af8804d4ba66efde3770f87fef` | Tek çalışma/hedef dal |
| `experiment/hex-world-laboratory` | `9e909a45d1b2dca3d0f97986fde9fc2ad832fd26` | Salt okunur kaynak/arşiv |
| `main` | `01dd11e17a345624748b724467a09beb8e309ea0` | Korunan yayın dalı |
| `demo_eldoria` | `7d53d431d5c3639fd95d273de9043b64483a5125` | Korunan demo dalı |

GitHub branch metadata alanında dört dalın da `protected=false` olduğu görüldü. Branch-protection ayrıntı endpoint'i entegrasyon yetkisi nedeniyle okunamadı (HTTP 403); bu nedenle ayrıntılı ruleset/branch-rule bulunmadığı iddia edilmemektedir. Güvenlik kuralı olarak bu çalışma yalnızca `experiment/map-cleanup` dalına yazacaktır.

Laboratuvar ve temizlik dalları karşılaştırması `diverged`: cleanup, laboratuvara göre 186 commit önde ve 843 commit geridedir; karşılaştırma 300 dosya değişikliği döndürmüştür. Bu iki dalın geçmişleri doğrudan birleştirilmeye uygun değildir. **Merge, rebase veya toplu cherry-pick yapılmayacaktır.** Kaynak kodlar seçilerek, dosya/sorumluluk bazında aktarılacaktır.

## 2. Sabitlenen hedef ve kapsam

Hedef, laboratuvarda geliştirilen yeni Hex World yeteneklerini Eldoria'nın mevcut runtime'ına kontrollü biçimde kazandırmaktır. Laboratuvarın bağımsız demo uygulaması ana oyunun yerine geçirilmez.

Dahil:
- Gerekli Hex geometry, world/map, entity/spatial, movement/physics, simulation, camera/rendering ve vector-content altyapısının sorumluluk bazında değerlendirilmesi.
- Eldoria'nın mevcut actor/entity, hex runtime, gameplay service, renderer, asset catalog, placement catalog ve persistence sınırlarıyla açık adapter/bridge kurulması.
- Seçilen her entegrasyon dilimi için küçük commit, hedefli test, tam CI ve geri dönüş noktası.

Hariç:
- Laboratuvar demo launcher'ı, demo tick pump'ı ve demo-only application harness'ı.
- Laboratuvar senaryo/harita içerikleri, görsel asset'ler, benchmark çıktıları, raporları ve laboratuvar dokümantasyonunun kopyalanması.
- Eski kare harita veya eski yedi haritalı Hex demo/portal sisteminin geri getirilmesi.
- Eski NPC, resource, quest, dialogue, market ve map-placement demo kayıtlarının taşınması. Yeni oyun içerikleri entegrasyon sonrasında sıfırdan oluşturulacaktır.
- `main`, `demo_eldoria` veya laboratuvar dalına yazma.

## 3. Korunacak mimari sınırlar

1. `experiment/hex-world-laboratory` değiştirilmeyecek; referans/arşiv dalı olarak kalacaktır.
2. `experiment/map-cleanup` tek entegrasyon dalıdır. Her commit öncesi HEAD yeniden okunacak; ref güncellemesi beklenen SHA ile yapılacaktır.
3. `main` ve `demo_eldoria` değiştirilmeyecek; kullanıcı açıkça onaylamadan PR/merge yapılmayacaktır.
4. Eski Hex demo portalı ile yeni laboratuvar Hex altyapısı aynı sistem kabul edilmeyecektir.
5. Genel NPC, resource, quest, dialogue, economy, inventory, save ve core simulation domain davranışları korunacaktır; yalnızca eski demo verileri dışarıda kalır.
6. Aynı actor, world position, tick, content record veya render state için iki authoritative owner oluşturulmayacaktır.
7. Main'in mevcut axial map/runtime, actor persistence, renderer, asset/placement catalog ve güvenli content store altyapısı karşılaştırma yapılmadan silinmeyecek veya topluca değiştirilmeyecektir.
8. Kare koordinatlar axial koordinata dönüştürülmeyecek; eski save verileri sessizce yeni Hex konumu olarak yorumlanmayacaktır.
9. Veri ve schema migration'ı ayrı, açıkça test edilmiş ve geri alınabilir bir dilim olmadan yapılmayacaktır.

## 4. Aktarım stratejisi

- Kaynak, `experiment/hex-world-laboratory` dalındaki `experiments/hex_world_laboratory/src/hex_world_lab` paketidir.
- Hedef, `experiment/map-cleanup` içindeki `hex_world_lab/` paketidir. Aktarım, kaynak `src` yerleşimini hedef projenin paketleme düzenine uyarlayan seçici dosya aktarımıdır; depo geçmişi birleştirilmez.
- Önce Pygame bağımsız domain modülleri ve sözleşmeleri; ardından yalnızca gereken Pygame adaptörleri, uygulama köprüleri ve testler değerlendirilir.
- Demo launcher/harness dosyaları ve yalnızca bunlara bağlı testler ana pakete alınmaz. Testler, gerçek runtime sözleşmesini doğrulayacak şekilde seçilir veya uyarlanır.
- Her dilim ayrı commit edilir. Sıra: package/runtime spike → geometry/world identity bridge → actor/movement ownership bridge → physics/spatial bridge → simulation orchestration → camera/render bridge → vector content read adapter → persistence/content coexistence → platform/release acceptance.
- Her dilim için Linux ve Windows testleri, Ruff, wheel/sdist veya izole kurulum smoke testi ve ilgili regresyon testleri geçmeden sonraki dilime geçilmez.

## 5. Aşama 0 denetiminde bulunan mevcut teknik blokajlar

### 5.1 Pygame dağıtımı

Temizlik dalının `pyproject.toml` dosyası `pygame-ce>=2.5`; laboratuvarın `pyproject.toml` dosyası `pygame>=2.6,<3` tanımlıyor. İki dağıtım da `pygame` import namespace'ini sağlıyor. Context7'nin güncel Pygame-CE kurulum dokümanı, `pygame` dağıtımı kuruluysa kaldırılmasını ve ardından `pygame-ce` kurulmasını öneriyor. Bu nedenle iki dağıtım aynı sanal ortama birlikte eklenmeyecek.

Hedef dal için dağıtım kararı verildi: Eldoria kök projesinin mevcut standardı olan `pygame-ce>=2.5` korunacaktır. Yeni Hex World modülleri bu tek dağıtımı kullanır; `pygame` dağıtımı hedef ortama eklenmez. Laboratuvar dalının bağımsız `pyproject.toml` dosyası ve bağımlılık tanımı değiştirilmemiştir. Context7 dokümanı `pygame-ce` dağıtımının `pygame` import adını sağladığını, kurulu `pygame` dağıtımının kaldırılması gerektiğini ve Python 3.11+ ile Windows/Linux platformlarını desteklediğini doğrular. Hedef dalın CI ortamları (Linux/Python 3.11 ve Windows/Python 3.12) bu standardı başarıyla çalıştırmıştır.

### 5.2 Son aktarım CI hatası

Temizlik dalındaki aktarım commit'i `2d459e46978d93af8804d4ba66efde3770f87fef` için Actions run `44507655166` hem Linux hem Windows'ta başarısızdır. Ruff ve legacy cleanup boundary adımları başarılıdır; release verification sırasında pytest collection dört testte durmuştur:
- `test_entity_world_lifecycle.py`: `hex_world_lab.application.entity_demo` bulunamadı.
- `test_simulation_tick_flow.py`: aynı demo-only modül bulunamadı.
- `test_movement_tick_contract.py`: `DemoTickPump` export'u bulunamadı.
- `test_environment_collision_footprints.py`: `movement_demo` modülü bulunamadı.

Bu dosyalar laboratuvarın demo harness katmanına bağımlıdır; hedef entegrasyon kapsamı demo launcher/harness değildir. Hedef dalda şu ayrıştırma yapıldı: `test_entity_world_lifecycle.py` içindeki gerçek `EntityWorldCoordinator` yaşam döngüsü testi korundu; `EntityDemo` ve `MovementDemo` kullanan demo testleri runtime testlerinden çıkarıldı. `test_simulation_tick_flow.py`, `test_movement_tick_contract.py` ve `test_environment_collision_footprints.py` yalnızca hariç tutulan demo harness/sahne/scheduler davranışını doğruladıkları için hedef dalın runtime test kümesine alınmadı. Ayrıca `test_map_persistence.py` ve `test_runtime_persistence.py` içindeki laboratuvar `starting_valley.json` örnek dosyasına bağlı iki test çıkarıldı; aynı dosyalardaki geçici dosya (`tmp_path`) kullanan genel persistence testleri korundu. Kaynak laboratuvar dalındaki dosyaların hiçbirine dokunulmadı.

Sonuç: pytest collection hataları giderildi. Linux ve Windows'ta 2.125 test, 235 subtest geçti; 59 uyarı kaldı. Bu uyarılar pygame görüntü serileştirme API'sinin deprecated olduğunu bildiriyor; testleri başarısız kılmıyor.

### 5.3 Kaynak-hedef farkı

Laboratuvar kodu `src/hex_world_lab` altında, cleanup dalı ise `hex_world_lab` kök paketinde tutulmaktadır. Kaynak-hedef manifest karşılaştırması tamamlandı: laboratuvar paketinde 129 dosya, hedef pakette 123 dosya vardır; hedefte kaynakta bulunmayan fazla dosya yoktur. Eksik altı dosya `__main__.py`, `app.py`, `application/demo_tick_pump.py`, `application/entity_demo.py`, `application/movement_demo.py` ve `config.py` dosyalarıdır. Bunların tamamı bağımsız laboratuvar demo kabuğu/başlatıcısı veya demo scheduler'ıdır; runtime paketinden bilinçli olarak dışarıda tutulmuştur.

İlk package/runtime spike kapsamında `scripts/verify_release.py` güncellendi: `hex_world_lab` compileall kapsamına eklendi; üretilen wheel geçici/izole hedefe kuruluyor ve kurulu wheel içinden `EntityWorldCoordinator`, `PygameWorldRenderer`, `SimulationTickCoordinator` ve `MovementSystem` import ediliyor. Böylece yalnızca kaynak ağacından import değil, dağıtılabilir pakette bulunma da doğrulanıyor.

## 6. Aşama 0 çıkış kararı

**Aşama 0'ın tüm çıkış kapıları geçildi.** Son doğrulama commit'i: `e29d5cf73f62f52f6de335918586d269009e73b8`. GitHub Actions run `44509987003` hem Linux hem Windows işlerinde başarılıdır: [CI run](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44509987003).

Her iki platformda da:
- Ruff kontrolü başarılı.
- Eski harita temizliği sınır kontrolü başarılı.
- 2.125 pytest testi ve 235 subtest başarılı; 59 pygame deprecation uyarısı mevcut.
- `hex_world_lab` dahil compileall başarılı.
- Wheel oluşturma ve izole hedefe kurulum başarılı.
- Kurulu wheel içinden Hex World runtime sınıflarının import smoke testi başarılı.
- Release-candidate verification başarılı.

Sonraki adım Aşama 16'nın ilk gerçek entegrasyon dilimidir: geometry/world identity bridge tasarımı. Bu aşama, laboratuvarın Hex kimliklerini ve dünya koordinatlarını Eldoria'nın mevcut authoritative axial runtime'ına nasıl bağlayacağını belirleyecek; actor, movement, physics veya renderer sahipliği bu dilimde değiştirilmemelidir. Bu belge tek başına ana oyuna geçiş/merge yetkisi vermez.
