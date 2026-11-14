# Aşama 8 — Bölüm 9 Riskler ve Önleyici Kararlar Denetim Raporu

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Denetlenen dal | `demo_eldoria` |
| Denetim bölümü | Aşama 8 planı, Bölüm 9 |
| Denetim tarihi | 14 Kasım 2026 |
| Denetim sonucu | **GEÇTİ — risk önlemleri uygulanmış; bilinçli artık riskler kayıt altına alınmıştır** |
| Denetim referansı | `reports/phase-8-content-editor-foundation-plan.md` Bölüm 9 |

## 1. Denetim yöntemi

Bölüm 9'daki on risk, planın öngördüğü olası sonuç ve önlemle birlikte tek tek incelendi. Karşılaştırma; Aşama 8.2–8.8 raporları, mimari sözleşmeler `docs/architecture/45`–`49`, uygulama kodu ve test kapsamı üzerinden yapıldı.

Bir önlemin dokümante edilmiş olması tek başına yeterli sayılmadı. Mümkün olduğunda ilgili üretim kodu sınırı ve otomatik test kanıtı da kontrol edildi. Riskler “önlem uygulanmış”, “bilinçli olarak sınırlandırılmış” veya “artık risk” olarak ayrıldı.

## 2. Risk bazında denetim

| # | Plan riski | Uygulanan önleyici karar ve kanıt | Değerlendirme |
|---:|---|---|---|
| 1 | Mevcut Asset Catalog'ın yeniden yazılması | Yeni paralel katalog/AssetManager oluşturulmadı. Mevcut `AssetCatalog` sınıfı genişletildi; eski `get()`, `available()` davranışları korundu. AssetManager üretim cache kodu değiştirilmedi; cache sözleşmesi testlerle güvenceye alındı. | **Önlem uygulandı** |
| 2 | Asset ve placement verisinin karışık kalması | Kanonik `asset_catalog.json` ile harita bazlı `placements/*.json` ayrıldı. Placement yalnızca `asset_id` referansı taşır; tekrar kullanılabilir görsel metadata'sını kopyalamaz. Yeni servisler split kaynaklara yazar. | **Önlem uygulandı; artık risk var** |
| 3 | Anchor biriminin belirsizliği | `docs/architecture/46-presentation-geometry-contract.md` anchor'ı normalize [0,1] koordinat olarak, ofset/depth'i dünya sunum pikseli olarak tanımlar. TreeSkeleton'ın ground/depth anchor ayrımı da açıklanır. Geometri modelleri bu sınırları doğrular. | **Önlem uygulandı** |
| 4 | Collision ile görsel boyutun karışması | Görsel PNG ölçüsü/scale, anchor, collision AABB ve map-cell footprint birbirinden ayrıldı. Collision'ın mevcut HexWorldView'de hassas alt-hücre çarpışması olmadığını; blocker'ın axial hücre occupancy'si kullandığını sözleşme açıkça belirtir. | **Önlem uygulandı; davranış sınırı açık** |
| 5 | Mutlak dosya yolları | Asset ve package path çözümlemesi mutlak POSIX/Windows yollarını, drive yollarını, `..` kaçışını, ters eğik çizgili yolları ve symlink ile paket kökü dışına çıkışı reddeder. Store yazma/migration yollarında da aynı kök sınırı uygulanır. | **Önlem uygulandı** |
| 6 | Şema değişiminde eski verinin kaybı | Legacy-to-split migration açıkça çağrılır; kaynak ve çıktı paketi doğrulanır. Deterministik JSON, aynı dizinde atomik replace, önceki baytların `.bak` yedeği, manifest-last yayınlama, rollback ve idempotent yeniden deneme uygulanır. Legacy dosya silinmez. | **Önlem uygulandı; çok dosyalı FS işlemi sınırı belgeli** |
| 7 | Geçersiz referansın runtime'a ulaşması | Canonical content loader asset, object ID, asset referansı, map ID ve geçerli hex hücre q/r kontrollerini runtime'a paket sunulmadan önce yapar. Split snapshot'lar ancak tüm doğrulamalar başarılı olduğunda birlikte yayımlanır. | **Önlem uygulandı** |
| 8 | Fazla soyutlama | Yeni servis, mevcut loader/catalog/placement/store modellerinin ince bir uygulama katmanı cephesidir. İkinci şema veya paralel runtime yoktur; Pygame/UI bağımlılığı eklenmemiştir. | **Önlem uygulandı** |
| 9 | Editör UI'sine erken başlanması | Content Editor penceresi, düzenleme modu, fareyle yerleştirme, sürükle-bırak, önizleme ve editör kısayolları eklenmedi. Servis/API UI'dan bağımsız tutuldu. | **Önlem uygulandı** |
| 10 | Hex varsayımlarının kare haritaya sızması | Placement q/r sözleşmesi yalnızca hex map tanımlarıyla doğrulanır. Mimari belgeler kare haritaların kendi x/y koordinat ve runtime modelinin korunduğunu, kare haritaya axial q/r dönüştürülmediğini açıkça belirtir. | **Önlem uygulandı; kare placement desteği kapsam dışı** |

## 3. Artık riskler ve bilinçli sınırlar

### 3.1 Legacy ve split kaynakların birlikte bulunması

`presentation_assets.json` geriye dönük uyumluluk için depoda tutulmaktadır. Split kaynaklar yeni runtime yolunda kanonik kaynak olsa da eski dosyanın içeriği ileride split dosyalardan farklılaşabilir. Yeni servis yalnızca split kaynaklara yazdığı için bu eski dosya otomatik senkronize edilmez.

Bu durum Aşama 8 kapsamında bilinen ve kontrollü bir geçiş riskidir; dosya sessizce silinmemiştir. Legacy dosyanın kaldırılması veya senkronizasyon politikası ayrı ve açık bir migration/uyumluluk kararı gerektirir. Bu nedenle risk tamamen ortadan kalkmış sayılmamıştır.

### 3.2 Collision ve footprint'in mevcut runtime anlamı

Collision AABB ve footprint sözleşmeleri artık açık ve doğrulanabilir durumdadır. Ancak bunların varlığı hassas piksel çarpışması veya çok hücreli occupancy davranışı anlamına gelmez. Mevcut hex blocker sistemi hücre tabanlıdır. Bu ayrım dokümante edilerek yanlış beklenti ve ilerideki editörün hatalı varsayımı önlenmiştir. Yeni fizik/occupancy davranışı bu aşamanın kapsamına alınmamıştır.

### 3.3 Kare harita yerleşim modeli

Aşama 8'in split placement sözleşmesi axial q/r kullanan hex haritalara yöneliktir. Kare haritalar kendi mevcut x/y tanımı ve runtime'ı ile korunmuştur; bu aşamada onlara yeni placement sistemi eklenmemiştir. Dolayısıyla “hex varsayımı kare haritaya sızmadı” kararı doğrulanmıştır; ancak bu, kare haritalar için yeni Content Editor placement desteği hazır demek değildir.

### 3.4 Çok dosyalı kayıt atomikliği

Dosya sistemi birden çok bağımsız yolu tek bir atomik işlemle değiştirmez. Uygulama bunu manifest-last yayınlama, önce yedek alma, dosya başına atomik replace ve başarısızlıkta rollback ile yönetir. Bu strateji mimari belgede açıkça sınırlandırılmıştır. İşletim sistemi/dosya sistemi kaynaklı rollback hatası olasılığı teorik olarak tamamen yok edilemez; hata durumunda kurtarma yedek yolları raporlanır.

## 4. Kanıt envanteri

- `reports/phase-8.2-asset-catalog-hardening-report.md`: Mevcut AssetCatalog'ın genişletilmesi ve AssetManager cache davranışının korunması.
- `reports/phase-8.3-content-placement-separation-report.md`: Split asset/placement kaynakları ve legacy uyumluluğu.
- `docs/architecture/45-presentation-content-separation.md`: Veri sorumlulukları, tekil asset referansı ve geçiş düzeni.
- `docs/architecture/46-presentation-geometry-contract.md`: Anchor, scale, collision, footprint, depth ve layer birimleri.
- `docs/architecture/47-content-validation-and-safe-loading.md`: Runtime öncesi paket bütünlüğü ve hex map koordinat doğrulaması.
- `docs/architecture/48-presentation-content-safe-persistence.md`: Staged validation, atomik kayıt, backup, rollback, manifest-last migration ve path/concurrency güvenliği.
- `docs/architecture/49-presentation-content-service-api.md`: UI/Pygame bağımsız, mevcut altyapıyı kullanan servis sınırı.
- `reports/phase-8-section-7-architecture-boundaries-audit.md`: Korunan mimari sistemlerin değişiklik envanteri denetimi.
- `reports/phase-8-section-8-test-strategy-quality-gates-audit.md`: Otomatik test ve CI kalite kapıları.

## 5. Nihai karar

**Bölüm 9 GEÇTİ.** Planın on riskinin her biri için karşılık gelen önleyici teknik kararın uygulandığı veya kapsam sınırı olarak açıkça korunduğu doğrulanmıştır. Bölüm 9'da bloke edici, önlemsiz bırakılmış bir risk tespit edilmemiştir.

Bununla birlikte, legacy dosya ile split kaynakların geçiş dönemi birlikteliği, mevcut collision/footprint runtime sınırı, kare haritalar için yeni placement desteğinin bulunmaması ve çok dosyalı dosya sistemi işlemlerinin doğal sınırı artık risk olarak kayda geçirilmiştir. Bunlar gizlenmemiş ve Aşama 8'in mevcut kapsamı dışında yeni davranış geliştirilerek çözülmeye çalışılmamıştır.

Bu rapor yalnızca Bölüm 9'u kapatır. Aşama 8 bütünüyle kapanmış değildir; Bölüm 10–14 ayrıca denetlenmelidir.
