# Aşama 15.5 — Bağımlılık, Paketleme ve Lisans Denetimi

Denetim tarihi: 19 Kasım 2026. Kaynaklar: iki dalın pyproject.toml dosyaları, content loader/asset yolları, CI workflow tanımları ve Context7 resmi dokümantasyon sonuçları.

## 1. Python ve build metadata

| Alan | Lab | demo_eldoria | Sonuç |
|---|---|---|---|
| Python | >=3.11 | >=3.11 | Uyumlu aralık |
| Build backend | setuptools.build_meta | setuptools.build_meta | Aynı backend ailesi |
| setuptools | >=68 | >=68 | Uyumlu minimum |
| Layout | src/hex_world_lab | repository root package discovery | Farklı packaging düzeni |
| Runtime Pygame | pygame>=2.6,<3 | pygame-ce>=2.5 | Kritik dağıtım kararı |
| Test | pytest>=8,<9 extra | unittest discovery / requirements-test workflow | Farklı test entry point |
| Quality | Ruff extra | Core Quality workflow | Ortak kalite politikası tanımlanmalı |
| Entry point | python -m hex_world_lab | rpg-kaynak-yonetimi = main:main | Ayrı launcher; birleşik entry point yok |

## 2. pygame / pygame-ce çakışması

Lab pyproject pygame>=2.6,<3; Main pyproject pygame-ce>=2.5 tanımlıyor. Her iki dağıtım da Python'da pygame import namespace'ini sağlar. Pygame-CE kurulum rehberi, çakışmayı önlemek için pygame dağıtımının kaldırılmasını ve ardından pygame-ce kurulmasını açıkça önerir.

Bu nedenle aynı sanal ortama iki bağımlılığı birlikte kurmak güvenli varsayım değildir. Import adının aynı olması binary/API davranışlarının her sürümde eşdeğer olduğunu kanıtlamaz.

**A15 kararı:** Paket metadata'sı değiştirilmez ve hangi dağıtımın seçileceği burada kesinleştirilmez.

A16 öncesi seçenekler:
1. Tek dağıtım standardizasyonu: Lab ve Main temiz ortamda tek bir pygame dağıtımıyla çalışır; tüm API ve görsel regresyon testleri geçmeden seçilmez.
2. Ayrı runtime/venv: Lab ve Main bağımsız Python ortamlarında kalır; entegrasyon sınırı IPC değilse paylaşılan kod ve paketlerin import/Surface nesnesi taşımaması gerekir.
3. Ayrı paket sınırı: Pygame bağımsız domain çekirdeği ortak paket olur; her uygulama kendi Pygame adaptörünü kendi dağıtımında tutar.

Önerilen değerlendirme sırası: önce seçenek 3'ün Pygame bağımsız modüller için uygulanabilirliği, sonra tek dağıtım standardizasyonu; ayrı venv son çare/izolasyon alternatifi. Bu öneri henüz kullanıcı kararı değildir.

## 3. API ve runtime uyumluluk kontrolü

Context7 dokümanından doğrulanan hususlar:
- Pygame event queue display initialization ile yakından ilişkilidir; event pump/get/wait işlemleri display'i başlatan thread'de yürütülmelidir.
- Event queue düzenli işlenmezse dolabilir ve yeni event'ler düşebilir.
- Pygame-CE import namespace'i pygame'dir; paket adı pygame-ce olsa da kaynak kodu import pygame kullanır.
- Pygame-CE kurulum talimatı pygame dağıtımını önce kaldırmayı söyler.
- Pygame-CE metadata'sı Python >=3.11 ve LGPL v2.1 olarak tanımlanır.
- Setuptools src layout için package-dir ve packages.find.where; flat/root layout için include/exclude ayarları sunar. Flat-layout package discovery gereğinden fazla dizin paketleyebilir; Main açık include/exclude listesi kullanıyor.

Bunlar kaynak doküman bulgularıdır; iki oyunun bütün Surface/event/draw API kullanımının sürüm bazında eşdeğer olduğunu kanıtlamaz.

## 4. Packaging ve asset erişimi

Lab:
- src layout, package-dir = src ve packages.find.where = src.
- Tek modül girişi python -m hex_world_lab.
- İçerik şemaları ve demo assets repo içinde; dağıtımda gerekli dosyaların wheel/sdist içine girip girmediği temiz paket testiyle ayrıca kanıtlanmalı.

Main:
- Root/flat layout, py-modules = main ve açık package include listesi.
- game_ui assets/*.png package-data.
- Content dosyaları tool.setuptools.data-files ile content ve alt dizinlere dağıtılıyor.
- Main loader manifest-relative path ve package-root containment kontrolü yapıyor.
- AssetCatalog path traversal ve PNG metadata doğrulaması yapıyor.

Risk: data-files ile kurulan içerik dosyalarının runtime package root/path çözümü, source checkout dışındaki kurulu wheel ortamında ayrı doğrulanmalı. Lab package data ve JSON schemas da wheel/sdist smoke testinden geçirilmelidir.

## 5. CI matrix

- Main Eldoria CI: Ubuntu + Windows; Python 3.11 ve 3.12; unittest discovery; ayrıca Ubuntu headless Pygame smoke.
- Core Quality: Ubuntu Python 3.11 ve Windows Python 3.12; release-candidate verification.
- Lab CI ve Core Quality mevcut workflow dosyalarında ayrı çalışır; A15 sonunda güncel HEAD üzerinde yeniden doğrulanmalıdır.

A16 için önerilen minimum: temiz venv, pip install -e ., wheel/sdist build ve install smoke; Windows ve Linux; seçilen Python sürümleri; Pygame dummy display; import/asset resolution.

## 6. Lisans ve asset provenance

- Pygame-CE Context7 metadata'sı LGPL v2.1 gösterir; kullanılan tam sürümün paket metadata'sı ve dağıtım bildirimleri build öncesi doğrulanmalıdır.
- Pygame dağıtımının lisans metni ve bundled SDL/native library bildirimleri seçilen wheel/sdist içeriğinden kontrol edilmelidir.
- İncelenen repository tree'de root LICENSE/COPYING/NOTICE dosyası bulunmadı.
- Main content/demo_eldoria raster asset katalogları dosya yollarını ve metadata'yı tanımlar; incelenen kayıtlar kaynak üretici/lisans/provenance alanı sağlamaz.
- Lab procedural vector profiles kodla üretilir; bu, üçüncü taraf Pygame/SDL bağımlılık lisans yükümlülüklerini ortadan kaldırmaz.

**Sonuç:** Bu denetim hukuki lisans onayı değildir. Proje ve raster asset kaynak lisansları belgelenmeden dağıtım lisans uyumu kesin kabul edilemez. A16 öncesi asset provenance manifesti ve bağımlılık notice paketi gereklidir.

## 7. A16 öncesi zorunlu kontroller

1. Pygame dağıtım tercihi kullanıcı onayıyla sabitlenmeli.
2. Seçilen dağıtımla Lab/Main API smoke ve görsel regresyon testleri geçmeli.
3. Lab ve Main wheel/sdist temiz kurulum testleri geçmeli.
4. Content/asset dosyaları kurulu paketten bulunabilmeli.
5. Third-party license/notice ve asset provenance listesi tamamlanmalı.
6. Bu kontroller bitmeden pyproject veya requirements sürümleri değiştirilmemeli.
