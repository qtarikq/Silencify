"""
Dil dosyasının (dil.py) otomatik testi.

Her dilde AYNI yazıların olduğunu ve {ad} gibi boşlukların eşleştiğini kontrol eder.
Bir yazının İngilizcesini (ya da Türkçesini) unutursan bu test HATALI der.
Çalıştırmak için:  python testler/test_dil.py
"""

import string
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "silencify"))   # Uygulamanın modüllerini bulabilmek için

from arayuz import EKRANLAR
from dil import YAZILAR, dil_sec, secili_dil, yazi


def bosluklar(metin):
    """Metindeki {ad} gibi doldurulacak yerlerin adları."""
    return {ad for _, ad, _, _ in string.Formatter().parse(metin) if ad}


hatali = 0
kontrol = 0


def kontrol_et(aciklama, tamam):
    global hatali, kontrol
    kontrol += 1
    hatali += not tamam
    print(f"{'TAMAM ' if tamam else 'HATALI'}  {aciklama}")


if __name__ == "__main__":
    tr, en = YAZILAR["tr"], YAZILAR["en"]
    eksik_en = sorted(set(tr) - set(en))
    eksik_tr = sorted(set(en) - set(tr))
    kontrol_et(f"İngilizcede eksik yazı yok {eksik_en or ''}", not eksik_en)
    kontrol_et(f"Türkçede eksik yazı yok {eksik_tr or ''}", not eksik_tr)

    for dil, yazilar in YAZILAR.items():
        bos = [a for a, m in yazilar.items() if not m.strip()]
        kontrol_et(f"{dil}: boş yazı yok {bos or ''}", not bos)

    farkli = [a for a in tr if a in en and bosluklar(tr[a]) != bosluklar(en[a])]
    kontrol_et(f"{{ad}} gibi boşluklar iki dilde aynı {farkli or ''}", not farkli)

    for dil in YAZILAR:
        eksik = [f"{d}.{p}" for d in EKRANLAR for p in ("baslik", "alt", "etiket", "dugme")
                 if f"{d}.{p}" not in YAZILAR[dil]] + \
                [f"ipucu.{d}" for d in EKRANLAR if f"ipucu.{d}" not in YAZILAR[dil]]
        kontrol_et(f"{dil}: her ekranın yazıları var {eksik or ''}", not eksik)

    dil_sec("en")
    kontrol_et("İngilizce seçilince İngilizce yazı geliyor", yazi("menu_kapat") == "Quit completely")
    dil_sec("tr")
    kontrol_et("{ad} dolduruluyor", yazi("arka_plan_baslik", ad="Silencify") == "Silencify arka planda çalışıyor")
    dil_sec("fr")
    kontrol_et("Bilinmeyen dil seçilince İngilizceye düşüyor", secili_dil() == "en")

    print("-" * 60)
    print(f"{kontrol} kontrolden {kontrol - hatali} tanesi TAMAM, {hatali} tanesi HATALI")
