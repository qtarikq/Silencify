"""
Reklam tanıma kuralını test eden program.

gozlem_kaydi.txt dosyasındaki her satıra programın kuralını (PROGRAM) ve
karşılaştırma için ilk önerilen kuralı (SENİN) uygular, kararları yan yana gösterir.
Spotify'a, sese ya da Windows'a dokunmaz; sadece metin okur.

(Elenen FORMAT ve BİRLEŞİK kuralları Git geçmişinde: commit 1043518)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # Ana proje klasöründeki modülleri (motor, spotify...) bulabilmek için


# ---------------------------------------------------------------------------
# 1. KÜTÜPHANELER (hepsi Python'la birlikte geliyor)
# ---------------------------------------------------------------------------
import ast    # "['A', 'B']" gibi bir metni gerçek Python listesine çevirmek için
import re     # Metnin içinde belli bir kalıbı bulmak için (düzenli ifadeler)

from kural import bilinen_reklam_metni_mi, karar_ver   # Programın gerçek kuralı (kural.py)
from yollar import GOZLEM_KAYDI                        # Dosya yolu (programın kendi konumuna göre)

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
KAYIT_DOSYASI = GOZLEM_KAYDI

# Bir kayıt satırının kalıbı. Parantez içindeki her (.*?) bir parçayı yakalar.
# "başlık(?:lar)?" hem eski "başlık=" hem yeni "başlıklar=" satırlarını kabul eder.
SATIR_KALIBI = re.compile(
    r"^(\d\d:\d\d:\d\d)  başlık(?:lar)?=(.*?)  şarkı=(.*?)  sanatçı=(.*?)  durum=(\S+)$"
)


# ---------------------------------------------------------------------------
# 3. YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------
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

# Programın kuralı (karar_ver) artık kural.py dosyasında.


# ---------------------------------------------------------------------------
# 5. ANA PROGRAM
# ---------------------------------------------------------------------------
if not KAYIT_DOSYASI.exists():        # Gözlem kaydı yoksa (ör. proje yeni indirildiyse) çökme, açıkla
    print(f"Gözlem kaydı bulunamadı: {KAYIT_DOSYASI}")
    print("Önce bir süre 'python araclar/gozlem.py' çalıştırıp kayıt topla.")
    raise SystemExit

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
        program = karar_ver(baslik, sarki, sanatci)

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
