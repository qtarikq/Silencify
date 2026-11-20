"""
Ses kısma denemesi.

Spotify'ın sesini 5 saniyeliğine sessize alır, sonra geri açar.
Ne olursa olsun (hata, Ctrl+C) program biterken ses geri açılır.
"""

# ---------------------------------------------------------------------------
# 1. KÜTÜPHANELER
# ---------------------------------------------------------------------------
import time                                   # Beklemek için
from pycaw.pycaw import AudioUtilities        # Windows'un ses karıştırıcısına erişmek için

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
SESSIZ_SURE = 5   # Kaç saniye sessiz kalacak


# ---------------------------------------------------------------------------
# 3. FONKSİYONLAR
# ---------------------------------------------------------------------------
def spotify_ses_oturumlari():
    """Ses karıştırıcısında Spotify'a ait bütün ses kaynaklarını (oturumları) döndürür."""
    bulunanlar = []
    for oturum in AudioUtilities.GetAllSessions():          # Ses çıkaran her uygulamaya bak
        if oturum.Process and oturum.Process.name().lower() == "spotify.exe":
            bulunanlar.append(oturum)
    return bulunanlar


def sessiz_mi(oturumlar):
    """Spotify'ın oturumlarından herhangi biri sessizdeyse True döndürür."""
    return any(oturum.SimpleAudioVolume.GetMute() for oturum in oturumlar)


def sessize_al(oturumlar, sessiz):
    """sessiz=True ise sessize alır, False ise sesi açar. Ses seviyesine dokunmaz."""
    for oturum in oturumlar:
        oturum.SimpleAudioVolume.SetMute(1 if sessiz else 0, None)


# ---------------------------------------------------------------------------
# 4. ANA PROGRAM
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    oturumlar = spotify_ses_oturumlari()

    if not oturumlar:
        print("Spotify'ın ses kaynağı bulunamadı. Spotify açık mı ve müzik çalıyor mu?")
    else:
        print(f"Spotify'a ait {len(oturumlar)} ses kaynağı bulundu.")
        print("Şu an sessizde mi?", "EVET" if sessiz_mi(oturumlar) else "HAYIR")

        try:
            sessize_al(oturumlar, True)
            print(f"[SESSİZ] Spotify sessize alındı. {SESSIZ_SURE} saniye bekleniyor...")
            time.sleep(SESSIZ_SURE)
        finally:                                  # Hata olsa da Ctrl+C'ye basılsa da çalışır
            sessize_al(oturumlar, False)
            print("[SES AÇIK] Spotify'ın sesi geri açıldı.")
