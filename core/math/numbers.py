"""
RPG Kaynak Yönetimi
Çekirdek 1.1.1 - Sayı Sistemi

Oyunun temel sayısal değerlerini kontrol etmek ve
standartlaştırmak için kullanılan yardımcı fonksiyonlar.
"""


def sayi_mi(deger):
    """
    Verilen değerin sayısal olup olmadığını kontrol eder.

    bool değerleri sayı olarak kabul etmez.
    """
    return isinstance(deger, (int, float)) and not isinstance(deger, bool)


def tam_sayi_mi(deger):
    """
    Verilen değerin tam sayı olup olmadığını kontrol eder.
    """
    return isinstance(deger, int) and not isinstance(deger, bool)


def pozitif_mi(deger):
    """
    Verilen değerin sıfırdan büyük olup olmadığını kontrol eder.
    """
    if not sayi_mi(deger):
        return False

    return deger > 0


def negatif_mi(deger):
    """
    Verilen değerin sıfırdan küçük olup olmadığını kontrol eder.
    """
    if not sayi_mi(deger):
        return False

    return deger < 0


def sifir_mi(deger):
    """
    Verilen değerin sıfır olup olmadığını kontrol eder.
    """
    if not sayi_mi(deger):
        return False

    return deger == 0


def negatif_olmayan_mi(deger):
    """
    Verilen değerin sıfır veya pozitif olup olmadığını kontrol eder.
    """
    if not sayi_mi(deger):
        return False

    return deger >= 0


def pozitif_veya_sifir(deger):
    """
    negatif_olmayan_mi() için okunabilir bir alternatif.
    """
    return negatif_olmayan_mi(deger)


def mutlak_deger(deger):
    """
    Sayının mutlak değerini döndürür.
    """
    if not sayi_mi(deger):
        raise TypeError("Değer sayısal olmalıdır.")

    return abs(deger)
