# Aşama 12 — Uygulama ve Doğrulama Kaydı

> **Durum:** UYGULAMA TAMAMLANDIĞI VARSAYILMAZ — 12.8 OTOMATİK DOĞRULAMA SÜRÜYOR
> **Çalışma dalı:** `experiment/hex-world-laboratory`
> **Kapsam:** Yalnızca Hex World Laboratory; ana oyun entegrasyonu yok.

## Uygulanan iş paketleri

| Paket | Uygulama durumu | Kanıt / not |
|---|---|---|
| 12.1 Altyapı denetimi | Tamamlandı | Render snapshot, sprite anchor, Y-sort, fizik obstacle, culling ve asset path kaynakları incelendi |
| 12.2 Ortak sözleşme | Uygulandı | Immutable definition, placement, scene ve adapter katmanı |
| 12.3 Ağaç prototipi | Uygulandı | Laboratuvar assets içine kopyalanan tree_test.png; bağımsız gövde collider'ı |
| 12.4 Depth sorting | Uygulandı | Normalized anchor ve depth metadata ortak draw queue'ya bağlandı |
| 12.5 Çarpışma ayrımı | Uygulandı | Tree/rock mevcut ObstacleDefinition hattında; canopy collider değildir |
| 12.6 Farklı profiller | Uygulandı | Kaya polygon collider; çalı collider'sız görsel profil |
| 12.7 Debug | Uygulandı | F3 collider; F4 anchor/depth/visual/canopy bounds + kimlik/konum |
| 12.8 Bütünleşik doğrulama | Devam ediyor | Tam test paketi, 3 oturum benchmark, PNG kanıtları, Linux/Windows CI ve son kullanıcı kabulü |

## Mimari kayıt

- Environment domain paketi Pygame import etmez.
- World placement `WorldPoint` ile authoritative kalır.
- Visual bounds ve canopy bounds fizik collider'ı üretmez.
- Collider tanımı mevcut `CircleShape` / `ConvexPolygonShape` türlerini kullanır.
- Render snapshot ve renderer simulation state değiştirmez.
- Çevresel sprite'lar mevcut Y-sort kuyruğunda actor/NPC/resource sprite'larıyla birlikte sıralanır.
- Sprite culling tam görsel dikdörtgenini kullanır; ground anchor tek başına culling ölçütü değildir.
- Laboratuvar tek başlatıcısı `python -m hex_world_lab` korunur.

## İlk otomatik doğrulama gözlemleri

Bu kayıt, CI sonuçları ve benchmark artifact'leri tamamlandığında gerçek sayılarla güncellenecektir. Başarısız veya iptal edilmiş ara CI çalıştırmaları başarılı kabul edilmez.
