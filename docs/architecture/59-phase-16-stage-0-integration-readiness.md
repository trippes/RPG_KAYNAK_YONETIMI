# Aşama 16 — Aşama 0: Entegrasyon Öncesi Hazırlık

Tarih: 19 Kasım 2026  
Çalışma dalı: `experiment/map-cleanup`  
Durum: **HAZIRLIK VE KAPSAM KARARLARI TAMAMLANDI — TEKNİK BLOKAJLAR KAYIT ALTINDA**  
Kod entegrasyonu onayı: **BU BELGE TEK BAŞINA ENTEGRASYON YETKİSİ VERMEZ**

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

Henüz dağıtım seçimi yapılmadı. Aşama 16'nın package/runtime spike'ında (a) tek dağıtım standardizasyonu, (b) Pygame bağımsız çekirdek + uygulamaya özel adaptör, (c) ayrı ortam yaklaşımı temiz Linux/Windows kurulumlarıyla karşılaştırılacak. Kullanıcı kararı ve smoke test olmadan `pyproject.toml` değiştirilmeyecek.

### 5.2 Son aktarım CI hatası

Temizlik dalındaki aktarım commit'i `2d459e46978d93af8804d4ba66efde3770f87fef` için Actions run `44507655166` hem Linux hem Windows'ta başarısızdır. Ruff ve legacy cleanup boundary adımları başarılıdır; release verification sırasında pytest collection dört testte durmuştur:
- `test_entity_world_lifecycle.py`: `hex_world_lab.application.entity_demo` bulunamadı.
- `test_simulation_tick_flow.py`: aynı demo-only modül bulunamadı.
- `test_movement_tick_contract.py`: `DemoTickPump` export'u bulunamadı.
- `test_environment_collision_footprints.py`: `movement_demo` modülü bulunamadı.

Bu dosyalar laboratuvarın demo harness katmanına bağımlıdır; hedef entegrasyon kapsamı demo launcher/harness değildir. Çözüm, bu demo dosyalarını körlemesine taşımak değil; testleri gerçek runtime sözleşmelerine göre ayırmak/uyarlamak ve dışarıda bırakılan demo davranışının ana oyuna yanlışlıkla bağlanmadığını doğrulamaktır. Bu düzeltme sonraki teknik dilimde yapılmalıdır.

### 5.3 Kaynak-hedef farkı

Laboratuvar kodu `src/hex_world_lab` altında, cleanup dalı ise `hex_world_lab` kök paketinde tutulmaktadır. Bu fark bilinçli paket yerleşimi uyarlamasıdır; aktarım sırasında modül listesinin kaynak paketle karşılaştırılması ve eksik/fazla dosya denetimi gereklidir.

## 6. Aşama 0 çıkış kararı

**Hazırlık kapsamı, dal güvenliği, koruma sınırları ve seçici aktarım stratejisi belirlendi. Aşama 0 planlama çıktısı tamamlandı.**

Ancak sistem henüz entegrasyona hazır/CI-yeşil kabul edilmez. Sonraki aşamanın giriş kapıları:
1. Dört test collection hatasının demo harness ile runtime testleri ayrıştırılarak giderilmesi.
2. Kaynak/hedef runtime dosya envanterinin eksiksiz karşılaştırılması.
3. Pygame dağıtım stratejisinin temiz Linux/Windows ortamlarında kanıtlanması ve kullanıcı kararı.
4. İlk package/runtime spike'ın Linux ve Windows CI'dan geçmesi.

Bu kapılar geçmeden geometry, movement, physics, simulation, renderer veya content entegrasyonuna başlanmayacaktır.
