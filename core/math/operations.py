"""
RPG Kaynak Yönetimi
Çekirdek 1.1.2 - Temel Matematik İşlemleri

Oyunun temel matematiksel işlemlerini merkezi olarak yönetir.
"""

from core.math.numbers import sayi_mi


def topla(a, b):
    """
    İki sayıyı toplar.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Toplama işlemi için değerler sayısal olmalıdır.")

    return a + b


def cikar(a, b):
    """
    Birinci sayıdan ikinci sayıyı çıkarır.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Çıkarma işlemi için değerler sayısal olmalıdır.")

    return a - b


def carp(a, b):
    """
    İki sayıyı çarpar.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Çarpma işlemi için değerler sayısal olmalıdır.")

    return a * b


def bol(a, b):
    """
    Birinci sayıyı ikinci sayıya böler.

    Sıfıra bölme engellenir.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Bölme işlemi için değerler sayısal olmalıdır.")

    if b == 0:
        raise ZeroDivisionError("Bir sayı sıfıra bölünemez.")

    return a / b


def mod(a, b):
    """
    Birinci sayının ikinci sayıya bölümünden kalanı döndürür.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Modulo işlemi için değerler sayısal olmalıdır.")

    if b == 0:
        raise ZeroDivisionError("Modulo işleminde bölen sıfır olamaz.")

    return a % b


def minimum(a, b):
    """
    İki sayıdan küçük olanı döndürür.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Minimum işlemi için değerler sayısal olmalıdır.")

    return min(a, b)


def maksimum(a, b):
    """
    İki sayıdan büyük olanı döndürür.
    """
    if not sayi_mi(a) or not sayi_mi(b):
        raise TypeError("Maksimum işlemi için değerler sayısal olmalıdır.")

    return max(a, b)
