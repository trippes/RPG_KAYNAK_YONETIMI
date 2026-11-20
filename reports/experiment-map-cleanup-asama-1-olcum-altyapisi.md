# Eldoria — Aşama 1 Ölçüm ve Teşhis Altyapısı

**Dal:** `experiment/map-cleanup`  
**Aşama:** 1 — Ölçüm ve teşhis altyapısı  
**Uygulama tarihi:** 20 Kasım 2026

## Uygulanan değişiklikler

- `application/performance_monitor.py` eklendi. Son 600 kare için sınırlı bellek kullanan kayan ölçüm penceresi tutar.
- Kare süresi için ortalama, minimum, p50, p95, p99 ve maksimum değerleri hesaplanır.
- 16,67 ms ve 25 ms bütçelerini aşan kare sayıları raporlanır.
- `GameWindow` içinde toplam oyun adımı, oyuncu fiziği, NPC simülasyonu, dünya güncellemesi, render ve ekran sunumu ayrı zamanlanır.
- `HexGameplayView` gerçek render sayaçlarını yayımlar: toplam/görünür/çizilen hücreler, toplam aktör/NPC, çizilen aktörler ve sahne nesneleri.
- Terrain çizimi, kamera güncellemesi, NPC görsel güncellemesi ve dünya güncellemesi ayrı ölçülür.
- Fare navigasyonunda gerçek `runtime.path_to()` çağrısı sayısı ve toplam süresi ölçülür.
- Telemetri varsayılan olarak kapalıdır. Etkinleştirildiğinde her 300 karede bir JSON biçimli `ELDORIA_PERF` özeti terminale yazılır.
- Ölçüm örnekleri sınırlı tutulur; eski örnekler pencere dolduğunda otomatik düşer.

## Yerel kullanım

Windows PowerShell'de proje kök dizininde:

```powershell
$env:ELDORIA_PERF = "1"
python main.py --play
```

Oyunu normal şekilde oynat. Terminalde yaklaşık her 300 karede bir `ELDORIA_PERF` satırı görünür. Telemetriyi kapatmak için:

```powershell
Remove-Item Env:ELDORIA_PERF
```

Python içinden son ölçümler `GameWindow.performance_stats` özelliğiyle okunabilir.

## Ölçüm alanları

| Alan | Açıklama |
|---|---|
| `frames` | Kare süresi dağılımı ve uzun kare sayıları |
| `player_physics` | Oyuncu hareket fiziği ve kontrolcü maliyeti |
| `npc_simulation` | NPC davranış simülasyonu |
| `world_update` | Dünya/görsel durum güncellemesi |
| `render` | Ana render işlemi |
| `camera_ms` | Kamera güncellemesi |
| `terrain_ms` | Terrain hücrelerinin çizimi |
| `npc_visual_update_ms` | NPC görsel durumlarının güncellenmesi |
| `path_queries`, `path_query_ms` | Karedeki yol sorgusu sayısı ve süresi |
| sayaçlar | Harita hücresi, aktör, NPC ve sahne nesnesi sayıları |

## Henüz yapılmayan doğrulama

Bu değişiklikler GitHub dalına işlendi; fakat bu çalışma ortamında Eldoria oyunu kullanıcının yerel donanımında çalıştırılamadığı için gerçek FPS baseline'ı üretilmedi. 384/1.000/5.000/10.000 hücre ve 10/50/100/250 NPC senaryolarının ölçümleri yerel çalıştırma sonrasında alınmalıdır. Bu rapor performans iyileşmesi iddia etmez; Aşama 2 ve 5 kararları için ölçüm altyapısını sağlar.

Pytest/Ruff ve GitHub Actions sonucu ayrıca doğrulanmadan aşama çıkış kapısı başarılı sayılmamalıdır.
