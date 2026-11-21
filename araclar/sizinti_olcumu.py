"""
Kaynak sızıntısı ölçümü.

Programın kullandığı okuma fonksiyonlarını tek tek TEKRAR_SAYISI kez çağırır,
her birinden önce ve sonra bu programın thread / handle / bellek kullanımını ölçer.
Hangi fonksiyon kaynak sızdırıyorsa onun satırında sayılar büyür.
Hiçbir şeyi değiştirmez: ses kısmaz, Spotify'a dokunmaz, sadece okur.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "silencify"))   # Uygulamanın modüllerini (motor, spotify...) bulabilmek için


import asyncio
import gc                                   # Çöp toplayıcı: kullanılmayan nesneleri temizlemek için

import psutil
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MedyaYoneticisi,
)

from gozlem import spotify_medya_bilgisi
from spotify import spotify_ana_pencere_basligi, spotify_ses_oturumlari
from spotify import spotify_medya_bilgisi as yeni_medya_bilgisi   # Düzeltilmiş hali

TEKRAR_SAYISI = 300
bu_program = psutil.Process()               # Kendimizi ölçüyoruz


def kaynaklar():
    """Bu programın şu anki thread sayısı, handle sayısı ve belleği (MB)."""
    gc.collect()                            # Önce çöpleri topla, sadece gerçekten tutulanlar kalsın
    return (bu_program.num_threads(),
            bu_program.num_handles(),
            bu_program.memory_info().rss / 1024 / 1024)


def rapor(ad, once, sonra):
    print(f"{ad:<42} thread {once[0]:>5} -> {sonra[0]:<5} (+{sonra[0] - once[0]:<4})  "
          f"handle {once[1]:>6} -> {sonra[1]:<6} (+{sonra[1] - once[1]:<5})  "
          f"bellek {once[2]:6.1f} -> {sonra[2]:6.1f} MB")


async def ana():
    print(f"Her fonksiyon {TEKRAR_SAYISI} kez çağrılıyor...\n")

    # 1. Pencere başlığı (win32gui + psutil)
    once = kaynaklar()
    for _ in range(TEKRAR_SAYISI):
        spotify_ana_pencere_basligi()
    rapor("1. Pencere başlığı", once, kaynaklar())

    # 2. Ses oturumları (pycaw)
    once = kaynaklar()
    for _ in range(TEKRAR_SAYISI):
        spotify_ses_oturumlari()
    rapor("2. Ses oturumları (pycaw)", once, kaynaklar())

    # 3. Medya bilgisi - şu anki yöntem: yöneticiyi HER SEFERİNDE baştan iste
    once = kaynaklar()
    for _ in range(TEKRAR_SAYISI):
        await spotify_medya_bilgisi()
    rapor("3. Medya bilgisi (yönetici her sefer yeni)", once, kaynaklar())

    # 4. Medya bilgisi - alternatif: yöneticiyi BİR KERE iste, tekrar kullan
    yonetici = await MedyaYoneticisi.request_async()
    once = kaynaklar()
    for _ in range(TEKRAR_SAYISI):
        for oturum in yonetici.get_sessions():
            if "spotify" in oturum.source_app_user_model_id.lower():
                await oturum.try_get_media_properties_async()
                oturum.get_playback_info()
    rapor("4. Medya bilgisi (yönetici tek, tekrar)", once, kaynaklar())

    # 5. Düzeltilmiş program: bir turun okuma kısmı, UZUN_TEKRAR kez
    uzun_tekrar = 2000
    await yeni_medya_bilgisi()                # Yöneticiyi önceden iste (ilk seferlik maliyet sayılmasın)
    once = kaynaklar()
    for _ in range(uzun_tekrar):
        spotify_ana_pencere_basligi()
        await yeni_medya_bilgisi()
    rapor(f"5. DÜZELTİLMİŞ tur x{uzun_tekrar}", once, kaynaklar())


if __name__ == "__main__":
    asyncio.run(ana())
