# Core 2.0 Architecture Baseline

Durum: Tasarım sözleşmesi
Sürüm: Core 2.0 baseline
Kapsam: Core altyapısı; gameplay implementasyonu kapsam dışıdır.

## Amaç

Core, gelecekteki gameplay ve simulation sistemlerinin altında çalışan,
genre-independent ve deterministik bir altyapıdır. Core hiçbir gameplay
paketini import etmez.

## Kesin kararlar

1. Kod ve public API isimleri İngilizce olacaktır.
2. Dokümantasyon Türkçe, kod içi açıklamalar gerektiğinde kısa İngilizce olacaktır.
3. `Game` bir application façade'sidir; domain veya gameplay kuralı taşımaz.
4. Entity'nin World ownership işlemi application/runtime katmanında tek noktadan yapılır.
5. World-local eventler global event akışına runtime dispatcher tarafından aktarılır.
6. Event zamanı simulation tick'tir; wall-clock zamanı yalnızca opsiyonel metadata'dır.
7. Simulation zamanı ile gerçek zaman kesinlikle ayrı kavramlardır.
8. RPG anlamındaki Resource gameplay/simulation katmanındadır; Core yalnızca genel quantity/unit value object'leri sağlayabilir.
9. `GameState` session/runtime durumudur; World state değildir.
10. Core → gameplay bağımlılığı yasaktır; gameplay → Core kabul edilir.
11. Standart test komutu `python -m unittest discover -s tests -t . -p "test_*.py"` olacaktır.
12. Python kaynakları UTF-8 BOM'suz tutulacaktır.
13. Runtime dependency yoktur; proje metadata'sı `pyproject.toml` içinde tutulur.
14. 1.x import yolları compatibility façade ile geçici olarak korunur.
15. Deprecation warning'leri bir sürüm önceden verilir; removal yalnızca major sürümde yapılır.
16. Save/load serialization contract'ı versioned, typed ve deterministic olacaktır.
17. Scheduler doğrudan gameplay callback zinciri yerine typed scheduled command/event üretir.
18. Action lifecycle eventleri create/start/complete/cancel/fail durumlarını kapsar.
19. Position mutation yalnızca domain command/service üzerinden yapılır; World bounds burada doğrulanır.
20. Architecture testleri yalnızca dependency, import, cycle ve public boundary kurallarını doğrular.
21. Canonical 2.0 layout `01-package-layout.md` içinde sabittir.
22. Gameplay geliştirmesi yalnızca baseline exit criteria sağlandıktan sonra başlayabilir.

## Baseline exit criteria

- Doküman sözleşmeleri onaylanmış olmalı.
- Public API inventory tamamlanmış olmalı.
- Architecture tests standart discovery ile çalışmalı.
- 1.x regression suite başarılı olmalı.
- Core kaynaklarında gameplay import'u bulunmamalı.
- Compatibility ve deprecation politikası uygulanabilir olmalı.
- Serialization contract'ı implementation'dan bağımsız şekilde tanımlanmış olmalı.

Phase 10 freeze'ta canonical foundation, domain, application, simulation ve
persistence contract'ları sabittir. Legacy yüzeyler yalnızca compatibility
sınırında korunur; yeni gameplay/Core 2.1 World Model bu baseline'ın dışındadır.
