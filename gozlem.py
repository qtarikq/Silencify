"""
Spotify gözlem programı.

Her saniye Spotify'ın pencere başlığına ve Windows medya bilgisine bakar.
Bir şey değiştiğinde saatiyle birlikte ekrana ve gozlem_kaydi.txt dosyasına yazar.
Durdurmak için: Ctrl+C
"""

# ---------------------------------------------------------------------------
# 1. KÜTÜPHANELER
# ---------------------------------------------------------------------------
import asyncio                     # async/await ile bekleme işleri için
import faulthandler                # Takılma olursa programın nerede beklediğini yazmak için
from datetime import datetime      # Saati yazmak için

import psutil                      # Program numarasından program adını bulmak için
import win32gui                    # Windows pencereleriyle konuşmak için
import win32process                # Bir pencerenin hangi programa ait olduğunu bulmak için
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MedyaYoneticisi,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as OynatmaDurumu,
)

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
KAYIT_DOSYASI = "gozlem_kaydi.txt"
KONTROL_ARALIGI = 1  # Kaç saniyede bir bakılacak
KARA_KUTU_DOSYASI = "kara_kutu.txt"
SURE_SINIRI = 10     # Bir tur bundan uzun sürerse takıldı say (saniye)

# Spotify'ın gizli yardımcı pencereleri. Bunlar hiç değişmiyor, yok sayıyoruz.
YARDIMCI_PENCERELER = {"GDI+ Window (Spotify.exe)", "MSCTFIME UI", "Default IME"}

# Windows'un İngilizce durum adlarını Türkçeye çeviren sözlük
DURUM_ADLARI = {
    OynatmaDurumu.PLAYING: "ÇALIYOR",
    OynatmaDurumu.PAUSED: "DURDU",
    OynatmaDurumu.STOPPED: "DURDURULDU",
}


# ---------------------------------------------------------------------------
# 3. FONKSİYONLAR
# ---------------------------------------------------------------------------
def spotify_pencere_basliklari():
    """Spotify'ın tüm pencerelerinin (ana pencere, mini oynatıcı...) başlıklarını liste olarak döndürür.
    Spotify kapalıysa boş liste döndürür."""
    bulunanlar = []

    def pencereye_bak(pencere, _):
        baslik = win32gui.GetWindowText(pencere)
        if baslik and baslik not in YARDIMCI_PENCERELER:
            _, program_no = win32process.GetWindowThreadProcessId(pencere)
            try:
                program_adi = psutil.Process(program_no).name()
            except psutil.NoSuchProcess:
                return True
            if program_adi.lower() == "spotify.exe":
                bulunanlar.append(baslik)
        return True

    win32gui.EnumWindows(pencereye_bak, None)
    return bulunanlar   # Kaç pencere varsa hepsi (mini oynatıcı açıksa 2, değilse 1, Spotify kapalıysa 0)


async def spotify_medya_bilgisi():
    """Windows medya bilgisinden (şarkı, sanatçı, durum) döndürür. Spotify yoksa None."""
    yonetici = await MedyaYoneticisi.request_async()
    for oturum in yonetici.get_sessions():
        if "spotify" in oturum.source_app_user_model_id.lower():
            bilgi = await oturum.try_get_media_properties_async()
            durum_kodu = oturum.get_playback_info().playback_status
            durum = DURUM_ADLARI.get(durum_kodu, str(durum_kodu))  # Sözlükte yoksa olduğu gibi yaz
            return bilgi.title, bilgi.artist, durum
    return None


def kaydet(mesaj):
    """Mesajı saatiyle birlikte hem ekrana hem kayıt dosyasına yazar."""
    satir = f"{datetime.now():%H:%M:%S}  {mesaj}"
    print(satir)
    with open(KAYIT_DOSYASI, "a", encoding="utf-8") as dosya:   # "a" = dosyanın sonuna ekle
        dosya.write(satir + "\n")


# ---------------------------------------------------------------------------
# 4. ANA DÖNGÜ
# ---------------------------------------------------------------------------
async def ana_dongu():
    kaydet("--- Gözlem başladı (durdurmak için Ctrl+C) ---")
    onceki = None

    # Kara kutu dosyasını aç ve programın başladığı saati yaz
    kara_kutu = open(KARA_KUTU_DOSYASI, "a", encoding="utf-8")
    kara_kutu.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} program başladı ---\n")
    kara_kutu.flush()                             # Yazılanı hemen diske gönder

    while True:                                   # Sonsuza kadar tekrar et
        faulthandler.dump_traceback_later(SURE_SINIRI, file=kara_kutu)  # Alarmı kur: 10 sn
        try:
            basliklar = spotify_pencere_basliklari()
            medya = await spotify_medya_bilgisi()
        except Exception as hata:                 # Beklenmedik bir hata olursa programı çökertme
            kaydet(f"HATA: {hata}")
            await asyncio.sleep(KONTROL_ARALIGI)
            continue
        finally:                                  # Hata olsa da olmasa da en sonda çalışır
            faulthandler.cancel_dump_traceback_later()  # Tur bitti: alarmı iptal et

        simdiki = (basliklar, medya)
        if simdiki != onceki:                     # Sadece bir şey değiştiyse yaz
            if not basliklar and medya is None:   # Pencere de yok, medya bilgisi de yok
                kaydet("Spotify bulunamadı (kapalı)")
            else:
                sarki, sanatci, durum = medya if medya else ("-", "-", "-")
                kaydet(f"başlıklar={basliklar!r}  şarkı={sarki!r}  sanatçı={sanatci!r}  durum={durum}")
            onceki = simdiki

        await asyncio.sleep(KONTROL_ARALIGI)      # 1 saniye bekle


# ---------------------------------------------------------------------------
# 5. BAŞLATMA
# ---------------------------------------------------------------------------
if __name__ == "__main__":       # Sadece bu dosya doğrudan çalıştırılınca başla
    try:
        asyncio.run(ana_dongu())
    except KeyboardInterrupt:    # Ctrl+C'ye basılınca
        kaydet("--- Gözlem durduruldu ---")
