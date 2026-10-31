from core.math.numbers import *


print("=== SAYI TESTLERİ ===")

print("10 sayı mı?              ", sayi_mi(10))
print("10.5 sayı mı?            ", sayi_mi(10.5))
print('"10" sayı mı?            ', sayi_mi("10"))
print("True sayı mı?            ", sayi_mi(True))

print()
print("=== TAM SAYI TESTLERİ ===")

print("10 tam sayı mı?          ", tam_sayi_mi(10))
print("10.5 tam sayı mı?        ", tam_sayi_mi(10.5))

print()
print("=== İŞARET TESTLERİ ===")

print("10 pozitif mi?           ", pozitif_mi(10))
print("-5 negatif mi?           ", negatif_mi(-5))
print("0 sıfır mı?              ", sifir_mi(0))
print("0 negatif olmayan mı?    ", negatif_olmayan_mi(0))

print()
print("=== MUTLAK DEĞER TESTİ ===")

print("-25 mutlak değer:        ", mutlak_deger(-25))
