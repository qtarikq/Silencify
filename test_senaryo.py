"""
Reklam susturucunun ana döngüsünü SAHTE bir Spotify ile test eder.

Gerçek Spotify'a, gerçek sese ve gerçek kayıt dosyalarına hiç dokunmaz:
- Spotify'ın penceresi, medya bilgisi ve ses kaynakları taklit edilir (mock).
- Her tur ne çalacağı ve kullanıcının ne yapacağı aşağıdaki SENARYO'da yazılıdır.
- Beklemeler (1 saniye) atlanır, test saniyeler içinde biter.

Ana döngüye dokunduğun her seferde çalıştır:  python test_senaryo.py
"""

import asyncio
import tempfile
from pathlib import Path

import reklam_susturucu as r

# ---------------------------------------------------------------------------
# 1. SAHTE SPOTIFY
# ---------------------------------------------------------------------------
class SahteSes:
    """pycaw'daki SimpleAudioVolume'un taklidi: sadece sessiz/açık bilgisini tutar."""
    def __init__(self):
        self.sessiz = 0
    def GetMute(self):
        return self.sessiz
    def SetMute(self, deger, _):
        self.sessiz = deger


class SahteOturum:
    """Ses karıştırıcısındaki bir ses kaynağının taklidi."""
    def __init__(self, kimlik):
        self.InstanceIdentifier = kimlik
        self.SimpleAudioVolume = SahteSes()


A, B, C = SahteOturum("A"), SahteOturum("B"), SahteOturum("C")
oturumlar = [A, B]                      # Spotify'ın gerçekte de 2 ses kaynağı var

SARKI = ("Gripin - Aşk Nereden Nereye", ("Aşk Nereden Nereye", "Gripin", "ÇALIYOR"))
REKLAM = ("ŞİMDİ DİNLE", ("ŞİMDİ DİNLE", "ADÉLA", "ÇALIYOR"))

# ---------------------------------------------------------------------------
# 2. SENARYO: her tur (ne çalıyor, tur sonunda ne oluyor)
# ---------------------------------------------------------------------------
SENARYO = (
    [(SARKI, None)] +                                   # tur 0
    [(REKLAM, None)] * 2 +                              # tur 1-2: 2. reklam turunda kısılmalı
    [(REKLAM, "kullanıcı A'yı açar")] +                 # tur 3
    [(REKLAM, None)] * 7 +                              # tur 4-10: program fark edip dokunmamalı
    [(SARKI, None)] +                                   # tur 11: reklam arası bitti
    [(REKLAM, None)] * 2 +                              # tur 12-13: yeni reklam, yine kısılmalı
    [(REKLAM, "Spotify yeni kaynak C açar")] +          # tur 14
    [(REKLAM, None)] * 6 +                              # tur 15-20: C de kısılmalı
    [(SARKI, None)] * 2                                 # tur 21-22: ses açılmalı
)

# Beklenen ses durumu: {tur: {kaynak: True=sessiz / False=açık}}
BEKLENEN = {
    0:  {"A": False, "B": False},
    2:  {"A": True,  "B": True},                        # reklam onaylandı, kısıldı
    7:  {"A": False, "B": False},                       # sen açtın -> B de açıldı
    10: {"A": False, "B": False},                       # reklam boyunca tekrar kısılmadı
    13: {"A": True,  "B": True},                        # yeni reklam arasında yine kısıldı
    20: {"A": True,  "B": True, "C": True},             # yeni kaynak C de kısıldı
    21: {"A": False, "B": False, "C": False},           # şarkı başladı, hepsi açıldı
}

# ---------------------------------------------------------------------------
# 3. PROGRAMI SAHTE DÜNYAYA BAĞLA
# ---------------------------------------------------------------------------
tur = 0
kayitlar = []
ses_durumlari = {}


class SenaryoBitti(Exception):
    pass


async def sahte_medya():
    return SENARYO[tur][0][1]


async def sahte_bekle(_):
    """Programın 1 saniyelik beklemesi yerine: o anki ses durumunu not al, kullanıcı/Spotify eylemini yap."""
    global tur
    ses_durumlari[tur] = {o.InstanceIdentifier: bool(o.SimpleAudioVolume.GetMute()) for o in oturumlar}
    eylem = SENARYO[tur][1]
    if eylem == "kullanıcı A'yı açar":
        A.SimpleAudioVolume.sessiz = 0
    elif eylem == "Spotify yeni kaynak C açar":
        oturumlar.append(C)
    tur += 1
    if tur >= len(SENARYO):
        raise SenaryoBitti


def main():
    with tempfile.TemporaryDirectory() as gecici:      # Sahte kayıtlar için geçici klasör (sonunda silinir)
        r.KARA_KUTU_DOSYASI = Path(gecici) / "kara_kutu.txt"
        r.KISTIM_NOTU = Path(gecici) / "kistim.txt"
        r.kaydet = lambda mesaj: kayitlar.append(f"tur {tur:>2}: {mesaj}")
        r.spotify_ses_oturumlari = lambda: list(oturumlar)
        r.spotify_ana_pencere_basligi = lambda: SENARYO[tur][0][0]
        r.medya_bilgisi_zaman_sinirli = sahte_medya
        r.asyncio.sleep = sahte_bekle

        try:
            asyncio.run(r.ana_dongu())
        except SenaryoBitti:
            pass
        not_kaldi_mi = r.KISTIM_NOTU.exists()

    # --- Sonuçları kontrol et ---
    print("Programın kayıtları:")
    print("\n".join("  " + k for k in kayitlar))
    print()

    hatali = 0
    for t, beklenen in BEKLENEN.items():
        gercek = ses_durumlari.get(t)
        tamam = gercek == beklenen
        hatali += not tamam
        goster = lambda d: " ".join(f"{k}={'sessiz' if v else 'açık'}" for k, v in d.items()) if d else "-"
        print(f"{'TAMAM ' if tamam else 'HATALI'}  tur {t:>2}  beklenen: {goster(beklenen):<34} gerçek: {goster(gercek)}")

    tamam = not not_kaldi_mi
    hatali += not tamam
    print(f"{'TAMAM ' if tamam else 'HATALI'}  sonunda 'kıstım' notu kalmamalı")

    print("-" * 80)
    print(f"{len(BEKLENEN) + 1} kontrolden {len(BEKLENEN) + 1 - hatali} tanesi TAMAM, {hatali} tanesi HATALI")


if __name__ == "__main__":
    main()
