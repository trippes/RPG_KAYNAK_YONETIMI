# Phase 5 — Canonical Event Dispatcher

`CanonicalEventDispatcher`, transport ile application consumer'ları arasındaki
dar sınırdır. Gameplay, World, UI veya persistence bilgisi taşımaz.

## Contract

- Consumer `consume(event)` metoduna sahip olmalıdır.
- Registration sırası deterministic consumer sırasıdır.
- Aynı consumer ikinci kez kaydedilemez.
- Event type filtresi `None` veya açık bir type kümesidir.
- `dispatch_pending()` cycle başında queue count snapshot alır.
- Consumer'ın enqueue ettiği nested event sonraki cycle'a bırakılır.
- Re-entrant `dispatch`/`dispatch_pending` çağrısı `RuntimeError` üretir.

Registration duplicate consumer'ı reddeder; registration ve dispatch sırası
deterministiktir. Bu dispatcher contract'ı Phase 10 freeze kapsamındadır.
