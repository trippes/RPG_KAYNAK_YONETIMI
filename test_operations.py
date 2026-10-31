from core.math.operations import *


print("=== TOPLAMA ===")
print("10 + 5 =", topla(10, 5))

print()
print("=== ÇIKARMA ===")
print("10 - 5 =", cikar(10, 5))

print()
print("=== ÇARPMA ===")
print("10 * 5 =", carp(10, 5))

print()
print("=== BÖLME ===")
print("10 / 5 =", bol(10, 5))

print()
print("=== MODULO ===")
print("10 % 3 =", mod(10, 3))

print()
print("=== MINIMUM ===")
print("10 ve 5 ->", minimum(10, 5))

print()
print("=== MAKSIMUM ===")
print("10 ve 5 ->", maksimum(10, 5))

print()
print("=== HATA KONTROLLER ===")

try:
    bol(10, 0)
except ZeroDivisionError as hata:
    print("Sıfıra bölme kontrolü OK:", hata)

try:
    topla(10, "5")
except TypeError as hata:
    print("Geçersiz sayı kontrolü OK:", hata)
