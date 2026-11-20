"""
Spotify Reklam Susturucu

Spotify'da reklam çalınca Spotify'ın sesini kısar, reklam bitince geri açar.
Sadece kendi kıstığı sesi açar; sen Spotify'ı kendin sessize aldıysan dokunmaz.
Durdurmak için: Ctrl+C (kapanırken ses kısıksa geri açılır)
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

from gozlem import spotify_medya_bilgisi                            # Şarkı, sanatçı, durum
from kural import karar_ver                                         # REKLAM / ŞARKI / PODCAST / DURDU
from ses_deneme import sessiz_mi, sessize_al, spotify_ses_oturumlari  # Ses kısma / açma

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
KAYIT_DOSYASI = "git-ignore-dosyalari/susturucu_kaydi.txt"
KARA_KUTU_DOSYASI = "git-ignore-dosyalari/kara_kutu.txt"

KONTROL_ARALIGI = 1        # Spotify açıkken kaç saniyede bir bakılacak
KAPALI_ARALIGI = 5         # Spotify kapalıyken kaç saniyede bir bakılacak
GEREKEN_TEKRAR = 2         # Bir karar kaç kontrol üst üste aynı olursa uygulanacak
MEDYA_ZAMAN_SINIRI = 3     # Windows medya bilgisi için en fazla kaç saniye beklenecek
SURE_SINIRI = 10           # Bir tur bundan uzun sürerse kara kutuya yaz (saniye)

YARDIMCI_PENCERELER = {"GDI+ Window (Spotify.exe)", "MSCTFIME UI", "Default IME"}


# ---------------------------------------------------------------------------
# 3. FONKSİYONLAR
# ---------------------------------------------------------------------------
def kaydet(mesaj):
    """Mesajı saatiyle birlikte hem ekrana hem kayıt dosyasına yazar."""
    satir = f"{datetime.now():%H:%M:%S}  {mesaj}"
    print(satir)
    with open(KAYIT_DOSYASI, "a", encoding="utf-8") as dosya:
        dosya.write(satir + "\n")


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


async def medya_bilgisi_zaman_sinirli():
    """Medya bilgisini okur; Windows MEDYA_ZAMAN_SINIRI saniyede cevap vermezse None döndürür."""
    try:
        return await asyncio.wait_for(spotify_medya_bilgisi(), MEDYA_ZAMAN_SINIRI)
    except asyncio.TimeoutError:
        kaydet(f"UYARI: Medya bilgisi {MEDYA_ZAMAN_SINIRI} saniyede gelmedi, bu tur atlandı")
        return None


# ---------------------------------------------------------------------------
# 4. ANA DÖNGÜ
# ---------------------------------------------------------------------------
async def ana_dongu():
    biz_kistik = False          # Spotify'ı BİZ mi sessize aldık?
    aday_karar = None           # En son görülen karar
    aday_sayisi = 0             # O karar kaç kontrol üst üste görüldü
    uygulanan_karar = None      # En son uygulanan (onaylanmış) karar
    uygulanan_baslik = None     # O karar verilirken pencere başlığı neydi (kayda yazmak için)
    spotify_acik = None         # Spotify'ın açık/kapalı durumu (değişince yazmak için)

    kara_kutu = open(KARA_KUTU_DOSYASI, "a", encoding="utf-8")
    kara_kutu.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} reklam_susturucu başladı ---\n")
    kara_kutu.flush()

    kaydet("=== Reklam susturucu başladı (durdurmak için Ctrl+C) ===")

    try:
        while True:
            faulthandler.dump_traceback_later(SURE_SINIRI, file=kara_kutu)   # Alarmı kur
            try:
                baslik = spotify_ana_pencere_basligi()
                medya = await medya_bilgisi_zaman_sinirli()
            except Exception as hata:
                kaydet(f"HATA: {hata}")
                await asyncio.sleep(KONTROL_ARALIGI)
                continue
            finally:
                faulthandler.cancel_dump_traceback_later()               # Alarmı iptal et

            # --- Spotify kapalı mı? ---
            if baslik is None and medya is None:
                if spotify_acik is not False:
                    kaydet("Spotify kapalı, bekleniyor...")
                    spotify_acik = False
                biz_kistik = False             # Spotify kapandıysa kıstığımız ses de gitti
                aday_karar = uygulanan_karar = uygulanan_baslik = None
                await asyncio.sleep(KAPALI_ARALIGI)
                continue
            if spotify_acik is not True:
                kaydet("Spotify açık, izleniyor")
                spotify_acik = True

            # --- Karar ver ---
            if medya is None:
                karar = "?"                    # Bilgi eksik, karar verme
            else:
                sarki, sanatci, _ = medya
                karar = karar_ver(baslik, sarki, sanatci)

            # --- Aynı karar üst üste kaç kez geldi? ---
            if karar == aday_karar:
                aday_sayisi += 1
            else:
                aday_karar = karar
                aday_sayisi = 1

            if aday_sayisi < GEREKEN_TEKRAR or karar == "?":
                await asyncio.sleep(KONTROL_ARALIGI)
                continue                       # Henüz emin değiliz, bir şey yapma

            if (karar, baslik) != (uygulanan_karar, uygulanan_baslik):   # Karar YA DA şarkı değiştiyse yaz
                kaydet(f"{karar}: {baslik!r}")
                uygulanan_karar = karar
                uygulanan_baslik = baslik

            # --- Kararı uygula ---
            if karar == "REKLAM":
                oturumlar = spotify_ses_oturumlari()
                if biz_kistik:
                    sessize_al(oturumlar, True)   # Reklamda yeni ses kaynağı açıldıysa onu da kıs
                elif oturumlar and sessiz_mi(oturumlar):
                    pass                          # Sen zaten sessize almışsın, dokunma
                elif oturumlar:
                    sessize_al(oturumlar, True)
                    biz_kistik = True
                    kaydet("  -> Spotify sessize alındı")

            elif karar in ("ŞARKI", "PODCAST"):
                if biz_kistik:
                    sessize_al(spotify_ses_oturumlari(), False)
                    biz_kistik = False
                    kaydet("  -> Ses geri açıldı")

            # DURDU: hiçbir şey yapma (reklamı duraklatıp başlatınca ses bir an bile açılmasın)

            await asyncio.sleep(KONTROL_ARALIGI)

    finally:                                   # Ctrl+C ya da hata: kıstığımız sesi geri aç
        faulthandler.cancel_dump_traceback_later()
        if biz_kistik:
            sessize_al(spotify_ses_oturumlari(), False)
            kaydet("  -> Program kapanırken ses geri açıldı")


# ---------------------------------------------------------------------------
# 5. BAŞLATMA
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(ana_dongu())
    except KeyboardInterrupt:
        kaydet("=== Reklam susturucu kapatıldı ===")
