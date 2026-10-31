from core.dice import *
from core.random import seed_ayarla


print("=== TEK ZAR TESTLER ===")

seed_ayarla(42)

print("d4  :", zar_at(4))
print("d6  :", zar_at(6))
print("d8  :", zar_at(8))
print("d10 :", zar_at(10))
print("d12 :", zar_at(12))
print("d20 :", zar_at(20))
print("d100:", zar_at(100))


print()
print("=== D20 TEST ===")

seed_ayarla(42)

print("d20:", d20())
print("d20:", d20())
print("d20:", d20())


print()
print("=== ZAR HAVUZU TEST ===")

seed_ayarla(42)

sonuclar = zar_havuzu_at(4, 6)

print("4d6 sonuçları:", sonuclar)
print("Toplam:", sum(sonuclar))


print()
print("=== ZAR TOPLAMI TEST ===")

seed_ayarla(42)

print("2d6 toplamı:", zar_toplami(2, 6))
print("3d8 toplamı:", zar_toplami(3, 8))


print()
print("=== EN DÜŞÜÜ ÇIKARMA TEST ===")

seed_ayarla(42)

sonuc = dusukleri_cikar(4, 6, 1)

print("Tüm sonuçlar :", sonuc["tum_sonuclar"])
print("Sıralı       :", sonuc["sirali_sonuclar"])
print("Çıkarılan    :", sonuc["cikarilanlar"])
print("Kalanlar     :", sonuc["kalanlar"])
print("Toplam       :", sonuc["toplam"])


print()
print("=== EN YÜKSE ÇIKARMA TEST ===")

seed_ayarla(42)

sonuc = yuksekleri_cikar(4, 6, 1)

print("Tüm sonuçlar :", sonuc["tum_sonuclar"])
print("Sıralı       :", sonuc["sirali_sonuclar"])
print("Çıkarılan    :", sonuc["cikarilanlar"])
print("Kalanlar     :", sonuc["kalanlar"])
print("Toplam       :", sonuc["toplam"])


print()
print("=== ZAR FADES AYRIŞTIRMA ===")

print("1d20   ->", zar_ifadesi_ayristir("1d20"))
print("2d6    ->", zar_ifadesi_ayristir("2d6"))
print("4d6    ->", zar_ifadesi_ayristir("4d6"))
print("2d8+3  ->", zar_ifadesi_ayristir("2d8+3"))
print("2d8-1  ->", zar_ifadesi_ayristir("2d8-1"))


print()
print("=== ZAR FADES ATMA ===")

seed_ayarla(42)

print("1d20  ->", zar_ifadesi_at("1d20"))
print("2d6   ->", zar_ifadesi_at("2d6"))
print("2d8+3 ->", zar_ifadesi_at("2d8+3"))
print("2d8-1 ->", zar_ifadesi_at("2d8-1"))


print()
print("=== 4D6 KARAKTER ÖZELL ===")

seed_ayarla(42)

for i in range(6):
    sonuc = dort_d_alti_eksi_en_dusuk()

    print(
        f"Özellik {i + 1}:",
        sonuc["tum_sonuclar"],
        "->",
        sonuc["kalanlar"],
        "=",
        sonuc["toplam"]
    )


print()
print("=== D100 TEST ===")

seed_ayarla(42)

print("d100:", d100())


print()
print("=== SEED TEKRARLAMA TEST ===")

seed_ayarla(12345)
sonuc_1 = zar_ifadesi_at("2d6+3")

seed_ayarla(12345)
sonuc_2 = zar_ifadesi_at("2d6+3")

print("lk sonuç   :", sonuc_1)
print("Tekrar sonuç:", sonuc_2)
print("Aynı sonuç mu?:", sonuc_1 == sonuc_2)


print()
print("=== HATA KONTROLLER ===")

try:
    zar_at(7)
except ValueError as hata:
    print("Geçersiz zar kontrolü OK:", hata)


try:
    zar_havuzu_at(0, 6)
except ValueError as hata:
    print("Geçersiz zar adedi kontrolü OK:", hata)


try:
    zar_ifadesi_ayristir("5d7")
except ValueError as hata:
    print("Geçersiz zar ifadesi kontrolü OK:", hata)


try:
    zar_ifadesi_ayristir("abc")
except ValueError as hata:
    print("Bozuk ifade kontrolü OK:", hata)


try:
    dusukleri_cikar(4, 6, 4)
except ValueError as hata:
    print("Tüm zarları çıkarma kontrolü OK:", hata)
