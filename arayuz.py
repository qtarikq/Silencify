"""
Reklam susturucunun penceresi (PySide6).

Pencere sadece GÖSTERİR: hangi ekranın görüneceğini dışarıdan söylerler
(durumu_goster). Motoru çalıştırmak/durdurmak bu dosyanın işi değildir.

5 (+1) ekran: KAPALI, SPOTIFY_BEKLENIYOR, ŞARKI, PODCAST, DURDU, REKLAM.
Ekran değişince bant ve çerçeve renkleri yumuşakça (animasyonla) değişir.
"""

from PySide6.QtCore import QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

GENISLIK, YUKSEKLIK = 260, 290
GECIS_SURESI = 450          # Ekranlar arası renk geçişi (milisaniye)

# Windows'un kendi simge yazı tipi (Windows 11: Segoe Fluent Icons, Windows 10: Segoe MDL2 Assets)
SIMGE_FONTU = "Segoe Fluent Icons"
SIMGE = {
    "guc": "", "kum_saati": "", "kalkan": "", "nota": "",
    "mikrofon": "", "duraklat": "", "sessiz": "",
}

# Her ekranın görünümü: renkler ve yazılar (tasarımdaki 5 ekran)
EKRANLAR = {
    "KAPALI": dict(
        cerceve="#888780", bant="#444441", simge="guc", simge_renk="#B4B2A9",
        baslik="Kapalı", baslik_renk="#F1EFE8", alt="Reklamlar susturulmuyor", alt_renk="#B4B2A9",
        etiket="Şu an çalan", sarki_renk="#D3D1C7", dugme="Başlat"),
    "SPOTIFY_BEKLENIYOR": dict(
        cerceve="#7F77DD", bant="#3C3489", simge="kum_saati", simge_renk="#AFA9EC",
        baslik="Spotify bekleniyor", baslik_renk="#EEEDFE",
        alt="Spotify açılınca kendiliğinden başlar", alt_renk="#CECBF6",
        etiket="Şu an çalan", sarki_renk="#888780", dugme="Durdur"),
    "ŞARKI": dict(
        cerceve="#1D9E75", bant="#085041", simge="kalkan", simge_renk="#5DCAA5",
        baslik="Açık", baslik_renk="#E1F5EE", alt="Reklam bekleniyor", alt_renk="#9FE1CB",
        etiket="Şu an çalan", sarki_renk="#F1EFE8", dugme="Durdur"),
    "PODCAST": dict(
        cerceve="#1D9E75", bant="#085041", simge="kalkan", simge_renk="#5DCAA5",
        baslik="Açık", baslik_renk="#E1F5EE", alt="Reklam bekleniyor", alt_renk="#9FE1CB",
        etiket="Şu an dinlenen", sarki_renk="#F1EFE8", dugme="Durdur"),
    "DURDU": dict(
        cerceve="#378ADD", bant="#0C447C", simge="duraklat", simge_renk="#85B7EB",
        baslik="Duraklatıldı", baslik_renk="#E6F1FB",
        alt="Koruma açık, müzik bekleniyor", alt_renk="#B5D4F4",
        etiket="Son çalan", sarki_renk="#B4B2A9", dugme="Durdur"),
    "REKLAM": dict(
        cerceve="#D85A30", bant="#712B13", simge="sessiz", simge_renk="#F0997B",
        baslik="Reklam", baslik_renk="#FAECE7", alt="Spotify'ın sesi kısıldı", alt_renk="#F5C4B3",
        etiket="Şu an çalan", sarki_renk="#F1EFE8", dugme="Durdur"),
}
ETIKET_SIMGESI = {"ŞARKI": "nota", "PODCAST": "mikrofon", "DURDU": "duraklat", "REKLAM": "sessiz"}

ZEMIN = QColor("#2C2C2A")
SOLUK = "#888780"


def _karistir(renk1, renk2, oran):
    """İki renk arasında 'oran' (0..1) kadar ilerlemiş rengi döndürür (animasyon için)."""
    a, b = QColor(renk1), QColor(renk2)
    return QColor(round(a.red() + (b.red() - a.red()) * oran),
                  round(a.green() + (b.green() - a.green()) * oran),
                  round(a.blue() + (b.blue() - a.blue()) * oran))


class Pencere(QWidget):
    """Reklam susturucunun küçük, sabit boyutlu, çerçevesiz penceresi."""

    dugmeye_basildi = Signal()      # Başlat/Durdur düğmesine basılınca
    kapatma_istendi = Signal()      # × düğmesine basılınca (ne yapılacağına dışarısı karar verir)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reklam susturucu")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)     # Yuvarlak köşeler için
        self.setFixedSize(GENISLIK, YUKSEKLIK)

        if SIMGE_FONTU not in QFontDatabase.families():
            globals()["SIMGE_FONTU"] = "Segoe MDL2 Assets"

        self._durum = "KAPALI"
        self._cerceve_renk = QColor(EKRANLAR["KAPALI"]["cerceve"])
        self._bant_renk = QColor(EKRANLAR["KAPALI"]["bant"])
        self._eski_cerceve = self._yeni_cerceve = QColor(self._cerceve_renk)   # Animasyonun başlangıç/bitiş renkleri
        self._eski_bant = self._yeni_bant = QColor(self._bant_renk)
        self._surukleme = None

        self._animasyon = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=GECIS_SURESI)
        self._animasyon.valueChanged.connect(self._animasyon_adimi)

        self._arayuzu_kur()
        self.durumu_goster("KAPALI")

    # -----------------------------------------------------------------------
    # DIŞARIYA AÇIK: hangi ekran gösterilsin?
    # -----------------------------------------------------------------------
    def durumu_goster(self, durum, baslik=None):
        """Ekranı 'durum'a göre değiştirir. Durum değiştiyse renkler animasyonla geçer."""
        ekran = EKRANLAR.get(durum, EKRANLAR["KAPALI"])
        if durum != self._durum:
            self._eski_cerceve, self._eski_bant = QColor(self._cerceve_renk), QColor(self._bant_renk)
            self._yeni_cerceve, self._yeni_bant = QColor(ekran["cerceve"]), QColor(ekran["bant"])
            self._animasyon.stop()
            self._animasyon.start()
        self._durum = durum

        self.simge.setText(SIMGE[ekran["simge"]])
        self.simge.setStyleSheet(f"color:{ekran['simge_renk']}; font-family:'{SIMGE_FONTU}'; font-size:24px;")
        self.baslik.setText(ekran["baslik"])
        self.baslik.setStyleSheet(f"color:{ekran['baslik_renk']}; font-size:18px; font-weight:600;")
        self.alt_yazi.setText(ekran["alt"])
        self.alt_yazi.setStyleSheet(f"color:{ekran['alt_renk']}; font-size:12px;")

        etiket_simgesi = ETIKET_SIMGESI.get(durum)
        self.etiket_simge.setText(SIMGE[etiket_simgesi] if etiket_simgesi else "")
        self.etiket_simge.setVisible(bool(etiket_simgesi))
        self.etiket.setText(ekran["etiket"])

        self.sarki.setText(self._sarki_metni(durum, baslik))
        self.sarki.setStyleSheet(f"color:{ekran['sarki_renk']}; font-size:14px;")

        self.dugme.setText(ekran["dugme"])
        self.dugme.setProperty("dolu", durum == "KAPALI")      # Başlat dolu yeşil, Durdur çerçeveli
        self.dugme.style().unpolish(self.dugme)
        self.dugme.style().polish(self.dugme)

    # -----------------------------------------------------------------------
    # İÇ İŞLER
    # -----------------------------------------------------------------------
    def _sarki_metni(self, durum, baslik):
        if durum == "KAPALI":
            return "—"
        if durum == "SPOTIFY_BEKLENIYOR":
            return "Spotify kapalı"
        if durum == "REKLAM":
            return "Reklam"
        if not baslik:
            return "—"
        metin = baslik.replace(" - ", " — ", 1)            # "Sanatçı - Şarkı" -> "Sanatçı — Şarkı"
        return self.sarki.fontMetrics().elidedText(metin, Qt.ElideRight, GENISLIK - 40)

    def _arayuzu_kur(self):
        self.setStyleSheet("""
            QLabel { background: transparent; }
            QPushButton#pencere_dugmesi { color:#B4B2A9; background:transparent; border:none; font-size:12px; }
            QPushButton#pencere_dugmesi:hover { color:#F1EFE8; }
            QPushButton#ana_dugme { color:#D3D1C7; background:transparent; border:1px solid #888780;
                                    border-radius:8px; padding:9px; font-size:14px; }
            QPushButton#ana_dugme:hover { background:#3a3a37; }
            QPushButton#ana_dugme[dolu="true"] { color:#04342C; background:#1D9E75; border:none; font-weight:600; }
            QPushButton#ana_dugme[dolu="true"]:hover { background:#25b385; }
        """)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(2, 2, 2, 2)              # Çerçeve kalınlığı kadar boşluk
        duzen.setSpacing(0)

        # --- Başlık çubuğu (sürüklenebilir) ---
        cubuk = QHBoxLayout()
        cubuk.setContentsMargins(12, 6, 6, 6)
        ad = QLabel("Reklam susturucu")
        ad.setStyleSheet("color:#B4B2A9; font-size:12px;")
        kucult = QPushButton(chr(0xE921)); kucult.setObjectName("pencere_dugmesi")
        kapat = QPushButton(chr(0xE8BB)); kapat.setObjectName("pencere_dugmesi")
        for d in (kucult, kapat):
            d.setFont(QFont(SIMGE_FONTU, 8))
            d.setFixedSize(28, 22)
            d.setCursor(Qt.PointingHandCursor)
        kucult.clicked.connect(self.showMinimized)
        kapat.clicked.connect(self.kapatma_istendi.emit)
        cubuk.addWidget(ad); cubuk.addStretch(); cubuk.addWidget(kucult); cubuk.addWidget(kapat)
        duzen.addLayout(cubuk)

        # --- Renkli bant ---
        self.bant = QWidget()
        self.bant.setFixedHeight(118)
        bant_duzen = QVBoxLayout(self.bant)
        bant_duzen.setContentsMargins(10, 16, 10, 16)
        bant_duzen.setSpacing(2)
        self.simge, self.baslik, self.alt_yazi = QLabel(), QLabel(), QLabel()
        for etiket in (self.simge, self.baslik, self.alt_yazi):
            etiket.setAlignment(Qt.AlignCenter)
            bant_duzen.addWidget(etiket)
        duzen.addWidget(self.bant)

        # --- Alt kısım ---
        alt = QVBoxLayout()
        alt.setContentsMargins(16, 16, 16, 16)
        alt.setSpacing(2)
        etiket_satiri = QHBoxLayout()
        etiket_satiri.addStretch()
        self.etiket_simge = QLabel()
        self.etiket_simge.setStyleSheet(f"color:{SOLUK}; font-family:'{SIMGE_FONTU}'; font-size:11px;")
        self.etiket = QLabel()
        self.etiket.setStyleSheet(f"color:{SOLUK}; font-size:12px;")
        etiket_satiri.addWidget(self.etiket_simge); etiket_satiri.addSpacing(4); etiket_satiri.addWidget(self.etiket)
        etiket_satiri.addStretch()
        alt.addLayout(etiket_satiri)
        self.sarki = QLabel()
        self.sarki.setAlignment(Qt.AlignCenter)
        alt.addWidget(self.sarki)
        alt.addSpacing(16)
        self.dugme = QPushButton()
        self.dugme.setObjectName("ana_dugme")
        self.dugme.setCursor(Qt.PointingHandCursor)
        self.dugme.clicked.connect(self.dugmeye_basildi.emit)
        alt.addWidget(self.dugme)
        alt.addStretch()
        duzen.addLayout(alt)

    def _animasyon_adimi(self, oran):
        """Animasyonun her karesinde (saniyede ~60 kez) renkleri biraz ilerletir."""
        self._cerceve_renk = _karistir(self._eski_cerceve, self._yeni_cerceve, oran)
        self._bant_renk = _karistir(self._eski_bant, self._yeni_bant, oran)
        self.update()

    def paintEvent(self, _):
        """Pencerenin zeminini, renkli bandı ve çerçeveyi çizer."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        dis = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.NoPen)
        p.setBrush(ZEMIN)
        p.drawRoundedRect(dis, 12, 12)
        bant = QRectF(self.bant.geometry())
        p.setBrush(self._bant_renk)
        p.drawRect(bant)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(self._cerceve_renk, 2))
        p.drawRoundedRect(dis, 12, 12)

    # --- Çerçevesiz pencereyi başlık çubuğundan sürükleyebilmek için ---
    def mousePressEvent(self, olay):
        if olay.button() == Qt.LeftButton and olay.position().y() < 34:
            self._surukleme = olay.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, olay):
        if self._surukleme is not None:
            self.move(olay.globalPosition().toPoint() - self._surukleme)

    def mouseReleaseEvent(self, _):
        self._surukleme = None


# ---------------------------------------------------------------------------
# SORU PENCERESİ (× düğmesi ve ilk açılış sorusu için)
# ---------------------------------------------------------------------------
class SoruPenceresi(QDialog):
    """
    Ana pencereyle aynı görünümde küçük bir soru penceresi.
    secenekler: [(anahtar, düğme yazısı, vurgulu_mu), ...]
    Kullanımı:  soru = SoruPenceresi(...);  soru.exec();  soru.secim  -> seçilen anahtar (kapatılırsa None)
    """

    def __init__(self, ust, baslik, metin, secenekler, cerceve="#888780"):
        super().__init__(ust)
        self.secim = None
        self._cerceve = QColor(cerceve)
        self.setWindowTitle(baslik)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(GENISLIK + 20)
        self.setStyleSheet("""
            QLabel { background: transparent; }
            QPushButton { color:#D3D1C7; background:transparent; border:1px solid #888780;
                          border-radius:8px; padding:9px; font-size:13px; }
            QPushButton:hover { background:#3a3a37; }
            QPushButton[vurgulu="true"] { color:#04342C; background:#1D9E75; border:none; font-weight:600; }
            QPushButton[vurgulu="true"]:hover { background:#25b385; }
        """)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(20, 18, 20, 18)
        duzen.setSpacing(8)
        b = QLabel(baslik)
        b.setStyleSheet("color:#F1EFE8; font-size:16px; font-weight:600;")
        m = QLabel(metin)
        m.setWordWrap(True)
        m.setStyleSheet("color:#B4B2A9; font-size:12px;")
        duzen.addWidget(b)
        duzen.addWidget(m)
        duzen.addSpacing(6)
        for anahtar, yazi, vurgulu in secenekler:
            d = QPushButton(yazi)
            d.setProperty("vurgulu", vurgulu)
            d.setCursor(Qt.PointingHandCursor)
            d.clicked.connect(lambda _=False, a=anahtar: self._sec(a))
            duzen.addWidget(d)

    def _sec(self, anahtar):
        self.secim = anahtar
        self.accept()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        dis = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setBrush(ZEMIN)
        p.setPen(QPen(self._cerceve, 2))
        p.drawRoundedRect(dis, 12, 12)


# ---------------------------------------------------------------------------
# TEPSİ SİMGESİ: durumun renginde, ortasında durumun simgesi olan küçük kare
# ---------------------------------------------------------------------------
def durum_simgesi(durum):
    """Bildirim alanı (saatin yanı) için durumun renginde bir simge çizer."""
    ekran = EKRANLAR.get(durum, EKRANLAR["KAPALI"])
    boyut = 64
    resim = QPixmap(boyut, boyut)
    resim.fill(Qt.transparent)
    p = QPainter(resim)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(ekran["cerceve"]))
    p.drawRoundedRect(QRectF(2, 2, boyut - 4, boyut - 4), 14, 14)
    font = QFont(SIMGE_FONTU if SIMGE_FONTU in QFontDatabase.families() else "Segoe MDL2 Assets")
    font.setPixelSize(36)
    p.setFont(font)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, 0, boyut, boyut), Qt.AlignCenter, SIMGE[ekran["simge"]])
    p.end()
    return QIcon(resim)
