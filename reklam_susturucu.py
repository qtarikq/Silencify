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

from kural import karar_ver                                         # REKLAM / ŞARKI / PODCAST / DURDU
from spotify import (                                               # Spotify ve Windows ile konuşma
    medya_yoneticisini_sifirla,
    sessiz_mi,
    sessize_al,
    spotify_ana_pencere_basligi,
    spotify_medya_bilgisi,
    spotify_ses_oturumlari,
)
from yollar import KARA_KUTU, KISTIM_NOTU, SUSTURUCU_KAYDI          # Dosya yolları

# ---------------------------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------------------------
KAYIT_DOSYASI = SUSTURUCU_KAYDI      # Yollar yollar.py'de, programın kendi konumuna göre
KARA_KUTU_DOSYASI = KARA_KUTU

KONTROL_ARALIGI = 1        # Spotify açıkken kaç saniyede bir bakılacak
KAPALI_ARALIGI = 5         # Spotify kapalıyken kaç saniyede bir bakılacak
GEREKEN_TEKRAR = 2         # Bir karar kaç kontrol üst üste aynı olursa uygulanacak
MEDYA_ZAMAN_SINIRI = 3     # Windows medya bilgisi için en fazla kaç saniye beklenecek
SURE_SINIRI = 10           # Bir tur bundan uzun sürerse kara kutuya yaz (saniye)
OTURUM_YENILEME_ARALIGI = 5  # Reklam boyunca kaç turda bir Spotify'ın ses kaynakları yeniden kısılacak


# ---------------------------------------------------------------------------
# 3. FONKSİYONLAR
# ---------------------------------------------------------------------------
def kaydet(mesaj):
    """Mesajı saatiyle birlikte hem ekrana hem kayıt dosyasına yazar."""
    satir = f"{datetime.now():%H:%M:%S}  {mesaj}"
    print(satir)
    with open(KAYIT_DOSYASI, "a", encoding="utf-8") as dosya:
        dosya.write(satir + "\n")


def spotify_sessize_al():
    """
    Spotify'ı sessize alır ve diske 'kıstım' notu bırakır.
    Kıstığı ses kaynaklarının kimliklerini (küme olarak) döndürür; ses kaynağı yoksa boş küme.
    """
    oturumlar = spotify_ses_oturumlari()
    if not oturumlar:
        return set()
    sessize_al(oturumlar, True)
    KISTIM_NOTU.write_text(f"{datetime.now():%H:%M:%S}", encoding="utf-8")
    return {oturum.InstanceIdentifier for oturum in oturumlar}


def spotify_sesini_ac():
    """Spotify'ın sesini açar ve 'kıstım' notunu siler. Ses kaynağı yoksa (Spotify kapalı) False döndürür."""
    oturumlar = spotify_ses_oturumlari()
    if not oturumlar:
        return False                          # Not kalsın: Spotify açılınca tekrar denenecek
    sessize_al(oturumlar, False)
    KISTIM_NOTU.unlink(missing_ok=True)       # Notu sil (zaten yoksa hata verme)
    return True


async def medya_bilgisi_zaman_sinirli():
    """Medya bilgisini okur; Windows MEDYA_ZAMAN_SINIRI saniyede cevap vermezse None döndürür."""
    try:
        return await asyncio.wait_for(spotify_medya_bilgisi(), MEDYA_ZAMAN_SINIRI)
    except asyncio.TimeoutError:
        kaydet(f"UYARI: Medya bilgisi {MEDYA_ZAMAN_SINIRI} saniyede gelmedi, bu tur atlandı")
        medya_yoneticisini_sifirla()          # Bir sorun var: bir sonraki turda yenisini iste
        return None
    except Exception:
        medya_yoneticisini_sifirla()          # Bir sorun var: bir sonraki turda yenisini iste
        raise                                 # Hatayı ana döngüye ilet (orada kaydediliyor)


# ---------------------------------------------------------------------------
# 4. ANA DÖNGÜ
# ---------------------------------------------------------------------------
async def ana_dongu():
    biz_kistik = KISTIM_NOTU.exists()   # Spotify'ı BİZ mi sessize aldık? (önceki çalışmadan not kaldıysa evet)
    aday_karar = None           # En son görülen karar
    aday_sayisi = 0             # O karar kaç kontrol üst üste görüldü
    uygulanan_karar = None      # En son uygulanan (onaylanmış) karar
    uygulanan_baslik = None     # O karar verilirken pencere başlığı neydi (kayda yazmak için)
    spotify_acik = None         # Spotify'ın açık/kapalı durumu (değişince yazmak için)
    reklam_turu = 0             # Sessize aldığımızdan beri kaç tur geçti
    kistigimiz = set()          # Kıstığımız ses kaynaklarının kimlikleri
    serbest = False             # Bu reklam arasında sesi kullanıcı açtı mı? (açtıysa dokunmuyoruz)

    kara_kutu = open(KARA_KUTU_DOSYASI, "a", encoding="utf-8")
    kara_kutu.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} reklam_susturucu başladı ---\n")
    kara_kutu.flush()

    kaydet("=== Reklam susturucu başladı (durdurmak için Ctrl+C) ===")
    if biz_kistik:
        kaydet('Önceki çalışmadan kalan "kıstım" notu bulundu, ses sırası gelince açılacak')

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
                # biz_kistik'i UNUTMUYORUZ: Windows Spotify'ın sessiz ayarını hatırlayabilir;
                # Spotify yeniden açılıp şarkı çalınca sesi biz açacağız.
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

            # Sesi KISMAK için kararın üst üste GEREKEN_TEKRAR kez gelmesini bekle (yanlışlıkla kısmayalım).
            # Sesi AÇMAK için bekleme: reklam bitti dendiği an şarkının başı kaçmasın.
            if karar == "?" or (karar == "REKLAM" and aday_sayisi < GEREKEN_TEKRAR):
                await asyncio.sleep(KONTROL_ARALIGI)
                continue                       # Henüz emin değiliz, bir şey yapma

            if (karar, baslik) != (uygulanan_karar, uygulanan_baslik):   # Karar YA DA şarkı değiştiyse yaz
                kaydet(f"{karar}: {baslik!r}")
                uygulanan_karar = karar
                uygulanan_baslik = baslik

            # --- Kararı uygula ---
            if karar == "REKLAM":
                if serbest:
                    pass                              # Bu reklam arasında sesi sen açtın, dokunma

                elif biz_kistik:
                    reklam_turu += 1
                    if reklam_turu % OTURUM_YENILEME_ARALIGI == 0:      # Her saniye değil, 5 turda bir bak
                        oturumlar = spotify_ses_oturumlari()
                        if not kistigimiz:            # Önceki çalışmadan kalan not: şu an sessiz olanlar bizimdir
                            kistigimiz = {o.InstanceIdentifier for o in oturumlar
                                          if o.SimpleAudioVolume.GetMute()}
                        bizimkiler = [o for o in oturumlar if o.InstanceIdentifier in kistigimiz]
                        yeniler = [o for o in oturumlar if o.InstanceIdentifier not in kistigimiz]

                        if any(not o.SimpleAudioVolume.GetMute() for o in bizimkiler):
                            # Kıstığımız bir kaynağın sesi açılmış: bunu sen yaptın, reklamı duymak istiyorsun.
                            # Kıstığımız DİĞER kaynakları da aç (yoksa yarım kalır, sonra da açan olmaz).
                            sessize_al(bizimkiler, False)
                            serbest = True
                            biz_kistik = False
                            kistigimiz = set()
                            KISTIM_NOTU.unlink(missing_ok=True)
                            kaydet("  -> Sesi sen açtın: bu reklam arası boyunca dokunmuyorum")
                        elif yeniler:
                            # Spotify reklam sırasında yeni bir ses kaynağı açmış: onu da kıs
                            sessize_al(yeniler, True)
                            kistigimiz |= {o.InstanceIdentifier for o in yeniler}

                else:
                    oturumlar = spotify_ses_oturumlari()
                    if oturumlar and sessiz_mi(oturumlar):
                        pass                          # Sen zaten sessize almışsın, dokunma
                    else:
                        kistigimiz = spotify_sessize_al()
                        if kistigimiz:
                            biz_kistik = True
                            reklam_turu = 0
                            kaydet("  -> Spotify sessize alındı")

            elif karar in ("ŞARKI", "PODCAST"):
                serbest = False                       # Reklam arası bitti: bir sonraki reklamda yine kısacağız
                if biz_kistik and spotify_sesini_ac():    # Ses kaynağı yoksa bir sonraki turda tekrar dener
                    biz_kistik = False
                    kistigimiz = set()
                    kaydet("  -> Ses geri açıldı")

            # DURDU: hiçbir şey yapma (reklamı duraklatıp başlatınca ses bir an bile açılmasın)

            await asyncio.sleep(KONTROL_ARALIGI)

    finally:                                   # Ctrl+C ya da hata: kıstığımız sesi geri aç
        faulthandler.cancel_dump_traceback_later()
        kara_kutu.close()                      # Açtığımız dosyayı kapat
        if biz_kistik:
            if spotify_sesini_ac():
                kaydet("  -> Program kapanırken ses geri açıldı")
            else:
                kaydet('  -> Spotify kapalı, ses açılamadı; "kıstım" notu bir sonraki açılış için bırakıldı')


# ---------------------------------------------------------------------------
# 5. BAŞLATMA
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(ana_dongu())
    except KeyboardInterrupt:
        kaydet("=== Reklam susturucu kapatıldı ===")
