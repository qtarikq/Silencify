"""
Reklam tanıma kuralını test eden program.

gozlem_kaydi.txt dosyasındaki her satıra programın kuralını (PROGRAM) ve
karşılaştırma için ilk önerilen kuralı (SENİN) uygular, kararları yan yana gösterir.
Spotify'a, sese ya da Windows'a dokunmaz; sadece metin okur.

(Elenen FORMAT ve BİRLEŞİK kuralları Git geçmişinde: commit 1043518)
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


def bilinen_reklam_metni_mi(sarki):
    """Şarkı adı bilinen bir reklam metniyse True döndürür. Harf büyüklüğüne ve sondaki noktaya bakmaz."""
    return turkce_kucuk_harf(sarki).strip().rstrip(".") in BILINEN_REKLAM_METINLERI


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
# 4. KURALLAR
# ---------------------------------------------------------------------------
def kural_senin(sarki, sanatci):
    """Karşılaştırma için: sanatçı 'Spotify' ise ya da şarkı adı bilinen bir reklam metniyse REKLAM."""
    if sanatci == "Spotify" or bilinen_reklam_metni_mi(sarki):
        return "REKLAM"
    return "-"   # Reklam değil (bu kural şarkı/podcast ayrımı yapmıyor)


def kural_program(baslik, sarki, sanatci):
    """Programın kullanacağı kural. Sorular SIRAYLA sorulur, ilk 'evet'te karar verilir."""
    if baslik is None:
        return "?"
    if baslik in DURAKLATMA_BASLIKLARI:      # 1. Duraklatılmış mı?
        return "DURDU"
    if sanatci == "Spotify":                 # 2. Sanatçı Spotify mı?
        return "REKLAM"
    if bilinen_reklam_metni_mi(sarki):       # 2+. Bilinen bir reklam metni mi?
        return "REKLAM"
    if sanatci == "":                        # 3. Sanatçı boş mu?
        return "PODCAST"
    if " - " in baslik:                      # 4. Başlık "Sanatçı - Şarkı" formatında mı?
        return "ŞARKI"
    return "REKLAM"                          # 5. Hiçbiri değilse


# ---------------------------------------------------------------------------
# 5. ANA PROGRAM
# ---------------------------------------------------------------------------
print(f"{'SAAT':<9} {'ANA BAŞLIK':<38} {'SANATÇI':<12} {'SENİN':<7} {'PROGRAM':<8}")
print("-" * 78)

reklam_sayilari = {"SENİN": 0, "PROGRAM": 0}
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
        program = kural_program(baslik, sarki, sanatci)

        # İki kural "reklam mı?" sorusuna aynı cevabı veriyor mu?
        isaret = "  <<< farklı" if (senin == "REKLAM") != (program == "REKLAM") else ""
        if isaret:
            anlasmazlik_sayisi += 1

        if senin == "REKLAM":
            reklam_sayilari["SENİN"] += 1
        if program == "REKLAM":
            reklam_sayilari["PROGRAM"] += 1

        print(
            f"{saat:<9} {kisalt(baslik or '(bulunamadı)', 38):<38} "
            f"{kisalt(sanatci or '(boş)', 12):<12} {senin:<7} {program:<8}{isaret}"
        )

print("-" * 78)
print("Kaç satıra REKLAM dendi:", reklam_sayilari)
print("Kuralların anlaşamadığı satır sayısı:", anlasmazlik_sayisi)
