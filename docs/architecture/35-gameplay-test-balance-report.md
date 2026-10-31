# Oynanış Testi ve Dengeleme Raporu

Deterministik ilk dikey dilim playtest'i `application.playtest` içindeki
`run_demo_playtest()` ile çalıştırılır.

```powershell
python -c "from application.playtest import run_demo_playtest; print(run_demo_playtest().as_dict())"
```

## Ölçülen akış

1. NPC ile konuşma ve görev alma
2. Seyahat
3. Lokasyon doğrulamalı kaynak toplama
4. Görev ödülü
5. Market satın alımı
6. Combat zaferi
7. Save/load restore

## Son ölçüm

- Seyahat: 1 tick
- Görev ödülü: 10 altın
- Satın alma sonrası bakiye: 8 altın
- Satın alma sonrası plank: 2
- Combat: 2 saldırı
- Düşman: yenildi
- Restore sonrası görev: tamamlandı

Denge eşikleri `data/playtest_balance.json` içinde tutulur. Playtest ayrıca iki
bağımsız çalıştırmanın aynı raporu üretmesini zorunlu kılar; böylece içerik
değişiklikleri deterministik davranıştan sessizce sapamaz.
