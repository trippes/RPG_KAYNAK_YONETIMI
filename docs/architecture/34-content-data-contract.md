# Veri Odaklı İçerik Sözleşmesi

Oynanış kuralları application/domain katmanında kalır; görev, NPC, diyalog,
kaynak, reçete, pazar ve karşılaşma değerleri içerik tanımlarından yüklenir.

## Demo içeriği

Kaynak dosya:

```text
data/demo_content.json
```

Yükleme giriş noktası:

```python
from application.content_pack import load_demo_content, populate_demo_content
```

`populate_demo_content()` mevcut çağrı sözleşmesini korur. Alternatif bir içerik
dosyası test veya mod desteği için `definition_path` ile verilebilir.

## Sürümleme ve güvenlik

- İçerik tanımı `schema_version` taşır.
- Bilinmeyen gelecek sürümler reddedilir.
- Zorunlu bölümler eksikse içerik runtime'a alınmaz.
- Kimlik anahtarları `DemoContentIds` ile aynı sözleşmeyi takip eder.
- İçerik tanımı Core canonical state'e eklenmez.

Mevcut demo paketinin görev, NPC, diyalog, kaynak ve denge değerleri JSON'dan
değiştirilebilir. Yeni bir içerik türü veya birden fazla içerik örneği için
önce yükleyicide ilgili liste sözleşmesi genişletilir; oyun kuralları yine
application/domain katmanında kalır.
