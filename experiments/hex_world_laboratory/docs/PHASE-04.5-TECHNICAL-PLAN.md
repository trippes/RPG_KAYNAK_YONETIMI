# Aşama 4.5 — Hareket ve Hex Dünya Entegrasyonu Teknik Mimari Planı

> **Belge türü:** Teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK PLAN — KULLANICI ONAYI BEKLİYOR  
> **Ön koşul:** Aşama 4.5 genel planı kullanıcı tarafından onaylandı.

---

## 1. Teknik hedef ve sınırlar

Sürekli hareket eden bir aktörün fiziksel dünya konumunu, bulunduğu hex hücreyle ilişkilendiren bağımsız bir entegrasyon katmanı oluşturulacaktır.

Temel ilke: **Aktörün gerçek konumu `WorldPoint` olarak kalır; hex hücre yalnızca bu konumdan hesaplanan mekânsal bağlamdır.** Aktör hücre merkezine taşınmayacak, koordinatı yuvarlanarak hareket durumu değiştirilmemeli ve hücre sınırında fiziksel hareket kesilmemelidir.

Bu aşama mevcut hareket hesaplamasını, tick sistemini veya klavye adaptörünü yeniden yazmayacaktır. Hareket ve dünya katmanları arasında kontrollü bir köprü kurulacaktır.

### Kapsama dahil

- Bir `HexWorld` ve o dünyadaki tek bir `MapId` için hareket-dünya bağlamı.
- Sürekli `WorldPoint` konumunu `AxialCoord` değerine dönüştürme.
- `CellAddress` üretimi ve güncel hücre verisini `HexWorldView` üzerinden okuma.
- Her hareket eden aktör için önceki hücre bilgisini tutma.
- Hareket tick'i sonrasında hücre bilgisini güncelleyen entegrasyon akışı.
- Harita yükleme durumu, harita dışı koordinatlar ve hücre sınırı davranışları.
- Birim, entegrasyon, regresyon ve CI doğrulamaları.

### Kapsam dışı

- Duvar/engel çarpışması ve yürünemez hücrede durma (Aşama 5).
- Harita sınırında hareketi durdurma veya komşu haritaya geçiş.
- Otomatik harita yükleme/boşaltma.
- Yol bulma, NPC kararları veya çoklu aktör çarpışması.
- Kamera, karakter çizimi, sprite/animasyon ve görsel dünya katmanları (Aşama 6–7).
- Ana Eldoria oyununa entegrasyon.
- Hareket sisteminin tick sayacını veya gerçek zamanlı tick pompasını değiştirmek.

---

## 2. İncelenen mevcut mimari

Çalışma dalı HEAD: `6f39af2d563bdb8f0e9dbd0bc207225b3329f4b1`.

| Mevcut modül | Mevcut sözleşme | Aşama 4.5'teki rolü |
|---|---|---|
| `geometry.coordinates.WorldPoint` | Kesirli/sürekli dünya koordinatı; sonlu X/Y | Aktörün tek gerçek fiziksel konumu |
| `geometry.coordinates.AxialCoord` | Tamsayı axial hücre koordinatı | Konumdan hesaplanan hücre |
| `geometry.layout.HexLayout` | Yönelim, circumradius ve dünya orijini | Haritaya ait geometrik dönüşüm bağlamı |
| `geometry.transforms.world_to_axial` | Dünya noktasını axial koordinata dönüştürür; `previous_cell` alır | Tek ve kanonik hücre seçimi |
| `world.identity.CellAddress` | `WorldId + MapId + AxialCoord` | Hücrenin dünya çapında benzersiz adresi |
| `world.map_registry.MapRegistry` | Kayıtlı haritaları yüklü haritalardan ayırır | Kayıt/yükleme durumunu doğrulama |
| `world.world.HexWorld` | Registry, Runtime ve View sahibi | Entegrasyonun dünya referansı |
| `world.world_view.HexWorldView` | Başlangıç verisi ve runtime override'larının salt okunur görünümü | Hücrenin güncel verisini okuma |
| `simulation.MovementSystem` | Harici ardışık tick başına bir hareket adımı; 60 TPS | Önce aktör konumunu güncelleme |
| `application.DemoTickPump` | 60 TPS tick akışı; render başına en fazla 8 tick; borç korunur | Demo zamanlaması; bu aşamada değişmez |
| `input.PygameKeyboardAdapter` | Klavye durumunu `MovementIntent` değerine çevirir | Hareket niyeti kaynağı; değişmez |

### Mevcut davranıştan çıkan önemli sonuçlar

1. `HexMapDefinition` kendi `HexLayout` değerini taşır. Entegrasyon, dışarıdan ikinci bir layout parametresi almayacak; haritanın kendi layout'unu kullanacaktır.
2. `MapRegistry.get_map(map_id)` yalnızca yüklü haritayı döndürür. Kayıtlı fakat yüklenmemiş harita ile hiç kayıt edilmemiş harita ayrımı korunacaktır.
3. `HexWorldView.get_cell(address)`, kayıtlı/yüklü harita ve hücre varlığı kontrollerini yapar; runtime değişikliklerini de hesaba katar.
4. `world_to_axial` sınır eşitliğinde önceki hücreyi koruyabilir. Bu davranış yeniden uygulanmayacak veya kopyalanmayacaktır.
5. `MovementSystem` dünya modelini bilmez. Bu bağımsızlık korunacaktır.

---

## 3. Hedef mimari ve bağımlılık yönü

Entegrasyon üç parçadan oluşacaktır:

1. **MovementWorldContext:** Tek dünya ve tek harita için doğrulanmış bağlam.
2. **MovementCellResolution:** Bir konumun hangi hücreye karşılık geldiğini ve hücrenin güncel verisini taşıyan değişmez sonuç.
3. **MovementCellTracker:** Tek aktörün önceki hücre bilgisini tutan ve yeni konumları çözen takipçi.

Bağımlılık yönü:

```text
MovementSystem ──> MovementState.position (WorldPoint)
                         |
                         v
              MovementCellTracker
                         |
                         v
               MovementWorldContext
                    /         \
                   v           v
          world_to_axial    HexWorldView
                   \           /
                    v         v
               MovementCellResolution
```

`movement` paketi `world` paketini import etmeyecektir. `MovementSystem` değişmeden kalacaktır. Dünya entegrasyonu `simulation` katmanındaki takipçi tarafından, hareket adımından sonra çağrılacaktır. Böylece hareket çekirdeği Pygame ve dünya modelinden bağımsız kalır.

---

## 4. Yeni modüller ve API sözleşmeleri

### 4.1 `world/movement_context.py` — MovementWorldContext

Bir hareketli aktörün hücre çözümlemesini yapacağı dünya/harita bağlamını temsil eder.

Önerilen API:

- `MovementWorldContext(world: HexWorld, map_id: MapId)`
- `world_id` — salt okunur özellik.
- `map_id` — salt okunur özellik.
- `resolve_position(position: WorldPoint, previous_cell: AxialCoord | None = None) -> MovementCellResolution`

Kurallar:

- Constructor, verilen nesne türlerini doğrular.
- Constructor sırasında haritanın dünyada kayıtlı ve yüklü olduğu doğrulanır.
- Her çözümlemede haritanın hâlen kayıtlı ve yüklü olduğu yeniden kontrol edilir. Bağlam, haritayı kendiliğinden yüklemez.
- Geometri dönüşümünde yüklü harita tanımının kendi `layout` değeri kullanılır.
- Harita sonradan boşaltılmışsa mevcut `MapNotLoadedError`; kaydı kaldırılmışsa mevcut `UnknownMapError` dışarı iletilir.
- Dünya/harita kimlikleri bağlam boyunca sabittir.
- Bağlam yalnızca tek haritayı kapsar. Komşu haritaya geçiş veya haritalar arasında otomatik seçim yapmaz.

### 4.2 `world/movement_resolution.py` — MovementCellResolution

Çözümleme sonucu değişmez bir veri nesnesi olacaktır.

Alanlar:

- `world_id: WorldId`
- `map_id: MapId`
- `coord: AxialCoord`
- `address: CellAddress`
- `cell_data: HexCellData | None`

Kurallar:

- `address`, aynı `world_id`, `map_id` ve `coord` değerlerinden oluşturulur.
- `cell_data`, `HexWorldView.get_cell(address)` üzerinden alınır.
- Axial koordinat harita geometrisine göre geçerli olsa da haritanın açık hücre kümesinde bulunmuyorsa `cell_data=None` olur.
- Hücre verisi varsa bu veri base definition yerine `HexWorldView` tarafından sunulan güncel veridir; runtime override'ları görünür.
- Sonuç, konumun hücre merkezine taşındığı anlamına gelmez. `WorldPoint` ayrı kalır.

### 4.3 `simulation/movement_cell_tracker.py` — MovementCellTracker

Tek bir hareketli aktörün son seçilmiş axial hücresini takip eder.

Önerilen API:

- `MovementCellTracker(context: MovementWorldContext)`
- `previous_cell` — son başarılı çözümlemenin axial koordinatı veya `None`.
- `current_resolution` — son başarılı çözümleme veya `None`.
- `update(position: WorldPoint) -> MovementCellResolution`

Kurallar:

- Takipçi kendi tick sayacını, saatini veya hareket durumunu tutmaz.
- Her aktör için ayrı takipçi örneği kullanılır; aktörlerin önceki hücre bilgileri paylaşılmaz.
- İlk çözümlemede `previous_cell=None` gönderilir.
- Sonraki çözümlemelerde önceki başarılı axial koordinat `world_to_axial` fonksiyonuna iletilir.
- Çözümleme tamamlanmadan takipçi iç durumu değiştirilmez. Hata oluşursa önceki hücre ve önceki sonuç korunur.
- Harita dışında kalan koordinatlar da geometrik bir axial hücreye karşılık gelebilir. Bu koordinat takip edilir; hücre verisi yoksa sonuçtaki `cell_data=None` olur.
- Önceki hücre, mutlaka haritanın mevcut hücre kümesinde bulunan bir hücre olmak zorunda değildir. Sınır seçiminde kullanılan son geometrik konum sınıfıdır.

### 4.4 Hareket tick'i ile entegrasyon

Bu aşamada `MovementSystem` içine dünya bağımlılığı eklenmeyecektir.

Dış orkestrasyonun sırası:

1. O tick için `MovementIntent` alınır.
2. `MovementSystem.step(tick_number, intent)` çağrılır.
3. Dönen `MovementState.position` değeri `MovementCellTracker.update(position)` metoduna verilir.
4. Elde edilen `MovementCellResolution` oyun mantığına/diagnostic katmanına sunulur.

Bu sıra her başarılı hareket tick'i için uygulanır. Takipçi hareketi ilerletmez, tick üretmez ve `MovementSystem` durumunu değiştirmez. Aynı tick içinde birden fazla hareket adımı çalıştırılmaz.

---

## 5. Hata ve sınır davranışları

| Durum | Beklenen davranış |
|---|---|
| Dünya içinde kayıtlı ve yüklü harita | Normal çözümleme |
| Harita kayıtlı fakat yüklenmemiş | `MapNotLoadedError`; otomatik yükleme yok |
| Harita kaydı bulunmuyor/kaldırılmış | `UnknownMapError` |
| Axial koordinat haritanın açık hücre kümesinde | `cell_data` güncel hücre verisini taşır |
| Axial koordinat açık hücre kümesinde değil | `cell_data=None`; hareket devam eder |
| Harita sınırının dışına yürüyüş | Fiziksel konum korunur; hücre verisi yoksa `None` |
| İki hücre arasındaki tam eşit uzaklıklı sınır | Önceki hücre, mevcut geometri sözleşmesine göre korunur |
| İlk çözümleme veya önceki hücrenin eşit uzaklığa sahip olmadığı durum | `world_to_axial` deterministik seçimi kullanılır |
| Aynı axial koordinat, farklı MapId | Farklı `CellAddress` değerleri |
| Hücre runtime verisi değiştirilmiş | `HexWorldView` üzerinden güncel override okunur |
| Harita çözümleme öncesinde unload edilmiş | Mevcut `MapNotLoadedError`; takipçi durumu korunur |

Önemli ayrım: **Haritanın geometrik alanı dışında olmak ile açık hücre kümesinde olmayan bir koordinata düşmek aynı şey değildir.** Aşama 3'te harita sınırı açık hücre kümesiyle tanımlandığından, bu aşamada hücre verisinin varlığı doğrudan `HexWorldView` sonucuyla belirlenir. Fiziksel konum hiçbir durumda bu nedenle değiştirilmez.

---

## 6. Dosya planı

Yeni üretim dosyaları:

```text
src/hex_world_lab/world/
    movement_context.py
    movement_resolution.py

src/hex_world_lab/simulation/
    movement_cell_tracker.py
```

Güncellenecek dışa aktarım dosyaları:

- `src/hex_world_lab/world/__init__.py`
- `src/hex_world_lab/simulation/__init__.py`

Test dosyaları:

```text
tests/unit/
    test_movement_world_context.py
    test_movement_resolution.py
    test_movement_cell_tracker.py

tests/integration/
    test_movement_world_integration.py
    test_movement_cell_boundaries.py
    test_movement_map_lifecycle.py
    test_movement_runtime_cell_data.py
```

Gerekirse mevcut test yardımcıları tekrar kullanılacak; yalnız bu aşama için gereksiz yeni test altyapısı kurulmayacaktır. Mevcut `MovementSystem`, `MovementIntegrator`, `DemoTickPump` ve Pygame klavye adaptöründe değişiklik hedeflenmemektedir.

---

## 7. Alt aşamalara bölünmüş uygulama sırası

### 4.5.1 — Dünya/harita hareket bağlamı
- `MovementWorldContext` oluşturulur.
- Kayıtlı/yüklü harita doğrulaması yapılır.
- Harita yaşam döngüsü hata davranışları test edilir.

### 4.5.2 — Konum-hücre çözümleme sonucu
- `MovementCellResolution` oluşturulur.
- `WorldPoint → AxialCoord → CellAddress → HexWorldView` akışı kurulur.
- Eksik hücre ve runtime override testleri yazılır.

### 4.5.3 — Önceki hücre takibi
- `MovementCellTracker` eklenir.
- Önceki hücre sınır eşitliği için kullanılır.
- Hata halinde iç durumun atomik korunması test edilir.

### 4.5.4 — Hareket sistemiyle entegrasyon
- Hareket tick'i sonrası takipçi çağrılır.
- Hareket konumu ve hücre çözümlemesi birlikte doğrulanır.
- Hareket çekirdeğine dünya bağımlılığı eklenmediği doğrulanır.

### 4.5.5 — Sınır ve harita yaşam döngüsü doğrulaması
- Flat-top ve pointy-top.
- Harita orijini ve farklı hex radius değerleri.
- Pozitif/negatif axial koordinatlar.
- Hücre sınırı, harita dışı koordinat, unload/reload davranışları.
- Farklı haritalarda aynı axial koordinat.

### 4.5.6 — Regresyon ve kalite doğrulaması
- Laboratuvarın tam pytest paketi.
- Core Quality CI Linux ve Windows.
- Laboratuvar CI.
- Geometri dönüşümü ve sözlük tabanlı hücre sorgusu için algoritmik karmaşıklık incelemesi.
- Ölçülmemiş performans kazanımı iddiası yoktur.

---

## 8. Test ve kabul ölçütleri

### Birim testleri

- Bağlamın doğru tipte dünya ve harita kimliği istemesi.
- Kayıtsız ve yüklenmemiş harita davranışı.
- Harita layout'unun tek kaynak olarak kullanılması.
- Çözümleme sonucunda kimlik/adres tutarlılığı.
- Hücre mevcutsa güncel verinin, yoksa `None` değerinin dönmesi.
- Takipçinin ilk konumu ve önceki hücreyi saklaması.
- Çözümleme hatasında takipçi durumunun değişmemesi.
- Aynı axial koordinatın farklı MapId değerlerinde ayrı adreslenmesi.

### Entegrasyon testleri

- 60 TPS hareket adımından sonra hücre çözümlemesinin doğru konumu izlemesi.
- Kesirli `WorldPoint` değerinin hiçbir aşamada hücre merkezine yuvarlanmaması.
- Hücre sınırı geçişinde önceki hücre eşitlik kuralının korunması.
- Flat-top ve pointy-top düzenlerinde doğru hücre seçimi.
- Runtime hücre değişikliklerinin çözümleme sonucuna yansıması.
- Harita unload edildiğinde otomatik yükleme yapılmaması.
- Harita dışı hareketin fiziksel konumu durdurmaması.
- Hareket çekirdeğinin Pygame veya world paketini import etmemesi.

### Kabul ölçütleri

- Tüm yeni testler başarılı.
- Önceki aşamalara ait testlerin tamamı başarılı.
- Hareketin sürekli dünya konumu tek doğruluk kaynağı olarak kalır.
- Hücre tespiti mevcut geometri fonksiyonunu kullanır; ikinci bir hex dönüşüm algoritması yazılmaz.
- Hücre araması tüm harita hücrelerini taramaz; doğrudan `HexWorldView`/mapping sorgusu kullanılır.
- Kayıtlı fakat yüklenmemiş harita otomatik yüklenmez.
- Hareket, harita sınırında veya eksik hücrede kesilmez.
- Linux ve Windows CI doğrulamaları başarılı.
- Kapanış raporu gerçek commit, test ve CI kanıtlarına dayanır.

---

## 9. Performans ve kaynak kullanımı

- Her çözümleme bir dünya-koordinat dönüşümü ve doğrudan hücre sözlüğü sorgusuyla sınırlı tutulur.
- Haritanın tüm hücreleri veya dünyadaki tüm haritalar taranmaz.
- Yalnızca bağlamda belirtilen tek yüklü harita kullanılır.
- Her aktörün takipçisi yalnızca bir önceki axial koordinatı ve son çözümleme sonucunu tutar.
- Tick başına gereksiz kopyalama veya tüm dünya snapshot'ı oluşturulmaz.
- Bu aşamada ölçüm yapılmadan FPS, CPU veya bellek kazanımı iddia edilmez.

---

## 10. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Hareket çekirdeğinin world katmanına bağımlı hale gelmesi | Entegrasyon yalnızca simulation takipçisinde tutulur |
| Hücre merkezine snap edilmesi | `MovementState.position` hiçbir zaman değiştirilmez |
| Sınırda hücre titremesi | Önceki hücre `world_to_axial` fonksiyonuna iletilir |
| Yanlış haritadan hücre okunması | Bağlam tek `WorldId + MapId` ile sınırlandırılır |
| Unload edilmiş haritaya erişim | Her çözümlemede yükleme durumu kontrol edilir |
| Harita dışı konumun hareketi durdurması | Eksik hücre `None` olarak temsil edilir; konum değişmez |
| Runtime değişikliklerinin görünmemesi | Hücre verisi doğrudan `HexWorldView` üzerinden okunur |
| Gereksiz dünya taraması | Geometri dönüşümü + doğrudan mapping lookup kullanılır |

---

## 11. Teslimatlar

1. `MovementWorldContext` ve harita yaşam döngüsü doğrulamaları.
2. `MovementCellResolution` değişmez veri sözleşmesi.
3. `MovementCellTracker` ve önceki hücre takibi.
4. Hareket tick'i sonrası konum-hücre entegrasyonu testleri.
5. Sınır, eksik hücre, runtime override ve harita unload testleri.
6. Tam regresyon ve Linux/Windows CI kanıtı.
7. `reports/PHASE-04.5-CLOSURE-REPORT.md` kapanış raporu.

---

## 12. Uygulama ve onay kapısı

Bu belge teknik planı tanımlar; kod uygulama izni değildir.

Uygulama sırası:

1. Kullanıcı bu teknik mimari planı onaylar veya değişiklik ister.
2. Onaydan sonra yalnızca `experiment/hex-world-laboratory` dalında 4.5.1–4.5.6 uygulanır.
3. Her alt aşamada ilgili testler çalıştırılır.
4. Tam test paketi ve CI doğrulamaları tamamlanır.
5. Kapanış raporu laboratuvar dalına eklenir ve GitHub üzerinden tekrar okunarak doğrulanır.
6. `main` ve `demo_eldoria` dallarına hiçbir değişiklik yapılmaz.

**Mevcut durum: TEKNİK PLAN KULLANICI ONAYI BEKLİYOR.**
