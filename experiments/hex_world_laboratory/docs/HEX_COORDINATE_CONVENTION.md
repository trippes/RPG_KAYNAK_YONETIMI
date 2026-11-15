# Eldoria Hex Coordinate Convention — Aşama 2

- Durum: Aşama 2 uygulama sözleşmesi
- Yönelim desteği: Flat-top ve pointy-top
- Dünya eksenleri: Matematiksel (X sağa, Y yukarı)
- Hex boyutu: Circumradius (merkezden köşeye)
- Başlangıç yarıçapı: 1.0 dünya birimi
- Origin: Axial (0,0) hücresinin merkezi

## Koordinat türleri
- AxialCoord(q,r): tam sayı hücre adresi.
- CubeCoord(q,r,s): tam sayı koordinatı; q+r+s=0.
- WorldPoint(x,y): sürekli dünya uzayı noktası; ekran koordinatı değildir.

## Axial/cube dönüşümü
s=-q-r. Axial -> Cube: (q,r,-q-r). Cube -> Axial: (q,r); girişte cube invariant doğrulanır.

## Axial -> World
R circumradius, (x0,y0) origin.

Flat-top:
x=x0+R*(3/2*q)
y=y0+R*sqrt(3)*(r+q/2)

Pointy-top:
x=x0+R*sqrt(3)*(q+r/2)
y=y0+R*(3/2*r)

## World -> fractional axial
u=(x-x0)/R, v=(y-y0)/R.

Flat-top:
qf=(2/3)*u
rf=(-1/3)*u+(sqrt(3)/3)*v

Pointy-top:
qf=(sqrt(3)/3)*u-(1/3)*v
rf=(2/3)*v

Fractional cube (qf,rf,-qf-rf) cube_round ile hücreye dönüştürülür.

## Deterministik rounding
- En yakın tam sayıya half-up rounding; tam yarımlar pozitif sonsuza.
- Toplam sıfır değilse en büyük mutlak yuvarlama hatasına sahip bileşen düzeltilir.
- Eşitlik önceliği q, sonra r, sonra s.
- Kenar/köşe noktası tek ve tekrarlanabilir hücreye atanır.

## Polygon
- Flat-top başlangıç açısı 0 derece.
- Pointy-top başlangıç açısı 30 derece.
- Köşeler matematiksel uzayda saat yönünün tersine sıralanır.
- Merkez-köşe uzaklığı R; düzenli altıgende kenar uzunluğu R.

## Komşuluk ve mesafe
Axial yönleri: (1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1).
dq,dr,ds=-dq-dr için distance=max(abs(dq),abs(dr),abs(ds)).

## Sayısal tolerans
Merkezi başlangıç toleransları mutlak 1e-9 ve göreli 1e-9. Bunlar floating-point karşılaştırmaları içindir; hücre atama alanını genişletmez. Çok büyük koordinatlarda hassasiyet ayrıca ölçülmelidir.

## Kapsam sınırı
Dünya hücre verisi, hareket, çarpışma, kamera, ekran dönüşümü ve render sonraki aşamalardadır.
