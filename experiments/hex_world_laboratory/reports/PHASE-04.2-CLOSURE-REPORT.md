# Aşama 4.2 — Hareket Çekirdeği Kapanış Raporu

**Durum:** UYGULAMA VE DOĞRULAMA TAMAMLANDI  
**Proje:** Eldoria — Hex World Laboratory  
**Dal:** `experiment/hex-world-laboratory`  
**Tarih:** 16 Kasım 2026  
**Teknik plan:** [PHASE-04-TECHNICAL-PLAN.md](../docs/PHASE-04-TECHNICAL-PLAN.md)  
**Genel plan:** [PHASE-04-GENERAL-PLAN.md](../docs/PHASE-04-GENERAL-PLAN.md)

---

## 1. Amaç ve kapsam

Aşama 4.2'nin amacı, 4.1'de tanımlanan hareket veri sözleşmelerini kullanan, saf Python ile çalışan ve sabit hızlı hareketi hesaplayan ilk hareket çekirdeğini oluşturmaktır.

Bu alt aşamada yalnızca tek bir hareket adımının hesaplanması ele alınmıştır. Tick üretimi, klavye girdisi, harita/hücre çözümleme, çarpışma, kamera, animasyon, NPC sistemi ve ana oyuna entegrasyon kapsam dışıdır.

## 2. Uygulama öncesi kabul edilen hareket modeli

- Hareketli varlığın fiziksel konumu, geometri paketindeki mevcut `WorldPoint` tipiyle temsil edilir.
- Yön ve hız vektörleri `Vector2` ile taşınır.
- Girdi, `MovementIntent`; hız sınırı `MovementConfig`; hareket durumu `MovementState` ile temsil edilir.
- İlk sürüm sabit hızlıdır. İvme, sürtünme ve atalet uygulanmaz.
- Hareket yönü normalize edilir. Böylece çapraz hareketin toplam hızı tek eksenli hareketten fazla olmaz.
- Hız vektörü, normalize edilmiş yön ile `max_speed` çarpılarak hesaplanır.
- Yeni konum, mevcut konuma hızın geçen süreyle çarpımının eklenmesiyle bulunur.
- Sıfır yön niyeti hareketi durdurur ve hızı sıfırlar.
- `delta_time = 0` konumu ilerletmez; ancak sıfır olmayan hareket niyetinde talep edilen hız vektörü state üzerinde korunur.
- Hareket fonksiyonu kendi saatini veya tick sayacını üretmez. Normal simülasyon çağrısında süre, dış orkestrasyon tarafından canonical 60 TPS sözleşmesine uygun olarak sağlanacaktır.

## 3. Gerçekleştirilen değişiklikler

### 3.1 Üretim kodu

Yeni dosya:
- `src/hex_world_lab/movement/integrator.py`

Güncellenen dosya:
- `src/hex_world_lab/movement/__init__.py`

`MovementIntegrator`, `MovementState`, `MovementIntent` ve `MovementConfig` girdileriyle yeni bir değişmez `MovementState` üretir. Girdi state'ini yerinde değiştirmez.

Doğrulamalar:
- Yapılandırmanın ve hareket girdilerinin beklenen tipte olması.
- `delta_time` değerinin bool veya sayısal olmayan tipte olmaması.
- Sürenin sonlu ve negatif olmayan bir sayı olması.
- Geçersiz sürelerin sessizce kabul edilmemesi.

### 3.2 Test kapsamı

Yeni test dosyası:
- `tests/unit/test_movement_integrator.py`

Testler şu davranışları kapsar:
- Yatay ve dikey hareket.
- Çapraz yönün normalize edilmesi.
- Hareket niyeti bırakıldığında durma ve hızın sıfırlanması.
- Hareket yönünün anında değişmesi.
- Sıfır azami hız.
- Sıfır zaman adımında konumun değişmemesi ve niyet hızının korunması.
- Negatif, sonlu olmayan ve geçersiz tipte zaman girdilerinin reddedilmesi.
- Geçersiz state/intent tiplerinin reddedilmesi.
- Girdi state'inin değiştirilmemesi.
- Büyük zaman adımının çekirdek içinde sessizce kırpılmaması.

## 4. Yerel test doğrulaması

Kullanıcının yerel Windows ortamında çalıştırdığı tam test komutunun sonucu:

```text
python -m pytest -q
334 passed in 1.51s
```

Bu sonuç kullanıcı tarafından bildirilen yerel test çıktısıdır; rapor, testi asistanın yerel ortamında çalıştırdığı iddiasında bulunmaz.

**Sonuç:** 334 test başarılı, başarısız test yok.

## 5. GitHub Actions doğrulaması

İlgili Core quality workflow koşusu:

- [GitHub Actions Run #1384 — 43851471263](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43851471263)
- Commit: `0d50d1d08584ba6107c12ec58c60610ded67caf0`
- Dal: `experiment/hex-world-laboratory`
- Genel sonuç: **success**

Job sonuçları:

| Job | Ortam | Sonuç |
|---|---|---|
| `verify` | `ubuntu-latest` | Başarılı |
| `verify-windows` | `windows-latest` | Başarılı |

Her iki job'da da bağımlılık kurulumu, Hex World Laboratory test paketinin kurulumu, legacy API kullanım raporu adımları ve release-candidate verification adımı başarıyla tamamlanmıştır.

Bu rapor hazırlanırken GitHub Actions run ve job kayıtları yeniden okunmuş; iki job'un da `completed / success` olduğu doğrulanmıştır.

## 6. Commit ve depo doğrulaması

Aşama 4.2 uygulama değişikliklerinin son kod commit'i:

- Commit: `0d50d1d08584ba6107c12ec58c60610ded67caf0`
- Mesaj: `Assert intent velocity for zero-time step`

Rapor eklenmeden önce laboratuvar dalının HEAD değeri aynı commit olarak doğrulanmıştır.

Bu rapor yalnızca `experiment/hex-world-laboratory` dalına eklenmiştir. `main` ve `demo_eldoria` dallarına herhangi bir yazma, merge veya geçmiş değiştirme işlemi yapılmamıştır.

## 7. Tasarım garantileri ve kapsam sınırları

Aşama 4.2 sonunda:
- Hareket çekirdeği saf Python olarak kalır; Pygame bağımlılığı eklenmemiştir.
- Fiziksel konum mevcut `WorldPoint` sözleşmesini kullanır; ikinci bir konum tipi oluşturulmamıştır.
- Çapraz hareket normalize edilir.
- State değişimi yeni nesne döndürerek yapılır; girdi state'i değiştirilmez.
- Zaman adımının kaynağı hareket çekirdeği değildir.
- Büyük zaman adımları çekirdek içinde gizlice kırpılmaz.

Henüz yapılmayan ve sonraki alt aşamalara bırakılan işler:
- 4.3: Canonical tick yürütümü ve laboratuvar demo tick pump.
- 4.4: Pygame klavye adaptörü.
- 4.5: Dünya/harita bağlamı ve hex hücre çözümlemesi.
- 4.6: Hareket prototipi, FPS bağımsızlığı ve performans kabulü.

Çarpışma, engeller, duvarlar, kamera, animasyon, NPC hareketi ve ana oyuna entegrasyon bu alt aşamanın kapsamı dışındadır.

## 8. Kabul değerlendirmesi

| Kabul ölçütü | Sonuç |
|---|---|
| Saf Python hareket integratörü | Karşılandı |
| Yön normalizasyonu ve sabit hız | Karşılandı |
| Durma ve yön değiştirme davranışları | Karşılandı |
| Geçersiz zaman girdilerinin reddi | Karşılandı |
| Girdi state'inin değişmez kalması | Karşılandı |
| Yerel tam test paketi | 334 başarılı |
| Linux CI | Başarılı |
| Windows CI | Başarılı |
| Laboratuvar dalı ve commit doğrulaması | Karşılandı |

**Nihai karar:** Aşama 4.2'nin onaylanmış kapsamı uygulanmış; yerel test sonucu ve Linux/Windows CI doğrulamaları başarılıdır. Aşama 4.2 teknik olarak tamamlanmıştır. Aşama 4.3'e geçiş, ayrı planlama ve kullanıcı onayı gerektirir.
