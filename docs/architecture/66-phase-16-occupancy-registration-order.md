# Aşama 16 — Non-blocking Occupancy Registration Semantics

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **OCCUPANCY KAYIT SIRASI DÜZELTİLDİ; LINUX/WINDOWS CI BAŞARILI**

## 1. Bulgu

Resource node adapter'ı kaynak düğümlerini `blocks_movement=False` ve `blocks_occupancy=False` ile kaydediyor. Önceki `HexOccupancyRegistry.add` uygulaması yeni occupant'ın blocking flags değerlerini dikkate almadan mevcut hücre blocker'larını kontrol ediyordu.

Bunun sonucu olarak:
- Önce resource node, sonra player kaydı başarılı olabiliyordu.
- Önce player, sonra aynı hücrede non-blocking resource node kaydı başarısız oluyordu.

Bu, aynı spatial state'in kayıt sırasına bağlı davranmasına yol açıyordu.

## 2. Düzeltme

`HexOccupancyRegistry.add` artık mevcut hücre blocker denetimini yalnızca yeni occupant hareketi veya occupancy'yi engelliyorsa yapıyor.

- Yeni occupant her iki blocking flag için de `False` ise mevcut actor ile aynı hücrede bulunabilir.
- Yeni occupant bu iki davranıştan en az birini engelliyorsa mevcut `can_enter` kontrolü uygulanır.
- Hareket sorguları değişmedi: mevcut blocker'lar diğer actor'ların girişini engellemeye devam eder.
- `HexWorldRuntime` ve resource node adapter'ında yeni bir position owner veya özel-case eklenmedi.

## 3. Testler

- `HexOccupancyRegistry` testinde blocking actor ve non-blocking object iki kayıt sırasıyla denenir.
- Resource node adapter testinde önce actor, sonra resource node aynı hücreye kaydedilir.
- Her iki durumda occupancy kayıtları korunur; actor hareketi blocker kurallarına tabi kalır.

## 4. CI

- Kod commit'i: `bdf986c989002e37b36d06e6274f53278ba00da0`
- GitHub Actions: [#44516742655](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44516742655)
- Linux ve Windows: başarılı.
- Her iki platformda: **2.193 test + 235 subtest başarılı**.
- Ruff ve legacy map cleanup boundary kontrolleri başarılı.
- Release-candidate verification iki platformda başarılı.
- 59 pygame deprecation uyarısı mevcut.

## 5. Sonraki teknik kapı

HexWorldRuntime için ayrı ve versioned bir snapshot/restore sözleşmesi hazırlanacaktır. Önce standalone snapshot doğrulaması yapılacak; GameSaveDocument sürüm yükseltmesi ve uygulama save/load entegrasyonu ancak world/map/entity owner doğrulamaları test edildikten sonra gerçekleştirilecektir.
