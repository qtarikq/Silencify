"""
Uygulamanın bütün yazıları (Türkçe ve İngilizce).

Kullanımı:
    from dil import yazi
    yazi("menu_goster")                 # -> "Pencereyi göster" ya da "Show window"
    yazi("arka_plan_baslik", ad=AD)     # {ad} yerine AD yazılır

Bir yazıyı değiştirmek ya da yeni bir dil eklemek için sadece bu dosyaya bakman yeterli.
Her dilde AYNI anahtarlar olmalı: testler/test_dil.py bunu kontrol eder.
"""

import ctypes

DIL_ADLARI = {"tr": "Türkçe", "en": "English"}

YAZILAR = {
    "tr": {
        # --- Pencere: her durumun başlığı, alt yazısı, etiketi ve düğmesi ---
        "KAPALI.baslik": "Kapalı",
        "KAPALI.alt": "Reklamlar susturulmuyor",
        "KAPALI.etiket": "Şu an çalan",
        "KAPALI.dugme": "Başlat",
        "SPOTIFY_BEKLENIYOR.baslik": "Spotify bekleniyor",
        "SPOTIFY_BEKLENIYOR.alt": "Spotify açılınca kendiliğinden başlar",
        "SPOTIFY_BEKLENIYOR.etiket": "Şu an çalan",
        "SPOTIFY_BEKLENIYOR.dugme": "Durdur",
        "ŞARKI.baslik": "Açık",
        "ŞARKI.alt": "Reklam bekleniyor",
        "ŞARKI.etiket": "Şu an çalan",
        "ŞARKI.dugme": "Durdur",
        "PODCAST.baslik": "Açık",
        "PODCAST.alt": "Reklam bekleniyor",
        "PODCAST.etiket": "Şu an dinlenen",
        "PODCAST.dugme": "Durdur",
        "DURDU.baslik": "Duraklatıldı",
        "DURDU.alt": "Koruma açık, müzik bekleniyor",
        "DURDU.etiket": "Son çalan",
        "DURDU.dugme": "Durdur",
        "REKLAM.baslik": "Reklam",
        "REKLAM.alt": "Spotify'ın sesi kısıldı",
        "REKLAM.etiket": "Şu an çalan",
        "REKLAM.dugme": "Durdur",
        "sarki_spotify_kapali": "Spotify kapalı",
        "sarki_reklam": "Reklam",
        "dil_dugmesi_ipucu": "Switch to English",

        # --- Saatin yanındaki simge: ipucu ve menü ---
        "ipucu.KAPALI": "Kapalı",
        "ipucu.SPOTIFY_BEKLENIYOR": "Spotify bekleniyor",
        "ipucu.ŞARKI": "Açık",
        "ipucu.PODCAST": "Açık",
        "ipucu.DURDU": "Duraklatıldı",
        "ipucu.REKLAM": "Reklam susturuldu",
        "menu_goster": "Pencereyi göster",
        "menu_baslat": "Başlat",
        "menu_durdur": "Durdur",
        "menu_otomatik": "Açılışta otomatik başlat",
        "menu_windows": "Windows açılınca başlat",
        "menu_kapat": "Tamamen kapat",

        # --- Soru pencereleri ve bildirimler ---
        "hosgeldin_baslik": "Hoş geldin!",
        "hosgeldin_metin": "Program açıldığında {ad} kendiliğinden başlasın mı? "
                           "Bunu sonradan saatin yanındaki simgeye sağ tıklayarak değiştirebilirsin.",
        "hosgeldin_evet": "Açılınca otomatik başlasın",
        "hosgeldin_hayir": "Ben elimle başlatayım",
        "kapat_baslik": "Kapatılsın mı?",
        "kapat_metin": "Arka planda çalışırsa reklamları susturmaya devam eder; "
                       "saatin yanındaki simgeden pencereyi tekrar açabilirsin.",
        "kapat_arka": "Arka planda çalışsın",
        "kapat_tamamen": "Uygulama tamamen kapansın",
        "kapat_vazgec": "Vazgeç",
        "arka_plan_baslik": "{ad} arka planda çalışıyor",
        "arka_plan_metin": "Pencereyi açmak için saatin yanındaki simgeye tıkla.",
        "windows_baslik": "Windows açılınca başlayacak",
        "windows_metin": "İpucu: Reklamların açılışta hemen susturulması için "
                         "'Açılışta otomatik başlat' seçeneğini de işaretleyebilirsin.",
        "zaten_baslik": "Zaten çalışıyor",
        "zaten_metin": "{ad} zaten açık (pencerede, saatin yanında ya da terminalde). "
                       "İkinci kopya açılmadı.",
        "tamam": "Tamam",
    },
    "en": {
        "KAPALI.baslik": "Off",
        "KAPALI.alt": "Ads are not being muted",
        "KAPALI.etiket": "Now playing",
        "KAPALI.dugme": "Start",
        "SPOTIFY_BEKLENIYOR.baslik": "Waiting for Spotify",
        "SPOTIFY_BEKLENIYOR.alt": "Starts by itself when Spotify opens",
        "SPOTIFY_BEKLENIYOR.etiket": "Now playing",
        "SPOTIFY_BEKLENIYOR.dugme": "Stop",
        "ŞARKI.baslik": "On",
        "ŞARKI.alt": "Waiting for ads",
        "ŞARKI.etiket": "Now playing",
        "ŞARKI.dugme": "Stop",
        "PODCAST.baslik": "On",
        "PODCAST.alt": "Waiting for ads",
        "PODCAST.etiket": "Now listening",
        "PODCAST.dugme": "Stop",
        "DURDU.baslik": "Paused",
        "DURDU.alt": "Protection on, waiting for music",
        "DURDU.etiket": "Last played",
        "DURDU.dugme": "Stop",
        "REKLAM.baslik": "Ad",
        "REKLAM.alt": "Spotify is muted",
        "REKLAM.etiket": "Now playing",
        "REKLAM.dugme": "Stop",
        "sarki_spotify_kapali": "Spotify is closed",
        "sarki_reklam": "Ad",
        "dil_dugmesi_ipucu": "Türkçeye geç",

        "ipucu.KAPALI": "Off",
        "ipucu.SPOTIFY_BEKLENIYOR": "Waiting for Spotify",
        "ipucu.ŞARKI": "On",
        "ipucu.PODCAST": "On",
        "ipucu.DURDU": "Paused",
        "ipucu.REKLAM": "Ad muted",
        "menu_goster": "Show window",
        "menu_baslat": "Start",
        "menu_durdur": "Stop",
        "menu_otomatik": "Start automatically on launch",
        "menu_windows": "Start with Windows",
        "menu_kapat": "Quit completely",

        "hosgeldin_baslik": "Welcome!",
        "hosgeldin_metin": "Should {ad} start by itself when the program opens? "
                           "You can change this later by right-clicking the icon next to the clock.",
        "hosgeldin_evet": "Start automatically on launch",
        "hosgeldin_hayir": "I'll start it myself",
        "kapat_baslik": "Close?",
        "kapat_metin": "If it keeps running in the background, it keeps muting ads; "
                       "you can open the window again from the icon next to the clock.",
        "kapat_arka": "Keep running in the background",
        "kapat_tamamen": "Close the app completely",
        "kapat_vazgec": "Cancel",
        "arka_plan_baslik": "{ad} is running in the background",
        "arka_plan_metin": "Click the icon next to the clock to open the window.",
        "windows_baslik": "Will start with Windows",
        "windows_metin": "Tip: To mute ads right from startup, "
                         "also check 'Start automatically on launch'.",
        "zaten_baslik": "Already running",
        "zaten_metin": "{ad} is already open (in a window, next to the clock or in a terminal). "
                       "A second copy was not opened.",
        "tamam": "OK",
    },
}

_secili = "tr"


def windows_dili():
    """Windows Türkçeyse "tr", değilse "en" döndürür (ilk açılıştaki varsayılan dil)."""
    try:
        kod = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return "tr" if kod & 0x3FF == 0x1F else "en"      # 0x1F = Windows'un Türkçe dil numarası
    except (AttributeError, OSError):
        return "en"


def dil_sec(dil):
    """Kullanılacak dili seçer ("tr" ya da "en"). Bilinmeyen bir dil gelirse İngilizce kullanılır."""
    global _secili
    _secili = dil if dil in YAZILAR else "en"


def secili_dil():
    return _secili


def diger_dil():
    """Dil düğmesine basınca geçilecek dil."""
    return "en" if _secili == "tr" else "tr"


def yazi(anahtar, **degerler):
    """Seçili dildeki yazıyı döndürür. {ad} gibi boşluklar 'degerler' ile doldurulur."""
    return YAZILAR[_secili][anahtar].format(**degerler)
