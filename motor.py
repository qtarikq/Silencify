"""
Silencify'ın MOTORU (beyni).

ReklamSusturucu sınıfı bir TV kumandası gibidir:
- Düğmeleri:  calis()  ve  durdur()
- Ekranı:     durum, baslik, ses_kisik   (arayüz bunları okuyarak hangi ekranı göstereceğini bilir)

Kullanımı:
    motor = ReklamSusturucu(kaydet=print)
    asyncio.run(motor.calis())        # durdur() çağrılana kadar çalışır
    motor.durum                       # "KAPALI", "SPOTIFY_BEKLENIYOR", "ŞARKI", "PODCAST", "DURDU" ya da "REKLAM"
"""

import asyncio                     # async/await ile bekleme işleri için
import faulthandler                # Takılma olursa programın nerede beklediğini yazmak için
from datetime import datetime      # Saati yazmak için

from kayit import buyukse_kenara_al
from kural import karar_ver
from surum import AD
from spotify import (
    medya_yoneticisini_sifirla,
    sessiz_mi,
    sessize_al,
    spotify_ana_pencere_basligi,
    spotify_medya_bilgisi,
    spotify_ses_oturumlari,
)
from yollar import KARA_KUTU, KISTIM_NOTU

# ---------------------------------------------------------------------------
# AYARLAR
# ---------------------------------------------------------------------------
KARA_KUTU_DOSYASI = KARA_KUTU
KONTROL_ARALIGI = 1          # Spotify açıkken kaç saniyede bir bakılacak
KAPALI_ARALIGI = 5           # Spotify kapalıyken kaç saniyede bir bakılacak
GEREKEN_TEKRAR = 2           # Sesi kısmak için REKLAM kararı kaç kontrol üst üste gelmeli
MEDYA_ZAMAN_SINIRI = 3       # Windows medya bilgisi için en fazla kaç saniye beklenecek
SURE_SINIRI = 10             # Bir tur bundan uzun sürerse kara kutuya yaz (saniye)
OTURUM_YENILEME_ARALIGI = 5  # Reklam boyunca kaç turda bir Spotify'ın ses kaynaklarına bakılacak


class ReklamSusturucu:
    """Spotify'da reklam çalınca Spotify'ın sesini kısan, reklam bitince açan motor."""

    # -----------------------------------------------------------------------
    # Kurulum: kumandayı eline aldığın an
    # -----------------------------------------------------------------------
    def __init__(self, kaydet=None):
        # 'kaydet' dışarıdan verilir: terminal sürümü dosyaya+ekrana yazar, arayüz başka bir şey yapabilir
        self.kaydet = kaydet or (lambda mesaj: None)

        # --- EKRAN: dışarıdan (arayüzden) okunabilen bilgiler ---
        self.calisiyor = False       # Motor açık mı?
        self.durum = "KAPALI"        # Arayüzde hangi ekran gösterilecek
        self.baslik = None           # Şu an (ya da en son) çalan şeyin başlığı
        self.ses_kisik = False       # Spotify'ı şu an BİZ mi sessize aldık?

        # --- İÇ HAFIZA: sadece motorun kendisi kullanır ---
        self._aday_karar = None      # En son görülen karar
        self._aday_sayisi = 0        # O karar kaç kontrol üst üste görüldü
        self._reklam_turu = 0        # Sessize aldığımızdan beri kaç tur geçti
        self._kistigimiz = set()     # Kıstığımız ses kaynaklarının kimlikleri
        self._serbest = False        # Bu reklam arasında sesi kullanıcı açtı mı?
        self._son_kayit = None       # En son kayda yazılan (karar, başlık): aynısını tekrar yazmamak için
        self._spotify_acik = None    # Spotify'ın en son açık/kapalı durumu: değişince kayda yazmak için

    # -----------------------------------------------------------------------
    # DÜĞMELER
    # -----------------------------------------------------------------------
    async def calis(self):
        """Motoru çalıştırır; durdur() çağrılana (ya da Ctrl+C'ye basılana) kadar döner."""
        self.calisiyor = True
        self.durum = "SPOTIFY_BEKLENIYOR"
        self.ses_kisik = KISTIM_NOTU.exists()     # Önceki çalışmadan not kaldıysa sesi biz kısmışız
        self._dongu = asyncio.get_running_loop()  # durdur() başka bir thread'den çağrılabilsin diye
        self._dur_isareti = asyncio.Event()       # durdur() bunu "kaldırınca" bekleme anında biter

        buyukse_kenara_al(KARA_KUTU_DOSYASI)      # Kara kutu 1 MB'ı geçtiyse eskisini kenara al
        kara_kutu = open(KARA_KUTU_DOSYASI, "a", encoding="utf-8")
        kara_kutu.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} motor başladı ---\n")
        kara_kutu.flush()

        self.kaydet(f"=== {AD} başladı ({datetime.now():%d.%m.%Y}) ===")
        if self.ses_kisik:
            self.kaydet('Önceki çalışmadan kalan "kıstım" notu bulundu, ses sırası gelince açılacak')

        try:
            while self.calisiyor:
                faulthandler.dump_traceback_later(SURE_SINIRI, file=kara_kutu)   # Alarmı kur
                try:
                    bekleme = await self.bir_tur()
                except Exception as hata:
                    self.kaydet(f"HATA: {hata}")
                    bekleme = KONTROL_ARALIGI
                finally:
                    faulthandler.cancel_dump_traceback_later()                   # Alarmı iptal et
                await self._bekle(bekleme)
        finally:                                  # Durduruldu, Ctrl+C ya da hata: kıstığımız sesi aç
            faulthandler.cancel_dump_traceback_later()
            kara_kutu.close()
            if self.ses_kisik:
                if self._sesi_ac():
                    self.kaydet("  -> Program kapanırken ses geri açıldı")
                else:
                    self.kaydet('  -> Spotify kapalı, ses açılamadı; "kıstım" notu bir sonraki açılış için bırakıldı')
            self.calisiyor = False
            self.durum = "KAPALI"
            self.kaydet(f"=== {AD} kapatıldı ===")

    def durdur(self):
        """
        Motoru durdurur (kıstığı sesi açarak). Arayüzden, yani BAŞKA bir thread'den
        çağrılabilir: bekleme anında kesilir, motor beklemesini bitirmeden durur.
        """
        self.calisiyor = False
        dongu = getattr(self, "_dongu", None)
        if dongu is not None and not dongu.is_closed():
            dongu.call_soon_threadsafe(self._dur_isareti.set)   # Motorun kendi thread'ine "dur" de

    async def _bekle(self, saniye):
        """'saniye' kadar bekler; durdur() çağrılırsa beklemeyi hemen bitirir."""
        try:
            await asyncio.wait_for(self._dur_isareti.wait(), saniye)
        except asyncio.TimeoutError:
            pass                                  # Süre doldu: normal, bir sonraki tura geç

    # -----------------------------------------------------------------------
    # BİR TUR: bak, karar ver, uygula. Bir sonraki tura kadar kaç saniye bekleneceğini döndürür.
    # -----------------------------------------------------------------------
    async def bir_tur(self):
        baslik = spotify_ana_pencere_basligi()
        medya = await self._medya_oku()

        # --- Spotify kapalı mı? ---
        if baslik is None and medya is None:
            if self._spotify_acik is not False:
                self.kaydet("Spotify kapalı, bekleniyor...")
                self._spotify_acik = False
            self.durum = "SPOTIFY_BEKLENIYOR"
            # ses_kisik'i UNUTMUYORUZ: Windows Spotify'ın sessiz ayarını hatırlayabilir;
            # Spotify yeniden açılıp şarkı çalınca sesi biz açacağız.
            self._aday_karar = self._son_kayit = None
            return KAPALI_ARALIGI
        if self._spotify_acik is not True:
            self.kaydet("Spotify açık, izleniyor")
            self._spotify_acik = True

        # --- Karar ver ---
        if medya is None:
            karar = "?"                           # Bilgi eksik, karar verme
        else:
            sarki, sanatci, _ = medya
            karar = karar_ver(baslik, sarki, sanatci)

        # --- Aynı karar üst üste kaç kez geldi? ---
        if karar == self._aday_karar:
            self._aday_sayisi += 1
        else:
            self._aday_karar = karar
            self._aday_sayisi = 1

        # Sesi KISMAK için kararın üst üste GEREKEN_TEKRAR kez gelmesini bekle (yanlışlıkla kısmayalım).
        # Sesi AÇMAK için bekleme: reklam bitti dendiği an şarkının başı kaçmasın.
        if karar == "?" or (karar == "REKLAM" and self._aday_sayisi < GEREKEN_TEKRAR):
            return KONTROL_ARALIGI                # Henüz emin değiliz, bir şey yapma

        # --- Ekranı güncelle (karar YA DA şarkı değiştiyse kayda yaz) ---
        if (karar, baslik) != self._son_kayit:
            self.kaydet(f"{karar}: {baslik!r}")
            self._son_kayit = (karar, baslik)
        self.durum = karar
        if karar != "DURDU":                      # Duraklatınca "son çalan" ekranda kalsın
            self.baslik = baslik

        # --- Kararı uygula ---
        if karar == "REKLAM":
            self._reklam_sirasinda()
        elif karar in ("ŞARKI", "PODCAST"):
            self._serbest = False                 # Reklam arası bitti: bir sonraki reklamda yine kısacağız
            if self.ses_kisik and self._sesi_ac():    # Ses kaynağı yoksa bir sonraki turda tekrar dener
                self.ses_kisik = False
                self.kaydet("  -> Ses geri açıldı")
        # DURDU: hiçbir şey yapma (reklamı duraklatıp başlatınca ses bir an bile açılmasın)

        return KONTROL_ARALIGI

    # -----------------------------------------------------------------------
    # YARDIMCI İŞLER (sadece motorun içinden çağrılır)
    # -----------------------------------------------------------------------
    def _reklam_sirasinda(self):
        """REKLAM kararı onaylandığında her tur çağrılır."""
        if self._serbest:
            return                                # Bu reklam arasında sesi sen açtın, dokunma

        if not self.ses_kisik:
            oturumlar = spotify_ses_oturumlari()
            if oturumlar and sessiz_mi(oturumlar):
                return                            # Sen zaten sessize almışsın, dokunma
            self._kistigimiz = self._sessize_al()
            if self._kistigimiz:
                self.ses_kisik = True
                self._reklam_turu = 0
                self.kaydet("  -> Spotify sessize alındı")
            return

        self._reklam_turu += 1
        if self._reklam_turu % OTURUM_YENILEME_ARALIGI != 0:
            return                                # Her saniye değil, 5 turda bir bak

        oturumlar = spotify_ses_oturumlari()
        if not self._kistigimiz:                  # Önceki çalışmadan kalan not: şu an sessiz olanlar bizimdir
            self._kistigimiz = {o.InstanceIdentifier for o in oturumlar if o.SimpleAudioVolume.GetMute()}
        bizimkiler = [o for o in oturumlar if o.InstanceIdentifier in self._kistigimiz]
        yeniler = [o for o in oturumlar if o.InstanceIdentifier not in self._kistigimiz]

        if any(not o.SimpleAudioVolume.GetMute() for o in bizimkiler):
            # Kıstığımız bir kaynağın sesi açılmış: bunu sen yaptın, reklamı duymak istiyorsun.
            # Kıstığımız DİĞER kaynakları da aç (yoksa yarım kalır, sonra da açan olmaz).
            sessize_al(bizimkiler, False)
            self._serbest = True
            self.ses_kisik = False
            self._kistigimiz = set()
            KISTIM_NOTU.unlink(missing_ok=True)
            self.kaydet("  -> Sesi sen açtın: bu reklam arası boyunca dokunmuyorum")
        elif yeniler:
            # Spotify reklam sırasında yeni bir ses kaynağı açmış: onu da kıs
            sessize_al(yeniler, True)
            self._kistigimiz |= {o.InstanceIdentifier for o in yeniler}

    def _sessize_al(self):
        """Spotify'ı sessize alır, 'kıstım' notu bırakır. Kıstığı kaynakların kimliklerini döndürür."""
        oturumlar = spotify_ses_oturumlari()
        if not oturumlar:
            return set()
        sessize_al(oturumlar, True)
        KISTIM_NOTU.write_text(f"{datetime.now():%H:%M:%S}", encoding="utf-8")
        return {oturum.InstanceIdentifier for oturum in oturumlar}

    def _sesi_ac(self):
        """Spotify'ın sesini açar, 'kıstım' notunu siler. Ses kaynağı yoksa (Spotify kapalı) False."""
        oturumlar = spotify_ses_oturumlari()
        if not oturumlar:
            return False                          # Not kalsın: Spotify açılınca tekrar denenecek
        sessize_al(oturumlar, False)
        KISTIM_NOTU.unlink(missing_ok=True)
        self._kistigimiz = set()
        return True

    async def _medya_oku(self):
        """Medya bilgisini okur; Windows MEDYA_ZAMAN_SINIRI saniyede cevap vermezse None döndürür."""
        try:
            return await asyncio.wait_for(spotify_medya_bilgisi(), MEDYA_ZAMAN_SINIRI)
        except asyncio.TimeoutError:
            self.kaydet(f"UYARI: Medya bilgisi {MEDYA_ZAMAN_SINIRI} saniyede gelmedi, bu tur atlandı")
            medya_yoneticisini_sifirla()          # Bir sorun var: bir sonraki turda yenisini iste
            return None
        except Exception:
            medya_yoneticisini_sifirla()
            raise                                 # Hatayı calis()'a ilet (orada kaydediliyor)
