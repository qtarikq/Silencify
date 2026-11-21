"""
Spotify ve Windows ile konuşan her şey.

- Spotify'ın ana pencere başlığını bulmak
- Windows medya bilgisinden şarkı / sanatçı / durum okumak
- Ses karıştırıcısında Spotify'ın ses kaynaklarını bulmak, sessize almak, açmak

Bu dosya karar VERMEZ (reklam mı değil mi -> kural.py) ve hafıza TUTMAZ
(kıstım mı, kullanıcı mı açtı -> reklam_susturucu.py). Sadece bakar ve uygular.
"""

import psutil                      # Program numarasından program adını bulmak için
import win32gui                    # Windows pencereleriyle konuşmak için
import win32process                # Bir pencerenin hangi programa ait olduğunu bulmak için
from pycaw.pycaw import AudioUtilities        # Windows'un ses karıştırıcısına erişmek için
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MedyaYoneticisi,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as OynatmaDurumu,
)

# Spotify'ın gizli yardımcı pencereleri. Bunlar hiç değişmiyor, yok sayıyoruz.
YARDIMCI_PENCERELER = {"GDI+ Window (Spotify.exe)", "MSCTFIME UI", "Default IME"}

# Windows'un İngilizce durum adlarını Türkçeye çeviren sözlük
DURUM_ADLARI = {
    OynatmaDurumu.PLAYING: "ÇALIYOR",
    OynatmaDurumu.PAUSED: "DURDU",
    OynatmaDurumu.STOPPED: "DURDURULDU",
}


# ---------------------------------------------------------------------------
# PENCERE
# ---------------------------------------------------------------------------
def spotify_ana_pencere_basligi():
    """
    Spotify'ın ANA penceresinin başlığını döndürür. Spotify kapalıysa None.
    Ana pencere = Spotify'ın en büyük penceresi (mini oynatıcı hep küçüktür).
    Pencere simge durumuna küçültülmüş olsa bile "normal" boyutuna bakılır.
    """
    en_buyuk_alan = 0
    en_buyuk_baslik = None

    def pencereye_bak(pencere, _):
        nonlocal en_buyuk_alan, en_buyuk_baslik   # Dıştaki değişkenleri değiştirebilmek için
        baslik = win32gui.GetWindowText(pencere)
        if not baslik or baslik in YARDIMCI_PENCERELER:
            return True
        _, program_no = win32process.GetWindowThreadProcessId(pencere)
        try:
            if psutil.Process(program_no).name().lower() != "spotify.exe":
                return True
        except psutil.NoSuchProcess:
            return True
        sol, ust, sag, alt = win32gui.GetWindowPlacement(pencere)[4]   # Normal boyut
        alan = (sag - sol) * (alt - ust)
        if alan > en_buyuk_alan:
            en_buyuk_alan = alan
            en_buyuk_baslik = baslik
        return True

    win32gui.EnumWindows(pencereye_bak, None)
    return en_buyuk_baslik


# ---------------------------------------------------------------------------
# MEDYA BİLGİSİ
# ---------------------------------------------------------------------------
# Windows'un medya yöneticisi. Her saniye baştan istemek bellek sızdırıyordu
# (bkz. sizinti_olcumu.py), bu yüzden BİR KERE isteyip saklıyoruz.
medya_yoneticisi = None


async def spotify_medya_bilgisi():
    """Windows medya bilgisinden (şarkı, sanatçı, durum) döndürür. Spotify yoksa None."""
    global medya_yoneticisi                   # Dosyanın en üstündeki değişkeni değiştirebilmek için
    if medya_yoneticisi is None:              # İlk sefer (ya da bir hatadan sonra) iste
        medya_yoneticisi = await MedyaYoneticisi.request_async()
    for oturum in medya_yoneticisi.get_sessions():
        if "spotify" in oturum.source_app_user_model_id.lower():
            bilgi = await oturum.try_get_media_properties_async()
            durum_kodu = oturum.get_playback_info().playback_status
            return bilgi.title, bilgi.artist, DURUM_ADLARI.get(durum_kodu, str(durum_kodu))
    return None


def medya_yoneticisini_sifirla():
    """Bir sorun olduğunda çağrılır: bir sonraki okumada Windows'tan yeni bir yönetici istenir."""
    global medya_yoneticisi
    medya_yoneticisi = None


# ---------------------------------------------------------------------------
# SES
# ---------------------------------------------------------------------------
def spotify_ses_oturumlari():
    """Ses karıştırıcısında Spotify'a ait bütün ses kaynaklarını (oturumları) döndürür."""
    bulunanlar = []
    for oturum in AudioUtilities.GetAllSessions():          # Ses çıkaran her uygulamaya bak
        if oturum.Process and oturum.Process.name().lower() == "spotify.exe":
            bulunanlar.append(oturum)
    return bulunanlar


def sessiz_mi(oturumlar):
    """Verilen ses kaynaklarından herhangi biri sessizdeyse True döndürür."""
    return any(oturum.SimpleAudioVolume.GetMute() for oturum in oturumlar)


def sessize_al(oturumlar, sessiz):
    """sessiz=True ise sessize alır, False ise sesi açar. Ses seviyesine dokunmaz."""
    for oturum in oturumlar:
        oturum.SimpleAudioVolume.SetMute(1 if sessiz else 0, None)
