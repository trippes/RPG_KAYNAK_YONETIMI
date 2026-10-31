"""
RPG Kaynak Yönetimi
Çekirdek 1.1.7 - Zar Sistemi

Oyundaki bütün zar atışlarını merkezi olarak yönetir.

Desteklenen temel zarlar:
    d4
    d6
    d8
    d10
    d12
    d20
    d100

Ayrıca zar ifadeleri:
    1d20
    2d6
    4d6
    2d8+3
    2d8-1
"""

import re

from core.random import tam_sayi


# ============================================================
# ZAR TİPLERİ
# ============================================================

GECERLI_ZARLAR = {
    4,
    6,
    8,
    10,
    12,
    20,
    100,
}


# ============================================================
# TEK ZAR
# ============================================================

def zar_at(zar_tipi):
    """
    Tek bir zar atar.

    Örnek:
        zar_at(6)  -> 1 ile 6 arasında sonuç
        zar_at(20) -> 1 ile 20 arasında sonuç
    """

    if not isinstance(zar_tipi, int) or isinstance(zar_tipi, bool):
        raise TypeError("Zar tipi tam sayı olmalıdır.")

    if zar_tipi not in GECERLI_ZARLAR:
        raise ValueError(
            f"Geçersiz zar tipi: d{zar_tipi}. "
            f"Geçerli zarlar: {sorted(GECERLI_ZARLAR)}"
        )

    return tam_sayi(1, zar_tipi)


# ============================================================
# ÇOKLU ZAR
# ============================================================

def zar_havuzu_at(adet, zar_tipi):
    """
    Belirtilen miktarda aynı zarı atar.

    Örnek:
        zar_havuzu_at(4, 6)
        -> [3, 6, 2, 5]
    """

    if not isinstance(adet, int) or isinstance(adet, bool):
        raise TypeError("Zar adedi tam sayı olmalıdır.")

    if adet <= 0:
        raise ValueError("Zar adedi 0'dan büyük olmalıdır.")

    return [
        zar_at(zar_tipi)
        for _ in range(adet)
    ]


# ============================================================
# ZAR TOPLAMI
# ============================================================

def zar_toplami(adet, zar_tipi):
    """
    Belirtilen miktarda zar atar ve toplamını döndürür.

    Örnek:
        zar_toplami(2, 6)
        -> 2d6 toplamı
    """

    sonuclar = zar_havuzu_at(adet, zar_tipi)

    return sum(sonuclar)


# ============================================================
# EN DÜŞÜĞÜ ÇIKARMA
# ============================================================

def dusukleri_cikar(adet, zar_tipi, cikarilacak):
    """
    Zar havuzundan en düşük sonuçları çıkarır.

    Örnek:
        4d6 -> [6, 3, 5, 2]

        1 düşük çıkarılırsa:
        [6, 3, 5]

        toplam = 14
    """

    if not isinstance(cikarilacak, int) or isinstance(cikarilacak, bool):
        raise TypeError("Çıkarılacak zar adedi tam sayı olmalıdır.")

    if cikarilacak < 0:
        raise ValueError("Çıkarılacak zar adedi negatif olamaz.")

    if cikarilacak >= adet:
        raise ValueError(
            "Çıkarılacak zar sayısı toplam zar sayısından küçük olmalıdır."
        )

    sonuclar = zar_havuzu_at(adet, zar_tipi)

    sirali = sorted(sonuclar)

    kalanlar = sirali[cikarilacak:]

    return {
        "tum_sonuclar": sonuclar,
        "sirali_sonuclar": sirali,
        "cikarilanlar": sirali[:cikarilacak],
        "kalanlar": kalanlar,
        "toplam": sum(kalanlar),
    }


# ============================================================
# EN YÜKSEĞİ ÇIKARMA
# ============================================================

def yuksekleri_cikar(adet, zar_tipi, cikarilacak):
    """
    Zar havuzundan en yüksek sonuçları çıkarır.
    """

    if not isinstance(cikarilacak, int) or isinstance(cikarilacak, bool):
        raise TypeError("Çıkarılacak zar adedi tam sayı olmalıdır.")

    if cikarilacak < 0:
        raise ValueError("Çıkarılacak zar adedi negatif olamaz.")

    if cikarilacak >= adet:
        raise ValueError(
            "Çıkarılacak zar sayısı toplam zar sayısından küçük olmalıdır."
        )

    sonuclar = zar_havuzu_at(adet, zar_tipi)

    sirali = sorted(sonuclar)

    kalanlar = sirali[:adet - cikarilacak]

    return {
        "tum_sonuclar": sonuclar,
        "sirali_sonuclar": sirali,
        "cikarilanlar": sirali[adet - cikarilacak:],
        "kalanlar": kalanlar,
        "toplam": sum(kalanlar),
    }


# ============================================================
# ZAR İFADESİ AYRIŞTIRMA
# ============================================================

def zar_ifadesi_ayristir(ifade):
    """
    Zar ifadesini ayrıştırır.

    Desteklenen örnekler:

        1d20
        2d6
        4d6
        2d8+3
        2d8-1

    Dönen yapı:

        {
            "adet": 2,
            "zar": 8,
            "degistirici": 3
        }
    """

    if not isinstance(ifade, str):
        raise TypeError("Zar ifadesi metin olmalıdır.")

    ifade = ifade.strip().lower()

    desen = r"^(\d+)d(\d+)([+-]\d+)?$"

    eslesme = re.match(desen, ifade)

    if not eslesme:
        raise ValueError(
            f"Geçersiz zar ifadesi: {ifade}"
        )

    adet = int(eslesme.group(1))
    zar_tipi = int(eslesme.group(2))

    degistirici = eslesme.group(3)

    if degistirici is None:
        degistirici = 0
    else:
        degistirici = int(degistirici)

    if adet <= 0:
        raise ValueError("Zar adedi 0'dan büyük olmalıdır.")

    if zar_tipi not in GECERLI_ZARLAR:
        raise ValueError(
            f"Geçersiz zar tipi: d{zar_tipi}"
        )

    return {
        "adet": adet,
        "zar": zar_tipi,
        "degistirici": degistirici,
    }


# ============================================================
# ZAR İFADESİ ATMA
# ============================================================

def zar_ifadesi_at(ifade):
    """
    Zar ifadesini çalıştırır.

    Örnek:

        zar_ifadesi_at("1d20")
        zar_ifadesi_at("2d6")
        zar_ifadesi_at("2d8+3")
        zar_ifadesi_at("2d8-1")
    """

    parcalar = zar_ifadesi_ayristir(ifade)

    sonuclar = zar_havuzu_at(
        parcalar["adet"],
        parcalar["zar"]
    )

    toplam = sum(sonuclar) + parcalar["degistirici"]

    return {
        "ifade": ifade,
        "adet": parcalar["adet"],
        "zar": parcalar["zar"],
        "sonuclar": sonuclar,
        "degistirici": parcalar["degistirici"],
        "toplam": toplam,
    }


# ============================================================
# 4D6 - EN DÜŞÜĞÜ ÇIKAR
# ============================================================

def dort_d_alti_eksi_en_dusuk():
    """
    Karakter özellikleri için kullanılan klasik 4d6
    yöntemini uygular.

    4d6 atılır.
    En düşük sonuç çıkarılır.
    Kalan üç zar toplanır.

    Örnek:

        Zarlar: [6, 4, 3, 2]

        Çıkarılan: 2

        Sonuç: 13
    """

    return dusukleri_cikar(
        adet=4,
        zar_tipi=6,
        cikarilacak=1,
    )


# ============================================================
# D20
# ============================================================

def d20():
    """
    1d20 atar.
    """
    return zar_at(20)


# ============================================================
# D100
# ============================================================

def d100():
    """
    1d100 atar.
    """
    return zar_at(100)