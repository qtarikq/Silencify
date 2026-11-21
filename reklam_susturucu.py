"""
Silencify - terminal sürümü

Spotify'da reklam çalınca Spotify'ın sesini kısar, reklam bitince geri açar.
Sadece kendi kıstığı sesi açar; sen Spotify'ı kendin sessize aldıysan dokunmaz.
Reklam sırasında sesi sen açarsan o reklam arası boyunca dokunmaz.

Çalıştırmak için:  python reklam_susturucu.py
Durdurmak için:    Ctrl+C (kapanırken ses kısıksa geri açılır)

Asıl iş motor.py'de yapılır; bu dosya sadece motoru terminalde çalıştırır.
Pencereli sürüm için: python uygulama.py
"""

import asyncio

from kayit import kayitci_olustur
from motor import ReklamSusturucu
from surum import AD
from tek_kopya import zaten_calisiyor_mu
from yollar import SUSTURUCU_KAYDI

kayitci = kayitci_olustur("susturucu", SUSTURUCU_KAYDI)   # Ekrana + dosyaya (1 MB'ı geçince eskiler silinir)


if __name__ == "__main__":
    if zaten_calisiyor_mu():
        print(f"{AD} zaten çalışıyor (terminalde ya da pencerede). İkinci kopya açılmadı.")
        raise SystemExit
    motor = ReklamSusturucu(kaydet=kayitci.info)
    try:
        asyncio.run(motor.calis())
    except KeyboardInterrupt:
        pass       # Ctrl+C: motor kendi temizliğini (sesi açma, kayıt) zaten yaptı
