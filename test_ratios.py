from core.math.ratios import *


print("=== YÜZDE HESAPLAMA ===")
print("100'ün %20'si =", yuzde_hesapla(100, 20))
print("250'nin %10'u =", yuzde_hesapla(250, 10))

print()
print("=== YÜZDE ARTIRMA ===")
print("100 + %20 =", yuzde_artir(100, 20))
print("200 + %50 =", yuzde_artir(200, 50))

print()
print("=== YÜZDE AZALTMA ===")
print("100 - %20 =", yuzde_azalt(100, 20))
print("200 - %25 =", yuzde_azalt(200, 25))

print()
print("=== KATSAYI ===")
print("100 x 1.25 =", katsayi_uygula(100, 1.25))
print("100 x 0.75 =", katsayi_uygula(100, 0.75))

print()
print("=== BONUS ===")
print("100 + %20 bonus =", bonus_uygula(100, 20))
print("250 + %10 bonus =", bonus_uygula(250, 10))

print()
print("=== CEZA ===")
print("100 - %20 ceza =", ceza_uygula(100, 20))
print("200 - %25 ceza =", ceza_uygula(200, 25))

print()
print("=== ORAN ===")
print("25 / 100 =", oran_hesapla(25, 100))
print("50 / 200 =", oran_hesapla(50, 200))

print()
print("=== HATA KONTROLLER ===")

try:
    yuzde_hesapla(100, "20")
except TypeError as hata:
    print("Geçersiz sayı kontrolü OK:", hata)

try:
    oran_hesapla(25, 0)
except ZeroDivisionError as hata:
    print("Sıfıra bölme kontrolü OK:", hata)
