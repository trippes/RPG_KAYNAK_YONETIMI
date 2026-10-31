"""
RPG Kaynak Yönetimi
Çekirdek 1.1.6 - Rastgelelik Sistemi

Oyundaki tüm rastgele sayı ve olasılık işlemlerini
merkezi olarak yönetir.
"""

import random as _random


# ============================================================
# SEED
# ============================================================

def seed_ayarla(seed):
    """
    Rastgelelik sisteminin başlangıç seed değerini belirler.

    Aynı seed kullanıldığında aynı rastgele sayı dizisi üretilebilir.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("Seed değeri tam sayı olmalıdır.")

    _random.seed(seed)


# ============================================================
# TAM SAYI
# ============================================================

def tam_sayi(minimum, maksimum):
    """
    Belirtilen aralıkta rastgele tam sayı üretir.

    Her iki sınır da dahildir.

    Örnek:
        tam_sayi(1, 20)
    """
    if not isinstance(minimum, int) or isinstance(minimum, bool):
        raise TypeError("Minimum değer tam sayı olmalıdır.")

    if not isinstance(maksimum, int) or isinstance(maksimum, bool):
        raise TypeError("Maksimum değer tam sayı olmalıdır.")

    if minimum > maksimum:
        raise ValueError("Minimum değer maksimumdan büyük olamaz.")

    return _random.randint(minimum, maksimum)


# ============================================================
# ONDALIK SAYI
# ============================================================

def ondalik_sayi(minimum=0.0, maksimum=1.0):
    """
    Belirtilen aralıkta rastgele ondalık sayı üretir.

    Minimum dahil, maksimum hariçtir.
    """
    if not isinstance(minimum, (int, float)) or isinstance(minimum, bool):
        raise TypeError("Minimum değer sayısal olmalıdır.")

    if not isinstance(maksimum, (int, float)) or isinstance(maksimum, bool):
        raise TypeError("Maksimum değer sayısal olmalıdır.")

    if minimum > maksimum:
        raise ValueError("Minimum değer maksimumdan büyük olamaz.")

    return _random.uniform(minimum, maksimum)


# ============================================================
# OLASILIK
# ============================================================

def olasilik_yuzde(yuzde):
    """
    Belirtilen yüzde olasılıkla True veya False döndürür.

    Örnek:
        olasilik_yuzde(25)
        -> %25 başarı ihtimali
    """
    if not isinstance(yuzde, (int, float)) or isinstance(yuzde, bool):
        raise TypeError("Olasılık yüzdesi sayısal olmalıdır.")

    if yuzde < 0 or yuzde > 100:
        raise ValueError("Olasılık yüzde değeri 0 ile 100 arasında olmalıdır.")

    return _random.random() < (yuzde / 100)


# ============================================================
# SEÇİM
# ============================================================

def sec(liste):
    """
    Verilen listeden rastgele bir eleman seçer.
    """
    if not isinstance(liste, (list, tuple)):
        raise TypeError("Seçim yapılacak değer liste veya tuple olmalıdır.")

    if len(liste) == 0:
        raise ValueError("Boş listeden seçim yapılamaz.")

    return _random.choice(liste)


# ============================================================
# YÜZDELİ AĞIRLIKLI SEÇİM
# ============================================================

def agirlikli_sec(degerler, agirliklar):
    """
    Verilen değerler arasından ağırlıklarına göre rastgele seçim yapar.

    Örnek:

        degerler = ["yay", "kilic", "balta"]
        agirliklar = [50, 30, 20]

        agirlikli_sec(degerler, agirliklar)

    Burada yay seçilme açısından en yüksek ağırlığa sahiptir.
    """
    if not isinstance(degerler, (list, tuple)):
        raise TypeError("Değerler liste veya tuple olmalıdır.")

    if not isinstance(agirliklar, (list, tuple)):
        raise TypeError("Ağırlıklar liste veya tuple olmalıdır.")

    if len(degerler) == 0:
        raise ValueError("Boş listeden seçim yapılamaz.")

    if len(degerler) != len(agirliklar):
        raise ValueError(
            "Değerler ve ağırlıklar aynı uzunlukta olmalıdır."
        )

    if any(
        not isinstance(agirlik, (int, float)) or isinstance(agirlik, bool)
        for agirlik in agirliklar
    ):
        raise TypeError("Ağırlıklar sayısal olmalıdır.")

    if any(agirlik < 0 for agirlik in agirliklar):
        raise ValueError("Ağırlıklar negatif olamaz.")

    if sum(agirliklar) == 0:
        raise ValueError("Ağırlıkların toplamı sıfır olamaz.")

    return _random.choices(
        degerler,
        weights=agirliklar,
        k=1
    )[0]