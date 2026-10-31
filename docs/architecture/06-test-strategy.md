# Core 2.0 Test Strategy

## Standart komut

```powershell
python -m unittest discover -s tests -t . -p "test_*.py"
```

Bu komut hem 1.x regression hem de architecture baseline testlerini çalıştırır.

## Test katmanları

1. Unit: value object, entity, action, time ve event davranışı.
2. Integration: Game/World/Entity/Action/Clock bağlantıları.
3. Architecture: forbidden imports, dependency direction, import cycle ve
   public boundary kuralları.
4. Contract: event, serialization, scheduler ve compatibility contract'ları.
5. Determinism: seed, tick ve aynı input için aynı sonuç.

## Baseline architecture test kapsamı

- Core dosyalarının gameplay import etmemesi
- Core dosyalarının UI/save/adapters import etmemesi
- Core import graph'ında cycle olmaması
- Public package export'larının inventory ile uyumu
- Test discovery'nin standart komutla çalışması

Architecture testleri gameplay davranışı veya gameplay sınıfı test etmez.

