# Eldoria RPG — Aşama 1 Anatomik İskelet Uygulama Raporu

**Çalışma dalı:** \`experiment/map-cleanup\`  
**Ana plan:** \`reports/eldoria-karakter-anatomisi-ve-rig-genel-gelistirme-plani.md\`  
**Durum:** İlk 3B anatomik model uygulandı; yerel ve CI doğrulaması bekleniyor.  
**Kullanıcı tasarım kararı:** A-Pose, sağ elli X/Y/Z koordinat sistemi, yardımcı kürek kemiği kontrolü.

## 1. Uygulanan değişiklik

Yeni \`game_ui/world_rendering/humanoid_rig_3d.py\` modülü eklendi. Modül Pygame'den bağımsızdır ve mevcut 2B \`character_skeleton.py\`, rig renderer, animator veya gameplay çağrılarını değiştirmez.

### Koordinat sözleşmesi

- Sağ elli yerel koordinat sistemi.
- +X: karakterin anatomik sağı.
- +Y: karakterin ileri yönü.
- +Z: yukarı.
- Poz açıları radyan cinsinden XYZ Euler girdileridir.
- İç dönüşüm temsili normalize quaternion'dır.
- Kök eklem pelvis; zemin ankrajı pelvis köküne göre \`(0, 0, -0.47)\`.
- Runtime dünya konumu bu modülün dışında kalır.

### Anatomik hiyerarşi

- Pelvis → alt omurga → üst omurga → göğüs → boyun → baş.
- Göğüs → sol/sağ köprücük kemiği → omuz → dirsek → bilek → el.
- Göğüs üzerinde sol/sağ yardımcı kürek kemiği kontrol eklemleri.
- Pelvis → kalça → diz → ayak bileği → topuk ve ayak topu → parmak ucu.

Kürek kemiği düğümleri kontrol amaçlı işaretlenmiştir; mevcut sürümde deformasyon kemiği veya otomatik skapula çözümü değildir.

### Matematik ve doğrulama

- Yerel ebeveyn-çocuk dönüşümleri quaternion çarpımıyla çözülür.
- Eklem sınırları XYZ yerel Euler girdilerine bileşen bazında uygulanır.
- Bilinmeyen eklem, bozuk vektör, sıfır quaternion, döngülü hiyerarşi ve geçersiz kemik bağlantıları reddedilir.
- Rest poz kemik uzunlukları hesaplanabilir.
- Poz çözümü değişmez rig tanımını değiştirmez.

## 2. Korunan sınırlar

- Eski 2B iskelet ve renderer değiştirilmedi.
- Eski oyuncu/NPC sprite altyapısı değiştirilmedi.
- Gameplay, runtime dünya konumu, hareket, çarpışma, NPC itişi ve depth sorting değiştirilmedi.
- Blender veya Godot bağımlılığı eklenmedi.
- Yeni modül Pygame import etmez.

## 3. Test kapsamı

Yeni unittest dosyası \`tests/test_game_ui/test_humanoid_rig_3d.py\` eklendi. Testler koordinat sözleşmesini, anatomik zincirleri, sol/sağ simetriyi, topuk ankrajını, köprücük kemiği ebeveynliğini, kontrol eklemlerini, quaternion dönüşüm aktarımını, eklem sınırlarını, kemik uzunluklarını ve hatalı verilerin reddini kontrol eder.

Bu rapor yazılırken depo testleri yerel çalışma ortamında çalıştırılmamıştır. Test başarısı iddia edilmemektedir. GitHub Actions sonuçları ayrıca doğrulanmalıdır.

## 4. Bilinen sınırlamalar

- Bu teslim yalnızca iskelet veri modeli ve poz matematiğidir; henüz Pygame projeksiyonu veya görsel önizleme renderer'ı yoktur.
- A-Pose uzuv yerleşimi ilk anatomik taslaktır; nötr kol açısı için ayrı bir rest-orientation kalibrasyonu sonraki teknik düzeltme olabilir.
- Eklem limitleri ilk oyun kısıtlarıdır; anatomik/oyunsal görsel kabul ile ayarlanacaktır.
- Kürek kemiği kontrol düğümleri tanımlanmıştır ancak omuz hareketine otomatik katkı henüz uygulanmamıştır.
- Ayak tabanı ankrajı topuk yüksekliğine göre tanımlanmıştır; ayak temas düzlemi ve ayak ucu projeksiyonu sonraki görsel doğrulamada kontrol edilecektir.
- 3B rig mevcut runtime'a bağlanmamıştır.

## 5. Sonraki adımlar ve kabul kapısı

1. Yerel hedefli unittest ve pytest çalıştırması.
2. Ruff kontrolü.
3. GitHub Actions sonuçlarının incelenmesi.
4. İskelet debug önizlemesi ve anatomik oranların görsel kontrolü.
5. Kullanıcı görsel kabulü.

Bu rapor, Aşama 1'in tamamlandığı anlamına gelmez. Görsel önizleme, test/CI doğrulaması ve kullanıcı kabulü beklenmektedir.
