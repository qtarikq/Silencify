"""
Arayüz PROTOTİPİ (deneme sürümü): motor bağlı DEĞİL, Spotify'a dokunmaz.

Pencere 5 ekran arasında kendiliğinden dolaşır (2,5 saniyede bir), böylece
tasarımı ve renk geçişlerini görebilirsin. Klavyeden de geçebilirsin:
  1 = Kapalı   2 = Spotify bekleniyor   3 = Şarkı   4 = Podcast   5 = Duraklatıldı   6 = Reklam
  Boşluk = otomatik dolaşmayı durdur/başlat     × = kapat

Çalıştırmak için:  python araclar/arayuz_prototip.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "silencify"))   # Uygulamanın modüllerini (motor, spotify...) bulabilmek için


import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from arayuz import Pencere

SIRA = [
    ("KAPALI", None),
    ("SPOTIFY_BEKLENIYOR", None),
    ("ŞARKI", "Mabel Matiz - Gel"),
    ("DURDU", "Mabel Matiz - Gel"),
    ("ŞARKI", "Mabel Matiz - Gel"),
    ("REKLAM", "ŞİMDİ DİNLE"),
    ("ŞARKI", "Gripin - Aşk Nereden Nereye"),
    ("PODCAST", "How to Trick Your Brain Into Liking Discipline"),
]
TUSLAR = {Qt.Key_1: SIRA[0], Qt.Key_2: SIRA[1], Qt.Key_3: SIRA[2], Qt.Key_4: SIRA[7],
          Qt.Key_5: SIRA[3], Qt.Key_6: SIRA[5]}


class Prototip(Pencere):
    def __init__(self):
        super().__init__()
        self.sira = 0
        self.zamanlayici = QTimer(self, interval=2500)
        self.zamanlayici.timeout.connect(self.sonraki)
        self.zamanlayici.start()
        self.kapatma_istendi.connect(self.close)

    def sonraki(self):
        self.sira = (self.sira + 1) % len(SIRA)
        self.durumu_goster(*SIRA[self.sira])

    def keyPressEvent(self, olay):
        if olay.key() in TUSLAR:
            self.durumu_goster(*TUSLAR[olay.key()])
        elif olay.key() == Qt.Key_Space:
            self.zamanlayici.stop() if self.zamanlayici.isActive() else self.zamanlayici.start()


if __name__ == "__main__":
    uygulama = QApplication(sys.argv)
    pencere = Prototip()
    pencere.show()
    sys.exit(uygulama.exec())
