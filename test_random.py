from core.random import *


print("=== RASTGELE TAM SAYI ===")

seed_ayarla(42)

print("1-20 arası:", tam_sayi(1, 20))
print("1-20 arası:", tam_sayi(1, 20))
print("1-20 arası:", tam_sayi(1, 20))


print()
print("=== SEED TEST ===")

seed_ayarla(12345)
sonuc_1 = tam_sayi(1, 100)

seed_ayarla(12345)
sonuc_2 = tam_sayi(1, 100)

print("lk sonuç:", sonuc_1)
print("Tekrar sonuç:", sonuc_2)
print("Aynı sonuç mu?:", sonuc_1 == sonuc_2)


print()
print("=== ONDALIK SAYI ===")

seed_ayarla(42)

print("0-1 arası:", ondalik_sayi())
print("10-20 arası:", ondalik_sayi(10, 20))


print()
print("=== OLASILIK ===")

seed_ayarla(42)

print("%0 olasılık:", olasilik_yuzde(0))
print("%100 olasılık:", olasilik_yuzde(100))


print()
print("=== RASTGELE SEÇM ===")

seed_ayarla(42)

esyalalar = [
    "Bronz Kılıç",
    "Gümüş Kılıç",
    "Altın Kılıç"
]

print("Seçilen eşya:", sec(esyalalar))


print()
print("=== AIRLIKLI SEÇM ===")

seed_ayarla(42)

esyalalar = [
    "Bronz Kılıç",
    "Gümüş Kılıç",
    "Altın Kılıç"
]

agirliklar = [
    70,
    25,
    5
]

print(
    "Seçilen eşya:",
    agirlikli_sec(esyalalar, agirliklar)
)


print()
print("=== HATA KONTROLLER ===")

try:
    tam_sayi(20, 10)
except ValueError as hata:
    print("Geçersiz aralık kontrolü OK:", hata)


try:
    olasilik_yuzde(150)
except ValueError as hata:
    print("Geçersiz olasılık kontrolü OK:", hata)


try:
    sec([])
except ValueError as hata:
    print("Boş liste kontrolü OK:", hata)


try:
    agirlikli_sec(
        ["A", "B"],
        [0, 0]
    )
except ValueError as hata:
    print("Sıfır ağırlık kontrolü OK:", hata)
