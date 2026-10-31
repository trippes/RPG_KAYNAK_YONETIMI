"""
RPG Kaynak Yönetimi
Çekirdek 1.1.3 - Yuvarlama Sistemi

Oyundaki sayısal değerlerin standart şekilde yuvarlanmasını sağlar.
"""

import math


def asagi_yuvarla(deger):
    """
    Değeri aşağı yuvarlar.

    Örnek:
        3.9 -> 3
        3.1 -> 3
        -3.1 -> -4
    """
    if not isinstance(deger, (int, float)) or isinstance(deger, bool):
        raise TypeError("Yuvarlanacak değer sayısal olmalıdır.")

    return math.floor(deger)


def yukari_yuvarla(deger):
    """
    Değeri yukarı yuvarlar.

    Örnek:
        3.1 -> 4
        3.9 -> 4
        -3.1 -> -3
    """
    if not isinstance(deger, (int, float)) or isinstance(deger, bool):
        raise TypeError("Yuvarlanacak değer sayısal olmalıdır.")

    return math.ceil(deger)


def en_yakina_yuvarla(deger):
    """
    Değeri matematiksel olarak en yakın tam sayıya yuvarlar.

    0.5 durumunda Python'un standart round() davranışından
    bağımsız olarak oyun sistemimizin yuvarlama kuralını kullanır.

    Örnek:
        3.4 -> 3
        3.5 -> 4
        3.6 -> 4
    """
    if not isinstance(deger, (int, float)) or isinstance(deger, bool):
        raise TypeError("Yuvarlanacak değer sayısal olmalıdır.")

    if deger >= 0:
        return math.floor(deger + 0.5)

    return math.ceil(deger - 0.5)


def oyun_yuvarla(deger):
    """
    Oyunun standart yuvarlama fonksiyonudur.

    0.5 ve üzerindeki değerler yukarı yuvarlanır.

    Örnek:
        2.4 -> 2
        2.5 -> 3
        2.6 -> 3
    """
    return en_yakina_yuvarla(deger)