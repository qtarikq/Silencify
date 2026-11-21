"""
Reklam kuralının (kural.py -> karar_ver) otomatik testi.

Gerçek gözlemlerden (gozlem_kaydi.txt, susturucu_kaydi.txt) alınmış vakalar.
Kural her değiştiğinde çalıştır:  python testler/test_kural.py
Hepsi TAMAM değilse kural bir şeyi bozmuş demektir.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # Ana proje klasöründeki modülleri (motor, spotify...) bulabilmek için


from kural import karar_ver

# (açıklama, pencere başlığı, medya şarkı, medya sanatçı, beklenen karar)
VAKALAR = [
    # --- Şarkılar ---
    ("Normal şarkı",                     "Gripin - Aşk Nereden Nereye", "Aşk Nereden Nereye", "Gripin", "ŞARKI"),
    ("Şarkı adında tire var",            "Dedublüman - Bunca Yıl - Dedub Sessions", "Bunca Yıl - Dedub Sessions", "Dedublüman", "ŞARKI"),
    ("Şarkı değişti, medya 1 sn geride", "Ebru Yaşar - Ben Ne Yangınlar Gördüm", "Kurşuni Renkler", "Sezen Aksu", "ŞARKI"),

    # --- Reklamlar ---
    ("Spotify reklamı",                  "İndir ve dinle.", "İndir ve dinle.", "Spotify", "REKLAM"),
    ("Rumence Spotify reklamı (VPN)",    "Ascultă muzică, fără anunțuri.", "Ascultă muzică, fără anunțuri.", "Spotify", "REKLAM"),
    ("ADÉLA reklamı",                    "ŞİMDİ DİNLE", "ŞİMDİ DİNLE", "ADÉLA", "REKLAM"),
    ("Maykrofon reklamı",                "ŞİMDİ DİNLE", "ŞİMDİ DİNLE", "Maykrofon", "REKLAM"),
    ("Yeni reklam veren (gece)",         "Yapı Kredi ile bir adım at", "Yapı Kredi ile bir adım at", "Yapı Kredi", "REKLAM"),
    ("Yeni reklam veren (gece)",         "Bu Pazar Bim'de", "Bu Pazar Bim'de", "Bim", "REKLAM"),
    ("Reklam başladı, medya 1 sn geride","ŞİMDİ DİNLE", "Aşk Nereden Nereye", "Gripin", "REKLAM"),

    # --- Reklam bitti ama medya bilgisi geride (gece görülen gecikme) ---
    ("Spotify reklamı bitti, medya geride", "Kubilay Karça - Ayaza Serdim", "İndir ve dinle.", "Spotify", "?"),
    ("ADÉLA reklamı bitti, medya geride",   "Gripin - Aşk Nereden Nereye", "ŞİMDİ DİNLE", "ADÉLA", "?"),

    # --- Podcast'ler ---
    ("Podcast",                          "Social media and language learning", "Social media and language learning", "", "PODCAST"),
    ("Podcast adında tire var",          "Episode 39 - What's On Your \"Bucket List\"", "Episode 39 - What's On Your \"Bucket List\"", "", "PODCAST"),

    # --- Duraklatma ve bilinmeyenler ---
    ("Şarkı duraklatıldı",               "Spotify Free", "Gel", "Mabel Matiz", "DURDU"),
    ("Reklam duraklatıldı",              "Spotify Free", "İndir ve dinle.", "Spotify", "DURDU"),
    ("Premium hesapta duraklatıldı",     "Spotify Premium", "Gel", "Mabel Matiz", "DURDU"),
    ("Pencere bulunamadı",               None, "Gel", "Mabel Matiz", "?"),
]


if __name__ == "__main__":
    hatali = 0
    for aciklama, baslik, sarki, sanatci, beklenen in VAKALAR:
        sonuc = karar_ver(baslik, sarki, sanatci)
        tamam = sonuc == beklenen
        hatali += not tamam
        print(f"{'TAMAM ' if tamam else 'HATALI'}  {aciklama:<38} beklenen={beklenen:<8} sonuç={sonuc}")

    print("-" * 80)
    print(f"{len(VAKALAR)} vakadan {len(VAKALAR) - hatali} tanesi TAMAM, {hatali} tanesi HATALI")
