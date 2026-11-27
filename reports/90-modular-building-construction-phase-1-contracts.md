# Eldoria — Modüler Yapı ve İnşa Sistemi
## Aşama 1: Genel Yapı ve Yapı Parçası Veri Sözleşmeleri

- **Durum:** Uygulama ve otomatik testler eklendi; kullanıcı kabulü bekleniyor
- **Hedef dal:** `experiment/map-cleanup`
- **Kapsam referansı:** `docs/architecture/90-modular-building-construction-system-roadmap.md`
- **Aşama:** 1 — Genel yapı ve yapı parçası veri sözleşmeleri

## 1. Kapsam

Bu aşama yalnızca yapı kataloğu tanımlarının domain sözleşmelerini kapsar. Yerleştirilmiş yapı örneği/runtime'ı, inşa koordinatı, snap/placement, fizik adaptörü, crafting tüketimi, render veya save/load entegrasyonu bu aşamada uygulanmamıştır.

## 2. Eklenen sözleşmeler

Kaynak: `core/domain/structures.py`

- `StructureGeometryDefinition`: Parçanın şekil türünü ve genişlik/derinlik/yükseklik zarfını tanımlar. Boyutlar mevcut `WorldPoint` ve fizik geometrisiyle uyumlu olarak canonical world unit cinsindendir. Renderer pikseli değildir.
- `StructureConnectionPort`: Bağlantı kimliği, bağlantı türü, uyumluluk anahtarı, kapasite ve zorunluluk bilgisini taşır. Bağlantı uyumluluğu aynı `connection_kind` ve `compatibility_key` eşleşmesiyle deterministik olarak değerlendirilir.
- `StructurePartDefinition`: Tekrar kullanılabilir katalog parçasının kimliğini, kategorisini, geometri zarfını, bağlantı portlarını, yönelim politikasını, düşey kullanım politikasını, malzeme profil referansını, dayanıklılığını, yerleştirme kuralı referanslarını ve görsel varlık referansını tanımlar.
- `StructureDefinition`: Bir yapı kategorisi/profili için izin verilen parça tanımlarını ve içerik etiketlerini tanımlar. Yerleştirilmiş bina veya oyuncunun canlı yapı örneği değildir; sabit prefab zorunluluğu getirmez.
- `StructureDefinitionCatalog`: Yapı ve parça tanımlarını tekil kimliklerle indeksler; yinelenen kimlikleri ve çözümlenemeyen parça referanslarını reddeder.

Sözleşmeler `core.domain` üzerinden dışa aktarılmıştır.

## 3. Bağlayıcı veri kararları

1. **Tanım ve örnek ayrıdır.** Bu aşamadaki nesneler immutable katalog tanımlarıdır. Dünyada kurulmuş yapının canlı durumu, parça örnek kimlikleri ve bağlantı grafı sonraki runtime aşamalarına aittir.
2. **Hex dünya kanonik kalır.** Bu sözleşmeler `HexCoord`, `WorldPoint`, world runtime veya entity sahipliğinin yerine geçmez.
3. **Ölçü birimi:** Geometri zarfı boyutları mevcut `WorldPoint`/fizik alanıyla tutarlı canonical world unit olarak tanımlanır. Kamera zoom'u veya piksel ölçüsü veri sözleşmesine girmez.
4. **İnşa koordinatı henüz tanımlanmadı.** Portların yerel anchor koordinatları ve parçaların yerleştirme dönüşümleri Aşama 2'ye bırakılmıştır. Aşama 1 yalnızca semantik bağlantı uyumluluğunu tanımlar.
5. **Yönelim ve düşey kullanım politikaları** sınırlı, sürümlü metin değerleridir: `fixed | quarter_turn | free` ve `ground | stackable | elevated`. Gerçek dönüşüm/kat koordinatı Aşama 2 kapsamındadır.
6. **Malzeme, yerleştirme kuralı ve görsel varlık alanları referanstır.** Bu aşama tarif, malzeme tüketimi, renderer veya asset loader entegrasyonu kurmaz.
7. **Schema version:** Yapı ve yapı parçası tanımlarının ayrı schema version alanı vardır; desteklenmeyen sürümler reddedilir. İlk sözleşme sürümü 1'dir.

## 4. Doğrulama davranışı

- Boş kimlik/ad/kategori ve boş referans metinleri reddedilir.
- Geometri boyutları ve dayanıklılık sonlu ve pozitif olmalıdır.
- Port kimlikleri bir parça tanımı içinde benzersiz olmalıdır.
- Parça referansları ve etiket listeleri boş/tekrarlı değer içeremez.
- Bir yapı tanımı en az bir izinli parça tanımı referansı taşımalıdır.
- Katalog, yinelenen parça/yapı kimliklerini ve mevcut olmayan parça tanımlarına giden referansları reddeder.
- Bağlantı portları yalnızca tür ve uyumluluk anahtarı eşleştiğinde uyumludur. Port kapasitesinin canlı bağlantı grafı üzerindeki tüketimi, henüz örnek/runtime bulunmadığı için sonraki bağlantı aşamasında uygulanacaktır.

## 5. Testler

Yeni test dosyası: `tests/test_domain/test_structure_definitions.py`

Test kapsamı:
- Geometri boyutu ve sonluluk doğrulaması
- Port kimliği, kapasite ve boolean doğrulaması
- Uyumlu/uyumsuz bağlantı portları
- Immutable parça tanımı ve yinelenen port reddi
- Yönelim politikası ve schema sürümü reddi
- Yapı tanımı parça referanslarının doğrulanması
- Katalogta yinelenen kimlik ve eksik referans reddi
- Deterministik katalog sorgusu

## 6. Kapsam dışı bırakılan işler

Yol haritası sırasına bağlı kalınarak aşağıdakiler bu aşamada yapılmamıştır:
- İnşa koordinat sistemi, port anchor koordinatları, snap ve yerleştirme doğrulayıcısı
- Yapı örneği/instance aggregate'i ve canlı bağlantı grafı
- Zemin, duvar, kapı, pencere runtime davranışı
- Crafting, envanter ve malzeme tüketimi
- Collision, navigasyon, render, save/load veya NPC entegrasyonu
- Mevcut gameplay davranışında değişiklik

## 7. Aşama 1 çıkış ölçütü değerlendirmesi

| Çıkış ölçütü | Durum |
|---|---|
| Yapı ve yapı parçası için ayrı immutable katalog sözleşmeleri | Uygulandı |
| Parça kategorisi, geometri, bağlantı, yönelim ve düşey politika alanları | Uygulandı |
| Malzeme, dayanıklılık, placement rule ve visual referansları | Uygulandı |
| Tanım verisi ile dünyadaki canlı örneğin ayrılması | Sözleşme sınırı tanımlandı; canlı örnek bu aşamada oluşturulmadı |
| Schema sürümleme ve kimlik benzersizliği | Uygulandı |
| Eksik parça referanslarının deterministik reddi | Uygulandı |
| Bağlantı portu uyumluluğunun deterministik değerlendirilmesi | Uygulandı |
| Otomatik testler | Eklendi; CI sonucu bekleniyor |
| Oyun davranışının değişmemesi | Bu aşamada gameplay/runtime entegrasyonu yapılmadı |

## 8. Değişiklik kaydı

- `core/domain/structures.py` — yeni domain sözleşmeleri
- `core/domain/__init__.py` — sözleşme dışa aktarımları
- `tests/test_domain/test_structure_definitions.py` — sözleşme testleri

Çalışma yalnızca `experiment/map-cleanup` dalına aittir. Yol haritası değiştirilmemiş, sonraki aşamalar başlatılmamıştır.

**Aşama 1'in resmî kapanışı, CI doğrulaması ve kullanıcının bu raporu kabul etmesine bağlıdır.**
