# Aşama 3.4 — HexWorld Çoklu Harita Yönetimi Teknik Planı

**Durum:** KULLANICI ONAYI ALINDI — UYGULAMA SIRASINDA  
**Hedef dal:** `experiment/hex-world-laboratory`  
**Laboratuvar:** `experiments/hex_world_laboratory/`  
**Bağımlılıklar:** Aşama 3.1 kimlik/adres, 3.2 hücre verisi, 3.3 harita tanımı

## 1. Amaç

Bir `WorldId` altında birden fazla `HexMapDefinition` yönetmek; harita kataloğundaki hafif kayıtları, bellekte yüklü harita tanımlarından ayırmak. Katalogda kayıtlı olmak, haritanın hücre verilerinin bellekte tutulduğu anlamına gelmemelidir.

Bu alt aşama yalnızca dünya/harita katalog modeli ve yüklenme kaydını kurar. Gerçek disk yükleyicisi, otomatik bellek politikası ve simülasyon döngüsü bu kapsamda değildir.

## 2. Mimari kararlar

### 2.1 HexWorld

- `HexWorld` değişmez bir `WorldId` taşır.
- Harita yönetimini `MapRegistry` üzerinden sunar.
- Başka bir `WorldId` değerine ait harita tanımının yüklenmesini reddeder.
- İç sözlükleri dışarıya açmaz; sorgu koleksiyonları immutable kopya/tuple olarak sunulur.

### 2.2 MapRegistry

Katalog ile yüklü harita verisi iki ayrı depoda tutulur:

- **Katalog kaydı:** Yalnızca `MapId` ve boş olmayan harita adı gibi hafif tanımlayıcı bilgiler.
- **Yüklü haritalar:** Yalnızca bellekte hazır bulunan `HexMapDefinition` nesneleri ve dolayısıyla hücre verileri.

API sözleşmesi:

- `register_map(map_id, name)`: Hafif katalog kaydı oluşturur; hücre verisi almaz.
- `load_map(definition)`: Önceden kayıtlı haritanın tanımını belleğe alır. Dünya/harita kimliği ve ad tutarlılığını doğrular.
- `unload_map(map_id)`: Yüklü tanımı bellek deposundan çıkarır; katalog kaydını korur.
- `remove_map(map_id)`: Katalog kaydını ve varsa yüklü tanımı kaldırır.
- `get_map(map_id)`: Yüklü tanımı döndürür; yüklenmemiş veya bilinmeyen harita için `None`.
- `is_registered(map_id)`, `is_loaded(map_id)`, `map_ids`, `loaded_map_ids`: Kayıt ve yüklenme durumunu sorgular.

Yinelenen kayıtlar, bilinmeyen kimliklerle yükleme/boşaltma ve tutarsız tanımlar açık, belirli istisnalarla reddedilir. Katalog ve yüklenmiş veri dışarıdan değiştirilemez.

### 2.3 Bellek ve performans sınırı

Kayıtlı ama yüklenmemiş harita için `HexMapDefinition` veya hücre koleksiyonu tutulmaz. Bu nedenle katalog kaydı hücre verisini bellekte tutmaz. Ancak bu aşama diskten yükleme, otomatik tahliye, cache limiti, eşzamanlı çoklu harita simülasyonu veya offline progression gerçekleştirmez.

Aynı anda kaç haritanın yükleneceğine karar veren politika sonraki aşama için ayrı tasarlanacaktır. Bu aşamada yalnızca yükleme/boşaltma API'si ve durum takibi sağlanır.

## 3. Dosya kapsamı

Yeni:
- `src/hex_world_lab/world/map_registry.py`
- `src/hex_world_lab/world/world.py`
- `tests/unit/test_world/test_map_registry.py`
- `tests/unit/test_world/test_world.py`

Güncellenecek:
- `src/hex_world_lab/world/__init__.py`

Aşama 2 geometri dosyaları, kimlik/hücre/harita tanımı dosyaları ve ana oyun modülleri değiştirilmeyecektir.

## 4. Test planı

- Bir dünyada birden fazla harita kaydı.
- Aynı axial koordinatın farklı haritalarda bağımsız kalması.
- Yinelenen MapId kaydının reddedilmesi.
- Farklı WorldId taşıyan haritanın yüklenmesinin reddedilmesi.
- Katalogda kayıtlı ama yüklenmemiş haritanın hücre verisi taşımaması.
- Yükleme sonrası haritanın sorgulanabilmesi.
- Boşaltma sonrası hücre verisinin registry tarafından tutulmaması ve katalog kaydının korunması.
- Katalog kaydını silmenin yüklenmiş veriyi de kaldırması.
- Bilinmeyen MapId davranışları.
- Dışarıya verilen ID listelerinin ve kayıt görünümlerinin iç durumu değiştirememesi.
- Aşama 2 geometri ve Aşama 3.1–3.3 testleri dahil tam laboratuvar test paketi.

## 5. Kabul ölçütleri

1. Bir `HexWorld` birden fazla haritayı yönetir.
2. Haritalar `MapId` ile benzersizdir.
3. Farklı dünyaya ait harita yüklenemez.
4. Katalog kaydı, harita hücre verisinden bağımsızdır.
5. Yüklenmemiş harita için registry hücre verisi tutmaz.
6. Yükleme ve boşaltma durumu deterministik biçimde sorgulanır.
7. Dışarıdan mutable iç koleksiyon erişimi yoktur.
8. Önceki tüm laboratuvar testleri geçer.
9. GitHub Actions laboratuvar CI başarılı olur.
10. Değişiklikler yalnızca laboratuvar dalında kalır.

## 6. Kapsam dışı

- JSON/disk loader veya kaydetme.
- Otomatik yükleme/boşaltma, LRU/cache limiti veya bellek bütçesi.
- Aktif harita simülasyon döngüsü ve pasif haritaların zaman telafisi.
- Harita geçişi, hareket, NPC/kaynak simülasyonu.
- Pygame çizimi ve ana oyuna entegrasyon.

## 7. Uygulama ve güvenlik sırası

1. Uygulama öncesi hedef dal HEAD ve dosya SHA'larını doğrula.
2. Bu plan belgesini hedef dala kaydet.
3. Yalnızca yukarıdaki dosyalarda kod/test değişikliklerini uygula.
4. Önce hedefli testleri, sonra tüm laboratuvar testlerini çalıştır.
5. GitHub Actions sonucunu kontrol et.
6. Commit, branch HEAD, dosya içerikleri ve değişen dosya listesini GitHub üzerinden tekrar doğrula.
7. `main` ve `demo_eldoria` dallarına yazma/merge yapma.

---

**Bu belge Aşama 3.4 kapsamını tanımlar. Kapsam dışı bellek politikası ve simülasyon davranışları ayrıca planlanıp onaylanmadan eklenmeyecektir.**
