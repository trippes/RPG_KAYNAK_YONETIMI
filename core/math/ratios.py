"""
RPG Kaynak Yönetimi
Çekirdek 1.1.4 - Oran ve Yüzde Sistemi

Oyundaki oran, yüzde, bonus, ceza ve katsayı
hesaplamalarını merkezi olarak yönetir.
"""

from core.math.numbers import sayi_mi


def yuzde_hesapla(deger, yuzde):
    """
    Bir değerin belirtilen yüzdesini hesaplar.

    Örnek:
        yuzde_hesapla(100, 20) -> 20
        yuzde_hesapla(250, 10) -> 25
    """
    if not sayi_mi(deger) or not sayi_mi(yuzde):
        raise TypeError("Değer ve yüzde sayısal olmalıdır.")

    return deger * yuzde / 100


def yuzde_artir(deger, yuzde):
    """
    Bir değeri belirtilen yüzde oranında artırır.

    Örnek:
        yuzde_artir(100, 20) -> 120
        yuzde_artir(200, 50) -> 300
    """
    if not sayi_mi(deger) or not sayi_mi(yuzde):
        raise TypeError("Değer ve yüzde sayısal olmalıdır.")

    return deger + yuzde_hesapla(deger, yuzde)


def yuzde_azalt(deger, yuzde):
    """
    Bir değeri belirtilen yüzde oranında azaltır.

    Örnek:
        yuzde_azalt(100, 20) -> 80
        yuzde_azalt(200, 25) -> 150
    """
    if not sayi_mi(deger) or not sayi_mi(yuzde):
        raise TypeError("Değer ve yüzde sayısal olmalıdır.")

    return deger - yuzde_hesapla(deger, yuzde)


def katsayi_uygula(deger, katsayi):
    """
    Bir değere doğrudan katsayı uygular.

    Örnek:
        katsayi_uygula(100, 1.25) -> 125
        katsayi_uygula(100, 0.75) -> 75
    """
    if not sayi_mi(deger) or not sayi_mi(katsayi):
        raise TypeError("Değer ve katsayı sayısal olmalıdır.")

    return deger * katsayi


def bonus_uygula(deger, bonus):
    """
    Değere yüzde tabanlı bonus uygular.

    Örnek:
        bonus_uygula(100, 20) -> 120
    """
    if not sayi_mi(deger) or not sayi_mi(bonus):
        raise TypeError("Değer ve bonus sayısal olmalıdır.")

    return yuzde_artir(deger, bonus)


def ceza_uygula(deger, ceza):
    """
    Değerden yüzde tabanlı ceza uygular.

    Örnek:
        ceza_uygula(100, 20) -> 80
    """
    if not sayi_mi(deger) or not sayi_mi(ceza):
        raise TypeError("Değer ve ceza sayısal olmalıdır.")

    return yuzde_azalt(deger, ceza)


def oran_hesapla(parca, toplam):
    """
    Bir parçanın toplam içerisindeki oranını hesaplar.

    Sonuç 0 ile 1 arasında olur.

    Örnek:
        oran_hesapla(25, 100) -> 0.25
        oran_hesapla(50, 200) -> 0.25
    """
    if not sayi_mi(parca) or not sayi_mi(toplam):
        raise TypeError("Parça ve toplam sayısal olmalıdır.")

    if toplam == 0:
        raise ZeroDivisionError("Oran hesaplamak için toplam sıfır olamaz.")

    return parca / toplam