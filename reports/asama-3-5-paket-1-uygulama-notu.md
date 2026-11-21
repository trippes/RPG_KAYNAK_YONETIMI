# Eldoria RPG — Aşama 3.5 Paket 1 Uygulama Notu

**Çalışma dalı:** `experiment/map-cleanup`  
**Referans mimari:** `reports/asama-3-5-serbest-hareket-teknik-mimari-plani.md`  
**Durum:** İlk domain ve hareket orkestrasyonu uygulaması tamamlandı; yerel test doğrulaması bekleniyor.

## 1. Uygulanan değişiklikler

### Domain hareket sözleşmesi
- `MovementConfig` alanlarına `acceleration`, `deceleration` ve `braking_deceleration` eklendi.
- Yeni alanlar finite, non-negative ve bool olmayan sayısal değerlerle doğrulanıyor.
- Varsayılan tuning değerleri sırasıyla 180, 240 ve 360 world units/s².
- `MovementTarget` immutable value object olarak eklendi; yalnızca `WorldPoint` ve varış toleransı taşıyor.
- `MovementIntegrator` önceki velocity değerini kullanıyor; ivmelenme, input bırakıldığında yavaşlama, hedef frenlemesi ve hedefi aşmayan displacement önerisi üretiyor.
- Domain katmanına Pygame, clock, route controller veya runtime bağımlılığı eklenmedi.

### Controller ve click-to-move
- `ContinuousPlayerMovementController` önceki kabul edilmiş state velocity değerini sonraki fixed step'e taşıyor.
- Runtime konumu dışarıdan değişmişse eski velocity devam ettirilmiyor.
- Başarısız runtime commit sonrasında proposal velocity sonraki adıma aktarılmıyor; NPC push rollback akışı korunuyor.
- Controller `GameWindow` içinde render karesi başına yeniden oluşturulmak yerine aktif hareket oturumu boyunca korunuyor. Binding, snapshot, body, actor veya config değişiminde yeniden kuruluyor.
- Click route, fiziksel waypoint'i `MovementTarget` olarak sunuyor.
- Rota cursor ilerlemesi yalnızca hex hücre sınırına geçişe bağlı değil; sıradaki fiziksel waypoint'e varış toleransı da kontrol ediliyor.
- Collinear smoothing hedefi frenleme hedefi olarak korunuyor; dönüş waypoint'leri erken geçilmiyor.
- Nihai varış adımında terminal hedef metadata'sı bir kez tüketilerek son velocity'nin hedef ötesine taşması engelleniyor.

### Fixed-step ve telemetri
- `FixedStepAccumulator` varsayılan olarak kare başına en fazla 8 substep çalıştırıyor.
- Fazla tam adımlar atılıyor, kesirli kalan süre korunuyor.
- Atılan süre toplamı ve son karedeki atılan süre ölçülebiliyor.
- Son karede çalıştırılan substep sayısı ve limit, opt-in performans sayaçlarına eklendi.
- Click route metrikleri performans sayaçlarına bağlandı.

### İçerik
- Gameplay rules doğrulaması ve movement config yükleyicisi yeni üç parametreyi destekliyor.
- `content/movement_test/gameplay_rules.json` profilleri açık tuning değerleriyle güncellendi.
- Demo paketine gelişigüzel movement profile eklenmedi.

## 2. Değiştirilen dosyalar

- `core/domain/movement/config.py`
- `core/domain/movement/target.py` (yeni)
- `core/domain/movement/integrator.py`
- `core/domain/movement/__init__.py`
- `application/content_pack.py`
- `application/continuous_player_movement.py`
- `application/click_move_route.py`
- `application/gameplay_step_clock.py`
- `game_ui/game_window.py`
- `game_ui/screens/main_screen.py`
- `game_ui/world_rendering/hex_gameplay_view.py`
- `content/movement_test/gameplay_rules.json`
- `tests/test_application/test_continuous_player_movement.py`
- `tests/test_application/test_click_move_route.py`
- `tests/test_application/test_content_pack.py`
- `tests/test_application/test_gameplay_step_clock.py`

## 3. Eklenen test kapsamı

- İvmelenme ve delta-time sınırı.
- Input bırakıldığında kademeli yavaşlama.
- RUNNING hız çarpanı.
- Hedef frenlemesi ve hedefi aşmayan displacement.
- Geçersiz arrival tolerance.
- Controller state velocity sürekliliği.
- Click route'un smoothed ve turning waypoint hedefleri.
- Hex sınırına geçince erken dönüş yapılmaması.
- Nihai hedefte terminal frenleme hedefinin korunması.
- Movement profile alanlarının content loader üzerinden yüklenmesi.
- Fixed-step catch-up sınırı, atılan süre ve substep telemetrisi.

## 4. Korunan mimari sınırlar

- `HexWorldRuntime` authoritative konum, occupancy ve spatial index sahibi olarak bırakıldı.
- Statik collision → dinamik actor collision/NPC push → runtime commit sırası değiştirilmedi.
- NPC push rollback mekanizması kaldırılmadı.
- Eski kare harita veya legacy demo sistemi eklenmedi.
- Yeni harici dependency eklenmedi.
- Bütün değişiklikler `experiment/map-cleanup` dalına işlendi.

## 5. Doğrulama durumu ve sonraki işlem

Bu çalışma ortamında depo testlerini çalıştıran bir yerel Python runtime bulunmadığından testlerin geçtiği iddia edilmemektedir. Aşağıdaki komutlar yerel çalışma kopyasında çalıştırılmalıdır:

```powershell
git pull origin experiment/map-cleanup
python -m pytest tests/test_application/test_continuous_player_movement.py tests/test_application/test_click_move_route.py tests/test_application/test_gameplay_step_clock.py tests/test_application/test_content_pack.py -q
```

Hedefli testler başarılı olduktan sonra tam test paketi çalıştırılmalıdır. Test sonuçlarına göre düzeltmeler yapılmadan Paket 1'in doğrulanmış kabulü verilmemelidir.

**Bir sonraki teknik paket:** hareket oturumu ve hedef/waypoint entegrasyonunun yerel testlerle doğrulanması; ardından klavye yön değişimi, duvar kayması ve gerçek oyun içi click-to-move frenleme tuning testleri.
