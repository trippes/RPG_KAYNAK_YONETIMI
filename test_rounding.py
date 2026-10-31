from core.math.rounding import *


print("=== AŞAI YUVARLAMA ===")
print("3.9 ->", asagi_yuvarla(3.9))
print("3.1 ->", asagi_yuvarla(3.1))
print("-3.1 ->", asagi_yuvarla(-3.1))

print()
print("=== YUKARI YUVARLAMA ===")
print("3.1 ->", yukari_yuvarla(3.1))
print("3.9 ->", yukari_yuvarla(3.9))
print("-3.1 ->", yukari_yuvarla(-3.1))

print()
print("=== EN YAKINA YUVARLAMA ===")
print("3.4 ->", en_yakina_yuvarla(3.4))
print("3.5 ->", en_yakina_yuvarla(3.5))
print("3.6 ->", en_yakina_yuvarla(3.6))
print("-3.4 ->", en_yakina_yuvarla(-3.4))
print("-3.5 ->", en_yakina_yuvarla(-3.5))
print("-3.6 ->", en_yakina_yuvarla(-3.6))

print()
print("=== OYUN YUVARLAMASI ===")
print("2.4 ->", oyun_yuvarla(2.4))
print("2.5 ->", oyun_yuvarla(2.5))
print("2.6 ->", oyun_yuvarla(2.6))

print()
print("=== HATA KONTROLÜ ===")

try:
    asagi_yuvarla("5.5")
except TypeError as hata:
    print("Geçersiz sayı kontrolü OK:", hata)

try:
    oyun_yuvarla(True)
except TypeError as hata:
    print("Boolean kontrolü OK:", hata)
