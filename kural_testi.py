"""
Reklam tanıma kurallarını test eden program.

gozlem_kaydi.txt dosyasındaki her satıra üç farklı kuralı uygular
ve kararları yan yana bir tablo olarak gösterir.
Spotify'a, sese ya da Windows'a dokunmaz; sadece metin okur.
"""

# ---------------------------------------------------------------------------
# 1. KÜTÜPHANELER (hepsi Python'la birlikte geliyor)
# ---------------------------------------------------------------------------
import ast    # "['A', 'B']" gibi bir metni gerçek Python listesine çevirmek için
import re     # Metnin içinde belli bir kalıbı bulmak için (düzenli ifadeler)

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
KAYIT_DOSYASI = "git-ignore-dosyalari/gozlem_kaydi.txt"

DURAKLATMA_BASLIKLARI = {"Spotify Free", "Spotify Premium"}
BILINEN_REKLAM_METINLERI = {"şimdi dinle", "indir ve dinle"}   # Küçük harfle, noktasız

# Bir kayıt satırının kalıbı. Parantez içindeki her (.*?) bir parçayı yakalar.
# "başlık(?:lar)?" hem eski "başlık=" hem yeni "başlıklar=" satırlarını kabul eder.
SATIR_KALIBI = re.compile(
    r"^(\d\d:\d\d:\d\d)  başlık(?:lar)?=(.*?)  şarkı=(.*?)  sanatçı=(.*?)  durum=(\S+)$"
)


# ---------------------------------------------------------------------------
# 3. YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------
def turkce_kucuk_harf(metin):
    """Türkçeye uygun küçük harfe çevirir. (Python'un lower()'ı 'İ' ve 'I' harflerini yanlış çevirir.)"""
    return metin.replace("İ", "i").replace("I", "ı").lower()


def ana_pencereyi_sec(basliklar):
    """Mini oynatıcıyı (' • ' içeren başlık) eleyip ana pencerenin başlığını döndürür. GEÇİCİ ÇÖZÜM."""
    adaylar = [b for b in basliklar if " • " not in b]
    if adaylar:
        return adaylar[-1]
    return None


def kisalt(metin, uzunluk):
    """Uzun metni tabloya sığacak şekilde kısaltır."""
    if len(metin) <= uzunluk:
        return metin
    return metin[: uzunluk - 1] + "…"


# ---------------------------------------------------------------------------
# 4. ÜÇ KURAL
# ---------------------------------------------------------------------------
def kural_senin(sarki, sanatci):
    """Sanatçı 'Spotify' ise ya da şarkı adı bilinen bir reklam metniyse REKLAM."""
    if sanatci == "Spotify":
        return "REKLAM"
    if turkce_kucuk_harf(sarki).strip().rstrip(".") in BILINEN_REKLAM_METINLERI:
        return "REKLAM"
    return "-"   # Reklam değil (bu kural şarkı/podcast ayrımı yapmıyor)


def kural_format(baslik):
    """Pencere başlığında ' - ' yoksa REKLAM."""
    if baslik is None:
        return "?"
    if baslik in DURAKLATMA_BASLIKLARI:
        return "DURDU"
    if " - " in baslik:
        return "ŞARKI"
    return "REKLAM"


def kural_birlesik(baslik, sanatci):
    """Duraklatıldı / podcast / şarkı / reklam ayrımı."""
    if baslik is None:
        return "?"
    if baslik in DURAKLATMA_BASLIKLARI:
        return "DURDU"
    if sanatci == "":
        return "PODCAST"
    if " - " in baslik:
        return "ŞARKI"
    return "REKLAM"


def kural_son(baslik, sanatci):
    """Karar verdiğimiz kural: birleşik kural + 'sanatçı Spotify ise reklam' yedeği."""
    if baslik is None:
        return "?"
    if baslik in DURAKLATMA_BASLIKLARI:
        return "DURDU"
    if sanatci == "Spotify":          # Senin kuralından gelen yedek
        return "REKLAM"
    if sanatci == "":
        return "PODCAST"
    if " - " in baslik:
        return "ŞARKI"
    return "REKLAM"


# ---------------------------------------------------------------------------
# 5. ANA PROGRAM
# ---------------------------------------------------------------------------
print(f"{'SAAT':<9} {'ANA BAŞLIK':<38} {'SANATÇI':<12} {'SENİN':<7} {'FORMAT':<7} {'BİRLEŞİK':<9} {'SON':<8}")
print("-" * 96)

reklam_sayilari = {"SENİN": 0, "FORMAT": 0, "BİRLEŞİK": 0, "SON": 0}
anlasmazlik_sayisi = 0

with open(KAYIT_DOSYASI, encoding="utf-8") as dosya:
    for satir in dosya:
        eslesme = SATIR_KALIBI.match(satir.strip())
        if not eslesme:                       # Bilgi satırı (Gözlem başladı vb.), atla
            continue

        saat, basliklar_metni, sarki_metni, sanatci_metni, durum = eslesme.groups()
        basliklar = ast.literal_eval(basliklar_metni)
        sarki = ast.literal_eval(sarki_metni)
        sanatci = ast.literal_eval(sanatci_metni)

        if basliklar is None:                 # Eski satırlarda "Spotify kapalı" olabilir
            basliklar = []
        if isinstance(basliklar, str):        # Eski satırlarda tek başlık vardı, listeye çevir
            basliklar = [basliklar]

        baslik = ana_pencereyi_sec(basliklar)

        senin = kural_senin(sarki, sanatci)
        format_ = kural_format(baslik)
        birlesik = kural_birlesik(baslik, sanatci)
        son = kural_son(baslik, sanatci)

        # Dört kural "reklam mı?" sorusuna aynı cevabı veriyor mu?
        cevaplar = {k == "REKLAM" for k in (senin, format_, birlesik, son)}
        isaret = "  <<< farklı" if len(cevaplar) > 1 else ""
        if isaret:
            anlasmazlik_sayisi += 1

        for ad, karar in (("SENİN", senin), ("FORMAT", format_), ("BİRLEŞİK", birlesik), ("SON", son)):
            if karar == "REKLAM":
                reklam_sayilari[ad] += 1

        print(
            f"{saat:<9} {kisalt(baslik or '(bulunamadı)', 38):<38} "
            f"{kisalt(sanatci or '(boş)', 12):<12} {senin:<7} {format_:<7} {birlesik:<9} {son:<8}{isaret}"
        )

print("-" * 96)
print("Kaç satıra REKLAM dendi:", reklam_sayilari)
print("Kuralların anlaşamadığı satır sayısı:", anlasmazlik_sayisi)
